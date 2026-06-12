# 파일 기반 가계부 콘솔 프로그램 만들기

## 1. 미션소개
* 이번에 만드는 건 콘솔 가계부인데, 제너레이터 스트리밍, 데코레이터 분리, 타입 힌트까지 구조를 제대로 챙깁니다. 단순한 프로그램이 아니라, 유지보수 가능한 설계로 완성한다는 관점으로 접근하세요.
* 이번 미션은 Python으로 파일 입출력 기반의 가계부 콘솔 프로그램을 구현하는 과제입니다. 수입과 지출 내역을 단순히 저장하는 수준을 넘어, 수정/삭제, 검색, 월별 요약, 카테고리 관리, 예산 초과 경고까지 포함한 "작은 서비스" 형태로 완성합니다.
* 학습자는 터미널에서 명령어를 입력해 내역을 추가하고(add), 목록을 조회하며(list), 특정 조건으로 검색하고(search), 월별 요약과 카테고리 리포트를 출력하고(summary), 데이터를 내보내고(export), 기존 파일을 가져오는(import) 기능을 구현합니다. 데이터는 프로그램 종료 후에도 유지되도록 JSONL 또는 CSV 파일로 영구 저장해야 합니다.
* 또한, 저장 파일을 한 번에 모두 읽지 않고 제너레이터로 스트리밍 처리하며, 데코레이터로 공통 기능(예외 처리, 실행 로그, 실행 시간 측정 등)을 분리합니다. 타입 힌트를 적용해 함수와 데이터 구조의 계약을 명확히 하고, 모듈 분리로 유지보수 가능한 구조를 설계합니다.

---

## 2. 과제목표 설명
* 파일 기반 저장(JSONL/CSV)으로 데이터를 영구 저장하고, CRUD/검색/요약/입출력을 구현할 수 있다.
* 콘솔 프로그램을 클래스/모듈로 구조화하고, 각 계층(모델/저장소/서비스/CLI)의 책임을 설명할 수 있다.
* `yield` 기반 제너레이터로 대용량 파일도 스트리밍 처리하는 이유와 동작 방식을 설명할 수 있다.
* 데코레이터로 공통 관심사(로그/예외/시간 측정)를 분리한 구조와 이유를 설명할 수 있다.
* 타입 힌트를 통해 입출력 계약을 명확히 했을 때 얻는 이점을 실제 코드 예로 설명할 수 있다.

---

## 3. 기능 요구 사항

### 3.1. 실행 및 입력 방식
* **미션 요구사항**:
  * 실행 예시는 아래 중 하나를 권장합니다.
    `python -m budget_app <command> [options]`
  * 모든 명령은 `--help` 옵션으로 사용 방법이 출력되어야 합니다.
  * 입력 기본 방식은 “대화형” 입니다 (예: `add` 실행 시 날짜/타입/카테고리/금액 등을 `input()`으로 순차 입력).
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

### 3.2. 데이터 모델
* **미션 요구사항**:
  * 거래 내역(`Transaction`)은 최소 아래 필드를 포함해야 합니다:
    `id`(유일), `type`(income/expense), `date`(YYYY-MM-DD), `amount`(양수), `category`, `memo`(선택), `tags`(선택)
  * 데이터 모델은 `dataclass` 또는 그에 준하는 구조로 정의해야 합니다.
  * 최소 2개 이상의 클래스를 사용해야 합니다 (예시: `Transaction`, `RecurringTemplate`, `FileRepository` 등).
* **구현 방식 및 소스 코드**:
  * `models.py` 내에 `dataclass` 형태로 `Transaction` 및 `RecurringTemplate` 클래스를 구현했습니다.
  ```python
  # [models.py:L18-L30] - Transaction 데이터 구조 정의
  @dataclass
  class Transaction:
      id: str                                                                   # 고유 거래 ID (예: TX-000001)
      type: str  # "income" or "expense"                                        # 거래 타입 ("income": 수입, "expense": 지출)
      date: str  # YYYY-MM-DD                                                   # 거래 날짜 (YYYY-MM-DD 포맷)
      amount: int  # positive integer                                           # 거래 금액 (양의 정수)
      category: str                                                             # 카테고리 명칭 (예: food, rent)
      memo: str = ""                                                            # 선택적 메모 문자열
      tags: List[str] = field(default_factory=list)                             # 쉼표 구분 선택적 태그 목록 리스트
  ```

