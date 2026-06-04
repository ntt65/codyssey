# 충돌 해결 기록

팀 과제 진행 중 발생한 충돌과 해결 과정을 이곳에 기록합니다.

## 충돌 기록

### 참여자

- 작성자: 팀원 5
- 상대: 팀원 2

### 상황

- 작성자는 작업 브랜치 docs/3에서 충돌 대응 흐름 문서를 작성하고 있었다.
- 상대 팀원은 main 브랜치에 커밋 메시지 규칙 관련 문서를 반영한 상태였다.
- 작성자가 작업 브랜치에 최신 main 내용을 병합하는 과정에서 같은 문서의 같은 위치에 서로 다른 내용이 있어 충돌이 발생했다.
- Git은 docs/3 브랜치의 충돌 대응 흐름 내용과 main 브랜치의 커밋 메시지 규칙 내용 중 어떤 내용을 최종 문서에 남겨야 하는지 자동으로 판단하지 못했다.

### 충돌 내용

````text
## 충돌 대응 흐름
- PR에서 충돌이 발생했거나, 작업 브랜치에 최신 `main`을 반영하는 과정에서 충돌이 발생하면 PR 작성자가 우선 해결한다.
- 충돌 해결 전, 현재 작업 내용을 커밋하거나 저장한다.
- 로컬 `main` 브랜치를 최신 상태로 만든 뒤, 작업 브랜치에 병합한다.
우리 팀은 Git 히스토리에서 각 변경 사항의 목적과 대상을 쉽게 파악할 수 있도록 일관된 커밋 메시지 규칙을 사용한다.

### 기본 형식

```text
type: 작업 내용 요약

커밋 타입
feat: 새로운 기능 추가
fix: 버그 수정
docs: 문서 작성 또는 수정
refactor: 기능 변경 없이 코드 또는 문서 구조 개선
chore: 설정, 초기 구조, 기타 작업
test: 테스트 코드 추가 또는 수정
````

### 해결 과정

- 충돌 표시를 기준으로 현재 작업 브랜치 `docs/3`의 변경 내용과 `main` 브랜치에서 들어온 변경 내용을 비교했다.
- `docs/3`의 내용은 충돌 대응 흐름 문서이고, `main`의 내용은 커밋 메시지 규칙 문서였기 때문에 두 내용 모두 필요한 문서라고 판단했다.
- VS Code의 `Accept both changes`를 사용하여 양쪽 변경 사항을 모두 반영했다.
- 수정 후 `git status`로 충돌 파일 상태를 확인했다.
- 충돌 해결 파일을 `git add .`로 스테이징한 뒤, 충돌 해결 커밋을 작성했다.
- 작업 브랜치를 원격 저장소에 다시 push한 뒤 GitHub PR 화면에서 충돌이 해결되었는지 확인했다.

### 결과

- `main` 브랜치의 커밋 메시지 규칙 문서와 `docs/3` 브랜치의 충돌 대응 흐름 문서를 모두 보존했다.
- 충돌 표시가 제거되어 문서가 정상적인 Markdown 형식으로 정리되었다.
- PR에서 발생한 충돌이 해결되어 이후 리뷰 및 병합을 진행할 수 있는 상태가 되었다.

### 배운 점

- 같은 파일의 같은 위치를 여러 브랜치에서 동시에 수정하면 Git이 자동으로 병합하지 못해 충돌이 발생할 수 있다.
- 충돌이 발생했을 때는 한쪽 내용을 무조건 선택하기보다, 각 변경 사항의 목적을 확인한 뒤 필요한 내용을 모두 보존해야 한다.
- `Accept both changes`를 사용하더라도 충돌 표시가 남아 있지 않은지 반드시 직접 확인해야 한다.
- 충돌 해결 후에는 `git status`로 상태를 확인하고, 수정 파일을 다시 커밋한 뒤 원격 브랜치에 push해야 한다.
- 문서 작업에서도 코드 작업과 마찬가지로 최신 `main`을 자주 반영하면 큰 충돌을 줄일 수 있다.

---


## 충돌 기록 2

### 참여자

* 작성자: 팀원 4(김현서)
* 상대: 팀원 5

### 상황

* 작성자는 작업 브랜치 `feat/16`에서 `src/data_utils.py` 파일에 숫자 리스트 평균 계산 함수 `calculate_average()`를 작성하고 있었다.
* 상대 팀원은 작업 브랜치 `feat/19`에서 같은 파일인 `src/data_utils.py`에 빈 값 검증 함수 `is_blank()`를 작성하고 있었다.
* 두 작업 모두 `src/data_utils.py` 파일을 수정했으며, 함수 설명, 주석, 사용 예시 또는 파일 상단 설명 영역이 함께 수정되면서 같은 파일의 인접한 위치에 변경 사항이 생겼다.
* 먼저 병합된 변경 사항이 `main` 브랜치에 반영된 뒤, 작성자의 작업 브랜치에 최신 `main` 내용을 병합하는 과정에서 같은 파일의 변경 내용을 Git이 자동으로 병합하지 못해 충돌이 발생했다.
* Git은 평균 계산 함수 관련 변경 내용과 빈 값 검증 함수 관련 변경 내용 중 어떤 내용을 최종 파일에 남겨야 하는지 자동으로 판단하지 못했다.

### 충돌 내용

```text
"""데이터 처리를 위한 유틸 함수 모음.

- calculate_average(numbers): 숫자 리스트의 평균을 계산한다.
"""

