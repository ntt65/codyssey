"""
================================================================================
budget_app/repository.py - 데이터 영속성 계층 (Data Access & Storage Layer)
================================================================================

본 모듈은 가계부 프로그램(budget_app)에서 사용하는 JSONL(JSON Lines) 형식의 파일 데이터
(거래 내역, 카테고리 목록, 예산 한도, 반복 거래 템플릿)의 직접적인 파일 CRUD 처리를 전담합니다.

[주요 설계적 강점 및 구현 내용]
1. 원자적 파일 교체 (Atomic File Replacement): 
   - 데이터 수정/삭제 또는 카테고리/예산 저장 시, 원본에 스트림 쓰기를 하다가 비정상 종료 시
     발생할 수 있는 파일 오염을 방지하기 위해 임시 파일(tempfile)을 생성하여 쓰고, 
     안전하게 기록이 끝나면 os.replace() 연산으로 원자적 치환(Atomic Swap)을 구현했습니다.
2. 제너레이터 스트리밍 (Generator Streaming):
   - 거래 내역과 같이 규모가 지속적으로 증대할 수 있는 데이터 조회 시, 파일 전체를 메모리에
     동시에 올리지 않고 yield 제너레이터를 통하여 실시간 한 줄씩 순차적으로 스트리밍하여
     메모리 사용량을 제한된 자원 O(1) 수준으로 유지합니다.
================================================================================
"""

import os
import json
import tempfile
from typing import Generator, List, Dict, Optional
from budget_app.models import Transaction, RecurringTemplate

