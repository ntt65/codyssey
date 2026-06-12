# 💰 대화형 파일 기반 가계부 콘솔 프로그램 (budget_app) 사용자 가이드

본 가계부 애플리케이션(`budget_app`)은 파이썬 표준 라이브러리만을 활용해 최적화된 자원 관리(Generator)와 데이터 무결성 보호(Atomic Write)를 고려하여 구축된 강건한 콘솔 프로그램입니다.

---

## 1. 실행 방법 및 초기 기동

본 애플리케이션은 파이썬 패키지 실행 표준에 따라 가계부 루트 폴더 `/Users/mpeg46551/codyssey/b2_1` 내에서 가동합니다.

```bash
# 기본 데이터 경로(./data)를 기반으로 대화형 셸 실행
python3 -m budget_app

# 커스텀 데이터 경로를 옵션으로 지정하여 가동
python3 -m budget_app --data-dir ./my_custom_data
```

### 💡 패키지 구동 메커니즘
`python3 -m budget_app` 명령 기동 시 파이썬 인터프리터는 아래 순서로 파일을 분석합니다:
1. **패키지 초기화 (`__init__.py`)**: 패키지가 메모리에 로딩될 때 선행 실행되어 네임스페이스를 관리합니다.
2. **진입 스크립트 (`__main__.py`)**: 명령줄 인자를 파싱하고 `Repository -> Service -> InteractiveShell` 의존성을 결합해 셸을 정식 가동시킵니다.

---

## 2. 저장 파일 위치 및 포맷

모든 정보는 프로그램 종료 후에도 영구 유지되며, 데이터 안전성을 위해 3개 이상의 개별 JSONL 파일로 격리 저장됩니다.

* **거래 내역 파일**: `data_dir/transactions.jsonl`
* **카테고리 목록 파일**: `data_dir/categories.jsonl`
  * *초기 기동 정책*: 파일이 없거나 비어있는 경우 기본 권장 카테고리 9종(`food`, `transport`, `rent`, `shopping`, `health`, `education`, `salary`, `allowance`, `other`)이 원자적으로 자동 쓰여 보장됩니다.
* **월별 예산 한도 파일**: `data_dir/budgets.jsonl`
* **반복 내역 템플릿 파일**: `data_dir/recurring.jsonl`

---

## 3. CSV 가져오기/내보내기 (Import/Export) 스키마

외부 CSV 데이터와의 호환을 위해 헤더 및 UTF-8 인코딩을 포함하는 고정된 6열 스키마 규격을 전제합니다.

| 컬럼명 (Column) | 필수 여부 | 형식 및 내용 |
| :--- | :---: | :--- |
| **date** | Y | `YYYY-MM-DD` 형태의 유효 날짜 |
| **type** | Y | `income` (수입) 또는 `expense` (지출) |
| **category** | Y | 가계부에 등록되어 사용 가능한 카테고리 명칭 |
| **amount** | Y | 0보다 큰 양의 정수 금액 |
| **memo** | N | 선택적 상세 메모 문자열 |
| **tags** | N | 쉼표(`,`)로 나열된 거래 태그 문자열 |

---

## 4. 최종 결과물 10대 기능별 소스 구현 설명

### 4.1 거래 추가 (add)
* **설명**: 대화형 프롬프트를 통해 필드들을 순차적으로 입력받으며, 입력값들의 제약 규칙(날짜 포맷 및 윤년, 양수 금액, 등록 카테고리 여부)을 통합 검증한 뒤, 고유 거래 ID(TX-XXXXXX)를 채번해 영속 파일 끝에 추가 기록합니다.
* **소스 코드**: [service.py:L41-L68](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L41-L68)
```python
def add_transaction(self, date: str, type_str: str, category: str, amount: int, memo: str, tags: List[str]) -> str:
    # 1. 입력 필드의 비즈니스 제약 준수 여부 정밀 통합 검증
    self.validate_fields(date, type_str, category, amount)
    # 2. 다음 고유 거래 ID(TX-XXXXXX 형태) 순차 채번
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
    # 4. 저장소 파일의 끝에 데이터 직렬화 기입 수행
    self.repository.append_transaction(tx)
    return tx_id
```

