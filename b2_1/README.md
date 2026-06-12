# 💰 대화형 파일 기반 가계부 콘솔 프로그램 (budget_app) 사용자 가이드

본 가계부 애플리케이션(`budget_app`)은 파이썬 표준 라이브러리만을 활용해 최적화된 자원 관리(Generator)와 데이터 무결성 보호(Atomic Write)를 고려하여 구축된 강건한 콘솔 프로그램입니다.

---

## 1. 실행 방법 및 초기 기동

### 💡 미션 실행 및 입력 방식 요구사항
* **요구사항**:
  * 실행 방식은 `python -m budget_app <command> [options]` 패턴을 권장합니다.
  * 모든 명령은 `--help` 옵션으로 사용 방법이 출력되어야 합니다.
  * 입력 기본 방식은 **“대화형”** 입니다 (예: `add` 실행 시 날짜/타입/카테고리/금액 등을 `input()`으로 순차 입력).
  * 단, `search`, `list`, `summary`, `export`, `import`, `delete` 항목은 옵션 인자 방식도 권장하며, 옵션 표기는 리눅스 표준인 `--`로 통일해야 합니다 (예: `--help`, `--limit`, `--from`, `--to`, `--month`).
  * `update`는 대화형 방식 또는 옵션 방식 중 하나를 선택해도 되나 문서에 명확히 고정해야 합니다 (본 프로젝트는 대화형 수정을 기본 채택하여 아래 명시하였습니다).
* **구현 방식 및 소스 코드**:
  * 가계부 루트 폴더 `/Users/mpeg46551/codyssey/b2_1` 내에서 패키지 구동 표준(`-m`)에 맞춰 가동합니다.
  * `__main__.py`에서 명령줄 인자 파싱 및 의존성 주입을 완수하고 셸 프로그램 루프를 구동합니다.
  ```bash
  # 기본 ./data 폴더 경로 대화형 가동
  python3 -m budget_app

  # 커스텀 data 경로 지정 가동
  python3 -m budget_app --data-dir ./my_custom_data
  ```

---

## 2. 저장 파일 위치 및 포맷

### 💡 미션 저장 정책 및 파일 자동 생성 요구사항
* **요구사항**:
  * 저장 포맷은 JSONL 또는 CSV 중 1개를 선택합니다 (본 프로젝트는 JSONL 채택).
  * 데이터는 프로그램 종료 후에도 영구 유지되며, 최소 3개 이상(필수)의 파일로 격리 분리해 저장해야 합니다 (`transactions.<fmt>`, `categories.<fmt>`, `budgets.<fmt>`).
  * 파일이 없으면 자동 생성하거나, “초기화 안내 메시지”를 출력해야 합니다.
  * 카테고리 파일이 비어있으면 **기본 카테고리 자동 생성 (안 A)** 또는 category add를 먼저 하도록 유도하고 막는 것(안 B) 중 하나를 택해야 합니다 (본 프로젝트는 **기본 카테고리 자동 생성 안 A** 채택).
  * 기본 저장 폴더는 `./data`를 권장하며 옵션으로 변경 가능해야 합니다 (예: `--data-dir`).
* **구현 방식 및 소스 코드**:
  * `FileRepository`에서 저장소 데이터 디렉터리를 보장하고 각 파일 경로를 구성하며, 비어있을 시 기본 카테고리 9종을 원자적으로 자동 작성합니다.
  ```python
  # [repository.py:L33-L45] - 4대 파일 물리 분리 및 자동 초기화
  def __init__(self, data_dir: str):
      self.data_dir = data_dir
      self.transactions_path = os.path.join(data_dir, "transactions.jsonl") # 1. 거래 내역 파일 경로
      self.categories_path = os.path.join(data_dir, "categories.jsonl")     # 2. 카테고리 파일 경로
      self.budgets_path = os.path.join(data_dir, "budgets.jsonl")           # 3. 예산 관리 파일 경로
      self.recurring_path = os.path.join(data_dir, "recurring.jsonl")       # 4. 반복거래 관리 파일 경로
      self._ensure_dir()                                                    # 디렉터리 존재 자동 보장
  ```