### 3.3. 입력 검증
* **미션 요구사항**:
  * 날짜 형식 오류, 음수/0 금액, 허용되지 않은 `type`, 존재하지 않는 `category` 등은 재입력 요구 또는 오류 메시지 출력으로 처리합니다.
* **구현 방식 및 소스 코드**:
  * `service.py` 내부의 `validate_fields` 통합 검증 헬퍼 함수를 통해 잘못된 값을 필터링하고 `ValueError`를 던집니다.
  ```python
  # [service.py:L618-L636] - 입력 제약 규칙 통합 점검 코드
  def validate_fields(self, date: str, type_str: str, category: str, amount: int):
      self.validate_date_format(date)                                       # 날짜 포맷 규칙 확인
      if type_str not in ["income", "expense"]:
          raise ValueError(f"허용되지 않은 타입입니다: {type_str}")             # 허용 타입 외 차단
      categories = self.repository.load_categories()                         # 등록 카테고리 정보 로드
      if category not in categories:
          raise ValueError(f"존재하지 않는 카테고리입니다: {category}")             # 카테고리 미등록 단어 에러 차단
      if amount <= 0:
          raise ValueError(f"금액은 양수여야 합니다: {amount}")                 # 양수 금액 원칙 준수 확인
  ```

### 3.4. 저장 정책
* **미션 요구사항**:
  * 저장 포맷은 JSONL 또는 CSV 중 1개를 선택합니다 (본 프로젝트는 JSONL 채택).
  * 저장 파일은 3개 이상(필수)으로 분리해 영구 저장합니다 (`transactions.<fmt>`, `categories.<fmt>`, `budgets.<fmt>`).
  * 기본 저장 폴더는 `./data`를 권장하며, 옵션으로 변경 가능해야 합니다 (예: `-data-dir`).
* **구현 방식 및 소스 코드**:
  * `FileRepository`에서 저장 폴더 유연화 및 transactions, categories, budgets, recurring 4종의 JSONL 물리 분리 경로를 확보해 보존 상태를 통제합니다.
  ```python
  # [repository.py:L33-L45] - 4대 파일 물리 분리 및 자동 초기화
  def __init__(self, data_dir: str):
      self.data_dir = data_dir
      self.transactions_path = os.path.join(data_dir, "transactions.jsonl") # 1. 거래 내역 파일 경로
      self.categories_path = os.path.join(data_dir, "categories.jsonl")     # 2. 카테고리 파일 경로
      self.budgets_path = os.path.join(data_dir, "budgets.jsonl")           # 3. 예산 관리 파일 경로
      self.recurring_path = os.path.join(data_dir, "recurring.jsonl")       # 4. 반복거래 관리 파일 경로
      self._ensure_dir()                                                    # 데이터 저장 디렉터리 자동 생성 확인
  ```

### 3.5. 초기 실행(저장 파일이 없을 때)
* **미션 요구사항**:
  * 파일이 없으면 자동 생성하거나, “초기화 안내 메시지”를 출력해야 합니다.
  * 카테고리 파일이 비어있으면 아래 중 하나를 택해 동작을 명확히 하세요.
    * **(안 A)** 기본 카테고리 자동 생성 (예: food, transport, rent, etc)
    * **(안 B)** category add를 먼저 하도록 안내하고 add를 막음
  * 본 프로젝트는 **기본 카테고리 자동 생성 (안 A)**를 적용했습니다.
* **구현 방식 및 소스 코드**:
  * `load_categories` 시 카테고리 저장 파일이 없거나 비어있는 최초 구동 상태일 때 권장 기본 9종 카테고리를 파일에 원자적으로 자동 작성하고 반환합니다.
  ```python
  # [repository.py:L128-L156] - 초기 카테고리 로드 및 자동 복구
  def load_categories(self) -> List[str]:
      if not os.path.exists(self.categories_path):                          # 카테고리 저장 파일이 존재하지 않는 최초 구동 상태
          self.save_categories(self.get_default_categories())               # 기본 9종 카테고리를 파일에 원자적으로 작성
          return self.get_default_categories()                              # 기본 리스트 즉시 리턴
      
      categories = []
      with open(self.categories_path, "r", encoding="utf-8") as f:
          for line in f:
              line = line.strip()
              if not line: continue
              try:
                  data = json.loads(line)
                  categories.append(data["name"])
              except (json.JSONDecodeError, KeyError): continue
      if not categories:                                                    # 파일은 있으나 실제 내부 텍스트가 비어있을 때
          categories = self.get_default_categories()
          self.save_categories(categories)                                  # 기본 카테고리로 복구
      return categories
  ```