class FileRepository:
    """
    가계부 데이터를 파일 시스템에 영속적으로 저장하고 관리하는 저장소 클래스입니다.
    JSONL(JSON Lines) 포맷을 활용하여 데이터의 효율적인 로딩 및 입출력을 지원합니다.
    """

    def __init__(self, data_dir: str):
        """
        가계부 저장소 클래스를 초기화하고 파일 경로 설정 및 필요한 디렉터리를 생성합니다.

        Args:
            data_dir (str): 가계부 데이터 파일들이 저장될 디렉터리 경로
        """
        self.data_dir = data_dir                                              # 데이터 저장 디렉터리 경로 설정
        self.transactions_path = os.path.join(data_dir, "transactions.jsonl") # 거래 내역을 보관할 JSONL 파일 경로
        self.categories_path = os.path.join(data_dir, "categories.jsonl")     # 카테고리 목록을 보관할 JSONL 파일 경로
        self.budgets_path = os.path.join(data_dir, "budgets.jsonl")           # 월별 예산 정보를 보관할 JSONL 파일 경로
        self.recurring_path = os.path.join(data_dir, "recurring.jsonl")       # 반복 거래 템플릿을 보관할 JSONL 파일 경로
        self._ensure_dir()                                                    # 데이터 저장 디렉터리 자동 생성 확인

    def _ensure_dir(self):
        """
        데이터 저장 폴더가 존재하지 않는 경우 자동으로 폴더를 생성합니다.
        """
        os.makedirs(self.data_dir, exist_ok=True)  # exist_ok=True 옵션을 적용하여 이미 폴더가 있어도 에러 없이 조용히 넘어감

    def stream_transactions(self) -> Generator[Transaction, None, None]:
        """
        JSONL 파일로부터 거래 내역을 한 줄씩 제너레이터(yield) 형태로 로드하여 스트리밍합니다.
        대용량 파일 조회 시 메모리 자원을 O(1) 수준으로 극도로 아낄 수 있습니다.

        Yields:
            Generator[Transaction, None, None]: Transaction 객체를 순차적으로 반환
        """
        if not os.path.exists(self.transactions_path):  # 거래 내역 파일 자체가 아직 생성되지 않은 상태라면
            return                                      # 즉시 함수 종료 (빈 제너레이터 전달)
        with open(self.transactions_path, "r", encoding="utf-8") as f:  # UTF-8 인코딩으로 안전하게 파일 읽기 시작
            for line in f:                              # 파일에서 개행 단위로 한 줄씩 로드 (메모리 버퍼 낭비 방지)
                line = line.strip()                     # 줄바꿈 및 앞뒤 공백 문자 제거
                if not line:                            # 빈 행은 데이터 처리에 무의미하므로 무시
                    continue
                try:
                    data = json.loads(line)             # 단일 행의 JSON 데이터를 파이썬 딕셔너리로 복원
                    yield Transaction.from_dict(data)   # 데이터 딕셔너리를 Transaction 데이터 클래스로 변환하여 실시간 반환
                except (json.JSONDecodeError, KeyError):# 직렬화 에러 혹은 누락 필드 발생 시 프로그램 정지 없이 패스
                    continue                            # 문제 있는 라인만 스킵하고 다음 줄로 이동

    def append_transaction(self, tx: Transaction):
        """
        단일 거래 내역을 JSON 문자열로 직렬화하여 거래 파일 끝에 추가 기입(Append)합니다.

        Args:
            tx (Transaction): 파일 끝에 저장될 새로운 Transaction 객체
        """
        with open(self.transactions_path, "a", encoding="utf-8") as f:  # 추가 쓰기 모드(a)로 거래 내역 파일 오픈
            f.write(json.dumps(tx.to_dict(), ensure_ascii=False) + "\n") # 한글이 깨지지 않도록 ensure_ascii=False로 지정 후 개행을 붙여 작성

    def update_or_delete_transaction(self, tx_id: str, updated_tx: Optional[Transaction]) -> bool:
        """
        지정한 ID의 거래 내역을 찾아서 수정하거나 삭제합니다.
        비정상 종료 등 돌발 사고 시 파일 유실을 원천 차단하기 위해 임시 임시파일 작성 및
        os.replace() 커널 연산을 사용하는 '원자적 파일 교체(Atomic Replacement)' 전략을 사용합니다.

        Args:
            tx_id (str): 수정 또는 삭제하고자 하는 대상 거래 ID
            updated_tx (Optional[Transaction]): 수정될 새로운 Transaction 객체. None일 경우 삭제 처리를 의미함.

        Returns:
            bool: 대상을 찾아 성공적으로 연산을 수행했는지 여부 (성공: True, 대상 없음: False)
        """
        found = False  # 대상 거래 ID의 존재 및 처리 성공 유무 판별 플래그
        temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, prefix="transactions_tmp_", suffix=".jsonl")  # 안전 구역에 임시 파일 생성
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as out_f:  # 획득한 파일 디스크립터를 기반으로 쓰기 전용 파일 객체 오픈
                if os.path.exists(self.transactions_path):            # 수정/삭제할 대상 원본 파일이 존재하는 경우
                    with open(self.transactions_path, "r", encoding="utf-8") as in_f:  # 원본 읽기 모드로 오픈
                        for line in in_f:                             # 스트리밍식으로 순차 탐색 및 데이터 쓰기
                            line = line.strip()                       # 양끝 공백 제거
                            if not line:                              # 빈 줄 건너뜀
                                continue
                            try:
                                data = json.loads(line)               # JSON 구조 데이터로 복원
                                if data.get("id") == tx_id:           # 현재 줄의 거래 ID가 우리가 찾는 타겟 ID인 경우
                                    found = True                      # 대상을 발견했으므로 플래그 참 변경
                                    if updated_tx is not None:        # updated_tx가 제공되었다면 -> 수정(Update) 모드
                                        out_f.write(json.dumps(updated_tx.to_dict(), ensure_ascii=False) + "\n") # 수정된 신규 객체 직렬화 기입
                                    # updated_tx가 None인 경우에는 out_f에 아무것도 기입하지 않음으로써 삭제(Delete) 효과
                                else:                                 # 타겟 ID가 아닌 일반 내역들은 원본 그대로 보존
                                    out_f.write(line + "\n")          # 임시 파일로 원래 데이터를 그대로 옮김
                            except (json.JSONDecodeError, KeyError):   # 파싱 불가 행이 발견되어도 유실 방지를 위해 원문 그대로 임시 파일에 백업 복원
                                out_f.write(line + "\n")
            if found:                                                 # 탐색에 성공하여 파일 구조 갱신이 확정되었을 때
                os.replace(temp_path, self.transactions_path)         # 임시 파일을 원본 경로에 원자적(Atomic)으로 덮어씀으로써 변경 보장
            else:                                                     # 대상 ID가 없는 경우 변경 불필요하므로
                os.remove(temp_path)                                  # 임시 파일을 안전하게 파기
        except Exception as e:
            if os.path.exists(temp_path):                             # 내부 작업 도중 오류가 터지면 찌꺼기 방지를 위해
                os.remove(temp_path)                                  # 임시 파일을 확실하게 삭제하여 원본 보호
            raise e                                                   # 상위 서비스 또는 컨트롤러로 에러 다시 전파
        return found                                                  # 처리 성공 여부 리턴

    def load_categories(self) -> List[str]:
        """
        저장되어 있는 카테고리 목록을 모두 읽어옵니다.
        최초 실행으로 파일이 존재하지 않거나 데이터가 비어있을 때는 기본 카테고리 9종을 
        파일에 자동 기입한 뒤 반환합니다.

        Returns:
            List[str]: 카테고리 명칭이 담긴 문자열 리스트
        """
        if not os.path.exists(self.categories_path):                          # 카테고리 저장 파일이 존재하지 않는 최초 구동 상태
            self.save_categories(self.get_default_categories())               # 기본 9종 카테고리를 파일에 원자적으로 작성
            return self.get_default_categories()                              # 기본 리스트 즉시 리턴
        
        categories = []                                                       # 파일에서 읽은 카테고리를 축적할 동적 버퍼
        with open(self.categories_path, "r", encoding="utf-8") as f:          # 읽기 오픈
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)                                   # 카테고리 JSON 한 행 로드
                    categories.append(data["name"])                           # 카테고리명 리스트에 저장
                except (json.JSONDecodeError, KeyError):
                    continue
        if not categories:                                                    # 파일은 있으나 실제 내부 텍스트가 모두 텅 비어있던 이상 상태
            categories = self.get_default_categories()                         # 기본값 세팅
            self.save_categories(categories)                                  # 기본 카테고리로 덮어쓰기 복구
        return categories                                                     # 카테고리 목록 리턴

    def get_default_categories(self) -> List[str]:
        """
        가계부 초기 세팅용 기본 권장 카테고리 9종 리스트를 반환합니다.

        Returns:
            List[str]: ["food", "transport", "rent", ...] 구성의 9종 기본 카테고리명 리스트
        """
        return ["food", "transport", "rent", "shopping", "health", "education", "salary", "allowance", "other"] # 고정 기본 배열 반환

    def save_categories(self, categories: List[str]):
        """
        전달받은 신규 카테고리 목록 전체를 영속화하여 카테고리 파일에 새로 씁니다.
        데이터 신뢰성 확보를 위해 원자적 임시 쓰기 및 os.replace 교체를 이용합니다.

        Args:
            categories (List[str]): 영속화할 카테고리 명칭 목록 리스트
        """
        temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, prefix="categories_tmp_", suffix=".jsonl")  # 카테고리 임시 파일 할당
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:              # 파일 객체 오픈
                for cat in categories:                                        # 전체 카테고리명 순회
                    f.write(json.dumps({"name": cat}, ensure_ascii=False) + "\n") # JSON 구조 한 행씩 출력 기입
            os.replace(temp_path, self.categories_path)                       # 카테고리 파일에 덮어씌워 갱신 처리
        except Exception as e:
            if os.path.exists(temp_path):                                     # 장애 시 임시 잔존 파일 삭제
                os.remove(temp_path)
            raise e                                                           # 예외 전파

    def load_budgets(self) -> Dict[str, int]:
        """
        저장소에 기재된 월별 예산 내역 전체를 가져와 연동합니다.

        Returns:
            Dict[str, int]: 'YYYY-MM' 형식의 연월 문자열을 Key로 하고, 정수형 예산 한도를 Value로 하는 딕셔너리
        """
        budgets = {}                                                          # 예산 맵 준비
        if not os.path.exists(self.budgets_path):                             # 파일이 아직 없으면 설정된 예산이 없는 것이므로
            return budgets                                                    # 빈 딕셔너리 즉시 리턴
        with open(self.budgets_path, "r", encoding="utf-8") as f:             # 예산 파일 오픈
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)                                   # 데이터 로드
                    budgets[data["month"]] = data["amount"]                   # 월별 매핑 기입
                except (json.JSONDecodeError, KeyError):
                    continue
        return budgets                                                        # 예산 맵 리턴

    def save_budgets(self, budgets: Dict[str, int]):
        """
        월별 예산의 최신 변경 내용을 파일에 업데이트하여 씁니다.
        데이터 무결성 방어를 위해 원자적 파일 교체 기술을 동일하게 적용합니다.

        Args:
            budgets (Dict[str, int]): 저장할 'YYYY-MM' -> 예산액 매핑 정보
        """
        temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, prefix="budgets_tmp_", suffix=".jsonl") # 예산 임시 파일 빌림
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:              # 임시 파일 디스크립터 오픈
                for month, amount in budgets.items():                         # 예산 딕셔너리 아이템 루프
                    f.write(json.dumps({"month": month, "amount": amount}, ensure_ascii=False) + "\n") # 파일에 한 줄씩 기록
            os.replace(temp_path, self.budgets_path)                          # 원본 예산 파일과 교체
        except Exception as e:
            if os.path.exists(temp_path):                                     # 오류 상황 발생 시
                os.remove(temp_path)                                          # 임시 생성 파일 소각
            raise e                                                           # 에러 통보

    def get_next_transaction_id(self) -> str:
        """
        파일을 순차 탐색하여 등록되어 있는 거래 중 가장 큰 numeric ID 값을 추적하고,
        이를 1만큼 증가시켜 새롭게 할당받을 고유 거래 식별자 'TX-XXXXXX'를 반환합니다.

        Returns:
            str: 0으로 패딩된 6자리 숫자 형태의 ID 문자열 (예: 'TX-000005')
        """
        max_id = 0                                                            # 최댓값을 추적하기 위한 정수 변수 초기화
        if os.path.exists(self.transactions_path):                            # 거래 내역 파일 존재 여부 점검
            with open(self.transactions_path, "r", encoding="utf-8") as f:    # 파일 열기
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)                               # 라인 직렬화 해제
                        tx_id = data.get("id", "")                            # ID 문자열 취득
                        if tx_id.startswith("TX-"):                           # TX- 포맷 패턴인지 확인
                            val = int(tx_id.split("-")[1])                    # 접미사 숫자를 정수로 형변환
                            if val > max_id:                                  # 최댓값 갱신 여부 판단
                                max_id = val                                  # 최댓값 업데이트
                    except (json.JSONDecodeError, ValueError, IndexError):     # 이상 포맷 행 스킵
                        continue
        return f"TX-{max_id + 1:06d}"                                         # 0패딩 6자리 규격 포맷 조합으로 리턴 (예: TX-000001)

    def get_next_recurring_id(self) -> str:
        """
        반복 거래 내역 파일을 읽어와 등록된 템플릿 중 가장 큰 ID 값을 파악하고,
        이를 1 증가시킨 고유 반복 식별자 'REC-XXXXXX'를 발급합니다.

        Returns:
            str: 0으로 패딩된 6자리 숫자 형태의 ID 문자열 (예: 'REC-000002')
        """
        max_id = 0                                                            # 최댓값 변수 초기화
        if os.path.exists(self.recurring_path):                               # 반복 거래 파일 유무 검사
            with open(self.recurring_path, "r", encoding="utf-8") as f:       # 파일 열기
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        data = json.loads(line)                               # 파이썬 데이터 객체화
                        rec_id = data.get("id", "")                           # ID 읽어오기
                        if rec_id.startswith("REC-"):                         # 반복거래 규격 접두사 매칭
                            val = int(rec_id.split("-")[1])                   # 접미사 숫자를 파싱
                            if val > max_id:                                  # 최댓값 갱신 검사
                                max_id = val                                  # 최댓값 등록
                    except (json.JSONDecodeError, ValueError, IndexError):     # 이상 포맷 무시
                        continue
        return f"REC-{max_id + 1:06d}"                                        # 0패딩 6자리 규격 포맷으로 리턴 (예: REC-000001)

    def load_recurring_templates(self) -> List[RecurringTemplate]:
        """
        저장소에 보관된 모든 반복 거래 템플릿 목록을 로드합니다.

        Returns:
            List[RecurringTemplate]: 반복 거래 템플릿 객체 리스트
        """
        templates = []                                                        # 템플릿 축적 버퍼
        if not os.path.exists(self.recurring_path):                           # 반복 거래 파일이 아직 존재하지 않는 경우
            return templates                                                  # 빈 리스트 반환
        with open(self.recurring_path, "r", encoding="utf-8") as f:           # 읽기 오픈
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    data = json.loads(line)                                   # 데이터 역직렬화
                    templates.append(RecurringTemplate.from_dict(data))       # 객체로 변환하여 보관
                except (json.JSONDecodeError, KeyError):
                    continue
        return templates                                                      # 결과 리스트 반환

    def save_recurring_templates(self, templates: List[RecurringTemplate]):
        """
        전달받은 반복 거래 템플릿 목록 전체를 파일에 저장합니다.
        파일 손상을 방지하기 위해 임시 파일 생성 및 os.replace 원자적 교체를 사용합니다.

        Args:
            templates (List[RecurringTemplate]): 영속화할 반복 거래 템플릿 목록
        """
        temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, prefix="recurring_tmp_", suffix=".jsonl") # 임시 파일 확보
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:              # 파일 쓰기 스트림 오픈
                for t in templates:                                           # 전체 템플릿 순회
                    f.write(json.dumps(t.to_dict(), ensure_ascii=False) + "\n") # JSON 문자열 직렬화 및 개행 작성
            os.replace(temp_path, self.recurring_path)                        # 원자적 교체 완료
        except Exception as e:
            if os.path.exists(temp_path):                                     # 오류 시 임시 파일 파괴
                os.remove(temp_path)
            raise e                                                           # 에러 전파                                        # 0패딩 6자리 규격 포맷으로 리턴 (예: REC-000001)
