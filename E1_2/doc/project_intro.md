# 🎯 파이썬 퀴즈 게임 프로젝트 개요

## 프로젝트 소개
**Python과 Git을 함께 배우는 첫 발자국** - 터미널에서 동작하는 인터랙티브한 퀴즈 게임을 Python으로 구현한 프로젝트입니다.

### 주요 목표
- Python 기초 문법 학습 및 실전 활용
- MVC(Model-View-Controller) 디자인 패턴 이해
- JSON 파일을 이용한 데이터 영속성 구현
- Git을 사용한 버전 관리 및 협업 기초 습득

---

## 기술 스택

| 항목 | 내용 |
|------|------|
| **언어** | Python 3.10+ |
| **패턴** | MVC (Model-View-Controller) |
| **데이터 저장** | JSON (UTF-8 인코딩) |
| **외부 라이브러리** | 없음 (표준 라이브러리만 사용) |
| **주요 모듈** | `json`, `os`, `random`, `datetime` |

---

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

---

## 핵심 기능

### ✅ 필수 기능
1. **메뉴 시스템**
   - 퀴즈 풀기, 추가, 목록 보기, 점수 확인, 종료
   - 재시작 후에도 퀴즈와 점수 유지

2. **퀴즈 풀기**
   - 기본 데이터: 파이썬 문법 관련 5개 퀴즈
   - 정답 확인 및 점수 계산 (정답률 기반)

3. **퀴즈 추가**
   - 새로운 퀴즈 등록 (문제 + 4개 선택지 + 정답)
   - 유효성 검증 및 파일에 자동 저장

4. **퀴즈 목록 조회**
   - 등록된 모든 퀴즈 확인

5. **점수 관리**
   - 최고 점수 자동 추적
   - 최고 점수 갱신 시 사용자 알림

6. **데이터 영속성**
   - state.json에서 데이터 로드/저장
   - 파일 손상 시 기본값으로 자동 복구

### ⭐ 보너스 기능
- 🔀 **랜덤 출제**: `random.shuffle()`로 퀴즈 순서 섞기
- 🎯 **문제 수 선택**: 몇 문제를 풀지 사용자 선택
- 🗑️ **퀴즈 삭제**: 등록된 퀴즈 삭제 기능
- 📊 **게임 기록**: 모든 게임 플레이 기록 저장 및 히스토리 조회

---

## 에러 처리 (미션 요구사항 충족)

### 입력 검증
- ✅ 공백 제거: `.strip()` 적용
- ✅ 빈 입력 처리: 재입력 유도
- ✅ 숫자 변환 실패: `except ValueError` 처리
- ✅ 범위 체크: 1~4, 1~7 등 범위 검증

### 예외 처리
- ✅ `KeyboardInterrupt` (Ctrl+C): 안전하게 종료
- ✅ `EOFError` (입력 스트림 종료): 프로그램 중단 없음
- ✅ 파일 없음: 기본 데이터로 초기화
- ✅ 파일 손상: `json.JSONDecodeError`, `ValueError` 등 모두 처리

---

## 데이터 저장 형식 (state.json)

```json
{
  "quizzes": [
    {
      "question": "파이썬에서 함수를 정의할 때 사용하는 키워드는 무엇인가요",
      "choices": ["func", "define", "def", "function"],
      "answer": 3
    }
  ],
  "best_score": 80,
  "history": [
    {
      "date": "2026-04-09 14:30",
      "score": 80,
      "correct": 4,
      "total": 5
    }
  ]
}
```

---

## 아키텍처

### MVC 패턴 적용

```
┌─────────────────────────────────────┐
│   main.py (QuizController)          │  ← 게임 흐름 관리
├─────────────────────────────────────┤
│                                     │
│  ┌──────────────┐  ┌──────────────┐│
│  │ quizGame.py  │  │ quizView.py  ││
│  │ (Model)      │  │ (View)       ││
│  │              │  │              ││
│  │ - 데이터관리 │  │ - UI 출력    ││
│  │ - 파일I/O   │  │ - 입력처리   ││
│  └──────────────┘  └──────────────┘│
│         ↓
│  quiz.py (Quiz, DEFAULT_QUIZZES)
│  ↓
└─────────────────────────────────────┘
         ↓
    state.json (데이터 저장)
```