def calculate_average(numbers: list[int | float]) -> float:
    """숫자 리스트의 평균을 반환한다."""
    if not numbers:
        raise ValueError("numbers must not be empty")

    if not all(isinstance(number, (int, float)) for number in numbers):
        raise TypeError("all elements in numbers must be int or float")

    return sum(numbers) / len(numbers)
=======
"""데이터 처리를 위한 유틸 함수 모음.

- is_blank(value): 값이 비어 있는지 확인한다.
"""

def is_blank(value):
    """값이 None, 빈 문자열 또는 공백 문자열인지 확인한다."""
    return value is None or value == "" or value == " "
```

### 해결 과정

* 충돌 표시인 `<<<<<<<`, `=======`, `>>>>>>>`를 기준으로 현재 작업 브랜치 `feat/16`의 변경 내용과 `main` 브랜치에서 들어온 변경 내용을 비교했다.
* `feat/16`의 변경 내용은 팀원 4가 담당한 숫자 리스트 평균 계산 함수였고, `main` 브랜치에서 들어온 변경 내용은 팀원 5가 담당한 빈 값 검증 함수였기 때문에 두 함수 모두 필요한 기능이라고 판단했다.
* 한쪽 변경 사항만 선택하지 않고, `calculate_average()`와 `is_blank()` 함수가 모두 남도록 파일을 직접 수정했다.
* 파일 상단 docstring도 두 함수의 설명이 모두 포함되도록 정리했다.
* 충돌 마커가 남아 있지 않은지 확인한 뒤, 최종 파일이 정상적인 Python 문법을 유지하는지 검토했다.
* 수정 후 `git status`로 충돌 파일 상태를 확인했다.
* 충돌 해결이 완료된 `src/data_utils.py` 파일을 `git add`로 스테이징했다.
* 충돌 해결 커밋을 작성한 뒤 작업 브랜치를 원격 저장소에 push했다.
* GitHub PR 화면에서 충돌 표시가 사라졌는지 확인했다.

### 최종 반영 내용

```python
"""데이터 처리를 위한 유틸 함수 모음.

- calculate_average(numbers): 숫자 리스트의 평균을 계산한다.
- is_blank(value): 값이 비어 있는지 확인한다.
"""

def calculate_average(numbers: list[int | float]) -> float:
    """숫자 리스트의 평균을 반환한다."""
    if not numbers:
        raise ValueError("numbers must not be empty")

    if not all(isinstance(number, (int, float)) for number in numbers):
        raise TypeError("all elements in numbers must be int or float")

    return sum(numbers) / len(numbers)


def is_blank(value):
    """값이 None, 빈 문자열 또는 공백 문자열인지 확인한다."""
    return value is None or value == "" or value == " "