---

## 3. CSV 가져오기/내보내기 (Import/Export) 스키마

### 💡 미션 파일 연동 호환 요구사항
* **요구사항**:
  * `import` 및 `export`는 아래의 CSV 최소 스키마를 고정해 구현해야 합니다.
  * 공통 조건: UTF-8 인코딩, 첫 행 헤더 포함
* **CSV 스키마 규격**:

| Column | Required | 설명 |
| :--- | :---: | :--- |
| **date** | Y | YYYY-MM-DD 포맷 |
| **type** | Y | `income` (수입) 또는 `expense` (지출) |
| **category** | Y | 가계부에 등록된 유효 카테고리명 |
| **amount** | Y | 양의 정수 금액 |
| **memo** | N | 문자열 |
| **tags** | N | 쉼표(`,`)로 구분된 태그 문자열 |

---

## 4. 최종 결과물 10대 기능 및 상세 설계 요구사항

### 4.1 거래 추가 (add)
* **미션 기능 요구사항**:
  * `add` 실행 후 대화형으로 필드(날짜, 타입, 카테고리, 금액, 메모, 태그)를 입력받아 거래를 저장해야 합니다.
  * `category`는 등록된 목록에 존재해야 합니다 (없으면 안내 후 재입력/등록 유도).
  * 저장 완료 시 생성된 id를 사용자에게 출력해야 합니다.
  * **입력 검증**: 날짜 형식 오류, 음수/0 금액, 허용되지 않은 type, 존재하지 않는 category 등은 재입력 요구 또는 오류 메시지 출력으로 처리해야 합니다.
* **구현 방식 및 소스 코드**:
  * 대화식 입력을 받아 `validate_fields`로 비즈니스 제약을 일괄 검증하고 통과 시 고유 식별자(TX-ID)를 발급하여 JSONL 행으로 추가 기입합니다.
  * 존재하지 않는 카테고리 작성 시, 프로그램이 예외로 터지는 대신 새 카테고리 등록 서브메뉴 분기로 부드럽게 안내합니다.
  ```python
  # [service.py:L41-L68] - 거래 추가 구현 코드 및 주석
  def add_transaction(self, date: str, type_str: str, category: str, amount: int, memo: str, tags: List[str]) -> str:
      # 1. 입력 필드의 비즈니스 제약(날짜, 타입, 등록 카테고리, 금액) 통합 점검
      self.validate_fields(date, type_str, category, amount)
      # 2. 저장소 계층으로부터 순차 증가된 신규 고유 ID 채번
      tx_id = self.repository.get_next_transaction_id()
      # 3. 데이터 도메인 구조인 Transaction 객체 인스턴스화
      tx = Transaction(
          id=tx_id,
          type=type_str,
          date=date,
          amount=amount,
          category=category,
          memo=memo,
          tags=tags
      )
      # 4. 파일 끝에 데이터 기입(Append) 수행
      self.repository.append_transaction(tx)
      return tx_id
  ```

### 4.2 거래 목록 (list)
* **미션 기능 요구사항**:
  * `list`는 최신순으로 거래를 출력해야 합니다.
  * `--limit N` 옵션을 지원해야 합니다 (기본값 제공).
  * 파일 전체를 한 번에 메모리에 로드하지 않고, **제너레이터 기반 스트리밍 처리**로 구현해야 합니다.
* **구현 방식 및 소스 코드**:
  * yield 제너레이터로 한 행씩 파싱해 읽어 오며, 최대 limit 크기로 버퍼를 제한하고 새 데이터를 내림차순 정렬 삽입 및 초과 시 pop() 처리하는 버퍼를 두어 고정 메모리 $O(\text{limit})$로 정렬을 완수합니다.
  ```python
  # [service.py:L70-L96] - O(limit) 정렬 삽입 버퍼를 활용한 최신 거래 추출
  def list_transactions(self, limit: int) -> List[Transaction]:
      top_txs: List[Transaction] = [] # 정렬 순서대로 최대 limit 만큼 보관할 버퍼
      # 1. stream_transactions 제너레이터로부터 한 줄씩 순차 로딩
      for tx in self.repository.stream_transactions():
          inserted = False
          for i, existing in enumerate(top_txs):
              # 2. 날짜 최신순, 날짜 같으면 ID 역순 정렬 위치 삽입 탐색
              if tx.date > existing.date or (tx.date == existing.date and tx.id > existing.id):
                  top_txs.insert(i, tx)
                  inserted = True
                  break
          if not inserted:
              top_txs.append(tx)
          
          # 3. 버퍼 크기가 limit 한계를 상회하면 끝단의 가장 낡은 요소 제거
          # -> 메모리 점유율을 언제나 O(limit)로 억제해 대량 데이터 처리 최적화
          if len(top_txs) > limit:
              top_txs.pop()
              
      return top_txs
  ```