**각 모듈의 역할:**
- **main.py (Controller)**: 사용자 선택 → 적절한 로직 실행
- **quizGame.py (Model)**: 데이터 관리, 저장, 불러오기
- **quizView.py (View)**: 화면 출력, 사용자 입력
- **quiz.py**: 개별 퀴즈 표현 (문제, 선택지, 정답)

---

## 클래스 및 메서드 정의

### 1️⃣ Quiz 클래스 (quiz.py)
개별 퀴즈를 표현하는 데이터 모델

| 메서드 | 파라미터 | 반환값 | 설명 |
|--------|---------|--------|------|
| `__init__()` | question(str), choices(list), answer(int) | - | 퀴즈 객체 초기화 |
| `is_correct()` | user_answer(int) | bool | 사용자 정답과 정확한 정답 비교 |
| `to_dict()` | - | dict | Quiz 객체를 JSON 저장 가능한 딕셔너리로 변환 |
| `from_dict()` (정적) | data(dict) | Quiz | JSON 데이터에서 Quiz 객체 생성 |

**상수:**
- `DEFAULT_QUIZZES`: 기본 퀴즈 5개 (파이썬 문법)

---

### 2️⃣ QuizView 클래스 (quizView.py)
사용자 인터페이스 및 입력 처리

| 메서드 | 파라미터 | 반환값 | 설명 |
|--------|---------|--------|------|
| `display_menu()` | - | - | 메인 메뉴 콘솔 출력 (7개 선택지) |
| `show_message()` | msg(str) | - | 안내 메시지 출력 |
| `get_valid_number()` | prompt(str), min_val(int), max_val(int) | int | **미션 검증**: 공백제거, 범위체크, 숫자검증 |
| `get_new_quiz_input()` | - | (str, list, int) | 새 퀴즈 입력: 문제 + 4개 선택지 + 정답번호 |
| `show_quiz_list()` | quizzes(list) | - | 등록된 퀴즈 목록 표시 |
| `show_history()` | history(list) | - | 게임 기록 히스토리 표시 (보너스) |

---

### 3️⃣ QuizModel 클래스 (quizGame.py)
데이터 관리 및 파일 I/O

| 메서드 | 파라미터 | 반환값 | 설명 |
|--------|---------|--------|------|
| `__init__()` | - | - | 모델 초기화, 데이터 로드 |
| `_load_data()` | - | - | state.json에서 데이터 로드 (파일 손상 시 복구) |
| `_save_data()` | - | - | 현재 상태를 state.json에 저장 (UTF-8, ensure_ascii=False) |
| `_reset_to_default()` | - | - | 기본 데이터로 초기화 |
| `add_quiz()` | new_quiz(Quiz) | - | 새로운 퀴즈 추가 후 저장 |
| `delete_quiz()` | index(int) | bool | 퀴즈 삭제 (보너스) |
| `update_best_score()` | score(int) | bool | 최고 점수 업데이트 |
| `add_history()` | record(dict) | - | 게임 기록 추가 (보너스) |

**속성:**
- `quizzes`: Quiz 객체 리스트
- `best_score`: 최고 점수 (int)
- `history`: 게임 기록 히스토리 (list, 보너스)
- `DATA_FILE`: "state.json" (상수)

---

### 4️⃣ QuizController 클래스 (main.py)
게임 흐름 관리 (MVC 컨트롤러)

| 메서드 | 파라미터 | 반환값 | 설명 |
|--------|---------|--------|------|
| `__init__()` | - | - | Model(QuizModel)과 View(QuizView) 인스턴스 생성 |
| `play_quiz()` | - | - | 퀴즈 풀기: 문제 선택→정답 확인→점수계산→기록저장 |
| `run()` | - | - | 메인 루프: 메뉴 표시→선택→기능 실행 (Ctrl+C 안전처리) |

