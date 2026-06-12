# 가계부 애플리케이션 리팩토링 계획 및 결과 (V2)

이 문서는 가계부 애플리케이션(`budget_app`)의 코드 가독성, 유지보수성, 책임 분리(SRP)를 개선하기 위해 수립한 리팩토링 계획과 그 수행 결과를 기록합니다.

---

## 1. 리팩토링 목표 및 계획

### 📋 목표 1: 반복 거래 템플릿(Recurring Templates) 입출력 메서드 이관
* **현재 문제점**: `load_recurring_templates`와 `save_recurring_templates` 메서드가 비즈니스 계층인 `service.py` 내부에 구현되어 있어, `service.py`가 저장소의 상세 경로(`recurring_path`)와 임시 파일 생성 로직에 직접 의존하고 있습니다.
* **개선 방향**:
  * 두 메서드를 영속성 계층인 `repository.py` (`FileRepository` 클래스) 내부로 옮깁니다.
  * `service.py` (`BudgetService` 클래스)에서는 이를 `self.repository.load_recurring_templates()` 및 `self.repository.save_recurring_templates(templates)`로 대리 호출하도록 변경합니다.
  * 결과적으로 데이터 상세 저장 포맷 및 경로 처리를 `FileRepository`로 완전히 캡슐화합니다.

### 📋 목표 2: CSV 임포트 시 중복된 검증 로직 통합
* **현재 문제점**: `service.py`의 `import_from_csv` 메서드에서 CSV 행의 데이터 유효성 검사(날짜, 타입, 카테고리, 금액)를 자체 인라인 `try-except` 블록으로 중복 정의하고 있습니다.
* **개선 방향**:
  * 이미 정의되어 있는 `self.validate_fields(date, type_str, category, amount)` 헬퍼 메서드를 활용하도록 수정합니다.
  * 중복 유효성 검증 규칙 코드를 단일 메서드로 통합하여 코드 가독성과 유지보수성을 극대화합니다.

---

## 2. 작업 순서 및 진행 현황
1. [계획 작성]: `refactoringV2.md`에 계획을 문서화합니다. (완료)
2. [저장소 계층 리팩토링]: `repository.py`에 반복 거래 템플릿 로드/저장 메서드를 이관 및 보강합니다. (완료)
3. [비즈니스 계층 리팩토링]: `service.py`에서 기존 로직을 저장소의 새 메서드 호출로 대체하고, CSV 임포트 유효성 검사를 `validate_fields`로 대체합니다. (완료)
4. [기능 검증]: 통합 테스트 스크립트(`test_budget.py`)를 실행하여 모든 동작이 온전히 유지되는지 확인합니다. (완료)
5. [결과 정리]: 리팩토링 완료 결과를 본 문서 하단에 업데이트합니다. (완료)

---

## 3. 리팩토링 적용 세부 내역

### ① [repository.py](file:///Users/mpeg46551/codyssey/b2_1/budget_app/repository.py) 변경점
* `load_recurring_templates`와 `save_recurring_templates` 메서드를 `FileRepository` 내부로 이관하였습니다.
* 안전한 원자적 덮어쓰기 로직(`tempfile` + `os.replace`)을 그대로 유지하며 파일 경로 및 변수 참조를 `self.recurring_path`, `self.data_dir` 등으로 다듬었습니다.

### ② [service.py](file:///Users/mpeg46551/codyssey/b2_1/budget_app/service.py) 변경점
* 기존에 가지고 있던 파일 입출력 로직을 걷어내고 `self.repository`에 역할을 위임했습니다.
* `import_from_csv`의 인라인 하드코딩 유효성 검사 코드를 걷어내고, 공통 헬퍼인 `self.validate_fields`를 호출하도록 수정하였습니다.
* 사용하지 않는 `tempfile` 및 `json` 라이브러리 임포트를 깨끗하게 정리했습니다.

---

## 4. 최종 검증 결과
* **테스트 수행 명령어**: `PYTHONPATH=. python3 -m unittest tests/test_budget.py`
* **테스트 결과**: `Ran 12 tests in 0.144s. OK`
* **검증 의견**: 
  - 저장소와 서비스 계층 간의 SRP(단일 책임 원칙) 분리 및 CSV 임포트 검증 메서드 통합 이후에도 기존의 단위/통합 테스트 12개가 모두 정상 동작함을 확인하였습니다.
  - 리팩토링 결과 데이터 오염이나 기능 오동작 없이 성공적으로 구조가 정리되었습니다.