### 4.3 거래 검색 (search)
* **미션 기능 요구사항**:
  * 조건 기반 검색을 지원해야 합니다: 기간(`--from`/`--to`), 카테고리(`--category`), 타입(`--type`), 메모 키워드(`--q`), 태그(`--tag`)
  * 검색 결과는 최신순으로 출력해야 합니다.
  * 스트리밍 처리 (제너레이터 기반)를 유지해야 합니다.
* **구현 방식 및 소스 코드**:
  * 제너레이터 스트림 루프 내에서 조건 필터들을 통과한 거래 개체들만 선별하고 정렬 버퍼에 꽂아 넣어, 대용량 파일 탐색 시의 메모리 사용량 폭증을 우회합니다.
  ```python
  # [service.py:L98-L150] - 필터링 및 스트리밍 정렬 검색 코드
  def search_transactions(self, from_date: Optional[str] = None, to_date: Optional[str] = None, 
                          category: Optional[str] = None, type_str: Optional[str] = None, 
                          query: Optional[str] = None, tag: Optional[str] = None, limit: int = 50) -> List[Transaction]:
      top_txs: List[Transaction] = []
      # 1. 제너레이터 스트리밍 도중 필터링을 실시간 즉시 단행
      for tx in self.repository.stream_transactions():
          if from_date and tx.date < from_date: continue
          if to_date and tx.date > to_date: continue
          if category and tx.category != category: continue
          if type_str and tx.type != type_str: continue
          if query and query.lower() not in tx.memo.lower(): continue
          if tag and tag not in tx.tags: continue

          # 2. 필터 통과 데이터를 최신순 정렬 버퍼에 삽입 정렬
          inserted = False
          for i, existing in enumerate(top_txs):
              if tx.date > existing.date or (tx.date == existing.date and tx.id > existing.id):
                  top_txs.insert(i, tx)
                  inserted = True
                  break
          if not inserted:
              top_txs.append(tx)

          # 3. limit 버퍼 크기 제약 준수
          if len(top_txs) > limit:
              top_txs.pop()

      return top_txs
  ```

### 4.4 월별 요약 (summary)
* **미션 기능 요구사항**:
  * `summary --month YYYY-MM` 입력을 받아 해당 월의 요약을 출력해야 합니다.
  * 출력 항목: 총 수입, 총 지출, 잔액 (총수입 - 총지출) 및 카테고리별 지출 합계 TOP N (`--top` 옵션 지원)
  * 데이터가 없는 달은 “데이터 없음”을 명확히 화면에 출력해야 합니다.
