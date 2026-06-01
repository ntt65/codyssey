# 파일 기반 가계부 콘솔 프로그램 (Budget App)

본 프로젝트는 파이썬 표준 라이브러리만을 활용하여 구축된 **유지보수 가능하고 예외 상황에서도 데이터가 안전한 파일 기반 가계부 콘솔 프로그램**입니다. 
제너레이터 스트리밍, 데코레이터 패턴, 타입 힌트 및 모듈화 설계를 완벽하게 적용하였습니다.

---

## 1. 실행 방법

본 프로그램은 `python3 -m budget_app` 명령을 통해 실행할 수 있습니다. 
패키지 경로 인식을 위해 가계부 루트 폴더(`/Users/mpeg46551/git/codyssey/b2_1`) 내에서 실행해 주십시오.

```bash
# 기본 사용 방법
python3 -m budget_app <command> [options]

# 도움말 보기 (전체 또는 개별 서브커맨드)
python3 -m budget_app --help
python3 -m budget_app search --help
```

---

## 2. 저장 파일 위치 및 형식

프로그램 실행 시 데이터는 지정된 저장 폴더 내에 저장되며, 기본 경로는 `./data`입니다.
`--data-dir <경로>` 옵션을 통해 데이터 디렉터리를 커스텀하게 설정할 수 있습니다.

```bash
# 커스텀 데이터 경로 지정 예시
python3 -m budget_app --data-dir ./my_custom_data list
```

### 저장 파일 구조 (JSONL 형식)
데이터 저장 안전성과 제너레이터 스트리밍 성능 극대화를 위해 개행 구분 JSON 형식인 **JSONL (JSON Lines)** 형식을 채택했습니다. 
- **거래 내역**: `data_dir/transactions.jsonl`
- **카테고리 목록**: `data_dir/categories.jsonl` (최초 실행 시 기본 카테고리가 자동 생성됩니다)
- **월별 예산**: `data_dir/budgets.jsonl`
- **반복 내역 템플릿**: `data_dir/recurring.jsonl`

---

## 3. CSV 가져오기/내보내기 (Import/Export) 스키마

`import` 및 `export` 명령 수행 시 고정된 CSV 스키마 규칙을 준수합니다. (UTF-8 인코딩, 첫 번째 행 헤더 포함)

| 열 이름 (Column) | 필수 여부 (Required) | 형식 및 설명 (Format) |
| :--- | :---: | :--- |
| **date** | Y | `YYYY-MM-DD` 형식 (날짜) |
| **type** | Y | `income` (수입) 또는 `expense` (지출) |
| **category** | Y | 가계부에 등록된 카테고리 중 하나 |
| **amount** | Y | 양수 정수 |
| **memo** | N | 문자열 (메모) |
| **tags** | N | 쉼표(`,`)로 구분된 태그 문자열 |

---

## 4. 주요 명령 및 사용 예시

### 1) 거래 내역 추가 (add) - 대화형
날짜, 타입, 카테고리, 금액 등을 대화형 콘솔 입력(`input()`)을 통해 순차적으로 입력받습니다. 잘못된 입력값이 오면 명확한 에러 원인과 힌트를 출력하고 다시 입력을 요구합니다.
```bash
$ python3 -m budget_app add
날짜(YYYY-MM-DD): 2024-01-15
타입(income/expense): expense
카테고리: food
금액(양수): 15000
메모(선택): 점심식사
태그(쉼표로 구분, 없으면 엔터): 점심,맛있는식사
[저장 완료] id=TX-000001
```

### 2) 거래 내역 목록 조회 (list)
최신 거래 등록 순으로 목록을 테이블 형태로 예쁘게 정렬하여 출력합니다.
```bash
$ python3 -m budget_app list --limit 5
id        | date       | type    | category | amount | memo    | tags
TX-000002 | 2024-01-16 | income  | salary   | 300000 | 1월 월급 | monthly
TX-000001 | 2024-01-15 | expense | food     | 15000  | 점심식사 | 점심,맛있는식사
```

### 3) 조건별 검색 (search)
날짜 범위, 카테고리, 타입, 메모 검색어, 태그 등의 옵션 필터를 지원합니다.
```bash
$ python3 -m budget_app search --from 2024-01-01 --to 2024-01-31 --category food --type expense
```

