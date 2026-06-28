# 파일 기반 가계부 콘솔 프로그램 만들기

## 1. 미션소개
* 이번에 만드는 건 콘솔 가계부인데, 제너레이터 스트리밍, 데코레이터 분리, 타입 힌트까지 구조를 제대로 챙깁니다. 단순한 프로그램이 아니라, 유지보수 가능한 설계로 완성한다는 관점으로 접근.
* 이번 미션은 Python으로 파일 입출력 기반의 가계부 콘솔 프로그램을 구현하는 과제입니다. 수입과 지출 내역을 단순히 저장하는 수준을 넘어, 수정/삭제, 검색, 월별 요약, 카테고리 관리, 예산 초과 경고까지 포함한 "작은 서비스" 형태로 완성합니다.
* 학습자는 터미널에서 명령어를 입력해 내역을 추가하고(add), 목록을 조회하며(list), 특정 조건으로 검색하고(search), 월별 요약과 카테고리 리포트를 출력하고(summary), 데이터를 내보내고(export), 기존 파일을 가져오는(import) 기능을 구현합니다. 데이터는 프로그램 종료 후에도 유지되도록 JSONL 또는 CSV 파일로 영구 저장해야 합니다.
* 또한, 저장 파일을 한 번에 모두 읽지 않고 제너레이터로 스트리밍 처리하며, 데코레이터로 공통 기능(예외 처리, 실행 로그, 실행 시간 측정 등)을 분리합니다. 타입 힌트를 적용해 함수와 데이터 구조의 계약을 명확히 하고, 모듈 분리로 유지보수 가능한 구조를 설계합니다.

---

## 2. 과제목표
* 파일 기반 저장(JSONL/CSV)으로 데이터를 영구 저장하고, CRUD/검색/요약/입출력을 구현할 수 있다.
  - 달성 내용: 거래 내역, 카테고리, 예산, 반복 내역 데이터를 4개의 독립된 JSONL 파일(transactions.jsonl, categories.jsonl, budgets.jsonl, recurring.jsonl)로 분리하여 영구 저장합니다.
  - 안전성 (원자적 쓰기): 특히 파일 수정(Update) 및 삭제(Delete) 시 데이터 유실을 완벽히 방어하기 위해, 임시 파일(tempfile)에 먼저 기록한 후 OS 커널의 os.replace 연산으로 원본을 덮어씌우는 원자적 파일 교체(Atomic Swap) 기법을 적용해 완벽한 파일 CRUD를 구현했습니다. 관련 안전 처리는 [repository.py:L84-L127](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L84-L127)에서 직접 확인할 수 있습니다.