* **구현 방식 및 소스 코드**:
  * 지정 년월에 귀속되는 수입/지출을 스트리밍 누적하고 카테고리별 지출 순위를 분할 연산하며, 타겟 년월의 내역이 1건도 탐색되지 않은 비어있는 월은 리포트 생성을 취소하고 데이터 없음 안내를 수행합니다.
  ```python
  # [service.py:L279-L324] - 월별 통계 및 TOP N 집계 코드
  def get_monthly_summary(self, month: str, top_n: int) -> dict:
      self.validate_month_format(month)
      total_income = 0
      total_expense = 0
      category_expenses: Dict[str, int] = {}
      has_data = False

      # 1. 타겟 연월에 부합하는 내역들의 수입/지출 및 카테고리별 누적액 집계
      for tx in self.repository.stream_transactions():
          if tx.date.startswith(month + "-"):
              has_data = True
              if tx.type == "income":
                  total_income += tx.amount
              elif tx.type == "expense":
                  total_expense += tx.amount
                  category_expenses[tx.category] = category_expenses.get(tx.category, 0) + tx.amount

      if not has_data:
          return {"has_data": False} # 데이터 부재 시 조기 종료 알림

      # 2. 카테고리 지출 크기순 내림차순 정렬 후 상위 TOP N 분할
      sorted_categories = sorted(category_expenses.items(), key=lambda x: x[1], reverse=True)
      top_categories = sorted_categories[:top_n]

      # 3. 설정되어 보존 중인 예산 한도액 조회 연동
      budgets = self.repository.load_budgets()
      budget = budgets.get(month)

      return {
          "has_data": True,
          "total_income": total_income,
          "total_expense": total_expense,
          "balance": total_income - total_expense,
          "top_categories": top_categories,
          "budget": budget
      }
  ```

### 4.5 예산 설정/조회 (budget)
* **미션 기능 요구사항**:
  * `budget set --month YYYY-MM --amount <금액>`으로 월 예산을 영구 저장해야 합니다.
  * `summary` 실행 시 예산이 설정되어 있으면 **예산 대비 사용률(%)** 및 **초과 여부 (초과 시 경고 문구)**를 함께 화면에 출력해야 합니다.
* **구현 방식 및 소스 코드**:
  * 년월 예산을 책정해 `budgets.jsonl`에 저장하며, `get_monthly_summary` 반환값에 매핑 연계되어 사용자의 한도 지출 초과율을 계산 및 ⚠️ 경고를 터미널 표에 출력합니다.
  ```python
  # [service.py:L264-L278] - 예산 책정 저장 로직
  def set_budget(self, month: str, amount: int):
      # 1. 월 표기식(YYYY-MM) 유효성 점검
      self.validate_month_format(month)
      if amount < 0:
          raise ValueError("예산 금액은 0 이상이어야 합니다.")
      # 2. 기존 딕셔너리 예산 맵 조회 및 값 오버라이트 갱신
      budgets = self.repository.load_budgets()
      budgets[month] = amount
      # 3. 임시 파일 치환 전략으로 무결성을 지키며 원자적 파일 영속화 수행
      self.repository.save_budgets(budgets)
  ```

### 4.6 카테고리 관리 (category)
* **미션 기능 요구사항**:
  * `category add/list/remove`를 제공해야 합니다.
  * 카테고리 삭제 시, 해당 카테고리를 사용하는 내역이 존재하면 **삭제를 막거나 대체 카테고리를 요구**해야 합니다 (본 프로젝트는 **삭제 차단** 기법 채택).
* **구현 방식 및 소스 코드**:
  * 카테고리 추가 및 목록 반환 기능을 제공하며, 삭제 타겟 카테고리가 가계부 거래 파일에서 활용되고 있는 흔적이 발견되면 에러 문구를 발생시키며 삭제를 거부합니다.
  ```python
  # [service.py:L223-L245] - 카테고리 무결성 검증 및 제거 로직
  def remove_category(self, name: str) -> bool:
      name = name.strip()
      categories = self.repository.load_categories()
      if name not in categories:
          raise ValueError(f"존재하지 않는 카테고리입니다: {name}")
      
      # 1. 가계부 거래 파일 전체를 스캔하여 참조 무결성 유무 감시
      if self.is_category_in_use(name):
          # 2. 거래 파일에서 사용 중인 흔적이 발견되면 에러 발생시켜 삭제 반려
          raise ValueError(f"카테고리 '{name}'을 사용하는 거래 내역이 존재하여 삭제할 수 없습니다.")
      
      categories.remove(name)
      self.repository.save_categories(categories) # 안전하게 파일 저장
      return True
  ```