---

## 4. 최종 결과물

다음 10가지 기능이 정상 동작하는 애플리케이션 1개를 완성한다.

### 거래 추가(add)
* **입력/요청**: 대화형 입력(날짜, 타입, 카테고리, 금액, 메모/태그)
* **출력/화면**: 저장 성공 메시지 + 생성된 거래 id
* **미션 기능구현 요구사항**:
  * `add` 실행 후 대화형으로 필드를 입력받아 거래를 저장해야 합니다.
  * `category`는 등록된 목록에 존재해야 합니다 (없으면 안내 후 재입력/등록 유도).
  * 저장 완료 시 생성된 `id`를 사용자에게 출력해야 합니다.
* **구현 방식 및 소스 코드**:
  ```python
  # [service.py:L41-L68] - 거래 추가 구현 코드 및 주석
  def add_transaction(self, date: str, type_str: str, category: str, amount: int, memo: str, tags: List[str]) -> str:
      # 1. 입력 필드의 유효성(날짜 형식, 타입 검증, 금액 양수 여부 등) 통합 점검
      self.validate_fields(date, type_str, category, amount)
      # 2. 저장소 계층으로부터 순차 증가된 신규 고유 ID 채번
      tx_id = self.repository.get_next_transaction_id()
      # 3. 도메인 개체인 Transaction 인스턴스 구축
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

### 거래 목록(list)
* **입력/요청**: `-limit` 등 옵션
* **출력/화면**: 최신순 거래 리스트(스트리밍 처리)
* **미션 기능구현 요구사항**:
  * `list`는 최신순으로 거래를 출력해야 합니다.
  * `--limit N` 옵션을 지원해야 합니다 (기본값 제공).
  * 파일 전체를 한 번에 로드하지 않고, **제너레이터 기반 스트리밍 처리**로 구현해야 합니다.
* **구현 방식 및 소스 코드**:
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

### 거래 검색(search)
* **입력/요청**: `-from/--to`, `-category`, `-type`, `-q`, `-tag`
* **출력/화면**: 조건에 맞는 거래 리스트(최신순)
* **미션 기능구현 요구사항**:
  * 조건 기반 검색을 지원해야 합니다.
    * 기간: `--from`, `--to`
    * 카테고리: `--category`
    * 타입: `--type`
    * 메모 키워드: `--q`
    * 태그: `--tag`
  * 검색 결과는 최신순으로 출력해야 합니다.
  * 스트리밍 처리 (제너레이터 기반)를 유지해야 합니다.
* **구현 방식 및 소스 코드**:
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

### 월별 요약(summary)
* **입력/요청**: `-month YYYY-MM`, `-top N`
* **출력/화면**: 총수입/총지출/잔액 + 카테고리별 지출 TOP N
* **미션 기능구현 요구사항**:
  * `summary --month YYYY-MM` 입력을 받아 해당 월의 요약을 출력해야 합니다.
  * 출력 항목: 총 수입, 총 지출, 잔액 (총수입 - 총지출) 및 카테고리별 지출 합계 TOP N (`-top` 옵션 지원)
  * 데이터가 없는 달은 “데이터 없음”을 명확히 출력해야 합니다.
* **구현 방식 및 소스 코드**:
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

### 예산 설정/조회(budget)
* **입력/요청**: `budget set --month YYYY-MM --amount 금액`
* **출력/화면**: 저장 성공 메시지 + summary에서 예산 사용률/초과 경고
* **미션 기능구현 요구사항**:
  * `budget set --month YYYY-MM --amount <금액>`으로 월 예산을 저장해야 합니다.
  * `summary` 실행 시 예산이 설정되어 있으면 **예산 대비 사용률(%)** 및 **초과 여부 (초과 시 경고 문구)**를 함께 출력해야 합니다.
  * 예산 데이터도 반드시 영구 저장되어야 합니다.
* **구현 방식 및 소스 코드**:
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

### 카테고리 관리(category)
* **입력/요청**: `category add/list/remove`
* **출력/화면**: 카테고리 목록/추가/삭제 결과(사용 중 카테고리 처리 포함)
* **미션 기능구현 요구사항**:
  * `category add/list/remove`를 제공해야 합니다.
  * 카테고리 삭제 시, 해당 카테고리를 사용하는 내역이 존재하면 **삭제를 막거나 대체 카테고리를 요구**해야 합니다 (본 프로젝트는 **삭제 차단** 기법 채택).
* **구현 방식 및 소스 코드**:
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

### 거래 수정(update)
* **입력/요청**: `-id` 기반(옵션 방식 또는 대화형 중 1개로 고정)
* **출력/화면**: 수정 성공/실패 메시지(없는 id 처리 포함)
* **미션 기능구현 요구사항**:
  * **(안 A) 옵션 기반**: `update --id <id> [--date ...] [--type ...] [--category ...] [--amount ...] [--memo ...] [--tags ...]`
  * **(안 B) 대화형 기반**: 수정할 필드만 선택/재입력 받는 흐름 (본 프로젝트는 **대화형 기반 안 B** 채택)
  * 파일 기반 저장에서 `update`/`delete`는 “전체 재작성/임시 파일/원자적 교체(권장)” 등 안정성을 고려해야 합니다.
* **구현 방식 및 소스 코드**:
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

### 거래 삭제(delete)
* **입력/요청**: `delete --id <id>`
* **출력/화면**: 삭제 성공/실패 메시지(없는 id 처리 포함)
* **미션 기능구현 요구사항**:
  * `delete --id <id>`로 특정 거래를 삭제할 수 있어야 합니다.
  * 존재하지 않는 `id`는 “없는 데이터”로 처리하고 사용자 메시지를 출력해야 합니다.
  * 파일 기반 저장에서 `update`/`delete`는 “전체 재작성/임시 파일/원자적 교체(권장)” 등 안정성을 고려해야 합니다.
* **구현 방식 및 소스 코드**:
  ```python
  # [service.py:L180-L191] - 삭제 비즈니스 연동
  def delete_transaction(self, tx_id: str) -> bool:
      # 1. updated_tx 인자 자리에 None을 넘겨 해당 ID 행 복사를 유도 생략
      return self.repository.update_or_delete_transaction(tx_id, None)
  ```

### 가져오기/내보내기(import/export)
* **입력/요청**: `import --from <csv>`, `export --out <csv> --month ...` 또는 `-from/--to`
* **출력/화면**: 처리 건수 출력 + CSV 파일 생성/반영 확인
* **미션 기능구현 요구사항**:
  * `import --from <csv>`로 거래를 일괄 등록한다.
  * `export --out <csv>`로 조건에 맞는 거래를 CSV로 저장한다.
  * `export`는 `--month YYYY-MM` 또는 `--from YYYY-MM-DD --to YYYY-MM-DD` 중 하나 이상 조건을 필수로 받는다.
  * `import`/`export`는 CSV 최소 스키마를 고정한다.
* **구현 방식 및 소스 코드**:
  ```python
  # [service.py:L370-L439] - 깨진 행 무시 및 결과 부분 성공 리포트 구현 일부
  def import_from_csv(self, filepath: str) -> Tuple[int, int]:
      # ... CSV 파일 및 컬럼 검증 수행 ...
      imported = 0
      skipped = 0
      with open(filepath, "r", encoding="utf-8") as f:
          reader = csv.DictReader(f)
          for row in reader:
              clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None and v is not None}
              is_valid = True
              try:
                  # 1. 공통 유효성 검사 도구를 재사용해 개별 행 데이터 정합성 검증
                  self.validate_fields(date_str, type_str, category_str, int(amount_str))
              except Exception:
                  is_valid = False # 포맷 에러 시 False 플래그 처리
              
              if not is_valid:
                  # 2. 에러가 나더라도 전체 롤백하지 않고 해당 행만 스킵 처리하여 무결성 유지
                  skipped += 1
                  continue
              
              # ... 통과 데이터에 신규 ID를 매핑해 영속화 기입 ...
              imported += 1

      return imported, skipped # 3. 성공 건수 및 스킵 건수 결과 튜플 반환
  ```

### 추가 조건(최종 결과물의 필수 구성)
* **미션 기능구현 요구사항**:
  * 데이터는 3개 이상 파일로 영구 저장되어야 한다. (예: `transactions` / `categories` / `budgets`)
  * `README.md`에 실행 방법, 저장 파일 위치/형식, 주요 명령 예시, `import/export` CSV 스키마가 포함되어야 한다.
* **구현 방식 및 소스 코드**:
  * `FileRepository` 초기화 부분에서 데이터 정합성을 지키며 4가지 JSONL 개별 파일 경로를 구축해 독립 통제합니다.
  ```python
  # [repository.py:L33-L45] - 4대 파일 물리 분리 및 자동 초기화
  def __init__(self, data_dir: str):
      self.data_dir = data_dir
      self.transactions_path = os.path.join(data_dir, "transactions.jsonl") # 1. 거래 내역 파일 경로
      self.categories_path = os.path.join(data_dir, "categories.jsonl")     # 2. 카테고리 파일 경로
      self.budgets_path = os.path.join(data_dir, "budgets.jsonl")           # 3. 예산 관리 파일 경로
      self.recurring_path = os.path.join(data_dir, "recurring.jsonl")       # 4. 반복거래 관리 파일 경로
      self._ensure_dir()                                                    # 데이터 저장 디렉터리 자동 생성 확인
  ```

### 데코레이터(Decorator)
* **미션 기능구현 요구사항**:
  * 공통 관심사(예: 예외 처리/로그/시간 측정) 데코레이터를 1개 이상 구현하고 실제 적용한다.
* **구현 방식 및 소스 코드**:
  * `decorators.py`에 `@catch_errors`, `@measure_time`, `@log_action`를 구현하여 CLI 영역 오류 격리 및 시간 로깅을 횡단 관심사로 분리했습니다.
  ```python
  # [decorators.py:L20-L47] - 안전 프롬프트 환경을 위한 @catch_errors 데코레이터
  def catch_errors(func: Callable[..., Any]) -> Callable[..., Any]:
      @functools.wraps(func)
      def wrapper(*args, **kwargs):
          try:
              return func(*args, **kwargs)                                      # 실행 영역
          except ValueError as e:                                               # 데이터 규칙 에러 예외 격리
              print(f"[오류] {e}", file=sys.stderr)                              # 상세 오류 출력
              print("[힌트] 입력 형식을 확인하고 유효한 값을 입력해 주세요.", file=sys.stderr)
          except FileNotFoundError as e:                                        # 파일 손실 에러 격리
              print(f"[오류] 파일을 찾을 수 없습니다: {e}", file=sys.stderr)
              print("[힌트] 파일 경로가 정확한지, 또는 파일이 실제로 존재하는지 확인해 주세요.", file=sys.stderr)
          except PermissionError as e:                                          # IO 권한 에러 격리
              print(f"[오류] 파일 접근 권한이 없습니다: {e}", file=sys.stderr)
              print("[힌트] 대상 파일 또는 폴더의 쓰기/읽기 권한을 확인해 주세요.", file=sys.stderr)
          except Exception as e:                                                # 예측 외 오류 포착
              print(f"[오류] 실행 중 예외가 발생했습니다: {e}", file=sys.stderr)
              print("[힌트] 입력 파라미터를 다시 확인하시거나 저장 데이터가 손상되지 않았는지 점검해 주세요.", file=sys.stderr)
      return wrapper
  ```

### 예외 처리 및 종료 코드
* **미션 기능구현 요구사항**:
  * 오류는 스택트레이스 대신 원인 + 해결 힌트로 출력한다.
  * 정상 종료는 0, 오류 종료는 0이 아닌 값으로 종료한다.
* **구현 방식 및 소스 코드**:
  * 시작 시 디바이스 초기 장애에 대해서는 `sys.exit(1)`로 차단하고, 프롬프트 실행 오류 시에는 `@catch_errors`가 예외 포착 후 우아하게 셸을 유지하며 정상 탈출 시에는 루프를 이탈해 코드 0을 반환합니다.
  ```python
  # [__main__.py:L39-L48] - 초기 구동 실패 시의 exit code 1 처리
  try:
      repo = FileRepository(args.data_dir)                                  # 영속성 저장소 계층 인스턴스화
      service = BudgetService(repo)                                         # 서비스 조합 및 의존성 주입
      shell = InteractiveShell(service)                                     # CLI 콘솔 셸 빌드
      shell.run()                                                           # 대화형 프롬프트 루프 작동
  except Exception as e:
      print(f"[오류] 초기 구동 실패: {e}", file=sys.stderr)                   # stderr로 유효 에러 통지
      print("[힌트] 데이터 저장 경로의 읽기/쓰기 권한을 확인해 주세요.", file=sys.stderr)
      sys.exit(1)                                                           # 프로그램 비정상 마감 코드 반환 (1)
  ```

### 모듈화(구조화)
* **미션 기능구현 요구사항**:
  * 한 파일에 몰아넣지 않고 최소 3개 이상 모듈로 분리한다.
  * **(권장)** CLI / 서비스 / 저장소(파일 I/O) / 모델(데이터 구조)로 책임을 나눈다.
* **구현 방식 및 소스 코드**:
  * 레이어 아키텍처에 입각해 CLI(`cli.py`), Service(`service.py`), Repository(`repository.py`), Models(`models.py`), Decorators(`decorators.py`) 총 5개 핵심 모듈로 완전 계층 분리했습니다.
  ```python
  # 각 모듈 정의부
  from budget_app.models import Transaction, RecurringTemplate
  from budget_app.service import BudgetService
  from budget_app.repository import FileRepository
  from budget_app.decorators import catch_errors, measure_time, log_action
  ```

---

## 5. 보너스 과제 (선택)

### 백업 기능
* **미션 요구사항**:
  * `backup` 실행 시 타임스탬프가 포함된 백업 파일을 생성한다.
  * *배움 포인트*: 파일 처리 + 운영 안전장치(복구 가능성)
* **구현 방식 및 소스 코드**:
  * 타임스탬프 기반 ZIP 압축 파일을 backups 영역에 실시간 생성해 디바이스 복구 가능성을 제공합니다.
  ```python
  # [service.py:L443-L469] - 백업 ZIP 파일 생성
  def create_backup(self) -> str:
      timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
      backup_dir = os.path.join(self.repository.data_dir, "backups")
      os.makedirs(backup_dir, exist_ok=True)
      backup_path = os.path.join(backup_dir, f"backup_{timestamp}.zip")

      files_to_backup = [
          self.repository.transactions_path,
          self.repository.categories_path,
          self.repository.budgets_path,
          self.repository.recurring_path
      ]
      with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
          for file_path in files_to_backup:
              if os.path.exists(file_path):
                  zipf.write(file_path, os.path.basename(file_path))
      return backup_path
  ```

### 반복 내역 기능
* **미션 요구사항**:
  * 월급/월세처럼 반복되는 내역을 등록하고, 특정 월에 자동 생성한다.
  * *배움 포인트*: 규칙 기반 데이터 생성 + 예외 처리
* **구현 방식 및 소스 코드**:
  * 고정 결제 템플릿(REC-ID)을 활용해 타겟 연월에 다회 자동 기입하며, 중복 가산 방지를 위해 식별 태그(`recurring`) 비교 루틴을 내장했습니다.
  ```python
  # [service.py:L548-L614] - 반복 거래 일괄 생성 시의 중복 생성 검사 및 방지
  def generate_recurring_transactions(self, month: str) -> int:
      self.validate_month_format(month)
      # ... 템플릿 정보 로딩 ...
      existing_txs = [tx for tx in self.repository.stream_transactions() if tx.date.startswith(month + "-")]
      generated_count = 0
      # ... 다음 ID 발급 준비 ...
      for t in templates:
          actual_day = min(t.day, last_day)
          date_str = f"{month}-{actual_day:02d}"
          
          # 중복 감지 비교 로직: 날짜, 타입, 분류, 액수, 메모, 그리고 태그에 'recurring'을 가졌는지 비교 검증
          is_duplicate = False
          for etx in existing_txs:
              if (etx.date == date_str and etx.type == t.type and etx.category == t.category and
                  etx.amount == t.amount and etx.memo == t.memo and "recurring" in etx.tags):
                  is_duplicate = True
                  break
          if not is_duplicate:
              # ... Transaction 생성 및 append_transaction 기입 ...
              generated_count += 1
      return generated_count
  ```

### 출력 포맷 테이블 정렬
* **미션 요구사항**:
  * 외부 라이브러리 없이 문자열 정렬로 가독성을 개선한다.
  * *배움 포인트*: 콘솔 UX + 포맷터 분리
* **구현 방식 및 소스 코드**:
  * `unicodedata`를 활용해 CJK 동아시아 문자의 시각적 가로 너비를 2칸으로 자동 계산하여, 터미널 렌더링 시 컬럼 정렬 어긋남을 완벽 보정합니다.
  ```python
  # [cli.py:L295-L313] - east_asian_width 활용 CJK 폭 계산
  def visual_len(s: str) -> int:
      width = 0
      for char in s:
          if unicodedata.east_asian_width(char) in ('W', 'F', 'A'):
              width += 2
          else:
              width += 1
      return width
  ```

### 저장 원자성 강화
* **미션 요구사항**:
  * `update`/`delete` 시 임시 파일에 쓰고 `rename`으로 교체하는 방식을 적용한다.
  * *배움 포인트*: 파일 기반 트랜잭션/원자성 사고
* **구현 방식 및 소스 코드**:
  * `tempfile.mkstemp`로 변경분을 선기록한 후 완료 성공 시 운영체제 커널의 `os.replace`로 swap 치환함으로써 파일 정합성을 완벽 방어합니다.
  ```python
  # [repository.py:L84-L127] - update_or_delete_transaction 원자적 임시 쓰기 부분
  temp_fd, temp_path = tempfile.mkstemp(dir=self.data_dir, prefix="transactions_tmp_", suffix=".jsonl")
  try:
      # ... 임시 파일에 데이터 복사 쓰기 완수 ...
      if found:
          os.replace(temp_path, self.transactions_path) # 원자적 치환(Atomic Swap)으로 변경 확정
      else:
          os.remove(temp_path)
  except Exception as e:
      if os.path.exists(temp_path): os.remove(temp_path)
      raise e
  ```

---

## 6. 개발 환경
* **Python 3.10 이상** 환경에서 구동 및 테스트 검증이 완료되었습니다.

---

## 7. 제약 사항
* **라이브러리**: 표준 라이브러리만 사용 가능 (별도 `pip install`이 필요한 외부 라이브러리 사용 절대 금지)
* **저장 방식**: JSONL 또는 CSV 중 1개를 선택해 사용 (본 가계부는 JSONL을 사용)하며, 저장 파일은 최소 3개 이상 분리
* **CLI 규칙**: 옵션 표기는 리눅스 표준인 `--`로 통일
* **오류 처리**: 스택트레이스 출력 금지 (사용자 친화적 원인 + 해결 힌트 출력) 및 오류 종료 시 `exit code`는 0이 아니어야 함

---

## 8. 결과 예시

### add(거래 추가) 화면:
```text
$ python -m budget_app add
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심
태그(쉼표로 구분, 없으면 엔터): meal
[저장 완료] id=TX-000012
```

### list(거래 목록) 화면:
```text
$ python -m budget_app list --limit 3
TX-000012 | 2024-01-15 | expense | food | 15000 | 점심
TX-000011 | 2024-01-14 | income  | salary | 3000000 |
TX-000010 | 2024-01-12 | expense | transport | 20000 |
```

### category(카테고리 관리) 화면:
```text
$ python -m budget_app category add
카테고리명: food
[저장 완료] category=food

