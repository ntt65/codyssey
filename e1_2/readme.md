
동작하는 퀴즈 게임
프로그램 실행 시 메뉴에서 번호를 선택하면, 선택 결과에 따라 퀴즈 출제/등록/목록/점수 확인/종료 화면이 출력된다.
퀴즈 풀기, 퀴즈 추가, 퀴즈 목록, 점수 확인 기능이 동작한다.
본인이 선택한 주제의 퀴즈가 5개 이상 포함되어 있다.
프로그램을 종료하고 다시 실행해도 추가한 퀴즈와 최고 점수가 유지된다. (파일 저장)
코드 구조
최소 2개 이상의 클래스가 정의되어 있다. (예: Quiz, QuizGame)
기능별로 메서드가 분리되어 있다. (입력 처리/게임 진행/저장 로직 등)
데이터는 프로젝트 루트의 state.json에 UTF-8 인코딩으로 저장하고 불러온다.
GitHub 저장소
프로젝트 코드가 GitHub에 업로드되어 있다.
최소 10개 이상의 의미 있는 커밋이 존재한다.
최소 1회 이상의 브랜치 생성 및 병합(checkout, merge) 기록이 있다.
clone과 pull을 각각 1회 이상 사용한 기록이 있다.
README.md에 아래 항목이 포함되어 있다.
프로젝트 개요
퀴즈 주제 선정 이유
실행 방법
기능 목록
파일 구조
데이터 파일 설명(state.json 등)

# Git과 함께하는 Python 첫 발자국
## 프로젝트 개요
- 터미널에서 동작하는 인터랙티브한 퀴즈 게임을 Python으로 구현한 프로젝트입니다.
### 기술 스택
| 항목 | 내용 |
|------|------|
| **언어** | Python 3.10+ |
| **패턴** | MVC (Model-View-Controller) |
| **데이터 저장** | JSON (UTF-8 인코딩) |
| **외부 라이브러리** | 없음 (표준 라이브러리만 사용) |
| **주요 모듈** | `json`, `os`, `random`, `datetime` |
## 퀴즈 주제와 선정 이유
- Python, 현재 python학습중이라 친숙해지기 위해
## 실행 방법
- 터미널이나 CMD 창에서 **python main.py**를 입력하여 실행
# 기능 목록
- 퀴즈 풀기: 저장된 문제를 풀고 정답 여부를 확인하며, 최종 점수를 계산합니다.
- 퀴즈 추가: 새로운 문제와 4개의 선택지, 정답 번호를 입력받아 시스템에 등록합니다.
- 퀴즈 목록 조회: 현재 등록된 모든 퀴즈의 질문 리스트를 확인합니다.
- 최고 점수 관리: 역대 최고 점수를 기록하고, 퀴즈를 풀 때마다 갱신 여부를 확인합니다.
- 데이터 영속성 유지: 모든 데이터는 state.json에 저장되어 프로그램 재시작 후에도 유지됩니다.
# 파일 구조
## 프로젝트 구조
```
E1_2/
├── src/
│   ├── main.py           # 메인 컨트롤러 (게임 흐름 관리)
│   ├── quiz.py           # Quiz 데이터 모델
│   ├── quizGame.py       # QuizModel (데이터 저장/불러오기)
│   └── quizView.py       # QuizView (UI 및 입력 처리)
├── doc/
│   ├── mission.md        # 미션 요구사항
│   ├── project_intro.md  # 프로젝트 개요 (본 파일)
│   └── plan.md           # 개발 계획
├── README.md             # 프로젝트 설명서
└── state.json            # 데이터 저장 파일 (자동 생성)
```

### Class Diagram
```mermaid
classDiagram
    class Quiz {
        -question: str
        -choices: list
        -answer: int
        +__init__(question, choices, answer)
        +is_correct(user_answer) bool
        +to_dict() dict
        +from_dict(data) Quiz
    }
    
    class QuizModel {
        -quizzes: list
        -best_score: int
        -history: list
        -DATA_FILE: str
        +__init__()
        +_load_data()
        +_save_data()
        +_reset_to_default()
        +add_quiz(new_quiz)
        +delete_quiz(index) bool
        +update_best_score(score) bool
        +add_history(record)
    }
    
    class QuizView {
        +display_menu()
        +show_message(msg)
        +wait_for_enter()
        +get_valid_number(prompt, min_val, max_val) int
        +get_new_quiz_input() tuple
        +show_quiz(quiz) int
        +show_quiz_list(quizzes)
        +show_history(history)
    }
    
    class QuizController {
        -model: QuizModel
        -view: QuizView
        +__init__()
        +play_quiz()
        +run()
    }
    
    QuizController --> QuizModel : uses
    QuizController --> QuizView : uses
    QuizModel --> Quiz : manages
    QuizView --> Quiz : displays
``` 