**기능별 흐름:**
- **1번 선택**: `play_quiz()` 호출 → 랜덤 섞기 → 점수 계산
- **2번 선택**: `quizView.get_new_quiz_input()` → `quizModel.add_quiz()`
- **3번 선택**: `quizView.show_quiz_list()`
- **4번 선택**: 최고 점수 출력
- **5번 선택**: `quizModel.delete_quiz()` (보너스)
- **6번 선택**: `quizView.show_history()` (보너스)
- **7번 선택**: 루프 탈출 → 프로그램 종료

---

## 클래스 실행 순서 (프로그램 흐름)

### 초기화 단계 (Initialization)

| 단계 | 클래스 | 메서드 | 실행 내용 | 상태 |
|------|--------|--------|---------|------|
| 1 | - | `if __name__ == "__main__"` | 프로그램 진입점 | **시작** |
| 2 | QuizController | `__init__()` | Model, View 인스턴스 생성 | 초기화 |
| 3 | QuizModel | `__init__()` | 속성 초기화 (quizzes, best_score, history) | 준비 |
| 4 | QuizModel | `_load_data()` | state.json 파일 유무 확인 | 데이터 로드 |
| 4-1 | QuizModel | `_reset_to_default()` | (파일 없음) 기본 데이터 로드 | 초기 데이터 |
| 4-2 | QuizModel | `_save_data()` | (파일 없음) state.json 생성 및 저장 | 파일 저장 |
| 4-3 | QuizModel | (JSON 파싱) | (파일 있음) 데이터 로드 및 검증 | 데이터 로드 |
| 5 | QuizView | (자동 생성) | View 인스턴스 생성 완료 | **준비 완료** |

### 메인 루프 단계 (Main Game Loop)

| 단계 | 클래스 | 메서드 | 실행 내용 | 데이터 변화 |
|------|--------|--------|---------|-----------|
| 1 | QuizController | `run()` | 메인 루프 시작 (while True) | - |
| 2 | QuizView | `display_menu()` | 메뉴 7개 선택지 출력 | - |
| 3 | QuizView | `get_valid_number()` | 사용자 선택 입력 (1~7) | - |
| **4-1** | QuizController | `play_quiz()` | **(선택=1) 퀴즈 풀기** | |
| | QuizModel | (quizzes 참조) | 복사본 생성 및 랜덤 섞기 | - |
| | QuizView | `get_valid_number()` | 문제 수 선택 | - |
| | (반복) | - | 각 문제마다 정답 입력 → 채점 | correct++ |
| | QuizModel | `add_history()` | 게임 기록 저장 | history 추가 |
| | QuizModel | `update_best_score()` | 최고 점수 갱신 여부 확인 | best_score 업데이트 |
| | QuizModel | `_save_data()` | state.json에 저장 | 파일 동기화 |
| **4-2** | QuizView | `get_new_quiz_input()` | **(선택=2) 새 퀴즈 정보 입력** | |
| | Quiz | `__init__()` | 입력값으로 Quiz 객체 생성 | - |
| | QuizModel | `add_quiz()` | quizzes 리스트에 추가 | quizzes.append() |
| | QuizModel | `_save_data()` | state.json에 저장 | 파일 동기화 |
| **4-3** | QuizView | `show_quiz_list()` | **(선택=3) 퀴즈 목록 표시** | - |
| | (반복) | - | 번호와 함께 모든 퀴즈 출력 | - |
| **4-4** | QuizView | `show_message()` | **(선택=4) 최고 점수 출력** | - |
| **4-5** | QuizView | `show_quiz_list()` | **(선택=5) 퀴즈 목록 표시** (삭제용) | - |
| | QuizView | `get_valid_number()` | 삭제할 퀴즈 번호 입력 | - |
| | QuizModel | `delete_quiz()` | 해당 인덱스 퀴즈 삭제 | quizzes 수정 |
| | QuizModel | `_save_data()` | state.json에 저장 | 파일 동기화 |
| **4-6** | QuizView | `show_history()` | **(선택=6) 게임 기록 히스토리 표시** | - |
| | (반복) | - | 모든 플레이 기록 출력 | - |
| **4-7** | QuizController | (루프 탈출) | **(선택=7) break 실행** | - |
| | - | - | while True 탈출 | **종료 대기** |
| 5 | (except) | - | **Ctrl+C or EOFError 발생** | - |
| 6 | QuizView | `show_message()` | "안전하게 종료합니다" 메시지 표시 | - |
| 7 | - | - | **프로그램 종료** | ✅ 완료 |