### 4.7 거래 수정 (update)
* **미션 기능 요구사항**:
  * `update`는 `--id` 기반 방식 또는 대화형 방식 중 하나를 선택해 고정해 구현해야 합니다.
  * 본 프로젝트는 **대화형 기반 (안 B)**을 채택하여, 사용자가 수정할 필드를 선택적으로 쉽게 기입할 수 있는 완성도 높은 수정 흐름을 구축했습니다.
  * 수정 시 파일 기반 영속 저장 안정성을 고려한 원자적 쓰기(Atomic Write)가 적용되어야 합니다.
* **구현 방식 및 소스 코드**:
  * 프롬프트 갱신 시 기존 정보를 prefill(미리 값 채워넣기) 해 주어 수정하지 않을 항목은 그냥 엔터로 통과시키며, 변경 사항만 병합해 원자적 임시 파일 쓰기 교체를 완료합니다.
  ```python
  # [service.py:L152-L179] - 거래 내역 수정 코드
  def update_transaction(self, tx_id: str, date: str, type_str: str, category: str, amount: int, memo: str, tags: List[str]) -> bool:
      # 1. 갱신을 위해 투입된 새 필드들의 형식 유효성 통합 점검
      self.validate_fields(date, type_str, category, amount)
      # 2. 수정 변경할 데이터 필드들을 병합한 Transaction 도메인 객체 조립
      updated_tx = Transaction(
          id=tx_id,
          type=type_str,
          date=date,
          amount=amount,
          category=category,
          memo=memo,
          tags=tags
      )
      # 3. 저장소의 원자적 복사 치환(Atomic Replacement)을 호출해 영속 보장
      return self.repository.update_or_delete_transaction(tx_id, updated_tx)
  ```

### 4.8 거래 삭제 (delete)
* **미션 기능 요구사항**:
  * `delete --id <id>`로 특정 거래를 삭제할 수 있어야 합니다.
  * 존재하지 않는 id는 “없는 데이터”로 처리하고 사용자 메시지를 출력해야 합니다.
  * 파일 안정성을 고려한 원자적 교체(Atomic Swap)를 구현해야 합니다.
* **구현 방식 및 소스 코드**:
  * 삭제 타겟 ID의 존재 유무를 확인하고, 임시 파일에 기존 행을 순차 이식하는 도중 타겟 ID가 발견되면 쓰기 동작을 이행하지 않고 건너뜀(None 처리)으로써 안전하게 원자적으로 삭제합니다.
  ```python
  # [repository.py:L84-L127] - Atomic Write를 적용한 거래 정보의 원자적 교체
  def update_or_delete_transaction(self, tx_id: str, updated_tx: Optional[Transaction]) -> bool:
      found = False
      # 1. 원본 경로와 같은 디스크 위치에 안전하게 임시 파일 생성
      temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, prefix="transactions_tmp_", suffix=".jsonl")
      try:
          with os.fdopen(temp_fd, "w", encoding="utf-8") as out_f:
              if os.path.exists(self.transactions_path):
                  with open(self.transactions_path, "r", encoding="utf-8") as in_f:
                      for line in in_f:
                          line = line.strip()
                          if not line: continue
                          data = json.loads(line)
                          if data.get("id") == tx_id: # 대상 ID 발견
                              found = True
                              if updated_tx is not None: # 수정 기입 (None이면 삭제)
                                  out_f.write(json.dumps(updated_tx.to_dict(), ensure_ascii=False) + "\n")
                          else:
                              out_f.write(line + "\n") # 타 객체는 원문 그대로 임시 파일 복사
          if found:
              # 2. 임시 파일 기록이 성공하면 원본 파일과 원자적 치환(OS atomic swap) 단행
              os.replace(temp_path, self.transactions_path)
          else:
              os.remove(temp_path) # 미발견 시 조용히 소각
      except Exception as e:
          if os.path.exists(temp_path):
              os.remove(temp_path) # 실패 시 임시 잔존 찌꺼기 완벽 클린업
          raise e
      return found
  ```

### 4.9 가져오기/내보내기 (import/export)
* **미션 기능 요구사항**:
  * `import --from <csv>`로 거래를 일괄 등록하고, `export --out <csv>`로 조건에 맞는 거래를 CSV로 저장합니다.
  * `export`는 `--month YYYY-MM` 또는 `--from YYYY-MM-DD --to YYYY-MM-DD` 중 하나 이상 조건을 필수로 받아 수행해야 합니다.
  * 고정된 CSV 스키마 규격을 전제해야 합니다.