# 데이터 파일 설명(state.json 경로/역할/스키마)
경로: 프로젝트 루트 디렉토리 (./state.json)
역할: 프로그램 종료 후에도 추가된 퀴즈와 최고 점수가 유지되도록 데이터를 저장하는 데이터 영속성을 담당합니다
. 파일이 없거나 손상된 경우 기본 데이터로 자동 복구하는 기능도 포함합니다
```
state.json (데이터 구조)
├── 📂 quizzes (List: 퀴즈 목록)
│   └── 📄 Quiz Object
│       ├── ❓ question (String: 문제 내용)
│       ├── 📜 choices (List: 4개의 선택지)
│       └── ✅ answer (Integer: 정답 번호 1~4)
├── 🏆 best_score (Integer: 최고 점수)
└── 🕒 history (List: 게임 기록 히스토리)
``` 

# Git: README 작성 후 최종 푸시한다.

### ⚙️ Git 저장소 복제 실습

* 이 단계는 `clone`과 `pull` 명령어를 자연스럽게 경험하기 위한 실습이다. 퀴즈 게임 개발이 완료된 후 아래 절차를 순서대로 수행한다.
* 미션 수행 저장소를 `clone`하여 별도의 로컬 디렉터리에 복제한다.
* 복제된 저장소에서 간단한 변경(예: README에 한 줄 추가)을 하고 `commit` → `push`한다.
* 기존 로컬 작업 디렉터리에서 `pull`로 변경사항을 가져온다.
* `pull` 받은 내용이 정상적으로 반영되었는지 확인한다.

---

## 5. 보너스 과제 (선택)
* **랜덤 출제:** 퀴즈 풀기 시 문제 순서를 랜덤하게 섞는다. (`random` 모듈 사용법 스스로 학습)
* **문제 수 선택:** 퀴즈 풀기 시 몇 문제를 풀지 선택할 수 있다.
* **힌트 기능:** `Quiz` 클래스에 힌트 속성을 추가한다. 풀이 중 힌트를 볼 수 있으며, 사용 시 점수 차감 로직을 구현한다.
* **퀴즈 삭제 기능:** 등록된 퀴즈를 삭제할 수 있다. 삭제 후 파일에 반영한다.
* **점수 기록 히스토리:** 최고 점수뿐 아니라 모든 게임 기록을 저장한다. 날짜/시간, 푼 문제 수, 점수를 기록한다.

---

## 6. 개발 환경
* Python 3.10 이상을 사용해야 한다.
```bash
mpeg46551@c5r1s2 codyssey % python --version
Python 3.12.13
```
* 외부 라이브러리 없이 기본 문법만 사용해야 한다. (표준 라이브러리 사용 가능)

---

## 7. 제약 사항

### 📌 데이터 저장 규칙
* 데이터 파일은 프로젝트 루트의 `state.json`을 기본으로 한다.

