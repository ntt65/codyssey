# Interactive Shell Program Refactoring Plan (Refactoring.md)

본 계획서는 현재 단발성 실행(Option-based CLI) 구조인 가계부 애플리케이션을 단 한 번의 실행으로 내부 셸 루프에 진입하여 가볍고 친근하게 모든 명령을 실행할 수 있는 **대화형 통합 콘솔 프로그램(Interactive Shell Program)**으로 전환하기 위한 모듈별 세부 리팩토링 단계와 수정 규칙을 정의합니다.

---

## 1. 리팩토링 목표 (Goals)

1. **상태 유지형 셸 전환**: `python3 -m budget_app` 실행 시 배너와 함께 지속적인 프롬프트(`budget_app> `) 상태로 대기.
2. **에러 격리 (Fault Isolation)**: 셸 명령어 처리 중 `ValueError`, `FileNotFoundError` 등 어떤 에러가 발생해도, 해당 에러 메시지와 해결 힌트만 출력하고 **셸 루프가 계속 살아있어야 함**.
3. **입력 체계 개편**: 명령어 파싱부를 셸에 맞춰 변경하고, 복잡한 인자 대신 순차 대화식 `input()` 인터페이스로 단계별 입력 수립.
4. **안전한 세션 관리**: `exit` 또는 `quit` 입력 시에만 정상 종료 코드로 완전 종료.

---

## 2. 모듈별 상세 수정 계획

```mermaid
graph TD
    Main[__main__.py] --> Init[데이터 보장 및 서비스 로드]
    Init --> Shell[cli.py: InteractiveShell.run]
    Shell --> Loop[while True 루프 실행]
    Loop --> Read[사용자 명령어 한 줄 읽기]
    Read --> Parse[명령 및 인자 분리]
    Parse --> Dispatch{명령어 매핑}
    
    Dispatch -->|add/search/budget/category/update/delete/import/export/recurring| Exec[대화형 핸들러 구동]
    Dispatch -->|list/summary| ArgExec[인자 포함 핸들러 구동]
    Dispatch -->|help| HelpExec[도움말 출력]
    Dispatch -->|exit/quit| ExitExec[배너 출력 및 루프 break]
    
    Exec --> Decorate[@catch_errors 에러 처리]
    ArgExec --> Decorate
    Decorate --> Next[오류 출력 후 루프 계속 진행]
```

### 2.1 decorators.py 수정 계획
기존 `@catch_errors` 데코레이터는 에러 발생 시 `sys.exit()`를 호출하여 전체 가계부 프로세스를 끈다는 치명적인 문제가 있습니다. 셸 내부용 에러 핸들러로 탈바꿈합니다.

* **수정안**:
  * 데코레이터는 예외를 잡아서 에러 및 힌트만 출력하고, `sys.exit()`를 호출하는 대신 **아무것도 반환하지 않거나(None) 특정 에러 플래그를 반환**하도록 수정합니다.
  * 이를 통해 셸 루프(`cli.py`)가 비정상적인 호출에서도 죽지 않고 자연스럽게 다음 `continue` 루프로 진입할 수 있도록 조율합니다.

### 2.2 models.py, repository.py, service.py 활용 계획
* **비즈니스 및 저장소 로직 완전 재사용**:
  * `repository.py`와 `service.py`가 제공하는 스트리밍 연산, CSV 가공, 백업, 원자적 임시 파일 치환 기능은 셸 환경에서도 변경 없이 그대로 호환되므로 코드를 수정하지 않고 보존하여 설계 정합성을 유지합니다.

### 2.3 cli.py 전면 개편 계획
CLI 레이어인 `cli.py`는 단발성 인자 파싱 대신 **셸 루프와 명령어 배칭(routing)**을 수행하도록 완전히 재작성합니다.

* **`InteractiveShell` 클래스 설계**:
  * `__init__(self, service: BudgetService)`: 핵심 서비스를 연동받아 내부 인스턴스로 보유.
  * `run(self)`: 웰컴 메시지 출력 후 `while True` 구동. `KeyboardInterrupt` 혹은 `exit`/`quit` 시 루프를 안전하게 탈출.
  * `parse_and_execute(self, user_input: str)`: 첫 단어를 추출해 각 핸들러로 라우팅.
