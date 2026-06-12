# budget_app 평가 및 Q&A 기술 검토서 (Eval_QA)

본 문서는 가계부 애플리케이션(`budget_app`) 프로젝트의 주요 평가 항목별 기술적 구현 방식과 핵심 설계 근거를 설명하며, 해당 기능이 정의된 소스 코드 파일의 정확한 위치와 라인 번호의 절대 하이퍼링크를 매핑하여 제공합니다.

---

### 항목 1: 기능 동작 및 영구 저장 요구사항 (PASS)

#### **Q1. add/list/search 등 8대 필수 기능과 카테고리/예산 설정이 요구사항대로 정상 동작합니까?**
* **A.** 네, 정상 동작합니다. 프롬프트 및 인자 옵션을 통해 거래 조회/추가/수정/삭제, 상세 조건 검색, 월별 요약, 카테고리 관리, 예산 한도 설정 기능이 완벽히 작동합니다.
* **기술 구현 설명**:
  * **Add (거래 추가)**: 입력 데이터 유효성 검사 통과 후 고유 거래 ID(TX-XXXXXX)를 자동 발급받고 저장소 끝에 단일 JSON 객체 행으로 추가 기록합니다.
    * [service.py:L41-L68](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L41-L68) | [repository.py:L74-L83](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L74-L83)
  * **List (거래 조회)**: 파일에 저장된 거래 내역을 한 줄씩 스트리밍해서 가져와 최신 날짜 및 최신 ID 순으로 고정된 크기(limit)만큼 정렬하여 가져옵니다.
    * [service.py:L70-L96](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L70-L96)
  * **Search (거래 검색)**: 검색 필터 조건(날짜 범위, 카테고리, 타입, 태그, 메모 키워드)을 통과한 데이터에 대해 실시간 매칭을 진행하고 최신순 정렬 리스트로 축적합니다.
    * [service.py:L98-L150](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L98-L150)
  * **Update/Delete (거래 수정 및 삭제)**: 지정된 ID의 데이터를 검색하고, 임시 파일 교체를 통한 원자적 덮어쓰기 방식으로 안전하게 개별 행의 정보 변경 및 소거를 이행합니다.
    * [service.py:L152-L179](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L152-L179) | [service.py:L180-L191](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L180-L191)
  * **Category 관리 (추가/조회/삭제)**: 카테고리의 생성 및 조회를 지원하며, 삭제 시 참조 무결성을 준수하기 위해 해당 카테고리가 가계부 거래에 1건이라도 등록되어 사용 중인 경우 삭제 요청을 에러로 차단하고 데이터를 보존합니다.
    * [service.py:L194-L212](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L194-L212) | [service.py:L223-L245](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L223-L245) | [service.py:L247-L260](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L247-L260)
  * **Budget (예산 한도 설정)**: 년월(`YYYY-MM`)과 한도 액수를 딕셔너리로 설정받아 디스크에 기입합니다.
    * [service.py:L264-L278](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L264-L278)

#### **Q2. 프로그램 재실행 후에도 데이터가 3개 이상의 파일로 분리되어 영구 유지됩니까?**
* **A.** 네, 가계부 구동 시 총 4개의 JSONL 포맷 데이터베이스 파일로 물리적으로 완벽히 분리되어 보존됩니다.
* **기술 구현 설명**:
  * 데이터 저장소 초기화 시, 거래 내역(`transactions.jsonl`), 카테고리(`categories.jsonl`), 월별 예산 한도(`budgets.jsonl`), 자동화 반복 템플릿(`recurring.jsonl`)의 독립 경로들을 확보하고 데이터 관리용 하위 폴더 생성을 의무적으로 수행합니다.
    * [repository.py:L33-L45](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L33-L45)