* state.json 전체내용
```bash
mpeg46551@c5r1s2 e1_2 % cd src
mpeg46551@c5r1s2 src % ls
__pycache__     main.py         quiz.py         quizGame.py     quizView.py     state.json
mpeg46551@c5r1s2 src % cat state.json
{
  "quizzes": [
    {
      "question": "파이썬의 창시자는?",
      "choices": [
        "제임스 고슬링",
        "리누스 토르발스",
        "귀도 반 로섬",
        "브렌던 아이크"
      ],
      "answer": 3
    },
    {
      "question": "파이썬 내장 데이터 타입이 아닌 것은?",
      "choices": [
        "int",
        "str",
        "bool",
        "char"
      ],
      "answer": 4
    },
    {
      "question": "원격 저장소로 업로드하는 Git 명령어는?",
      "choices": [
        "git pull",
        "git commit",
        "git push",
        "git clone"
      ],
      "answer": 3
    },
    {
      "question": "JSON의 약자는?",
      "choices": [
        "Java Standard Object Notation",
        "JavaScript Object Notation",
        "Java Syntax Output Network",
        "JavaScript Online Node"
      ],
      "answer": 2
    },
    {
      "question": "파이썬 함수 정의 키워드는?",
      "choices": [
        "func",
        "define",
        "def",
        "function"
      ],
      "answer": 3
    }
  ],
  "best_score": 20,
  "history": [
    {
      "date": "2026-04-09 13:14",
      "score": 0,
      "correct": 0,
      "total": 1
    },
    {
      "date": "2026-04-09 15:24",
      "score": 0,
      "correct": 0,
      "total": 2
    },
    {
      "date": "2026-04-09 15:25",
      "score": 0,
      "correct": 0,
      "total": 1
    }
  ]
}%                
```
* 파일 인코딩은 UTF-8을 권장한다.
```bash
# state.json 파일 읽기 (UTF-8 인코딩)
            with open(self.DATA_FILE, "r", encoding="utf-8") as f:
```

### 📌 코드 구조
* 모든 코드를 한 함수에 작성하지 않고, 기능별로 함수를 분리해야 한다.
* 최소 2개 이상의 클래스로 역할을 분리해야 한다.

### Menu Sequence Diagram
```mermaid
sequenceDiagram
    participant User
    participant Main as main.py<br/>(Controller)
    participant View as quizView.py<br/>(View)
    participant Model as quizGame.py<br/>(Model)
    participant Quiz as quiz.py<br/>(Quiz)
    participant File as state.json

    User->>Main: python main.py 실행
    Main->>Model: __init__()
    Model->>File: _load_data()
    File-->>Model: JSON 데이터 로드
    Model->>Quiz: from_dict() 변환
    Quiz-->>Model: Quiz 객체 리스트
    Model-->>Main: 초기화 완료

    loop 메인 루프
        Main->>View: display_menu()
        View-->>User: 메뉴 표시
        User->>View: 선택 입력
        View->>View: get_valid_number() 검증
        View-->>Main: 선택값 반환

        alt 선택 == 1: 퀴즈 풀기
            Main->>View: get_valid_number(문제수)
            View-->>Main: count 반환
            Main->>Main: random.shuffle(quizzes)
            Main->>Main: 선택된 수만큼 퀴즈 추출
            loop 각 퀴즈마다
                Main->>View: show_quiz(quiz)
                View-->>User: 문제와 선택지 출력
                User->>View: 정답 입력
                View->>Quiz: is_correct(user_answer)
                Quiz-->>View: 정답 여부 반환
                View-->>User: ✅/❌ 피드백
                View-->>Main: 정답 개수 반환
            end
            Main->>Main: 점수 계산 (정답률%)
            Main->>Model: add_history(기록)
            Model->>File: _save_data()
            Main->>Model: update_best_score(score)
            Model->>File: _save_data()
            View-->>User: 점수 표시

        else 선택 == 2: 새 퀴즈 추가
            Main->>View: get_new_quiz_input()
            View-->>User: 문제, 선택지, 정답 입력
            User->>View: 퀴즈 정보 입력
            View->>View: get_valid_number() 검증
            View-->>Main: (문제, 선택지, 정답) 반환
            Main->>Quiz: __init__() 생성
            Main->>Model: add_quiz(quiz)
            Model->>File: _save_data()

        else 선택 == 3: 퀴즈 목록 보기
            Main->>View: show_quiz_list(quizzes)
            View-->>User: 퀴즈 목록 표시

        else 선택 == 4: 최고 점수 확인
            Main->>Model: best_score 조회
            View-->>User: 최고 점수 출력

        else 선택 == 5: 퀴즈 삭제
            Main->>View: show_quiz_list(quizzes)
            View-->>User: 퀴즈 목록 표시
            User->>View: 삭제할 번호 입력
            Main->>Model: delete_quiz(index)
            Model->>File: _save_data()

        else 선택 == 6: 게임 기록 보기
            Main->>Model: history 조회
            Main->>View: show_history(history)
            View-->>User: 게임 기록 표시

        else 선택 == 7: 게임 종료
            Main->>Main: break
        end
    end

    Main->>View: show_message(종료 메시지)
    Model->>File: _save_data()
    Main-->>User: 프로그램 종료
```