### 5) 월별 요약 및 예산 체크 (summary)
지정한 월의 총 수입, 총 지출, 잔액과 카테고리별 지출 상위 TOP N을 출력합니다. 예산이 설정된 달에는 예산 대비 사용률(%)과 초과 경고 문구를 출력합니다.
```bash
$ python3 -m budget_app summary --month 2024-01 --top 3
총 수입: 300000원
총 지출: 15000원
잔액: 285000원
예산: 100000원 (사용률 15.0%)

지출 TOP 3
1) food 15000원
```

### 6) 예산 설정 (budget set)
```bash
$ python3 -m budget_app budget set --month 2024-01 --amount 100000
[저장 완료] 2024-01 예산 100000원
```

### 7) 카테고리 관리 (category)
카테고리를 추가, 삭제, 목록 조회를 합니다. 삭제 시 해당 카테고리를 사용하는 기존 내역이 있다면 삭제를 안전하게 차단합니다.
```bash
$ python3 -m budget_app category list
- food
- transport
...

$ python3 -m budget_app category add
카테고리명: shopping
[저장 완료] category=shopping

$ python3 -m budget_app category remove
삭제할 카테고리명: shopping
[삭제 완료] category=shopping
```

### 8) 거래 수정 (update) - 대화형
수정하려는 ID를 인자로 넘겨주면, 각 필드의 기존 값을 대괄호`[]` 안에 보여주며 변경하고 싶지 않으면 엔터를 쳐서 그대로 보존할 수 있습니다.
```bash
$ python3 -m budget_app update --id TX-000001
날짜(YYYY-MM-DD) [2024-01-15]: 2024-01-15
타입(income/expense) [expense]: 
카테고리 [food]: 
금액(양수) [15000]: 16000
메모(선택) [점심식사]: 
태그(쉼표로 구분, 없으면 엔터) [점심,맛있는식사]: 
[수정 성공] id=TX-000001
```

### 9) 거래 삭제 (delete)
```bash
$ python3 -m budget_app delete --id TX-000001
[삭제 성공] id=TX-000001
```

### 10) 가져오기 및 내보내기 (import / export)
```bash
# 가져오기
python3 -m budget_app import --from data.csv

# 내보내기 (특정 달 또는 기간 필수 지정)
python3 -m budget_app export --out backup.csv --month 2024-01
```

### 11) 데이터 백업 (backup - 보너스 과제 1)
저장되어 있는 가계부 데이터(transactions, categories, budgets, recurring)를 하나의 타임스탬프 zip 파일로 압축하여 백업 폴더(`./data/backups/`)에 저장합니다.
```bash
$ python3 -m budget_app backup
[백업 완료] 백업 파일: ./data/backups/backup_20260601_201500.zip
```

### 12) 반복 내역 자동 관리 (recurring - 보너스 과제 2)
매달 고정적으로 지출/수입되는 월세, 월급 등을 규칙 템플릿으로 등록하고 특정 월에 일괄 자동 생성합니다. 중복 생성을 원천 방지하는 안전 알고리즘이 적용되어 있습니다.
```bash
# 반복 내역 등록 (일자 지정)
$ python3 -m budget_app recurring add
타입(income/expense): expense
카테고리: rent
금액(양수): 500000
매월 반복 일자(1-31): 25
메모(선택): 월세 납부
태그: 고정비
[저장 완료] template_id=REC-000001

# 반복 내역 목록 보기
$ python3 -m budget_app recurring list

# 특정 월에 반복 거래 내역 자동 생성
$ python3 -m budget_app recurring generate --month 2024-01
[생성 완료] 2024-01에 1건의 반복 거래 내역을 등록하였습니다.
```

---

## 5. 설계 및 기술적 특징 분석

이 프로그램은 교육적 목적과 유지보수 확장성을 고려하여 엄격한 아키텍처 규칙과 파이썬 고급 언어 특징들을 활용했습니다.