* **명령어별 대화형 핸들러 세부 설계**:
  * **`handle_add`**: `input()`으로 단계별 검증 루프. 카테고리 기등록 여부 검증 후 부재 시 동적 등록 유도(`y/n`).
  * **`handle_list(limit_arg)`**: 인자가 숫자인지 안전히 검사하고 limit으로 list 서비스 호출 후 Hangul 너비 정렬 표 출력.
  * **`handle_search`**: 시작일/종료일/타입/카테고리/검색어/태그 조건을 하나씩 물어보며 엔터 시 Skip.
  * **`handle_summary(month_arg)`**: 인자가 없으면 월을 물어보고 가입된 예산 대비 소모율 산정 후 TOP 3 표시.
  * **`handle_budget`**: 대상 월과 제한 예산액을 질문식으로 입력받아 연동.
  * **`handle_category`**: 서브메뉴(1: 조회, 2: 추가, 3: 삭제) 선택 유도 및 하위 동작 처리.
  * **`handle_update`**: 대상 ID가 없으면 입력을 요구하고, 존재 유무 확인 후 기존 데이터 `[현재값]` 형태 프롬프트로 수정 진행.
  * **`handle_delete`**: 대상 ID 입력을 요구하고 이중 안전 컨펌(`정말로 삭제하시겠습니까? (y/n)`) 후 삭제.
  * **`handle_import` / `handle_export`**: 대상 CSV 파일 및 필터 범위를 대화형으로 묻고 CSV 처리 진행.
  * **`handle_recurring`**: 서브메뉴(1: 템플릿 조회, 2: 템플릿 추가, 3: 템플릿 삭제, 4: 일괄 생성) 입력 분기 흐름 작동.

---

## 3. 리팩토링 수행 단계 (Step-by-Step)

### 1단계: `decorators.py` 개편
* `sys.exit()`를 배제한 사용자 친화적 에러 출력용으로 데코레이터 코드를 정밀 튜닝합니다.

### 2단계: `cli.py`에 `InteractiveShell` 및 14종 핸들러 작성
* 셸 실행 프레임워크를 올리고 각 대화식 흐름과 유효성 루프를 정밀 조립합니다.

### 3단계: `__main__.py` 갱신
* 단발 인자 처리를 없애고 `InteractiveShell`을 로드하여 구동하도록 진입 코드를 단순화합니다.

### 4단계: 단위 테스트 검증
* 기존 핵심 기능에 영향이 없는지 `PYTHONPATH=. python3 -m unittest tests/test_budget.py`를 실행해 정합성을 확보합니다.

### 5단계: 문서화 갱신
* `README.md` 가이드를 대화형 셸 실행 예시로 재단장하고 Mermaid 다이어그램을 업데이트합니다.

---

## 4. 자동완성 및 인터랙티브 입력 규칙 (Autocomplete & Interactive Input Rules)

가계부 콘솔의 사용 편의성과 입력 속도를 극대화하기 위해 다음과 같은 자동완성 및 키 입력 제어 규칙을 전격 구현하였습니다:

1. **메인 명령어 셸 프롬프트 (`budget_app>`)**:
   - **좌/우 화살표 키 (`Left`/`Right`)**: 사용 가능한 15개 가계부 명령어(`help`, `add`, `list`, `search` 등)를 차례대로 순환하며 표시합니다. 이미 인자(Arguments)가 작성되어 있는 경우에도 인자 내용은 유지하고 명령어 부분만 깔끔하게 변경됩니다.
   - **위/아래 화살표 키 (`Up`/`Down`)**: 터미널과 동일하게 이전에 입력한 명령 히스토리를 탐색하고 복구합니다.
   - **탭 키 (`Tab`)**: 입력된 접두사 글자 기반으로 어울리는 명령어를 자동으로 완성합니다.

2. **아이템/데이터 입력 프롬프트 (`prompt_choices`)**:
   - **디폴트 입력 prefill 및 덮어쓰기**: 디폴트 값(예: 오늘 날짜, 기본 카테고리 등)이 프롬프트 실행 시 입력창에 미리 작성되어 출력됩니다. 
     - 아무 값도 입력하지 않고 바로 `Enter`를 누르면 이 디폴트 값이 즉시 적용됩니다.
     - 사용자가 키보드로 첫 글자를 타이핑하거나 `Backspace`를 입력하면, 미리 채워져 있던 디폴트 값이 깨끗이 지워지고 입력된 글자로 덮어씌워집니다.
     - 사용자가 백스페이스로 입력창의 글자를 전부 지우고 빈칸 상태에서 `Enter`를 쳐도 기본 디폴트 값이 자동으로 완성되어 저장되도록 예외 처리가 강화되었습니다.
   - **좌/우/상/하 화살표 키 (`Left`/`Right`/`Up`/`Down`)**: 노출된 후보군(예: `income`/`expense`, 혹은 가계부 카테고리)을 순방향/역방향으로 순환하며 즉시 선택 변경할 수 있습니다. 
   - **중복 표시 배제**: 단일 후보군이자 디폴트 값인 아이템(예: 오늘 날짜)은 불필요하게 프롬프트 뒤에 후보군 괄호 `(YYYY-MM-DD )`나 디폴트 괄호 `[YYYY-MM-DD]`를 3번씩 중복해서 표시하지 않고, 입력창에 단 한 번만 직관적으로 표시합니다.
   - **탭 키 (`Tab`)**: 사용자가 첫 글자를 타이핑한 상태에서 `Tab` 키를 누르면 접두사와 어울리는 매칭 후보(예: `f` ➔ `food`)를 자동 완성합니다.