### 📌 Git 워크플로우
* 최소 10개 이상의 의미 있는 커밋이 있어야 한다.
![git log](e1_2/pic/git_log.png)
* 기능 단위 커밋(메뉴/Quiz/플레이/추가/저장/README 등) + 커밋 메시지에 변경 요약 포함
* 형식적인 커밋 메시지를 피하고, 아래처럼 작업 내용을 드러내는 형식을 권장한다.
    * `Feat: 퀴즈 출제 기능 구현`
    * `Fix: 점수 계산 오류 수정`
    * `Docs: README 실행 방법 추가`
    * `Refactor: QuizGame 책임 분리`
* Git 기초 명령어 7종(`init`, `add`, `commit`, `push`, `pull`, `checkout`, `clone`)을 각각 한 번 이상 사용해야 한다.

### 📌 제출물
* GitHub 저장소 URL
* 개발 환경 설정 스크린샷(예: VSCode, Python 버전, Git 설정)
* 프로그램 실행 결과 스크린샷(퀴즈 추가, 목록, 플레이, 점수)
* `git log --oneline --graph` 결과 스크린샷

---

## 8. 결과 예시
### ✅ 동작하는 퀴즈 게임
* 프로그램 실행 시 메뉴에서 번호를 선택하면, 선택 결과에 따라 퀴즈 출제/등록/목록/점수 확인/종료 화면이 출력된다.
```
mpeg46551@c5r1s2 e1_2 % python src/main.py
```p
mpeg46551@c5r1s2 codyssey % cd e1_2
mpeg46551@c5r1s2 e1_2 % python src/main.py

==============================
   파이썬 퀴즈 챌린지
==============================
1. 퀴즈 풀기 (랜덤/수량)
2. 새로운 퀴즈 추가
3. 퀴즈 목록 보기
4. 최고 점수 확인
5. 퀴즈 삭제하기 (보너스)
6. 전체 기록 보기 (보너스)
7. 게임 종료
==============================
선택: 
⚠ 입력이 비어있습니다.
선택: 0
⚠ 1~7 사이를 입력하세요.
선택: a
⚠ 숫자를 입력해주세요.
선택: 1
몇 문제를 푸시겠습니까? (1~6): 0
⚠ 1~6 사이를 입력하세요.
몇 문제를 푸시겠습니까? (1~6): 
=============================
   파이썬 퀴즈 챌린지
==============================
1. 퀴즈 풀기 (랜덤/수량)
2. 새로운 퀴즈 추가
3. 퀴즈 목록 보기
4. 최고 점수 확인
5. 퀴즈 삭제하기 (보너스)
6. 전체 기록 보기 (보너스)
7. 게임 종료
==============================
선택: 2

[새 퀴즈 추가]
문제: python의 변수 타입이 아닌것은?
보기1: ㅑint
보기2: float
보기3: str
보기4: print
정답(1-4): 4

==============================
   파이썬 퀴즈 챌린지
==============================
1. 퀴즈 풀기 (랜덤/수량)
2. 새로운 퀴즈 추가
3. 퀴즈 목록 보기
4. 최고 점수 확인
5. 퀴즈 삭제하기 (보너스)
6. 전체 기록 보기 (보너스)
7. 게임 종료
==============================
선택: 3
1. 파이썬에서 함수를 정의할 때 사용하는 키워드는 무엇인가요
2. 다음 중 파이썬의 기본 데이터 타입이 아닌 것은 무엇인가요
3. 화면에 값을 출력하기 위해 사용하는 함수는 무엇인가요
4. 리스트의 맨 끝에 새로운 요소를 추가하는 메서드는 무엇인가요
5. 조건에 따라 코드를 실행할지 결정하는 키워드는 무엇인가요
6. python의 변수 타입이 아닌것은?

==============================
   파이썬 퀴즈 챌린지
==============================
1. 퀴즈 풀기 (랜덤/수량)
2. 새로운 퀴즈 추가
3. 퀴즈 목록 보기
4. 최고 점수 확인
5. 퀴즈 삭제하기 (보너스)
6. 전체 기록 보기 (보너스)
7. 게임 종료
==============================
선택: 4