```

### 결과

* 팀원 4가 작성한 숫자 리스트 평균 계산 함수 `calculate_average()`와 팀원 5가 작성한 빈 값 검증 함수 `is_blank()`를 모두 보존했다.
* 충돌 표시가 제거되어 `src/data_utils.py` 파일이 정상적인 Python 코드 형식으로 정리되었다.
* 같은 파일을 여러 팀원이 수정할 때 발생할 수 있는 코드 충돌을 확인하고 해결했다.
* 충돌 해결 후 작업 브랜치를 다시 원격 저장소에 push하여 PR에서 리뷰와 병합을 진행할 수 있는 상태로 만들었다.

### 배운 점

* 같은 파일을 수정하더라도 함수 위치, 파일 상단 설명, 주석, 사용 예시 영역이 겹치면 충돌이 발생할 수 있다.
* 충돌이 발생했을 때는 단순히 한쪽 변경 사항만 선택하기보다 각 변경 사항의 목적과 담당 범위를 먼저 확인해야 한다.
* 기능이 서로 독립적이라면 두 변경 사항을 모두 보존하는 방향으로 해결하는 것이 적절하다.
* 충돌 해결 후에는 충돌 마커가 완전히 제거되었는지 반드시 확인해야 한다.
* 문법 오류가 없는지 확인하고, `git status`로 상태를 점검한 뒤 다시 커밋해야 한다.
* 같은 파일을 여러 팀원이 함께 수정할 때는 작업 전에 함수 배치 순서나 공통 설명 영역 수정 방식을 미리 정하면 충돌을 줄일 수 있다.

# 충돌 해결 기록 3

팀 과제 진행 중 발생한 충돌과 해결 과정을 이곳에 기록합니다.

## 충돌 기록

### 참여자

- 작성자: 팀원 3 (성원모)
- 상대: 팀원 1

### 상황

- 작성자는 작업 브랜치 `feat:문자열 길이 함수 작성`에서 `src/text_utils.py`에 `count_words` 함수를 추가하고 있었다.
- 상대 팀원은 같은 파일에 `truncate` 함수를 추가하는 `feat:문자열 공백 제거 유틸함수 추가` 브랜치를 먼저 `main`에 병합한 상태였다.
- 작성자가 작업 브랜치에 최신 `main` 내용을 rebase하는 과정에서 같은 파일의 두 위치(파일 상단 docstring 영역, 파일 하단 함수 추가 영역)에 서로 다른 내용이 있어 충돌이 발생했다.
- Git은 `feat:문자열 길이 함수작성`의 `truncate` 관련 변경 내용과 `feat:문자열 공백제거 유틸리티 함수`의 `count_words` 관련 변경 내용 중 어떤 내용을 최종 파일에 남겨야 하는지 자동으로 판단하지 못했다.

팀원1(윤대영) 추가: truncate 함수 포함

사용 예시:
from text_utils import validate_length, truncate

    validate_length("hello", min_length=3)  # True
    validate_length("hi", min_length=3)     # False
    truncate("hello world", max_length=5)   # "hello..."
팀원3(성원모) 추가: count_words 함수 포함

사용 예시:
from text_utils import validate_length, count_words

    validate_length("hello", min_length=3)  # True
    validate_length("hi", min_length=3)     # False
    count_words("hello world")              # 2
```

```text
def truncate(text: str, max_length: int, suffix: str = "...") -> str:
    """
    문자열을 지정된 길이로 자르고 suffix를 붙입니다.
    ...
    """
    if len(text) <= max_length:
        return text
    return text[:max_length] + suffix
def count_words(text: str) -> int:
    """
    문자열의 단어 수를 반환합니다.
    ...
    """
    return len(text.split())
```

### 해결 과정

- 충돌 표시를 기준으로 현재 작업 브랜치의 변경 내용과 `main` 브랜치에서 들어온 변경 내용을 비교했다.
- `HEAD`의 내용은 팀원1이 추가한 `truncate` 함수 관련 변경이고, 작업 브랜치의 내용은 팀원2가 추가한 `count_words` 함수 관련 변경이었기 때문에 두 내용 모두 필요하다고 판단했다.
- 두 충돌 구간 모두 양쪽 내용을 직접 수동으로 병합했다. docstring에는 두 함수를 모두 언급하도록 정리하고, 함수 본문은 `truncate`와 `count_words` 모두 남겼다.
- 수정 후 `git status`로 충돌 파일 상태를 확인했다.
- 충돌 해결 파일을 `git add src/text_utils.py`로 스테이징한 뒤, `git rebase --continue`로 rebase를 완료했다.
- 작업 브랜치를 원격 저장소에 다시 push한 뒤 GitHub PR 화면에서 충돌이 해결되었는지 확인했다.

### 결과

- `팀원1`의 `truncate` 함수와 `팀원2`의 `count_words` 함수를 모두 보존했다.
- 파일 상단 docstring과 사용 예시가 두 함수를 모두 반영하는 내용으로 정리되었다.
- 충돌 표시가 제거되어 파일이 정상적인 Python 코드 형식으로 정리되었다.
- PR에서 발생한 충돌이 해결되어 이후 리뷰 및 병합을 진행할 수 있는 상태가 되었다.

### 배운 점

- 같은 파일의 같은 위치를 여러 브랜치에서 동시에 수정하면 Git이 자동으로 병합하지 못해 충돌이 발생할 수 있다.
- 충돌이 발생했을 때는 한쪽 내용을 무조건 선택하기보다, 각 변경 사항의 목적을 확인한 뒤 필요한 내용을 모두 보존해야 한다.
- 충돌 구간이 한 파일에 여러 곳에 걸쳐 있을 수 있으므로, 충돌 표시(`<<<<<<<`, `=======`, `>>>>>>>`)가 파일 전체에 남아 있지 않은지 반드시 직접 확인해야 한다.
- 충돌 해결 후에는 `git status`로 상태를 확인하고, 수정 파일을 다시 스테이징한 뒤 `git rebase --continue`로 작업을 이어가야 한다.
- 파일 상단 docstring이나 공통 import 예시처럼 여러 사람이 동시에 수정할 가능성이 높은 영역은 작업 전에 팀원 간 미리 조율하면 충돌을 줄일 수 있다.