* 콘솔 프로그램을 클래스/모듈로 구조화하고, 각 계층(모델/저장소/서비스/CLI)의 책임을 설명할 수 있다.
  - [code review](file:///Users/mpeg46551/codyssey/b2_1/budget_app/readme.md)
  - 달성 내용: 철저한 **계층형 아키텍처(Layered Architecture)**와 **의존성 주입(DI)**을 도입하여 책임을 4개의 핵심 모듈로 완전히 분리했습니다.
  - [models.py](file:///Users/mpeg46551/codyssey/b2_1/budget_app/models.py): 데이터 구조 규격화 및 딕셔너리 직렬화/역직렬화(DTO) 전담.
  - [repository.py](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py): 물리적 파일 입출력, 임시 파일 교체 등 하드디스크 제어를 전담하는 데이터 영속성 계층.
  - [service.py](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py): 카테고리 참조 무결성 검증, 월별 집계, 중복 차단 등 핵심 비즈니스 로직 연산.
  - [cli.py](file:///Users/mpeg46551/codyssey/b2_1/budget_app/cli.py) & [__main__.py](file:///Users/mpeg46551/codyssey/b2_1/budget_app/__main__.py): 프롬프트 렌더링, 입력 보정(영어 자동 전환), 한글 크기 보정 정렬 테이블 출력 등 프레젠테이션(UI) 영역 통제.

* `yield` 기반 제너레이터로 대용량 파일도 스트리밍 처리하는 이유와 동작 방식을 설명할 수 있다.
  - [generator](file:///Users/mpeg46551/codyssey/b2_1/code_study.md)
  - 달성 내용: 수십만 건의 거래 데이터가 쌓여도 시스템 메모리가 고갈되지 않도록, 파일을 한 번에 배열로 읽어 들이지 않고 yield를 사용해 한 줄씩 실시간으로 파싱하는 스트리밍 구조를 채택했습니다.
  - 동작 방식 (O(limit) 정렬 버퍼): 목록 조회(list)나 검색(search) 시, 스트리밍으로 들어오는 데이터를 모두 리스트에 담지 않고, 사용자가 지정한 크기(limit)만큼의 고정된 정렬 버퍼만을 활용해 실시간으로 최신 N개만 추려냄으로써 메모리 복잡도를 O(limit) 수준으로 극대화하여 병목을 우회했습니다.
  - 상세 코드: [repository.py:L53-L72](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L53-L72)

* 데코레이터로 공통 관심사(로그/예외/시간 측정)를 분리한 구조와 이유를 설명할 수 있다.
  - 달성 내용: 핵심 비즈니스 로직에 예외 처리나 로그 코드가 뒤섞이는 것을 막기 위해 횡단 관심사를 데코레이터 패턴으로 분리했습니다.
  - `@catch_errors`: 대화형 CLI 경계에서 발생하는 파이썬 스택 트레이스 노출을 차단하고, 사용자에게 힌트만 출력한 뒤 프로그램 강제 종료 없이 셸을 우아하게 유지시킵니다.
  - `@measure_time`: 각 비즈니스 함수의 실행 소요 시간을 정밀하게 측정해 병목을 로깅합니다.
  - `@log_action`: 기능의 진입과 마감 상태를 기록하여 디버깅을 돕습니다.
  - 상세 코드는 [decorators.py:L20-L83](file:///Users/mpeg46551/codyssey/b2_1/budget_app/decorators.py#L20-L83)에서 볼 수 있습니다.

* 타입 힌트를 통해 입출력 계약을 명확히 했을 때 얻는 이점을 실제 코드 예로 설명할 수 있다.
  - 달성 내용: 모델 정의 및 서비스 계층에 적극적으로 타입 힌트를 지정하여 협업 안정성과 IDE 정적 분석(자동완성, 경고 등) 편의성을 확보했습니다.
  - 상세 코드: [models.py:L17-L28](file:///Users/mpeg46551/codyssey/b2_1/budget_app/models.py#L17-L28) / [service.py:L41-L68](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L41-L68)

---

## 3. 기능 요구 사항

### 3.1. 실행 및 입력 방식 (이중 실행 모드 - Dual-Mode Execution)
본 프로젝트는 과제의 **단발성 CLI 명령어 인터페이스** 요구사항과 사용자의 사용 편의성을 극대화하기 위해 직접 개발한 **대화형 상태 유지 셸(Interactive Shell)** 방식을 모두 만족하도록 **이중 실행 모드(Dual-Mode)**로 설계 및 구현되었습니다.

# 기본 데이터 폴더(./data) 경로로 대화형 셸 가동
  - python3 -m budget_app
  - python3 -m budget_app --help

## 대화형 (Interactive) 방식
  - 복잡한 값을 하나하나 입력해야 하는 거래 추가(add)와 수정(update)은 사용자의 편의와 정확성을 위해 대화형 프롬프트(input()) 방식을 채택했습니다.
  - 질문에 답하듯이 순차적으로 날짜, 타입, 금액 등을 기입하게 됩니다.
  - 참고로 update의 경우, 어떤 항목을 수정할지 특정하기 위해 명령어 옵션으로 ID를 먼저 전달(update --id TX-000001)한 뒤 대화형 수정 모드로 진입합니다.
  - 추가로, 기능 사용법이 기억나지 않을 때는 전체 프로그램뿐만 아니라 개별 서브 명령어 뒤에도 --help 옵션을 붙여(python3 -m budget_app search --help) 즉시 커맨드 사용법을 확인할 수 있습니다.
  - **대화형 셸 모드 인터랙션 특징**:
    - **입력기 영어 자동 전환**: macOS 환경에서 한글 오타 방지를 위해 ctypes로 CoreFoundation/Carbon API를 직접 동적 호출해 프롬프트 진입 시 키보드 입력 소스를 영문(US)으로 자동 강제 변환합니다.
    - **방향키 제어 및 자동완성**: 프롬프트 상에서 `Left/Right` 방향키로 사용 가능한 명령어를 순환하며 선택할 수 있고, `Up/Down` 방향키로 명령어 히스토리를 불러올 수 있으며, `Tab` 키 자동완성을 완벽하게 연동시켰습니다.
    - **Prefill (미리 입력 기능)**: 기본값 또는 수정할 기존 값이 프롬프트 창에 자동으로 채워진 상태로 출력되며, 아무 입력 없이 엔터를 치면 기본값으로 수락되고, 타이핑을 시작하거나 백스페이스를 누르면 깨끗하게 지워지고 새 입력이 받아집니다.

## 옵션 인자 (커맨드) 기반 방식
  - 데이터의 조회, 요약, 파일 입출력, 삭제 등 빠른 제어가 필요한 기능들(list, search, summary, export, import, delete)은 리눅스 표준 규격인 -- 기호를 사용하는 커맨드 옵션 방식으로 동작합니다.
  - 명령어 한 줄만 입력하면 대화형 프롬프트를 거치지 않고 즉시 결과를 출력합니다.
  - **CLI 모드 구동 방법**: `python3 -m budget_app <command> [options]` 형태로 실행하여 대화형 셸을 거치지 않고 즉시 개별 작업을 수행합니다.
  - 사용 예시:
    * 조건 검색: python3 -m budget_app search --from 2026-06-01 --to 2026-06-30 --category food
    * 목록 조회: python3 -m budget_app list --limit 5
    * 거래 삭제: python3 -m budget_app delete --id TX-000001
    * 월별 요약: python3 -m budget_app summary --month 2026-06 --top 3
    * 예산 설정: python3 -m budget_app budget set --month 2026-06 --amount 1000000
    * 카테고리 관리: python3 -m budget_app category list
    * 반복 내역 생성: python3 -m budget_app recurring generate --month 2026-06

# 전체 프로그램 또는 개별 명령어 도움말 확인
  - python3 -m budget_app --help
  - python3 -m budget_app search --help

# 커스텀 데이터 경로를 지정하여 가동
  - python3 -m budget_app --data-dir ./my_custom_data

  ```bash
  # 기본 ./data 폴더 경로 대화형 가동
  python3 -m budget_app

  # 커스텀 data 경로 지정 가동
  python3 -m budget_app --data-dir ./my_custom_data
  ```

#### 3. 모드 라우팅 및 연동 원리 (Entrypoint Routing)
`__main__.py`에서 `argparse`를 활용하여 명령어 인자가 제공되었는지 여부에 따라 실행 제어권을 동적으로 분기합니다.
* 상세 코드: [__main__.py:L120-L123](file:///Users/mpeg46551/codyssey/b2_1/budget_app/__main__.py#L120-L123)

---

### 3.2. 데이터 모델
* **미션 요구사항**:
  * 거래 내역(`Transaction`)은 최소 아래 필드를 포함해야 합니다:
    `id`(유일), `type`(income/expense), `date`(YYYY-MM-DD), `amount`(양수), `category`, `memo`(선택), `tags`(선택)
  * 데이터 모델은 `dataclass` 또는 그에 준하는 구조로 정의해야 합니다.
  * 최소 2개 이상의 클래스를 사용해야 합니다 (예시: `Transaction`, `RecurringTemplate`, `FileRepository` 등).
* **구현 방식 및 소스 코드**:
  * `models.py` 내에 `dataclass` 형태로 `Transaction` 및 `RecurringTemplate` 클래스를 구현했습니다.
  * 상세 코드: [models.py:L17-L28](file:///Users/mpeg46551/codyssey/b2_1/budget_app/models.py#L17-L28)

### 3.3. 입력 검증
* **미션 요구사항**:
  * 날짜 형식 오류, 음수/0 금액, 허용되지 않은 `type`, 존재하지 않는 `category` 등은 재입력 요구 또는 오류 메시지 출력으로 처리합니다.
* **구현 방식 및 소스 코드**:
  * `service.py` 내부의 `validate_fields` 통합 검증 헬퍼 함수를 통해 잘못된 값을 필터링하고 `ValueError`를 던집니다.
  * 상세 코드: [service.py:L616-L634](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L616-L634)

### 3.4. 저장 정책
* **미션 요구사항**:
  * 저장 포맷은 JSONL 또는 CSV 중 1개를 선택합니다 (본 프로젝트는 JSONL 채택).
  * 저장 파일은 3개 이상(필수)으로 분리해 영구 저장합니다 (`transactions.<fmt>`, `categories.<fmt>`, `budgets.<fmt>`).
  * 기본 저장 폴더는 `./data`를 권장하며, 옵션으로 변경 가능해야 합니다 (예: `-data-dir`).
* **구현 방식 및 소스 코드**:
  * `FileRepository`에서 저장 폴더 유연화 및 transactions, categories, budgets, recurring 4종의 JSONL 물리 분리 경로를 확보해 보존 상태를 통제합니다.
  * 상세 코드: [repository.py:L33-L45](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L33-L45)

### 3.5. 초기 실행(저장 파일이 없을 때)
* **미션 요구사항**:
  * 파일이 없으면 자동 생성하거나, “초기화 안내 메시지”를 출력해야 합니다.
  * 카테고리 파일이 비어있으면 아래 중 하나를 택해 동작을 명확히 하세요.
    * **(안 A)** 기본 카테고리 자동 생성 (예: food, transport, rent, etc)
    * **(안 B)** category add를 먼저 하도록 안내하고 add를 막음
  * 본 프로젝트는 **기본 카테고리 자동 생성 (안 A)**를 적용했습니다.
* **구현 방식 및 소스 코드**:
  * `load_categories` 시 카테고리 저장 파일이 없거나 비어있는 최초 구동 상태일 때 권장 기본 9종 카테고리를 파일에 원자적으로 자동 작성하고 반환합니다.
  * 상세 코드: [repository.py:L128-L156](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L128-L156)

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
  * 입력 필드의 유효성(날짜 형식, 타입 검증, 금액 양수 여부 등) 통합 점검 후 순차 증가된 신규 고유 ID를 채번하여 파일 끝에 기입합니다.
  * 상세 코드: [service.py:L41-L68](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L41-L68)

### 거래 목록(list)
* **입력/요청**: `-limit` 등 옵션
* **출력/화면**: 최신순 거래 리스트(스트리밍 처리)
* **미션 기능구현 요구사항**:
  * `list`는 최신순으로 거래를 출력해야 합니다.
  * `--limit N` 옵션을 지원해야 합니다 (기본값 제공).
  * 파일 전체를 한 번에 로드하지 않고, **제너레이터 기반 스트리밍 처리**로 구현해야 합니다.
* **구현 방식 및 소스 코드**:
  * `stream_transactions` 제너레이터로부터 한 줄씩 순차 로딩하여, limit 버퍼 크기 제약을 지켜 정밀 메모리(O(limit)) 점유율을 유지하며 최신 거래를 추출합니다.
  * 상세 코드: [service.py:L70-L96](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L70-L96)

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
  * 제너레이터 스트리밍 도중 필터링을 실시간 단행하며 최신순 정렬 버퍼에 삽입해 결과를 선별합니다.
  * 상세 코드: [service.py:L98-L150](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L98-L150)

### 월별 요약(summary)
* **입력/요청**: `-month YYYY-MM`, `-top N`
* **출력/화면**: 총수입/총지출/잔액 + 카테고리별 지출 TOP N
* **미션 기능구현 요구사항**:
  * `summary --month YYYY-MM` 입력을 받아 해당 월의 요약을 출력해야 합니다.
  * 출력 항목: 총 수입, 총 지출, 잔액 (총수입 - 총지출) 및 카테고리별 지출 합계 TOP N (`-top` 옵션 지원)
  * 데이터가 없는 달은 “데이터 없음”을 명확히 출력해야 합니다.
* **구현 방식 및 소스 코드**:
  * 해당 월에 부합하는 거래들을 스트리밍 합산하고, 카테고리별 정렬 후 TOP N과 설정 예산 한도액 조회를 수행합니다.
  * 상세 코드: [service.py:L279-L324](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L279-L324)

### 예산 설정/조회(budget)
* **입력/요청**: `budget set --month YYYY-MM --amount 금액`
* **출력/화면**: 저장 성공 메시지 + summary에서 예산 사용률/초과 경고
* **미션 기능구현 요구사항**:
  * `budget set --month YYYY-MM --amount <금액>`으로 월 예산을 저장해야 합니다.
  * `summary` 실행 시 예산이 설정되어 있으면 **예산 대비 사용률(%)** 및 **초과 여부 (초과 시 경고 문구)**를 함께 출력해야 합니다.
  * 예산 데이터도 반드시 영구 저장되어야 합니다.
* **구현 방식 및 소스 코드**:
  * 기존 예산 맵을 조회해 갱신하고, 임시 파일 치환 전략(Atomic Swap)으로 안정성을 유지하며 예산을 영속 파일에 저장합니다.
  * 상세 코드: [service.py:L264-L278](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L264-L278)

### 카테고리 관리(category)
* **입력/요청**: `category add/list/remove`
* **출력/화면**: 카테고리 목록/추가/삭제 결과(사용 중 카테고리 처리 포함)
* **미션 기능구현 요구사항**:
  * `category add/list/remove`를 제공해야 합니다.
  * 카테고리 삭제 시, 해당 카테고리를 사용하는 내역이 존재하면 **삭제를 막거나 대체 카테고리를 요구**해야 합니다 (본 프로젝트는 **삭제 차단** 기법 채택).
* **구현 방식 및 소스 코드**:
  * 가계부 전체 거래 내역을 실시간 스캔하여 무결성을 검증하고 사용 중인 카테고리가 있을 시 에러를 던져 삭제를 반려합니다.
  * 상세 코드: [service.py:L223-L245](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L223-L245)

### 거래 수정(update)
* **입력/요청**: `-id` 기반(옵션 방식 또는 대화형 중 1개로 고정)
* **출력/화면**: 수정 성공/실패 메시지(없는 id 처리 포함)
* **미션 기능구현 요구사항**:
  * **(안 A) 옵션 기반**: `update --id <id> [--date ...] [--type ...] [--category ...] [--amount ...] [--memo ...] [--tags ...]`
  * **(안 B) 대화형 기반**: 수정할 필드만 선택/재입력 받는 흐름 (본 프로젝트는 **대화형 기반 안 B** 채택)
  * 파일 기반 저장에서 `update`/`delete`는 “전체 재작성/임시 파일/원자적 교체(권장)” 등 안정성을 고려해야 합니다.
* **구현 방식 및 소스 코드**:
  * 갱신할 데이터 필드를 검증 및 머지해 임시 파일 복사 후 원자적 교체 전략으로 디스크에 안전하게 갱신 저장합니다.
  * 상세 코드: [service.py:L152-L179](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L152-L179)

### 거래 삭제(delete)
* **입력/요청**: `delete --id <id>`
* **출력/화면**: 삭제 성공/실패 메시지(없는 id 처리 포함)
* **미션 기능구현 요구사항**:
  * `delete --id <id>`로 특정 거래를 삭제할 수 있어야 합니다.
  * 존재하지 않는 `id`는 “없는 데이터”로 처리하고 사용자 메시지를 출력해야 합니다.
  * 파일 기반 저장에서 `update`/`delete`는 “전체 재작성/임시 파일/원자적 교체(권장)” 등 안정성을 고려해야 합니다.
* **구현 방식 및 소스 코드**:
  * 임시 파일 복제 기입 도중 대상 ID만 복제 대상에서 생략하여 원본을 덮어씌워 안전하게 삭제를 처리합니다.
  * 상세 코드: [service.py:L180-L191](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L180-L191)

### 가져오기/내보내기(import/export)
* **입력/요청**: `import --from <csv>`, `export --out <csv> --month ...` 또는 `-from/--to`
* **출력/화면**: 처리 건수 출력 + CSV 파일 생성/반영 확인
* **미션 기능구현 요구사항**:
  * `import --from <csv>`로 거래를 일괄 등록한다.
  * `export --out <csv>`로 조건에 맞는 거래를 CSV로 저장한다.
  * `export`는 `--month YYYY-MM` 또는 `--from YYYY-MM-DD --to YYYY-MM-DD` 중 하나 이상 조건을 필수로 받는다.
  * `import`/`export`는 CSV 최소 스키마를 고정한다.
* **구현 방식 및 소스 코드**:
  * CSV 파일을 한 행씩 읽으면서 데이터 규칙 정합성을 개별적으로 확인하고 포맷 에러가 발생한 행은 스킵해 안전성을 지키며 일괄 가져옵니다.
  * 상세 코드: [service.py:L368-L439](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L368-L439)

### 추가 조건(최종 결과물의 필수 구성)
* **미션 기능구현 요구사항**:
  * 데이터는 3개 이상 파일로 영구 저장되어야 한다. (예: `transactions` / `categories` / `budgets`)
  * `README.md`에 실행 방법, 저장 파일 위치/형식, 주요 명령 예시, `import/export` CSV 스키마가 포함되어야 한다.
* **구현 방식 및 소스 코드**:
  * 4가지 코어 데이터를 JSONL 파일 형태로 각각 경로 분리하여 초기화 및 독립 통제합니다.
  * 상세 코드: [repository.py:L33-L45](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L33-L45)

### 데코레이터(Decorator)
* **미션 기능구현 요구사항**:
  * 공통 관심사(예: 예외 처리/로그/시간 측정) 데코레이터를 1개 이상 구현하고 적용한다.
* **구현 방식 및 소스 코드**:
  * 예외 격리 처리를 전담하는 `@catch_errors`, 시간 측정을 담당하는 `@measure_time` 등 횡단 관심사 공통 제어기를 분리 구현했습니다.
  * 상세 코드: [decorators.py:L20-L47](file:///Users/mpeg46551/codyssey/b2_1/budget_app/decorators.py#L20-L47)

### 예외 처리 및 종료 코드
* **미션 기능구현 요구사항**:
  * 오류는 스택트레이스 대신 원인 + 해결 힌트로 출력한다.
  * 정상 종료는 0, 오류 종료는 0이 아닌 값으로 종료한다.
* **구현 방식 및 소스 코드**:
  * 초기 디렉터리 등 구동 오류 실패에 한해 `exit code` 1로 반환하고, 대화형 프로그램 중에는 데코레이터가 친화적 오류 메시지를 제공합니다.
  * 상세 코드: [__main__.py:L111-L118](file:///Users/mpeg46551/codyssey/b2_1/budget_app/__main__.py#L111-L118)

### 모듈화(구조화)
* **미션 요구사항**:
  * 한 파일에 몰아넣지 않고 최소 3개 이상 모듈로 분리한다.
  * **(권장)** CLI / 서비스 / 저장소(파일 I/O) / 모델(데이터 구조)로 책임을 나눈다.
* **구현 방식 및 소스 코드**:
  * CLI, Service, Repository, Models, Decorators 레이어를 정교히 분리하여 결합도를 낮추고 책임을 이관시켰습니다.
  * 상세 임포트 구문: [cli.py:L41-L45](file:///Users/mpeg46551/codyssey/b2_1/budget_app/cli.py#L41-L45)

---

## 5. 보너스 과제 (선택)

### 백업 기능
* **미션 요구사항**:
  * `backup` 실행 시 타임스탬프가 포함된 백업 파일을 생성한다.
  * *배움 포인트*: 파일 처리 + 운영 안전장치(복구 가능성)
* **구현 방식 및 소스 코드**:
  * 4종 코어 데이터 파일을 ZIP 포맷으로 합축 번들하여 backups 폴더 영역에 영구 보존합니다.
  * 상세 코드: [service.py:L441-L469](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L441-L469)

### 반복 내역 기능
* **미션 요구사항**:
  * 월급/월세처럼 반복되는 내역을 등록하고, 특정 월에 자동 생성한다.
  * *배움 포인트*: 규칙 기반 데이터 생성 + 예외 처리
* **구현 방식 및 소스 코드**:
  * `recurring` 템플릿 규칙들을 적재하고, 대상 월 생성 시 `recurring` 태그 값을 대조 비교해 안전하게 자동 생성합니다.
  * 상세 코드: [service.py:L546-L614](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L546-L614)

### 출력 포맷 테이블 정렬
* **미션 요구사항**:
  * 외부 라이브러리 없이 문자열 정렬로 가독성을 개선한다.
  * *배움 포인트*: 콘솔 UX + 포맷터 분리
* **구현 방식 및 소스 코드**:
  * `unicodedata.east_asian_width`를 판정해 CJK 가로 너비를 보정 연산합니다.
  * 상세 코드: [cli.py:L298-L313](file:///Users/mpeg46551/codyssey/b2_1/budget_app/cli.py#L298-L313)

### 저장 원자성 강화
* **미션 요구사항**:
  * `update`/`delete` 시 임시 파일에 쓰고 `rename`으로 교체하는 방식을 적용한다.
  * *배움 포인트*: 파일 기반 트랜잭션/원자성 사고
* **구현 방식 및 소스 코드**:
  * 변경 데이터를 `mkstemp` 임시 저장소에 선기록하고 쓰기 마감 완료 시 커널 `os.replace`로 atomic 치환합니다.
  * 상세 코드: [repository.py:L84-L127](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L84-L127)

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
```bash
mpeg46551@cx2r6s2 b2_1 %  python3 -m budget_app add 
[새 거래 추가를 시작합니다]
- 날짜 (YYYY-MM-DD): 2026-06-28
- 타입 (income /expense ): 
[정보] 입력이 생략되어 기본값 'expense'(으)로 적용되었습니다.
- 카테고리 (food /transport /rent /shopping /health /education /salary /allowance /other ): food
- 금액 (10000 /30000 /50000 ): 10000
- 메모 (선택) (점심 /저녁 /월세 /마트 ): 점심
- 태그 (선택) (식대 /생필품 /고정비 /교통 ): 식대
[저장 완료] id=TX-000024
id        | date       | type    | category | amount   | memo | tags
----------+------------+---------+----------+----------+------+-----
TX-000024 | 2026-06-28 | expense | food     | 10,000원 | 점심 | 식대
```

### list(거래 목록) 화면:
```bash
mpeg46551@cx2r6s2 b2_1 %  python3 -m budget_app list
id        | date       | type    | category  | amount   | memo | tags  
----------+------------+---------+-----------+----------+------+-------
TX-000011 | 2026-06-28 | income  | other     | 50,000원 | 저녁 | 고정비
TX-000010 | 2026-06-28 | expense | food      | 10,000원 | 점심 | 식대  
TX-000009 | 2026-06-01 | expense | food      | 10,000원 | 점심 | 식대  
TX-000008 | 2026-06-01 | expense | food      | 10,000원 |      |       
TX-000007 | 2026-06-01 | expense | food      | 10,000원 |      |       
TX-000006 | 2026-06-01 | expense | food      | 50,000원 |      | 생필품
TX-000005 | 2026-06-01 | income  | food      | 10,000원 |      |       
TX-000004 | 2026-06-01 | income  | food      | 10,000원 | 마트 | 식대  
TX-000003 | 2026-06-01 | income  | food      | 10,000원 | 점심 | 식대  
TX-000002 | 2026-06-01 | income  | education | 10,000원 | 점심 | 교통  
```

### category(카테고리 관리) 화면:
```bash
mpeg46551@cx2r6s2 b2_1 %  python3 -m budget_app category

[카테고리 설정 관리]
1. 등록된 카테고리 목록 조회
2. 신규 카테고리 추가
3. 기존 카테고리 삭제
엔터: 상위 메뉴로 이동
메뉴 선택 (1 /2 /3 ): 1
- food
- transport
- rent
- shopping
- health
- education
- salary
- allowance

[카테고리 설정 관리]
1. 등록된 카테고리 목록 조회
2. 신규 카테고리 추가
3. 기존 카테고리 삭제
엔터: 상위 메뉴로 이동
메뉴 선택 (1 /2 /3 ): 
```

### recurring(반복 고정 거래 관리) 화면:
```bash
mpeg46551@cx2r6s2 b2_1 %  python3 -m budget_app recurring

[매월 반복 고정 거래 관리 메뉴]
1. 등록된 반복 템플릿 목록 조회
2. 신규 반복 템플릿 등록
3. 기존 반복 템플릿 삭제
4. 특정 월 반복 거래 일괄 생성
엔터: 상위 메뉴로 이동
선택 (1 /2 /3 /4 ): 1
등록된 반복 내역이 없습니다.

[매월 반복 고정 거래 관리 메뉴]
1. 등록된 반복 템플릿 목록 조회
2. 신규 반복 템플릿 등록
3. 기존 반복 템플릿 삭제
4. 특정 월 반복 거래 일괄 생성
엔터: 상위 메뉴로 이동
선택 (1 /2 /3 /4 ): 
```

### budget 예산  설정 화면:
```bash
mpeg46551@cx2r6s2 b2_1 %  python3 -m budget_app budget  
- 예산을 책정할 대상 월 (YYYY-MM): 2026-06
- 한도 금액 (0 이상 정수) (500000 /1000000 ): 1000000
[저장 완료] 2026-06 예산 1,000,000원 설정 완료.
```

### summary(예산 + 월별 요약) 화면:
```bash
mpeg46551@cx2r6s2 b2_1 %  python3 -m budget_app summary
- 요약할 대상 월 (YYYY-MM): 2026-06
==================================================
   📊 2026-06 재정 요약 리포트
==================================================
- 총 수입: 105,000원
- 총 지출: 90,000원
- 잔액: 15,000원
- 책정 예산: 1,000,000원 (사용률: 9.0%)

[ 지출 TOP 3 카테고리 ]
1) food : 90,000원 (100.0%)
==================================================
```

### export / import(CSV 내보내기/가져오기) 화면:
```bash
mpeg46551@cx2r6s2 b2_1 %  python3 -m budget_app export
- 내보낼 CSV 파일 경로: backup.csv
- 필터 방식 선택 (1: 월별, 2: 기간, 엔터: 필터 없음) (1 /2 ): 
[내보내기 진행 중...]
[완료] backup.csv 파일로 11건의 기록을 성공적으로 추출 및 저장했습니다.
mpeg46551@cx2r6s2 b2_1 %  python3 -m budget_app export
- 내보낼 CSV 파일 경로: backup.csv
- 필터 방식 선택 (1: 월별, 2: 기간, 엔터: 필터 없음) (1 /2 ): 1
내보낼 대상 월 (YYYY-MM): 2026-06
[내보내기 진행 중...]
[완료] backup.csv 파일로 11건의 기록을 성공적으로 추출 및 저장했습니다.
mpeg46551@cx2r6s2 b2_1 %  python3 -m budget_app import
- 가져올 CSV 파일 경로 (backup.csv ): backup.csv
[가져오기 진행 중...]
[완료] backup.csv 처리 완료 - 가져옴: 11건, 건너뜀(오류): 0건
mpeg46551@cx2r6s2 b2_1 % 
```
### update
```bash
mpeg46551@cx2r6s2 b2_1 %  python3 -m budget_app                   
==================================================
   💰 대화형 파일 기반 가계부 (budget_app) v1.0 💰
   - 사용법 확인: help 입력
   - 프로그램 종료: exit 또는 quit 입력
==================================================
budget_app> update
- 수정할 거래 ID (TX-000024 /TX-000023 /TX-000022 /TX-000021 /TX-000020 /TX-000019 /TX-000018 /TX-000017 /TX-000016 /TX-000015 /TX-000014 /TX-000013 /TX-000012 /TX-000011 /TX-000010 /TX-000009 /TX-000008 /TX-000007 /TX-000006 /TX-000005 /TX-000004 /TX-000003 /TX-000002 /TX-000001 ): 
[오류] 존재하지 않는 거래 ID입니다.
- 수정할 거래 ID (TX-000024 /TX-000023 /TX-000022 /TX-000021 /TX-000020 /TX-000019 /TX-000018 /TX-000017 /TX-000016 /TX-000015 /TX-000014 /TX-000013 /TX- 수정할 거래 ID (TX-000024 /TX-000023 /TX-000022 /TX-000021 /TX-000020 /TX-000019 /TX-000018 /TX-000017 /TX-000016 /TX-000015 /TX-000014 /TX-000013 /TX- 수정할 거래 ID (TX-000024 /TX-000023 /TX-000022 /TX-000021 /TX-000020 /TX-000019 /TX-000018 /TX-000017 /TX-000016 /TX-000015 /TX-000014 /TX-000013 /TX- 수정할 거래 ID (TX-000024 /TX-000023 /TX-000022 /TX-000021 /TX-000020 /TX-000019 /TX-000018 /TX-000017 /TX-000016 /TX-000015 /TX-000014 /TX-000013 /TX-000012 /TX-000011 /TX-000010 /TX-000009 /TX-000008 /TX-000007 /TX-000006 /TX-000005 /TX-000004 /TX-000003 /TX-000002 /TX-000001 ): TX-000003

[기존 데이터를 로드했습니다. 수정을 원하지 않는 항목은 그대로 엔터를 누르세요]
- 날짜 (YYYY-MM-DD): 2026-06-01
- 타입 (income /expense ): income
- 카테고리 (food /transport /rent /shopping /health /education /salary /allowance /other ): food
- 금액 (양수): 10000
- 메모 (선택) (점심 /저녁 /월세 /마트 ): 점심
- 태그 (쉼표 구분) (식대 /생필품 /고정비 /교통 ): 식대
[수정 성공] id=TX-000003
id        | date       | type   | category | amount   | memo | tags
----------+------------+--------+----------+----------+------+-----
TX-000003 | 2026-06-01 | income | food     | 10,000원 | 점심 | 식대
budget_app> exit
==================================================
   이용해 주셔서 감사합니다. 가계부를 종료합니다! 
==================================================
mpeg46551@cx2r6s2 b2_1 % 
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