🔥 최고 점수: 0점
==============================
   파이썬 퀴즈 챌린지
==============================
1. 퀴즈 풀기 (랜덤/수량)
2. 새로운 퀴즈 추가
3. 퀴즈 목록 보기
4. 최고 점수 확인
5. 퀴즈 삭제하기 (보너스)
6. 전체 기록 보기 (보너스)
7. 게임 종료
==============================
선택: 5

1. 파이썬에서 함수를 정의할 때 사용하는 키워드는 무엇인가요
2. 다음 중 파이썬의 기본 데이터 타입이 아닌 것은 무엇인가요
3. 화면에 값을 출력하기 위해 사용하는 함수는 무엇인가요
4. 리스트의 맨 끝에 새로운 요소를 추가하는 메서드는 무엇인가요
5. 조건에 따라 코드를 실행할지 결정하는 키워드는 무엇인가요
6. python의 변수 타입이 아닌것은?
삭제할 번호: 

==============================
   파이썬 퀴즈 챌린지
==============================
1. 퀴즈 풀기 (랜덤/수량)
2. 새로운 퀴즈 추가
3. 퀴즈 목록 보기
4. 최고 점수 확인
5. 퀴즈 삭제하기 (보너스)
6. 전체 기록 보기 (보너스)
7. 게임 종료
==============================
선택: 6

[게임 기록 히스토리]
- 2026-04-10 21:08 | 점수: 0점 (0/1)

==============================
   파이썬 퀴즈 챌린지
==============================
1. 퀴즈 풀기 (랜덤/수량)
2. 새로운 퀴즈 추가
3. 퀴즈 목록 보기
4. 최고 점수 확인
5. 퀴즈 삭제하기 (보너스)
6. 전체 기록 보기 (보너스)
7. 게임 종료
==============================
선택: 7
```
* 퀴즈 풀기, 퀴즈 추가, 퀴즈 목록, 점수 확인 기능이 동작한다.

* 본인이 선택한 주제의 퀴즈가 5개 이상 포함되어 있다.
* 프로그램을 종료하고 다시 실행해도 추가한 퀴즈와 최고 점수가 유지된다. (파일 저장)
```p
==============================
   파이썬 퀴즈 챌린지
==============================
1. 퀴즈 풀기 (랜덤/수량)
2. 새로운 퀴즈 추가
3. 퀴즈 목록 보기
4. 최고 점수 확인
5. 퀴즈 삭제하기 (보너스)
6. 전체 기록 보기 (보너스)
7. 게임 종료
==============================
선택: 4
🔥 최고 점수: 100점

==============================
   파이썬 퀴즈 챌린지
==============================
1. 퀴즈 풀기 (랜덤/수량)
2. 새로운 퀴즈 추가
3. 퀴즈 목록 보기
4. 최고 점수 확인
5. 퀴즈 삭제하기 (보너스)
6. 전체 기록 보기 (보너스)
7. 게임 종료
==============================
선택: 7
mpeg46551@c5r1s2 e1_2 % python src/main.py

==============================
   파이썬 퀴즈 챌린지
==============================
1. 퀴즈 풀기 (랜덤/수량)
2. 새로운 퀴즈 추가
3. 퀴즈 목록 보기
4. 최고 점수 확인
5. 퀴즈 삭제하기 (보너스)
6. 전체 기록 보기 (보너스)
7. 게임 종료
==============================
선택: 4
🔥 최고 점수: 100점
stte.json
  "best_score": 100,
```

### state.json 예시 (데이터 형태 참고)
```json
{
    "quizzes": [
        {
            "question": "Python의 창시자는?",
            "choices": ["Guido", "Linus", "Bjarne", "James"],
            "answer": 1
        }
    ],
    "best_score": 3
}
```

### README 제출 체크리스트
* 프로젝트 개요
* 퀴즈 주제 선정 이유
* 실행 방법 (예: `python main.py`)
* 기능 목록(퀴즈 풀기/추가/목록/점수)
* 파일 구조
* 데이터 파일 설명(`state.json` 경로/역할/필드 구조)

### 실행 화면 스크린샷 구성 예시(학습자 캡처)
* `docs/screenshots/menu.png`
* `docs/screenshots/play.png`
* `docs/screenshots/add_quiz.png`
* `docs/screenshots/score.png`append one line at codyclone local repository