### 5.1 계층 구조 설계 (Layered Architecture) 및 책임 분리
코드 가독성과 쉬운 유지보수를 위해 계층 구조로 구조화했습니다.
- **모델 (`models.py`)**: `dataclass`를 사용하여 `Transaction` 및 `RecurringTemplate`의 데이터 규격(스키마)과 딕셔너리 직렬화/역직렬화 메서드만을 담당합니다.
- **저장소 (`repository.py`)**: 파일 시스템에 직접 접근해 데이터를 CRUD하고 파일의 존재 여부 보장, 순차적 ID 생성 등의 File I/O 기능을 캡슐화합니다.
- **서비스 (`service.py`)**: 비즈니스 로직(입력값 유효성 검증, 데이터 집계 및 계산, 중복 삽입 방지 검사, 백업 등)을 전담합니다.
- **CLI (`cli.py`, `__main__.py`)**: 사용자 입력 및 아규먼트를 파싱하고 테이블 정렬 포매팅 등 화면 입출력을 책임집니다.

### 5.2 제너레이터(Generator) 기반 파일 스트리밍 처리
대용량 트랜잭션 파일 상황에서도 메모리 오버플로우나 성능 저하가 발생하지 않도록 설계했습니다.
- **이유**: `read()`나 `readlines()`로 전체 파일의 내용을 한 번에 메모리에 적재하면 메모리 점유율이 데이터 크기에 비례하여 기하급수적으로 증가합니다. 
- **구현 방식**: `yield` 구문을 사용해 한 번에 파일의 단 한 줄(line)만 로드하여 파싱합니다.
  ```python
  def stream_transactions(self) -> Generator[Transaction, None, None]:
      if not os.path.exists(self.transactions_path):
          return
      with open(self.transactions_path, "r", encoding="utf-8") as f:
          for line in f:
              yield Transaction.from_dict(json.loads(line))
  ```
- **메모리 효율적 정렬 및 필터링 ($O(limit)$ 메모리)**:
  `list` 및 `search` 시 최신순으로 정렬하기 위해, 파일 내의 모든 레코드를 리스트로 받지 않고 **크기가 `limit`으로 고정된 리스트/힙 버퍼**만을 활용해 스트리밍 중에 실시간으로 최신 N개만 추려냄으로써 $O(\text{limit})$의 아주 작은 메모리 공간 복잡도 내에서 정렬 및 조회를 완료합니다.

### 5.3 데코레이터(Decorator)를 통한 공통 관심사 분리
로깅, 경과 시간 측정, 예외 처리 등의 공통 로직을 주 비즈니스 흐름과 분리해 유지보수성을 크게 높였습니다.
- **@catch_errors**: CLI 경계면에서 발생하는 예외를 잡아서 복잡한 파이썬 스택 트레이스를 숨기고 사용자 친화적인 원인과 힌트를 출력한 후, 올바른 비정상 종료 코드(0이 아닌 값)로 프로그램을 안전하게 종료시킵니다.
- **@measure_time**: 각 비즈니스 메서드의 경과 시간을 나노초/밀리초 수준에서 정밀 측정하여 로그를 stderr로 기록합니다.
- **@log_action**: 주요 트랜잭션 수명 주기 작업의 시작과 성공적인 마무리를 콘솔에 기록합니다.

### 5.4 타입 힌트(Type Hints)의 도입과 장점
모든 함수와 메서드의 인자, 리턴 타입에 명시적인 타입 힌트(`List`, `Dict`, `Tuple`, `Optional` 등)를 적용했습니다.
- **이유 및 이점**: 
  1. 개발자가 함수 시그니처만 보고도 어떤 구조의 입력값을 전달하고 어떤 결괏값을 받는지 파악할 수 있는 **명확한 개발 계약(Contract)** 역할을 수행합니다.
  2. IDE(Static Analyzer)가 타겟 유형이 다른 데이터를 할당하려 할 때 린트 오류로 즉각 알려주어 런타임 이전에 오류를 잡을 수 있습니다.
  ```python
  def export_to_csv(self, filepath: str, month: Optional[str] = None) -> int:
      ...
  ```

### 5.5 파일 저장 원자성(Atomicity) 강화
`update`, `delete`, `category remove`, `save_budgets` 등의 갱신형 연산 시, 원본 파일에 직접 수정 쓰기를 시도하다가 전원 공급 차단 등의 하드웨어 사고가 발생해 데이터가 날아가는 현상을 완벽하게 방지합니다.
- 임시 파일(`tempfile.mkstemp`)을 생성해 신규/정정 데이터를 우선 작성합니다.
- 쓰기가 정상적으로 완료되면 운영체제 수준에서 제공하는 원자적 덮어쓰기 기능인 `os.replace`를 사용하여 파일 교체를 완벽하게 완료합니다.