### 4.2 거래 목록 (list)
* **설명**: 최신 날짜 및 최신 ID 역순에 맞춰 상위 `--limit N`개의 거래를 정렬 리스트로 축적하여 표 형식으로 출력합니다.
* **소스 코드**: [service.py:L70-L96](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L70-L96)
```python
def list_transactions(self, limit: int) -> List[Transaction]:
    top_txs: List[Transaction] = [] # 정렬 순서대로 최대 limit 만큼 보관할 인메모리 버퍼
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
* **설명**: 복합 필터 조건(기간 범위, 특정 카테고리, 수입/지출 분류, 메모 키워드, 특정 태그)을 실시간으로 감정하여 매칭되는 레코드들을 최신순으로 정렬 추출합니다.
* **소스 코드**: [service.py:L98-L150](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L98-L150)
```python
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

        # 2. 필터 통과 데이터를 정렬 버퍼에 삽입 정렬
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
* **설명**: 타겟 월의 총수입, 총지출, 최종 정산 잔액을 산출하고 지출 규모가 가장 막강한 카테고리 순위 TOP N을 예산 설정 정보와 조합 출력합니다.
* **소스 코드**: [service.py:L279-L324](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L279-L324)
```python
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
* **설명**: `YYYY-MM` 연월 키값과 해당 월의 한도 정수 금액을 입력받아 budgets 영속화 파일에 저장합니다.
* **소스 코드**: [service.py:L264-L278](file:///file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L264-L278)
```python
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
* **설명**: 신규 카테고리를 고유하게 등록하거나 조회하며, 삭제(`remove_category`) 시 거래 내역 중 해당 카테고리를 활용 중인 로그가 발견될 시 삭제를 강제 반려하여 데이터 참조 무결성을 지킵니다.
* **소스 코드**: [service.py:L223-L245](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L223-L245) | [service.py:L247-L260](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L247-L260)
```python
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
* **설명**: 정정하고자 하는 거래 ID의 정보를 수정합니다. 콘솔 프롬프트 수정 시 기존 보관값들을 미리 인라인 완성 형태로 채워주어 필요한 항목만 바로 수정 변경할 수 있습니다.
* **소스 코드**: [service.py:L152-L179](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L152-L179)
```python
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
* **설명**: 지정 고유 ID를 지닌 거래 내역을 삭제하며, 삭제 요청 전 2차 컨펌(y/n)을 질의합니다.
* **소스 코드**: [service.py:L180-L191](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L180-L191) | [repository.py:L84-L127](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L84-L127)
```python
# [service.py:L180-L191] - 삭제 비즈니스 연동
def delete_transaction(self, tx_id: str) -> bool:
    # 1. updated_tx 인자 자리에 None을 넘겨 해당 ID 행 복사를 유도 생략
    return self.repository.update_or_delete_transaction(tx_id, None)

# [repository.py:L84-L127] - update_or_delete_transaction 내부 교체 루프 일부
# 임시 파일을 안전하게 생성 후 라인 복사를 이행하다가, 타겟 ID 발견 시 updated_tx 유무 판정
if data.get("id") == tx_id:
    found = True
    if updated_tx is not None: # 수정(Update) 시 신규 데이터 기입
        out_f.write(json.dumps(updated_tx.to_dict(), ensure_ascii=False) + "\n")
    # None인 경우(Delete) out_f에 쓰기를 생략함으로써 타겟 라인이 제거된 복사본 임시 파일 완결
```

### 4.9 가져오기/내보내기 (import/export)
* **설명**: 조건(월별 또는 날짜 범위)에 맞는 기록을 UTF-8 CSV 규격으로 추출(export)하고 외부 CSV를 가져옵니다(import). 가져올 때 오류 데이터 행은 안전하게 스킵하고 정상 행만 임포팅하는 부분 성공(Partial Success) 결과 처리를 수행합니다.
* **소스 코드**: [service.py:L328-L368](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L328-L368) | [service.py:L370-L439](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L370-L439)
```python
def import_from_csv(self, filepath: str) -> Tuple[int, int]:
    # ... CSV 파일 경로 검증 및 헤더 검증 수행 ...
    imported = 0
    skipped = 0
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            clean_row = {k.strip(): v.strip() for k, v in row.items() if k is not None and v is not None}
            # ... 데이터 추출 ...
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

### 4.10 추가 조건 (최종 결과물의 필수 구성)
* **설명**: 데이터 무결성과 제너레이터 스트리밍 효율을 위해 4개 파일로 격격 구조화하여 데이터를 관리하며, 명령 예시 및 스키마에 관한 구동 가이드를 제시합니다.
* **소스 코드**: [repository.py:L33-L45](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L33-L45)
```python
def __init__(self, data_dir: str):
    self.data_dir = data_dir
    # 1. 거래 내역, 카테고리, 월별 예산, 정기 반복 템플릿 총 4종의 JSONL 물리 경로 확보
    self.transactions_path = os.path.join(data_dir, "transactions.jsonl")
    self.categories_path = os.path.join(data_dir, "categories.jsonl")
    self.budgets_path = os.path.join(data_dir, "budgets.jsonl")
    self.recurring_path = os.path.join(data_dir, "recurring.jsonl")
    # 2. 물리 저장소 디렉터리 존재 여부 보장
    self._ensure_dir()
