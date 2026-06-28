"""
================================================================================
budget_app/service.py - 비즈니스 로직 계층 (Business Logic Service Layer)
================================================================================
본 모듈은 가계부 프로그램의 핵심 연산 및 검증 규칙, 집계, 백업, CSV 내보내기/가져오기,
그리고 반복 거래 내역 발생 등 데이터의 조작과 흐름을 직접 지휘하는 서비스 클래스를 정의합니다.

[주요 비즈니스 논리 구현 사항]
1. 제약 조건 검증: 거래 날짜 포맷, 거래 금액(양수 여부), 카테고리 기등록 여부 검증 통합.
2. 최적 정렬 제한: list, search 등에서 전체 거래를 다 올리지 않고 fixed-size sorted buffer O(limit) 기법으로 대용량 스트리밍 처리.
3. CSV 호환성: 가계부 표준 CSV 스키마 검증 및 파싱하여 일괄 입출력 제어.
4. 반복 거래 템플릿 처리: 중복 생성 자동 차단 조건을 조합하여 안전한 다회차 자동 등록 제어.
================================================================================
"""

import os
import csv
import zipfile
import datetime
import calendar
from typing import Generator, List, Dict, Tuple, Optional
from budget_app.models import Transaction, RecurringTemplate
from budget_app.repository import FileRepository