* **구현 방식 및 소스 코드**:
  * 내보내기 시 지정 범위 필터를 거쳐 6열 규격으로 엑스포팅하며, 가져오기 시 유효성 검사에서 탈락한 깨진 행은 스킵하고 온전한 레코드만 부분 임포팅 완수 후 총 성공/스킵 수량을 통보합니다.
  ```python
  # [service.py:L370-L439] - 깨진 행 무시 및 결과 부분 성공 리포트 구현 일부
  def import_from_csv(self, filepath: str) -> Tuple[int, int]:
      # ... CSV 파일 및 컬럼 검증 수행 ...
      imported = 0
      skipped = 0
      with open(filepath, "r", encoding="utf-8") as f:
          reader = csv.DictReader(f)
          for row in reader:
              # 공백 정규화 기입
              clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None and v is not None}
              # ... 데이터 파싱 ...
              
              is_valid = True
              try:
                  # 개별 행 단위로 엄밀한 비즈니스 룰 유효성 정밀 검증
                  self.validate_fields(date_str, type_str, category_str, int(amount_str))
              except Exception:
                  is_valid = False # 유효하지 않은 포맷 발견
              
              if not is_valid:
                  skipped += 1 # 튕기지 않고 스킵 카운트만 올린 뒤 다음 루프 진행
                  continue
              
              # ... 통과 데이터만 파일 쓰기 완료 ...
              imported += 1
              
      return imported, skipped # 최종 통계 리턴
  ```

### 4.10 추가 조건 (최종 결과물의 필수 구성)
* **미션 기능 요구사항**:
  * 데이터는 3개 이상 파일로 영구 저장되어야 합니다.
  * `README.md`에 실행 방법, 저장 파일 위치/형식, 주요 명령 예시, `import/export` CSV 스키마가 표로 포함되어야 합니다.
* **구현 방식 및 소스 코드**:
  * transactions, categories, budgets, recurring 4종의 물리 저장 파일을 확보해 보존 상태를 통제하며, 본 사용자 가이드 파일에 모든 세부 구동 방식 및 스펙 테이블을 명기해 지침을 달성했습니다.
  ```python
  # [repository.py:L53-L72] - yield 스트리밍 기반 거래 정보 로딩
  def stream_transactions(self) -> Generator[Transaction, None, None]:
      if not os.path.exists(self.transactions_path):
          return
      with open(self.transactions_path, "r", encoding="utf-8") as f:
          for line in f: # 한 번에 한 라인씩 메모리에 적재 (메모리 버퍼 낭비 방지)
              line = line.strip()
              if not line:
                  continue
              try:
                  data = json.loads(line)
                  yield Transaction.from_dict(data) # yield 제너레이터를 사용하여 실시간 스트리밍 제공
              except (json.JSONDecodeError, KeyError):
                  continue # 손상 데이터 라인은 무시하고 다음 줄 진행
  ```

---

## 5. 보너스 과제 구현 및 공통 횡단 관심사 요구사항

### 5.1 백업 기능 (backup)
* **미션 요구사항**: 실행 시 타임스탬프가 포함된 복구 가능한 백업 압축 파일을 생성해야 합니다.
* **구현 소스 코드**: [service.py:L443-L469](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L443-L469)
```python
def create_backup(self) -> str:
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = os.path.join(self.repository.data_dir, "backups")
    os.makedirs(backup_dir, exist_ok=True)
    backup_path = os.path.join(backup_dir, f"backup_{timestamp}.zip")

    # 핵심 데이터 4개 지정
    files_to_backup = [
        self.repository.transactions_path,
        self.repository.categories_path,
        self.repository.budgets_path,
        self.repository.recurring_path
    ]
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_path in files_to_backup:
            if os.path.exists(file_path):
                zipf.write(file_path, os.path.basename(file_path)) # Zip 아카이빙
    return backup_path
```