```

---

## 5. 보너스 과제 구현 및 공통 횡단 관심사

### 5.1 백업 아카이브 기능 (backup)
* 현재 사용 중인 영속 가계부 파일 4개를 timestamp를 포함하는 고유 명칭의 단일 ZIP 아카이브 압축 파일로 수집 통합하여 backups 하위 안전 영역에 기입합니다.
* [service.py:L443-L469](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L443-L469)

### 5.2 반복 내역 다회 자동 기입 (recurring)
* 매월 고정 결제 및 급여 정보 템플릿(REC-ID)을 영구 등록한 뒤 실행 시 일괄 자동 기입합니다. 이때 생성일자, 거래유형, 액수 및 자동 생성 표식 태그(`recurring`)를 비교하여 기등록 동일 거래가 있을 시 필터 처리해 이중 생성을 완벽히 방지합니다.
* [service.py:L548-L614](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L548-L614)

### 5.3 CJK(한글) 터미널 테이블 격자 정렬 및 macOS IME 스위칭
* **한영 키 자동 강제 전환**: 사용자 명령어 오타 방지를 위해 `ctypes` 모듈을 이용해 macOS Carbon 및 CoreFoundation TIS API를 바인딩 호출하여, 셸 대기 전 한글 모드를 US English 영문 자판 상태로 프로그래밍 방식으로 자동 변환합니다.
* **CJK 문자 폭 보정 정렬**: 동아시아 한글의 시각적 너비를 2칸으로 자동 계산해 테이블 표의 가로 열 배치가 삐뚤어지지 않게 정렬 공백 수치 패딩을 수동 계산해 격자 형태로 출력합니다.
* [cli.py:L38-L83](file:///Users/mpeg46551/codyssey/b2_1/budget_app/cli.py#L38-L83) | [cli.py:L295-L313](file:///Users/mpeg46551/codyssey/b2_1/budget_app/cli.py#L295-L313) | [cli.py:L331-L364](file:///Users/mpeg46551/codyssey/b2_1/budget_app/cli.py#L331-L364)

### 5.4 공통 데코레이터 및 종료 코드 분리
* **@catch_errors 데코레이터**: 입출력 인터페이스의 경계면에서 발생하는 런타임 예외를 한곳으로 포집하여 스택트레이스 유출을 제어하고 해결을 위한 친화적 에러 힌트만 출력한 뒤 셸 명령어 루프를 보존 복원합니다.
* **종료 코드 (Exit Code) 격리**: 시작 초기화 단계 도중 발생한 크래시에 대해서는 종료 코드 `1`로 비정상 종료하고, 셸을 통한 정상 이탈(exit/quit/EOF)은 루프를 안전하게 탈출 후 코드 `0`을 리턴하도록 처리합니다.
* [decorators.py:L20-L47](file:///Users/mpeg46551/codyssey/b2_1/budget_app/decorators.py#L20-L47) | [__main__.py:L39-L48](file:///Users/mpeg46551/codyssey/b2_1/budget_app/__main__.py#L39-L48) | [cli.py:L675-L701](file:///Users/mpeg46551/codyssey/b2_1/budget_app/cli.py#L675-L701)

---

*※ 보다 세부적인 레이어 아키텍처 설계와 5대 구조 다이어그램에 관한 분석이 필요하신 경우 [code_review.md](file:///Users/mpeg46551/codyssey/b2_1/code_review.md) 파일을 참조해 주십시오.*