$ python -m budget_app category list
- food
- transport
```

### budget + summary(예산 + 월별 요약) 화면:
```text
$ python -m budget_app budget set --month 2024-01 --amount 500000
[저장 완료] 2024-01 예산 500000원

$ python -m budget_app summary --month 2024-01 --top 3
총 수입: 3000000원
총 지출: 215000원
잔액: 2785000원
예산: 500000원 (사용률 43.0%)

지출 TOP 3
1) rent 150000원
2) food 45000원
3) transport 20000원
```

### export / import(CSV 내보내기/가져오기) 화면:
```text
$ python -m budget_app export --out export.csv --month 2024-01
[완료] export.csv (12 records)

$ python -m budget_app import --from import.csv
[완료] imported=5, skipped=0
```

### 오류 출력(예시) 화면:
```text
$ python -m budget_app add
날짜(YYYY-MM-DD): 2024-13-40
[오류] 날짜 형식이 올바르지 않습니다 (YYYY-MM-DD).
[힌트] 예: 2024-01-15
```

---
*※ 보다 세부적인 레이어 아키텍처 설계와 5대 구조 다이어그램에 관한 분석이 필요하신 경우 [code_review.md](file:///Users/mpeg46551/codyssey/b2_1/code_review.md) 파일을 참조해 주십시오.*