### 5.2 반복 내역 기능 (recurring)
* **미션 요구사항**: 반복 내역 등록 및 특정 월 자동 생성을 지원하고 중복 유입 예외를 제어해야 합니다.
* **구현 소스 코드**: [service.py:L548-L614](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L548-L614)
```python
def generate_recurring_transactions(self, month: str) -> int:
    self.validate_month_format(month)
    # ... 마지막 일 및 템플릿 로딩 ...
    existing_txs = [tx for tx in self.repository.stream_transactions() if tx.date.startswith(month + "-")]
    generated_count = 0
    # ... 다음 ID 카운터 초기화 ...
    for t in templates:
        actual_day = min(t.day, last_day)
        date_str = f"{month}-{actual_day:02d}"
        
        # 중복 감지 비교: 날짜, 타입, 카테고리, 액수, 메모가 같고 태그에 'recurring'을 지녔는지 체크
        is_duplicate = False
        for etx in existing_txs:
            if (etx.date == date_str and etx.type == t.type and etx.category == t.category and
                etx.amount == t.amount and etx.memo == t.memo and "recurring" in etx.tags):
                is_duplicate = True
                break
        if not is_duplicate:
            # ... Transaction 생성 및 저장 실행 ...
            generated_count += 1
    return generated_count
```

### 5.3 CJK 한글 터미널 정렬 및 macOS IME 제어
* **미션 요구사항**: 외부 라이브러리 없이 터미널 UX 가독성을 테이블 문자열 정렬 등으로 보완해야 합니다.
* **구현 소스 코드**: [cli.py:L38-L83](file:///Users/mpeg46551/codyssey/b2_1/budget_app/cli.py#L38-L83) | [cli.py:L295-L313](file:///Users/mpeg46551/codyssey/b2_1/budget_app/cli.py#L295-L313)
```python
# macOS TIS C-API ctypes 동적 연동을 통한 강제 영문 입력 전환 오타 제어
def switch_to_english():
    try:
        cf = ctypes.cdll.LoadLibrary(ctypes.util.find_library('CoreFoundation'))
        carbon = ctypes.cdll.LoadLibrary(ctypes.util.find_library('Carbon'))
        utf8_str = cf.CFStringCreateWithCString(None, b"en", 0x08000100)
        source = carbon.TISCopyInputSourceForLanguage(utf8_str)
        cf.CFRelease(utf8_str)
        if source:
            carbon.TISSelectInputSource(source)
            cf.CFRelease(source)
    except Exception:
        pass

# unicodedata.east_asian_width 활용 터미널 CJK 2바이트 실제 가로 출력폭 보정 연산
def visual_len(s: str) -> int:
    width = 0
    for char in s:
        if unicodedata.east_asian_width(char) in ('W', 'F', 'A'):
            width += 2
        else:
            width += 1
    return width
```

### 5.4 공통 데코레이터 및 종료 코드 분리
* **미션 요구사항**: 부가 기능 분리(Decorator) 및 예외 처리 가이드를 출력하고, 정상 종료 `0` 및 비정상 종료 `비0` 코드를 반환해야 합니다.
* **구현 소스 코드**: [decorators.py:L20-L47](file:///Users/mpeg46551/codyssey/b2_1/budget_app/decorators.py#L20-L47)
```python
def catch_errors(func: Callable[..., Any]) -> Callable[..., Any]:
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except ValueError as e: # 값 유효 에러 포집
            print(f"[오류] {e}", file=sys.stderr)
            print("[힌트] 입력 형식을 확인하고 유효한 값을 입력해 주세요.", file=sys.stderr)
        except FileNotFoundError as e: # 파일 에러 포집
            print(f"[오류] 파일을 찾을 수 없습니다: {e}", file=sys.stderr)
        except Exception as e: # 스택트레이스 방어 및 우아한 리포트
            print(f"[오류] 실행 중 예외가 발생했습니다: {e}", file=sys.stderr)
    return wrapper
```

---

*※ 보다 세부적인 레이어 아키텍처 설계와 5대 구조 다이어그램에 관한 분석이 필요하신 경우 [code_review.md](file:///Users/mpeg46551/codyssey/b2_1/code_review.md) 파일을 참조해 주십시오.*