class BudgetService:
    """
    가계부의 데이터 유효성 검사, 필터링, 정렬, 리포트 추출 등 비즈니스 로직을 수행합니다.
    """

    def __init__(self, repository: FileRepository):
        """
        저장소 인스턴스를 주입받아 서비스를 초기화합니다.

        Args:
            repository (FileRepository): 데이터 처리를 위임할 저장소 객체
        """
        self.repository = repository                                          # 주입받은 저장소 객체를 참조 변수에 할당

    # --- Transaction CRUD ---

    def add_transaction(self, date: str, type_str: str, category: str, amount: int, memo: str, tags: List[str]) -> str:
        """
        거래 항목들의 유효성을 점검하고, 통과하면 신규 거래 ID를 발급하여 파일에 기입합니다.

        Args:
            date (str): 날짜 (YYYY-MM-DD)
            type_str (str): 거래 타입 ("income"/"expense")
            category (str): 카테고리 이름
            amount (int): 정수형 금액
            memo (str): 선택적 한 줄 메모
            tags (List[str]): 거래와 연동할 태그 목록

        Returns:
            str: 발급된 신규 거래 ID
        """
        self.validate_fields(date, type_str, category, amount)                 # 전달받은 항목들의 유효성 유무 정밀 체크
        tx_id = self.repository.get_next_transaction_id()                     # 저장소로부터 고유한 다음 거래 ID 채번
        tx = Transaction(                                                      # 신규 거래 도메인 객체 조립
            id=tx_id,
            type=type_str,
            date=date,
            amount=amount,
            category=category,
            memo=memo,
            tags=tags
        )
        self.repository.append_transaction(tx)                                # 기입 함수 호출하여 파일 끝에 저장
        return tx_id                                                          # 생성된 거래 ID 반환

    def list_transactions(self, limit: int) -> List[Transaction]:
        """
        최근 날짜 및 ID 역순 정렬 기준에 맞춰 최대 limit 개수의 내역 목록을 추출합니다.
        메모리 복잡도를 O(limit)로 제한하는 스트리밍 정렬을 사용합니다.

        Args:
            limit (int): 목록으로 조회할 최대 개수

        Returns:
            List[Transaction]: 정렬된 상위 거래 내역 리스트
        """
        top_txs: List[Transaction] = []                                       # 정렬된 최신 항목들을 한계 크기(limit)만큼 축적할 리스트
        for tx in self.repository.stream_transactions():                      # 파일에서 한 줄씩 실시간 로드 시작
            inserted = False                                                  # 이번 항목 삽입 완료 유무 판별 플래그
            for i, existing in enumerate(top_txs):                            # 정렬 순서대로 순회
                # 날짜가 더 최신이거나 날짜가 같다면 ID 번호가 큰 순(ID desc)으로 삽입 위치 조정
                if tx.date > existing.date or (tx.date == existing.date and tx.id > existing.id):
                    top_txs.insert(i, tx)                                     # 정밀 정렬 위치에 삽입
                    inserted = True                                           # 삽입 상태 적용
                    break                                                     # 이번 루프 탈출
            if not inserted:                                                  # 현재 목록의 가장 끝 항목보다 이전 날짜라면
                top_txs.append(tx)                                            # 리스트 끝에 추가
            
            if len(top_txs) > limit:                                          # 리스트 크기가 허용된 limit 개수를 초과하면
                top_txs.pop()                                                 # 가장 오래된(끝 부분) 거래 정보를 제거하여 메모리 보호
                
        return top_txs                                                        # 정렬된 리스트 반환

    def search_transactions(self, 
                            from_date: Optional[str] = None, 
                            to_date: Optional[str] = None, 
                            category: Optional[str] = None, 
                            type_str: Optional[str] = None, 
                            query: Optional[str] = None, 
                            tag: Optional[str] = None, 
                            limit: int = 50) -> List[Transaction]:
        """
        다양한 조건들(기간, 카테고리, 타입, 키워드, 태그)을 만족하는 거래 내역만 추려내어 limit 크기 이하로 정렬 반환합니다.
        메모리 사용량을 아끼기 위해 실시간으로 필터링하며 상위 limit 개수만 정렬 버퍼에 축적합니다.

        Args:
            from_date (str): 검색 시작일 필터
            to_date (str): 검색 종료일 필터
            category (str): 카테고리 필터
            type_str (str): 거래 타입 필터
            query (str): 메모 내 키워드 검색 필터
            tag (str): 개별 태그 포함 여부 필터
            limit (int): 최종 조회할 최대 목록 크기

        Returns:
            List[Transaction]: 조건에 부합하며 최신순 정렬된 검색 결과 목록
        """
        top_txs: List[Transaction] = []                                       # 결과를 보관할 정렬 삽입 동적 배열
        
        for tx in self.repository.stream_transactions():                      # 한 줄씩 읽어가며 파싱 시작
            if from_date and tx.date < from_date:                             # 지정한 시작일 이전 데이터라면 무시
                continue
            if to_date and tx.date > to_date:                                 # 지정한 종료일 이후 데이터라면 무시
                continue
            if category and tx.category != category:                           # 지정 카테고리와 불일치 시 무시
                continue
            if type_str and tx.type != type_str:                              # 지정 타입과 다를 시 무시
                continue
            if query and query.lower() not in tx.memo.lower():                # 메모 대소문자 구분 없이 검색 키워드 미포함 시 무시
                continue
            if tag and tag not in tx.tags:                                    # 지정 태그 리스트에 해당 태그가 누락되어 있다면 무시
                continue

            inserted = False                                                  # 필터 통과 데이터를 정렬 삽입하기 위한 플래그
            for i, existing in enumerate(top_txs):                            # 정렬 위치 스캔
                if tx.date > existing.date or (tx.date == existing.date and tx.id > existing.id):
                    top_txs.insert(i, tx)                                     # 알맞은 위치 삽입
                    inserted = True
                    break
            if not inserted:                                                  # 가장 늦은 순서라면
                top_txs.append(tx)                                            # 끝에 추가

            if len(top_txs) > limit:                                          # limit 범위를 넘는 요소 청소
                top_txs.pop()                                                 # 초과분 제거

        return top_txs                                                        # 결과 반환

    def update_transaction(self, tx_id: str, date: str, type_str: str, category: str, amount: int, memo: str, tags: List[str]) -> bool:
        """
        기존의 거래 내역 정보를 수정합니다.

        Args:
            tx_id (str): 수정 대상 거래 식별자
            date (str): 신규 설정일
            type_str (str): 신규 설정 거래 타입
            category (str): 신규 지정 카테고리
            amount (int): 신규 지정 금액
            memo (str): 수정 메모
            tags (List[str]): 수정 태그 목록

        Returns:
            bool: 수정 처리 완수 여부
        """
        self.validate_fields(date, type_str, category, amount)                 # 갱신될 정보 필드 유효성 선검증
        updated_tx = Transaction(                                              # 수정본 Transaction 객체 준비
            id=tx_id,
            type=type_str,
            date=date,
            amount=amount,
            category=category,
            memo=memo,
            tags=tags
        )
        return self.repository.update_or_delete_transaction(tx_id, updated_tx) # 저장소의 원자적 파일 쓰기 교체 진행 및 유무 반환

    def delete_transaction(self, tx_id: str) -> bool:
        """
        지정한 거래 내역을 파일 데이터 상에서 영구히 삭제 처리합니다.

        Args:
            tx_id (str): 삭제할 대상 거래 ID

        Returns:
            bool: 삭제 완료 성공 여부
        """
        return self.repository.update_or_delete_transaction(tx_id, None)       # updated_tx 자리에 None을 전달하여 대상 행의 복사를 생략 처리

    # --- Category Management ---

    def add_category(self, name: str) -> bool:
        """
        신규 카테고리를 저장소 목록에 등록합니다. 공백 카테고리 및 중복명은 차단됩니다.

        Args:
            name (str): 신규 추가할 카테고리명

        Returns:
            bool: 정상 완료 여부
        """
        name = name.strip()                                                   # 양끝 여백 잘라냄
        if not name:
            raise ValueError("카테고리 이름은 공백일 수 없습니다.")             # 공백 예외 제어
        categories = self.repository.load_categories()                         # 저장소 카테고리 정보 로드
        if name in categories:
            raise ValueError(f"이미 존재하는 카테고리입니다: {name}")             # 중복 등록 사전 예방 차단
        categories.append(name)                                               # 목록에 덧붙임
        self.repository.save_categories(categories)                           # 저장소의 원자적 파일 기입 함수 호출
        return True

    def list_categories(self) -> List[str]:
        """
        등록되어 있는 전체 가계부 카테고리 목록을 로드합니다.

        Returns:
            List[str]: 카테고리명 리스트
        """
        return self.repository.load_categories()                              # 저장소 데이터 즉시 위임 로드

    def remove_category(self, name: str) -> bool:
        """
        지정한 카테고리를 삭제합니다.
        단, 해당 카테고리를 활용 중인 거래 기록이 하나라도 있을 시 무결성 방어를 위해 에러를 발생시키며 차단합니다.

        Args:
            name (str): 삭제 타겟 카테고리 명칭

        Returns:
            bool: 삭제 진행 완료 성공 여부
        """
        name = name.strip()                                                   # 공백 트림
        categories = self.repository.load_categories()                         # 카테고리 전체 목록 조회
        if name not in categories:
            raise ValueError(f"존재하지 않는 카테고리입니다: {name}")             # 없는 카테고리는 탈출
        
        # 무결성 검증: 거래 로그에 존재 여부 체크
        if self.is_category_in_use(name):                                     # 하나라도 사용 중이라면
            raise ValueError(f"카테고리 '{name}'을 사용하는 거래 내역이 존재하여 삭제할 수 없습니다.") # 삭제 거부 알림
        
        categories.remove(name)                                               # 리스트에서 분리
        self.repository.save_categories(categories)                           # 디스크 갱신 기입
        return True

    def is_category_in_use(self, category: str) -> bool:
        """
        가계부 전체 거래 로그를 스트리밍 탐색하여 특정 카테고리가 사용 중인지 여부를 판단합니다.

        Args:
            category (str): 확인할 카테고리명

        Returns:
            bool: 사용 중이면 True, 아니면 False
        """
        for tx in self.repository.stream_transactions():                      # 파일 한 줄씩 실시간 로드 탐색
            if tx.category == category:                                       # 사용하는 거래 발견 즉시
                return True                                                   # 탐색 중단 및 참 반환
        return False                                                          # 스캔이 끝났는데 없다면 거짓 반환

    # --- Budget and Summary ---

    def set_budget(self, month: str, amount: int):
        """
        특정 월의 지출 한도 예산을 책정 등록합니다.

        Args:
            month (str): 설정 월 (YYYY-MM 포맷)
            amount (int): 예산 정수 값 (0 이상)
        """
        self.validate_month_format(month)                                     # 월 날짜 형식 YYYY-MM 맞춤 검증
        if amount < 0:
            raise ValueError("예산 금액은 0 이상이어야 합니다.")                 # 음수 한도 설정 예외 차단
        budgets = self.repository.load_budgets()                               # 기존 예산 맵 조회
        budgets[month] = amount                                               # 월별 금액 매핑 갱신
        self.repository.save_budgets(budgets)                                 # 저장소 원자적 갱신 저장 호출

    def get_monthly_summary(self, month: str, top_n: int) -> dict:
        """
        특정 월의 총수입, 총지출, 잔액 및 지출이 높은 TOP N 카테고리 통계를 산출합니다.

        Args:
            month (str): 정산할 연월 (YYYY-MM)
            top_n (int): 산출할 소비 상위 카테고리 개수

        Returns:
            dict: 수입/지출 통계 및 예산 대비 경고 유무 정보 딕셔너리
        """
        self.validate_month_format(month)                                     # 월 표기 형식 정밀 체크

        total_income = 0                                                      # 총 수입 지표 누적합
        total_expense = 0                                                     # 총 지출 지표 누적합
        category_expenses: Dict[str, int] = {}                                # 지출 분류별 총액 누적합을 매핑할 임시 딕셔너리
        has_data = False                                                      # 해당 월 데이터 존재 기록 플래그

        for tx in self.repository.stream_transactions():                      # 거래 전체 목록 스트리밍 순회
            if tx.date.startswith(month + "-"):                               # 거래 날짜가 지정된 년월로 시작한다면
                has_data = True                                               # 데이터 있음을 기록
                if tx.type == "income":
                    total_income += tx.amount                                 # 수입 누적 증가
                elif tx.type == "expense":
                    total_expense += tx.amount                                # 지출 누적 증가
                    category_expenses[tx.category] = category_expenses.get(tx.category, 0) + tx.amount # 카테고리별 누적액 가산

        if not has_data:
            return {"has_data": False}                                        # 관련 기록 자체가 없는 경우 바로 종료 및 사전 반환

        # 카테고리별 누적 지출 크기 기준으로 정렬하여 상위 TOP N 추출
        sorted_categories = sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)
        top_categories = sorted_categories[:top_n]                            # 슬라이싱을 통해 순위 자름

        # 예산 로드 및 책정값 취득
        budgets = self.repository.load_budgets()
        budget = budgets.get(month)                                           # 책정된 예산 획득 (없을 시 None)

        return {
            "has_data": True,
            "total_income": total_income,
            "total_expense": total_expense,
            "balance": total_income - total_expense,
            "top_categories": top_categories,
            "budget": budget
        }

    # --- Import / Export ---

    def export_to_csv(self, filepath: str, month: Optional[str] = None, from_date: Optional[str] = None, to_date: Optional[str] = None) -> int:
        """
        필터링 범위에 속하는 거래 목록 전체를 기입 규격에 맞춘 CSV 형태로 추출하여 저장합니다.

        Args:
            filepath (str): 생성할 CSV 파일의 로컬 경로
            month (str): 대상 단일 월 범위 필터 (YYYY-MM)
            from_date (str): 기간 시작일 필터
            to_date (str): 기간 종료일 필터

        Returns:
            int: CSV 파일로 정상 저장 추출에 성공한 거래 건수
        """
        # 필터 조건이 없으면 전체 거래 내역을 내보냅니다.
        if month:
            self.validate_month_format(month)                                 # 형식 유효성 점검
        if from_date:
            self.validate_date_format(from_date)
        if to_date:
            self.validate_date_format(to_date)

        count = 0                                                             # 기입된 거래 수 카운트 변수
        with open(filepath, "w", encoding="utf-8", newline="") as f:          # UTF-8 기입 전용 CSV 오픈
            writer = csv.writer(f)
            writer.writerow(["date", "type", "category", "amount", "memo", "tags"]) # 가계부 표준 CSV 컬럼 정의 작성

            for tx in self.repository.stream_transactions():                      # 파일 한 행씩 로드
                if month and not tx.date.startswith(month + "-"):             # 월 불일치 스킵
                    continue
                if from_date and tx.date < from_date:                         # 일 범위 미달 스킵
                    continue
                if to_date and tx.date > to_date:                             # 일 범위 초과 스킵
                    continue

                tags_str = ",".join(tx.tags) if tx.tags else ""               # 복수 태그를 쉼표 문자열로 조인 직렬화
                writer.writerow([tx.date, tx.type, tx.category, tx.amount, tx.memo, tags_str]) # CSV 행 작성
                count += 1                                                    # 카운트 업

        return count                                                          # 내보낸 수량 리턴

    def import_from_csv(self, filepath: str) -> Tuple[int, int]:
        """
        지정 외부 CSV 파일을 한 행씩 검증 파싱한 뒤 가계부 거래 파일에 연동 기입합니다.
        손상되었거나 유효성 위반 행은 스킵 처리하며 처리 결과를 건수로 돌려줍니다.

        Args:
            filepath (str): 가져올 CSV 원본 파일 경로

        Returns:
            Tuple[int, int]: (성공적으로 임포트 완료 건수, 이상 스킵 처리 건수)
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"가져올 CSV 파일이 존재하지 않습니다: {filepath}")

        imported = 0                                                          # 정상 임포트 완료합
        skipped = 0                                                           # 오류 건수 스킵합

        # 여러 행을 동시에 대량 등록 시의 I/O 연산 속도를 보정하기 위해 번호 발급 접두/접미를 분해해 고속 갱신
        next_id = self.repository.get_next_transaction_id()                   # 다음 신규 ID 취득
        id_prefix, id_num_str = next_id.split("-")
        current_id_num = int(id_num_str)                                      # 정수 분할 변환

        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)                                        # 헤더 매핑 딕셔너리 리더 구성
            
            # 파일 컬럼 내 필수 스키마 헤더 존재 검증
            headers = [h.strip() for h in reader.fieldnames] if reader.fieldnames else []
            required_headers = ["date", "type", "category", "amount"]
            for req in required_headers:
                if req not in headers:
                    raise ValueError(f"CSV 파일에 필수 헤더가 부족합니다: '{req}'")

            for row in reader:
                # 데이터 유효성 공백 트림 정규화 처리
                clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None and v is not None}
                date_str = clean_row.get("date", "")
                type_str = clean_row.get("type", "")
                category_str = clean_row.get("category", "")
                amount_str = clean_row.get("amount", "")
                memo_str = clean_row.get("memo", "")
                tags_str = clean_row.get("tags", "")

                # 공통 유효성 검사 모듈을 사용해 행별 유효 검증 체크
                is_valid = True
                try:
                    self.validate_fields(date_str, type_str, category_str, int(amount_str)) # 정수 변환 및 규칙 확인
                except Exception:
                    is_valid = False                                          # 규격 미달 시 거짓 변경

                if not is_valid:                                              # 유효 위반 행 발견
                    skipped += 1                                              # 스킵 카운터 증가
                    continue                                                  # 다음 행 실행

                tx_id = f"{id_prefix}-{current_id_num:06d}"                   # 6자리 포맷 ID 작성
                current_id_num += 1                                           # 메모리 내 증가

                tags = [t.strip() for t in tags_str.split(",") if t.strip()] if tags_str else [] # 콤마 분리 태그 배열 생성
                tx = Transaction(                                              # Transaction 객체화
                    id=tx_id,
                    type=type_str,
                    date=date_str,
                    amount=int(amount_str),
                    category=category_str,
                    memo=memo_str,
                    tags=tags
                )
                self.repository.append_transaction(tx)                        # 파일의 끝에 바로 삽입
                imported += 1                                                 # 성공 수 증가

        return imported, skipped                                              # 결과 반환

    # --- Backup (Bonus 1) ---

    def create_backup(self) -> str:
        """
        거래 내역, 카테고리, 예산 한도, 반복 거래 데이터 전체를 포함하는 압축 백업(Zip) 파일을 생성합니다.

        Returns:
            str: 저장된 백업 Zip 파일의 로컬 전체 경로
        """
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")         # 고유 식별용 타임스탬프 문자 생성
        backup_dir = os.path.join(self.repository.data_dir, "backups")        # 백업 디렉터리 경로 설정
        os.makedirs(backup_dir, exist_ok=True)                                # 디렉터리가 없으면 자동 생성

        backup_path = os.path.join(backup_dir, f"backup_{timestamp}.zip")      # 최종 파일 명칭 확보

        # 가계부 구동 핵심 물리 데이터 파일 리스트 정의
        files_to_backup = [
            self.repository.transactions_path,
            self.repository.categories_path,
            self.repository.budgets_path,
            self.repository.recurring_path
        ]

        with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf: # OS 표준 ZIP 압축 모드로 열기
            for file_path in files_to_backup:
                if os.path.exists(file_path):                                 # 데이터 파일이 실제 존재하는 경우에만
                    zipf.write(file_path, os.path.basename(file_path))        # zip 아카이브 내부에 상대명으로 포함하여 압축 기입

        return backup_path                                                    # 최종 저장 주소 전달

    # --- Recurring Templates (Bonus 2) ---

    def load_recurring_templates(self) -> List[RecurringTemplate]:
        """
        저장소로부터 모든 반복 거래 템플릿 목록을 로드합니다.

        Returns:
            List[RecurringTemplate]: 반복 거래 템플릿 객체 리스트
        """
        return self.repository.load_recurring_templates()                     # 저장소 객체 기능 위임 실행

    def save_recurring_templates(self, templates: List[RecurringTemplate]):
        """
        전달받은 반복 거래 템플릿 목록 전체를 저장소에 영속화합니다.

        Args:
            templates (List[RecurringTemplate]): 저장할 템플릿 리스트
        """
        self.repository.save_recurring_templates(templates)                   # 저장소 객체 기능 위임 실행

    def add_recurring_template(self, type_str: str, category_str: str, amount: int, day: int, memo: str, tags: List[str]) -> str:
        """
        반복 거래 정보의 규칙을 검증한 뒤 유효한 경우 템플릿 저장 파일에 신규 템플릿을 등록합니다.

        Args:
            type_str (str): 거래 분류 ("income"/"expense")
            category_str (str): 카테고리명
            amount (int): 정수 금액
            day (int): 매달 반복할 정수형 일수 (1 ~ 31)
            memo (str): 반복 거래 기본 메모
            tags (List[str]): 반복 거래 태그 리스트

        Returns:
            str: 새로이 발급된 반복 템플릿 ID (REC-XXXXXX)
        """
        categories = self.repository.load_categories()                         # 카테고리 정보 조회
        if type_str not in ["income", "expense"]:
            raise ValueError("타입은 'income' 또는 'expense'여야 합니다.")
        if category_str not in categories:
            raise ValueError(f"등록되지 않은 카테고리입니다: {category_str}")
        if day < 1 or day > 31:
            raise ValueError("반복 일자(day)는 1에서 31 사이의 정수여야 합니다.")
        if amount <= 0:
            raise ValueError("금액은 양수여야 합니다.")

        templates = self.load_recurring_templates()                           # 기존 등록 템플릿 로드
        new_id = self.repository.get_next_recurring_id()                       # 신규 템플릿 고유 식별 번호 발급
        new_t = RecurringTemplate(                                            # 모델 조립
            id=new_id,
            type=type_str,
            category=category_str,
            amount=amount,
            day=day,
            memo=memo,
            tags=tags
        )
        templates.append(new_t)                                               # 목록에 추가
        self.save_recurring_templates(templates)                              # 영속화 파일 세이브
        return new_id                                                         # 발급 ID 반환

    def remove_recurring_template(self, template_id: str) -> bool:
        """
        지정한 ID를 가진 반복 거래 템플릿을 목록에서 삭제 제거합니다.

        Args:
            template_id (str): 삭제할 대상 반복 거래 식별자 (REC-XXXXXX)

        Returns:
            bool: 삭제 처리 반영 성공 여부 (매칭 대상이 부재할 시 False)
        """
        templates = self.load_recurring_templates()                           # 리스트 로드
        filtered = [t for t in templates if t.id != template_id]              # 식별자 다른 요소만 보관하도록 필터링
        if len(filtered) == len(templates):                                   # 소거된 항목이 없어 배열 길이가 같은 경우
            return False                                                      # 대상이 없는 것이므로 실패 전달
        self.save_recurring_templates(filtered)                               # 업데이트 파일 쓰기
        return True                                                           # 성공 전달

    def generate_recurring_transactions(self, month: str) -> int:
        """
        등록된 전체 반복 거래 템플릿을 기반으로 지정 연월의 실제 거래 로그들을 일괄 자동 생성합니다.
        중복 실행 시 돈이 이중 가산 기입되는 예외 방지를 위해 동일 기준 조건의 데이터가 있는지 사전 확인 필터링합니다.

        Args:
            month (str): 거래를 일괄 생성시킬 타겟 대상 연월 (YYYY-MM)

        Returns:
            int: 정상적으로 신규 생성되어 거래 로그 파일에 기입된 실제 거래 내역 건수
        """
        self.validate_month_format(month)                                     # 형식 일관성 검사
        year_part, month_part = map(int, month.split("-"))                    # 년/월 분리
        last_day = calendar.monthrange(year_part, month_part)[1]              # 특정 년월의 마지막 일(28~31일) 파악

        templates = self.load_recurring_templates()                           # 등록되어 있는 템플릿 리스트 로딩
        if not templates:
            return 0                                                          # 템플릿 미존재 시 생성 없이 조기 종료

        # 중복 방지를 위한 검사: 기등록된 타겟 연월 거래내역 사전 수집
        existing_txs = []
        for tx in self.repository.stream_transactions():
            if tx.date.startswith(month + "-"):
                existing_txs.append(tx)                                       # 해당 월에 이미 들어가있는 내역 축적

        generated_count = 0                                                   # 생성 건수 누적
        next_id = self.repository.get_next_transaction_id()                   # 다음 거래용 ID 추출
        id_prefix, id_num_str = next_id.split("-")
        current_id_num = int(id_num_str)                                      # 카운터 번호 정수화

        for t in templates:
            actual_day = min(t.day, last_day)                                 # 설정일이 31일인데 해당월이 30일까지라면 30일로 강제 안전 보정
            date_str = f"{month}-{actual_day:02d}"                            # 실제 삽입될 날짜 형태 구성

            # 중복 감지 비교 로직: 날짜, 타입, 분류, 액수, 메모, 그리고 태그에 'recurring'을 가졌는지 비교 검증
            is_duplicate = False
            for etx in existing_txs:
                if (etx.date == date_str and
                    etx.type == t.type and
                    etx.category == t.category and
                    etx.amount == t.amount and
                    etx.memo == t.memo and
                    "recurring" in etx.tags):
                    is_duplicate = True                                       # 매칭 항목이 있어 중복 감지 상태로 변경
                    break

            if not is_duplicate:                                              # 중복이 아니면 실제 신규 삽입 진행
                tx_id = f"{id_prefix}-{current_id_num:06d}"                   # 증가 번호에 맞춘 문자 아이디 제작
                current_id_num += 1                                           # 카운터 증가

                tags = list(t.tags)
                if "recurring" not in tags:
                    tags.append("recurring")                                  # 자동 생성 거래 표식 식별 태그('recurring') 강제 기재

                new_tx = Transaction(                                         # 신규 거래 객체 조립
                    id=tx_id,
                    type=t.type,
                    date=date_str,
                    amount=t.amount,
                    category=t.category,
                    memo=t.memo,
                    tags=tags
                )
                self.repository.append_transaction(new_tx)                    # 거래 내역 파일 끝에 추가
                generated_count += 1                                          # 생성합 합산

        return generated_count                                                # 최종 추가된 거래 건수 반환

    # --- Input Validation Helpers ---

    def validate_fields(self, date: str, type_str: str, category: str, amount: int):
        """
        가계부 입력 항목들의 비즈니스 제약 규칙 준수 여부를 통합 점검합니다.

        Args:
            date (str): 거래 일자
            type_str (str): 거래 타입
            category (str): 카테고리 명칭
            amount (int): 금액 수치
        """
        self.validate_date_format(date)                                       # 날짜 포맷 규칙 확인
        if type_str not in ["income", "expense"]:
            raise ValueError(f"허용되지 않은 타입입니다: {type_str}")             # 허용 타입 외 차단
        categories = self.repository.load_categories()                         # 등록 카테고리 정보 로드
        if category not in categories:
            raise ValueError(f"존재하지 않는 카테고리입니다: {category}")             # 카테고리 미등록 단어 에러 차단
        if amount <= 0:
            raise ValueError(f"금액은 양수여야 합니다: {amount}")                 # 양수 금액 원칙 준수 확인

    def validate_date_format(self, date_str: str):
        """
        날짜 텍스트가 정확한 YYYY-MM-DD 포맷을 갖는지와 유효한 날짜(윤년 등)인지 검사합니다.

        Args:
            date_str (str): 점검할 날짜 문자열
        """
        try:
            datetime.datetime.strptime(date_str, "%Y-%m-%d")                  # 내장 strptime 파싱 검증
        except ValueError:
            raise ValueError(f"날짜 형식이 올바르지 않습니다 (YYYY-MM-DD): {date_str}") # 실패 시 에러 출력 안내

    def validate_month_format(self, month_str: str):
        """
        연월 텍스트가 정확한 YYYY-MM 포맷을 갖는지와 유효한 범위인지 검사합니다.

        Args:
            month_str (str): 점검할 연월 문자열
        """
        try:
            datetime.datetime.strptime(month_str, "%Y-%m")                    # 내장 strptime 파싱 검증
        except ValueError:
            raise ValueError(f"월 형식이 올바르지 않습니다 (YYYY-MM): {month_str}")  # 실패 시 에러 출력 안내