### 데이터 흐름도

각 선택별 state.json 동기화:

```
┌─────────────────────────────────────────────────┐
│  선택 1~7 입력                                    │
└─────────────────────────────────────────────────┘
                      ↓
        ┌──────────────────────────────┐
        │  사용자 입력 검증              │
        │  (get_valid_number)          │
        └──────────────────────────────┘
                      ↓
    ┌─────────────────────────────────────────┐
    │ 선택에 따른 메서드 호출                   │
    ├─────────────────────────────────────────┤
    │ 1: play_quiz()   ─→ add_history()    │
    │ 2: add_quiz()    ─→ _save_data()     │
    │ 3: show_quiz_list()  (읽기만)         │
    │ 4: show_message()    (읽기만)         │
    │ 5: delete_quiz()  ─→ _save_data()    │
    │ 6: show_history()    (읽기만)         │
    │ 7: break (루프 탈출)                  │
    └─────────────────────────────────────────┘
                      ↓
    ┌─────────────────────────────────────────┐
    │  데이터 변경 시 _save_data() 호출       │
    │  (JSON 형식으로 state.json 저장)        │
    └─────────────────────────────────────────┘
                      ↓
    ┌─────────────────────────────────────────┐
    │  메뉴 재표시 또는 프로그램 종료           │
    └─────────────────────────────────────────┘
```

---

## 개발 과정

### 완성된 작업
1. ✅ 4개 모듈 구현 (main, quiz, quizGame, quizView)
2. ✅ 기본 퀴즈 5개 데이터
3. ✅ 메뉴, 풀기, 추가, 목록, 점수 기능
4. ✅ state.json 저장/불러오기
5. ✅ 미션 요구 에러 처리 100%
6. ✅ 보너스 기능 구현 (4가지)
7. ✅ 모든 모듈 주석 및 독스트링 추가
8. ✅ Git 머지 완료

### 남은 작업
- README.md 작성
- Git 저장소 복제 실습 (clone → push → pull)

---

## 주요 학습 포인트

### Python 문법
- 클래스와 객체 지향 프로그래밍 (`__init__`, `self`)
- 메서드와 정적 메서드 (`@staticmethod`)
- 예외 처리 (`try-except`)
- JSON 처리 (`json.load`, `json.dump`)
- 리스트 컴프리헨션 (`[... for ...]`)
- f-string 포매팅

### Git 워크플로우
- `git init`: 저장소 초기화
- `git add/commit`: 변경사항 저장
- `git branch/checkout`: 브랜치 관리
- `git merge`: 브랜치 병합
- `git clone/pull`: 원격 저장소 동기화
- `git push`: 로컬 변경사항 업로드

---

## 실행 방법

```bash
# 프로젝트 디렉토리 진입
cd E1_2/src

# 프로그램 실행
python main.py
```

---

## 미션 요구사항 체크리스트

- [x] **Python 코드**: 2개 이상 클래스 (Quiz, QuizModel), 메서드 분리
- [x] **기본 데이터**: 파이썬 문법 관련 5개 이상 퀴즈
- [x] **파일 저장**: state.json (UTF-8, JSON 형식)
- [x] **에러 처리**: 공백, 숫자 검증, 범위 체크, Ctrl+C
- [x] **Git 저장소**: 10개 이상 의미있는 커밋
- [x] **브랜치 병합**: checkout, merge 사용
- [x] **README.md**: (작성 예정)
- [x] **clone/pull 실습**: (진행 예정)

---

## 버전 정보

- **Python**: 3.10+
- **최종 업데이트**: 2026년 4월 9일
- **상태**: 기본 기능 완성 + 보너스 기능 포함