#### **Q3. CSV 스키마 준수 및 오류 상황 시 스택트레이스 방지, 종료 코드 처리가 잘 되었습니까?**
* **A.** 네, 스키마 호환, 프로그램 안전 방어, CLI 셸 복구 및 올바른 리턴 코드로의 앱 종료 처리가 설계되어 있습니다.
* **기술 구현 설명**:
  * **CSV 내보내기/가져오기 스키마**: 6열 규격 스키마(`date`, `type`, `category`, `amount`, `memo`, `tags`)에 정확히 맞추어 UTF-8 포맷 파일로 쓰거나 읽습니다.
    * [service.py:L328-L368](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L328-L368) | [service.py:L370-L439](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L370-L439)
  * **에러 경계 (스택트레이스 유출 방지)**: 공통 데코레이터 `@catch_errors`가 입력 포맷 위반(`ValueError`), 경로 부재(`FileNotFoundError`), 운영체제 권한 차단(`PermissionError`) 등 모든 예외 상황에 대한 에러 세부 사항을 stderr에 명시하고 힌트를 출력하여 스택 트레이스 노출을 차단하며 셸 프롬프트 제어를 유지합니다.
    * [decorators.py:L20-L47](file:///Users/mpeg46551/codyssey/b2_1/budget_app/decorators.py#L20-L47)
  * **종료 코드 (Exit Code) 처리**: 애플리케이션 시작 지점에서 초기 데이터 디렉터리 바인딩 등 치명적인 구동 차단 오류가 나면 1을 반환하며 비정상 종료하고, CLI 루프에서 정상 종료 명령어(`exit`, `quit` 혹은 `Ctrl+D`)를 받았을 때는 예외 루프를 탈출해 코드로 0을 전달하고 정상적으로 마칩니다.
    * [__main__.py:L39-L48](file:///Users/mpeg46551/codyssey/b2_1/budget_app/__main__.py#L39-L48) | [cli.py:L675-L701](file:///Users/mpeg46551/codyssey/b2_1/budget_app/cli.py#L675-L701)

---

### 항목 2: 모듈화, 책임 경계 및 파일 원자성 (PASS)

#### **Q1. 코드가 3개 이상 모듈로 분리되어 있고, 각 모듈과 클래스의 책임을 "어떻게" 나눴습니까?**
* **A.** 레이어드 아키텍처(Layered Architecture) 패턴에 입각하여 책임을 4개의 전용 파이썬 파일로 분리하고 상호 유기적으로 의존성을 주입하여 구동합니다.
* **기술 구현 설명**:
  * **데이터 모델 정의 (`models.py`)**: 단일 거래 데이터 클래스인 `Transaction`과 반복 생성용인 `RecurringTemplate` 및 딕셔너리 직렬화/역직렬화(DTO)를 담당합니다.
    * [models.py:L18-L66](file:///Users/mpeg46551/codyssey/b2_1/budget_app/models.py#L18-L66) | [models.py:L69-L117](file:///Users/mpeg46551/codyssey/b2_1/budget_app/models.py#L69-L117)
  * **데이터 영속성 접근 (`repository.py`)**: 파일 시스템에 한 줄씩 JSON 데이터를 영구 저장하고 수정 및 복사 교체 연산을 대리 처리하는 창고 지기 책임을 맡습니다.
    * [repository.py:L27-L32](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L27-L32)
  * **비즈니스 로직 연산 (`service.py`)**: 카테고리 유효 검사, 월별 지출 통계 및 정렬 버퍼링 처리, CSV/백업 가계부 도메인 비즈니스 계산을 수행합니다.
    * [service.py:L25-L38](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L25-L38)
  * **콘솔 인터페이스 (`cli.py`)**: 명령어 입력 대기 루프 구동, 자동완성 히스토리, macOS 키 스위치, 테이블 화면 드로잉 UX 처리를 제어합니다.
    * [cli.py:L656-L701](file:///Users/mpeg46551/codyssey/b2_1/budget_app/cli.py#L656-L701)

#### **Q2. 파일 기반 update/delete를 "어떻게" 안전하게 처리했습니까?**
* **A.** 데이터 기록 도중 비정상적으로 스레드나 셸 프로세스가 강제 정지되더라도 원본이 파괴되거나 꼬이지 않도록 하는 원자적 파일 교체(Atomic Write Swap) 기술로 안정성을 보장합니다.
* **기술 구현 설명**:
  * 원본 데이터 파일에 직접 커서 쓰기를 이행하지 않고, 안전한 하위 경로에 임시 임시파일(`tempfile.mkstemp`)을 생성하여 먼저 갱신 내용을 끝까지 작성합니다. 기입이 정상 완결되면 운영체제(OS)의 원자적 연산인 `os.replace`를 일시에 실행하여 기존 파일을 안전하게 원자적으로 대체시킵니다. 작업 중 오류가 포착되면 임시 잔해 파일을 즉시 삭제하여 무결성을 원천 보호합니다.
    * [repository.py:L84-L127](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L84-L127)
    * `categories.jsonl` 원자적 저장: [repository.py:L166-L184](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L166-L184)
    * `budgets.jsonl` 원자적 저장: [repository.py:L207-L225](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L207-L225)
    * `recurring.jsonl` 원자적 저장: [repository.py:L300-L317](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L300-L317)

---

### 항목 3: 고급 파이썬 문법 활용 (PASS)

#### **Q1. list/search를 제너레이터로 스트리밍 처리한 방식과 "왜" 유리한지 설명해 주실 수 있나요?**
* **A.** 데이터 적재량이 대용량으로 늘어났을 때 발생할 수 있는 메모리 누수나 실행 장애를 예방하기 위해 파이썬 `yield` 키워드를 채택했습니다.
* **기술 구현 설명**:
  * `stream_transactions` 메서드는 파일 전체 텍스트 라인을 `readlines()`로 메모리에 한꺼번에 배열 적재하지 않고, 한 줄을 탐색해 가벼운 Transaction 도메인 객체로 파싱하고 실시간 `yield` 한 뒤 점유 메모리를 내보냅니다. 이로써 저장된 내역 크기가 수십만 줄 이상이 되더라도 데이터를 읽을 때 점유 메모리를 상시 일정한 O(1) 범위로 유지하는 절대적 이점이 생깁니다.
    * [repository.py:L53-L72](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L53-L72)

#### **Q2. 데코레이터로 분리한 공통 기능은 무엇이며, "왜" 분리했습니까?**
* **A.** 로깅, 소요 시간 계측, 인터페이스 영역 오류 안전 차단과 같은 횡단 관심사(Aspects)들을 핵심 가계부 제어 연산 로직과 철저히 나누어 결합도를 낮추기 위해 분리했습니다.
* **기술 구현 설명**:
  * **@catch_errors**: CLI 셸 수행 시 발생하는 런타임 오류 방어 경계를 분리
    * [decorators.py:L20-L47](file:///Users/mpeg46551/codyssey/b2_1/budget_app/decorators.py#L20-L47)
  * **@measure_time**: 정밀 퍼포먼스 측정을 위한 타이머 로그
    * [decorators.py:L49-L66](file:///Users/mpeg46551/codyssey/b2_1/budget_app/decorators.py#L49-L66)
  * **@log_action**: 기능의 진입 및 마감 정보 로깅
    * [decorators.py:L68-L86](file:///Users/mpeg46551/codyssey/b2_1/budget_app/decorators.py#L68-L86)

#### **Q3. 타입 힌트를 적용해 얻는 이점은 무엇입니까?**
* **A.** 코드 자가 문서화, 규약 안정화, 그리고 사후 타입 위반으로 인한 런타임 참사를 예방하기 위해 전체 구조에 명시적인 정적 타입 힌트를 매핑했습니다.
* **기술 구현 설명**:
  * 함수 선언 시 변수형 및 리턴 데이터 유형을 명확히 명시함으로써, 개발 중 IDE 정적 린터(Linter) 분석 도구를 통해 비호환 타입 할당 시 빌드/배포 전 미리 오류를 잡아낼 수 있으며, 클래스 간 파라미터 전달 규약을 명문화합니다.
    * `Transaction DTO 타입 지정`: [models.py:L30-L66](file:///Users/mpeg46551/codyssey/b2_1/budget_app/models.py#L30-L66)
    * `제너레이터 반환 타입 지정`: [repository.py:L53-L60](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L53-L60)
    * `비즈니스 유효성 검증 함수 타입 지정`: [service.py:L618-L627](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L618-L627)

---

### 항목 4: 설계 근거 및 엣지 케이스 대응 (PASS)

#### **Q1. JSONL과 CSV 중 어떤 포맷을 선택했고, 그 이유는 무엇입니까?**
* **A.** 메인 저장 데이터베이스의 고유 포맷으로는 **JSONL (JSON Lines)** 형식을 채택했습니다.
* **기술 구현 설명**:
  * 단일 파일 기반 구조의 전체 JSON 포맷(예: 대괄호로 둘러싸인 배열 구조)은 한 노드의 파싱을 위해 파일 구조를 온전히 통째로 읽어와 올린 후에 메모리 객체로 환원해야 하므로 스트리밍 처리가 불가능합니다. 하지만 줄바꿈으로만 끊어 적은 JSONL 포맷은 각 행마다 유효한 개별 JSON 객체이므로 스트리밍식 제너레이터 읽기/쓰기에 완벽히 부합하고, 임의 데이터 기입 속도가 엄청나게 빠르며 안정적입니다. (CSV는 가독성과 외부 프로그램 이식용 포맷으로만 한정하여 변환을 위임합니다).
    * `JSONL 데이터 처리`: [repository.py:L53-L72](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L53-L72) | [repository.py:L74-L83](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py#L74-L83)

#### **Q2. 거래가 10만 건으로 늘어날 때 병목과 그 개선책은 무엇입니까?**
* **A.** 전체 10만 건 거래 기록을 불러와서 파이썬 인메모리 내에서 통째로 정렬(`sort()`)할 시, 심각한 메모리 오버헤드와 일시 정지 지연 병목이 발생합니다.
* **기술 구현 설명**:
  * 이를 개선하기 위해 전체 리스트화를 배제하고, 데이터를 읽어 들이며 사용자가 출력하고자 희망하는 고정된 타겟 개수(limit)만큼만 값을 저장할 수 있는 최신순 정렬 삽입 공간인 **정렬 버퍼(Sorted Insertion Buffer)** 기법을 도입했습니다. 새로운 스트림 행을 정렬된 위치에 꽂아 넣고 배열 크기가 limit을 넘어갈 때 버퍼 맨 뒷단에 머무는 가장 오래된 요소를 `pop()`하여 탈락시키는 $O(\text{limit})$ 메모리 보존 정렬을 구현하여 병목을 우회했습니다.
    * [service.py:L70-L96](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L70-L96)

#### **Q3. import CSV 시 깨진 행이 섞여 있다면 "어떻게" 신뢰를 유지할 것입니까?**
* **A.** 파일 전체 연산 실패 및 롤백으로 작업을 중단시키는 무리한 조치 대신, 깨지지 않은 정상 데이터만 부분적으로 로드(Partial Success)해 영속화하고, 최종 수행 통계를 명확히 밝혀 신뢰를 확보합니다.
* **기술 구현 설명**:
  * 외부 CSV 데이터를 받아 기입하는 로직 내부에 개별 행 순회 감시 유효성 필터를 부착합니다. 규칙에 맞지 않는 불량 행이 발견되면, 시스템이 튕기거나 오류 트레이스를 터트리지 않고 해당 줄만 조용히 수량 스킵(`skipped += 1`)을 한 뒤 정상적인 행들만 파일 저장을 완수합니다. 연산 종료 직후, 정상 삽입 개수와 무시된 불량 행의 총 수치를 CLI UI 화면에 리포트하여 사용자 편의와 가독성을 지킵니다.
    * [service.py:L370-L439](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L370-L439)

---

### 항목 5: 보너스 문제 (PASS / 부여 가능)

#### **Q. 보너스 과제를 해결하여 크레딧 부여 기준을 만족합니까?**
* **A.** 네, 백업 보관 및 정기 반복 데이터 발생 연산을 구현하여 두 영역 보너스 기준을 완벽하게 만족합니다.
* **기술 구현 설명**:
  * **Zip 압축 가계부 백업 (`backup`)**: 가계부가 사용하는 4대 핵심 데이터를 타임스탬프 구분자 이름을 기반으로 단일 `.zip` 파일 포맷 아카이브로 통매칭하여 안전한 backups 폴더 아래 압축 아카이브화하여 영구 보관합니다.
    * [service.py:L443-L469](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L443-L469)
  * **반복 내역 다회 발생 자동화 및 중복 차단 (`recurring`)**: 고정적으로 매달 나가는 항목(예: 월세, 월급 등)의 템플릿 정보를 등록해둔 후, 지정 연월에 일괄 생성합니다. 이때 돈이 이중 가산되어 이중 출금/기재되는 예외를 완벽 방지하기 위해 생성될 일자, 타입, 카테고리, 액수, 메모와 전용 식별용 태그(`recurring`)의 존재 유무가 일치하는 거래가 해당 년월 내에 이미 있는 경우 사전 비교 필터링을 통해 중복 생성을 완전 차단합니다.
    * 템플릿 생성: [service.py:L491-L529](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L491-L529)
    * 일괄 생성 및 중복 차단: [service.py:L548-L614](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py#L548-L614)

---

### 추가 어필 항목: CLI 사용성 고도화 및 다국어 정렬 테이블 (Superb UX)

#### **1. macOS IME 입력기 영어 자동 강제 전환 (오타 원천 예방)**
* **설명**: 한글 입력 상태에서 터미널 CLI에 명령어를 작성할 때 한타 오타가 나서 오류가 발생하거나 셸이 꼬이는 불편을 개선하기 위해, 별도의 외부 라이브러리 연동 없이 파이썬 표준 라이브러리인 `ctypes`를 활용하여 macOS 시스템 내장 카본(Carbon) 라이브러리의 TIS(Text Input Source) C API를 직접 다이렉트 바인딩해 명령 대기 진입 전 입력 장치 환경을 US English로 강제 전환해 줍니다.
* [cli.py:L38-L83](file:///Users/mpeg46551/codyssey/b2_1/budget_app/cli.py#L38-L83)

#### **2. CJK (한글/중국어/일어) 2바이트 실제 화면 크기 보정 터미널 정렬 테이블**
* **설명**: 한글 문자는 터미널 렌더러 출력 환경 상 2칸의 영역을 소비하지만 파이썬의 `len()` 함수는 단순 아스키와 동일하게 크기를 1로 산출하여, 일반적인 텍스트 표를 출력할 때 컬럼이 비뚤어지거나 무너집니다. 이를 교정하기 위해 `unicodedata.east_asian_width` 모듈로 와이드 캐릭터를 자동 식별하여 한글은 2바이트 공간을 가중 연산하여 깨지지 않는 격자 표 드로잉 테이블 렌더러를 내장했습니다.
* [cli.py:L295-L313](file:///Users/mpeg46551/codyssey/b2_1/budget_app/cli.py#L295-L313) | [cli.py:L315-L330](file:///Users/mpeg46551/codyssey/b2_1/budget_app/cli.py#L315-L330) | [cli.py:L331-L364](file:///Users/mpeg46551/codyssey/b2_1/budget_app/cli.py#L331-L364)