
class Quiz:
    def __init__(self, question, choices, answer):
        self.question = question # 문제 (str)
        self.choices = choices   # 선택지 4개 (list)
        self.answer = answer     # 정답 번호 (int, 1~4)

    def is_correct(self, user_answer):
        """사용자 입력과 정답 비교"""
        return user_answer == self.answer

    def to_dict(self):
        """JSON 저장용 딕셔너리 변환"""
        return {
            "question": self.question,
            "choices": self.choices,
            "answer": self.answer,
        }

    @staticmethod
    def from_dict(data):
        """딕셔너리에서 Quiz 객체 생성"""
        return Quiz(data["question"], data["choices"], data["answer"])

# 특수 문자를 배제한 파이썬 문법 기본 퀴즈 데이터
DEFAULT_QUIZZES = [
    Quiz("파이썬에서 함수를 정의할 때 사용하는 키워드는 무엇인가요", ["func", "define", "def", "function"], 3),
    Quiz("다음 중 파이썬의 기본 데이터 타입이 아닌 것은 무엇인가요", ["int", "str", "bool", "char"], 4),
    Quiz("화면에 값을 출력하기 위해 사용하는 함수는 무엇인가요", ["input", "print", "write", "show"], 2),
    Quiz("리스트의 맨 끝에 새로운 요소를 추가하는 메서드는 무엇인가요", ["add", "push", "append", "insert"], 3),
    Quiz("조건에 따라 코드를 실행할지 결정하는 키워드는 무엇인가요", ["if", "for", "while", "def"], 1)
]


### 2. `quizGame.py` (데이터 관리 모델)
# state.json` 파일을 관리하며, 퀴즈 목록과 **최고 점수**, **보너스용 히스토리**를 저장하고 불러옵니다.


import json
import os
from quiz import Quiz, DEFAULT_QUIZZES

class QuizModel:
    DATA_FILE = "state.json"

    def __init__(self):
        self.quizzes = []
        self.best_score = 0
        self.history = [] # 보너스: 게임 기록 히스토리
        self._load_data()

    def _load_data(self):
        """파일이 없거나 손상된 경우 기본 데이터로 복구"""
        if not os.path.exists(self.DATA_FILE):
            self._reset_to_default()
            self._save_data()
            return

        try:
            with open(self.DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                if "quizzes" not in raw or "best_score" not in raw:
                    raise ValueError("필수 키 누락")
                self.quizzes = [Quiz.from_dict(q) for q in raw["quizzes"]]
                self.best_score = int(raw["best_score"])
                self.history = raw.get("history", []) # 히스토리 로드
        except (json.JSONDecodeError, ValueError, KeyError, TypeError):
            self._reset_to_default()
            self._save_data()

    def _save_data(self):
        """현재 상태를 state.json에 저장"""
        try:
            data = {
                "quizzes": [q.to_dict() for q in self.quizzes],
                "best_score": self.best_score,
                "history": self.history # 히스토리 저장
            }
            with open(self.DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass

    def _reset_to_default(self):
        """기본 데이터 초기화"""
        self.quizzes = [Quiz(q.question, q.choices[:], q.answer) for q in DEFAULT_QUIZZES]
        self.best_score = 0
        self.history = []

    def add_quiz(self, new_quiz):
        self.quizzes.append(new_quiz)
        self._save_data()

    def delete_quiz(self, index):
        """보너스: 퀴즈 삭제"""
        if 0 <= index < len(self.quizzes):
            del self.quizzes[index]
            self._save_data()
            return True
        return False

    def update_best_score(self, score):
        if score > self.best_score:
            self.best_score = score
            self._save_data()
            return True
        return False

    def add_history(self, record):
        """보너스: 게임 기록 추가"""
        self.history.append(record)
        self._save_data()


### 3. `quizView.py` (화면 출력 및 입력 뷰)
#사용자 인터페이스와 미션 필수 예외 처리(공백 제거, 숫자 검증 등)를 담당합니다.


class QuizView:
    def display_menu(self):
        print("\n" + "="*30)
        print("   파이썬 퀴즈 챌린지")
        print("="*30)
        print("1. 퀴즈 풀기 (랜덤/수량)")
        print("2. 새로운 퀴즈 추가")
        print("3. 퀴즈 목록 보기")
        print("4. 최고 점수 확인")
        print("5. 퀴즈 삭제하기 (보너스)")
        print("6. 전체 기록 보기 (보너스)")
        print("7. 게임 종료")
        print("="*30)

    def show_message(self, msg):
        print(msg)

    def get_valid_number(self, prompt, min_val, max_val):
        """미션 요구 예외 처리 (공백 제거, 범위 체크 등)"""
        while True:
            try:
                user_input = input(prompt).strip()
                if not user_input:
                    print("⚠ 입력이 비어있습니다.")
                    continue
                num = int(user_input)
                if min_val <= num <= max_val:
                    return num
                print(f"⚠ {min_val}~{max_val} 사이를 입력하세요.")
            except ValueError:
                print("⚠ 숫자를 입력해주세요.")

    def get_new_quiz_input(self):
        print("\n[새 퀴즈 추가]")
        q = input("문제: ").strip()
        c = [input(f"보기{i}: ").strip() for i in range(1, 5)]
        a = self.get_valid_number("정답(1-4): ", 1, 4)
        return q, c, a

    def show_quiz_list(self, quizzes):
        if not quizzes:
            print("⚠ 등록된 퀴즈가 없습니다.")
            return
        for i, q in enumerate(quizzes, 1):
            print(f"{i}. {q.question}")

    def show_history(self, history):
        if not history:
            print("⚠ 기록이 없습니다.")
            return
        print("\n[게임 기록 히스토리]")
        for h in history:
            print(f"- {h['date']} | 점수: {h['score']}점 ({h['correct']}/{h['total']})")


### 4. `main.py` (전체 흐름 제어 컨트롤러)
# `QuizController`를 통해 전체 게임 루프를 실행하며 보너스 로직(랜덤 섞기 등)을 제어합니다.


import random
from datetime import datetime
from quizGame import QuizModel
from quiz import Quiz
from quizView import QuizView

class QuizController:
    def __init__(self):
        self.model = QuizModel()
        self.view = QuizView()

    def play_quiz(self):
≈       미션의 요구사항(MVC 패턴, 데이터 영속성, 예외 처리)과 요청하신 **보너스 기능(삭제, 기록, 랜덤/수량 선택)** 및 **특수 문자가 없는 파이썬 문법 퀴즈**를 반영한 전체 코드를 구성해 드립니다. 코드는 총 4개의 파일(`quiz.py`, `quizGame.py`, `quizView.py`, `main.py`)로 나뉩니다.

### 1. `quiz.py` (개별 퀴즈 모델)
# 개별 퀴즈의 속성을 정의하고, 객체와 딕셔너리 간 변환을 담당합니다. 또한 특수 문자를 배제한 파이썬 문법 기본 문제를 포함합니다.

class Quiz:
    def __init__(self, question, choices, answer):
        self.question = question # 문제 (str)
        self.choices = choices   # 선택지 4개 (list)
        self.answer = answer     # 정답 번호 (int, 1~4)

    def is_correct(self, user_answer):
        """사용자 입력과 정답 비교"""
        return user_answer == self.answer

    def to_dict(self):
        """JSON 저장용 딕셔너리 변환"""
        return {
            "question": self.question,
            "choices": self.choices,
            "answer": self.answer,
        }

    @staticmethod
    def from_dict(data):
        """딕셔너리에서 Quiz 객체 생성"""
        return Quiz(data["question"], data["choices"], data["answer"])

# 특수 문자를 배제한 파이썬 문법 기본 퀴즈 데이터
DEFAULT_QUIZZES = [
    Quiz("파이썬에서 함수를 정의할 때 사용하는 키워드는 무엇인가요", ["func", "define", "def", "function"], 3),
    Quiz("다음 중 파이썬의 기본 데이터 타입이 아닌 것은 무엇인가요", ["int", "str", "bool", "char"], 4),
    Quiz("화면에 값을 출력하기 위해 사용하는 함수는 무엇인가요", ["input", "print", "write", "show"], 2),
    Quiz("리스트의 맨 끝에 새로운 요소를 추가하는 메서드는 무엇인가요", ["add", "push", "append", "insert"], 3),
    Quiz("조건에 따라 코드를 실행할지 결정하는 키워드는 무엇인가요", ["if", "for", "while", "def"], 1)
]


### 2. `quizGame.py` (데이터 관리 모델)
# `state.json` 파일을 관리하며, 퀴즈 목록과 **최고 점수**, **보너스용 히스토리**를 저장하고 불러옵니다.


import json
import os
from quiz import Quiz, DEFAULT_QUIZZES

class QuizModel:
    DATA_FILE = "state.json"

    def __init__(self):
        self.quizzes = []
        self.best_score = 0
        self.history = [] # 보너스: 게임 기록 히스토리
        self._load_data()

    def _load_data(self):
        """파일이 없거나 손상된 경우 기본 데이터로 복구"""
        if not os.path.exists(self.DATA_FILE):
            self._reset_to_default()
            self._save_data()
            return

        try:
            with open(self.DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                if "quizzes" not in raw or "best_score" not in raw:
                    raise ValueError("필수 키 누락")
                self.quizzes = [Quiz.from_dict(q) for q in raw["quizzes"]]
                self.best_score = int(raw["best_score"])
                self.history = raw.get("history", []) # 히스토리 로드
        except (json.JSONDecodeError, ValueError, KeyError, TypeError):
            self._reset_to_default()
            self._save_data()

    def _save_data(self):
        """현재 상태를 state.json에 저장"""
        try:
            data = {
                "quizzes": [q.to_dict() for q in self.quizzes],
                "best_score": self.best_score,
                "history": self.history # 히스토리 저장
            }
            with open(self.DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError:
            pass

    def _reset_to_default(self):
        """기본 데이터 초기화"""
        self.quizzes = [Quiz(q.question, q.choices[:], q.answer) for q in DEFAULT_QUIZZES]
        self.best_score = 0
        self.history = []

    def add_quiz(self, new_quiz):
        self.quizzes.append(new_quiz)
        self._save_data()

    def delete_quiz(self, index):
        """보너스: 퀴즈 삭제"""
        if 0 <= index < len(self.quizzes):
            del self.quizzes[index]
            self._save_data()
            return True
        return False

    def update_best_score(self, score):
        if score > self.best_score:
            self.best_score = score
            self._save_data()
            return True
        return False

    def add_history(self, record):
        """보너스: 게임 기록 추가"""
        self.history.append(record)
        self._save_data()
```

### 3. `quizView.py` (화면 출력 및 입력 뷰)
# 사용자 인터페이스와 미션 필수 예외 처리(공백 제거, 숫자 검증 등)를 담당합니다.
class QuizView:
    def display_menu(self):
        print("\n" + "="*30)
        print("   파이썬 퀴즈 챌린지")
        print("="*30)
        print("1. 퀴즈 풀기 (랜덤/수량)")
        print("2. 새로운 퀴즈 추가")
        print("3. 퀴즈 목록 보기")
        print("4. 최고 점수 확인")
        print("5. 퀴즈 삭제하기 (보너스)")
        print("6. 전체 기록 보기 (보너스)")
        print("7. 게임 종료")
        print("="*30)

    def show_message(self, msg):
        print(msg)

    def get_valid_number(self, prompt, min_val, max_val):
        """미션 요구 예외 처리 (공백 제거, 범위 체크 등)"""
        while True:
            try:
                user_input = input(prompt).strip()
                if not user_input:
                    print("⚠ 입력이 비어있습니다.")
                    continue
                num = int(user_input)
                if min_val <= num <= max_val:
                    return num
                print(f"⚠ {min_val}~{max_val} 사이를 입력하세요.")
            except ValueError:
                print("⚠ 숫자를 입력해주세요.")

    def get_new_quiz_input(self):
        print("\n[새 퀴즈 추가]")
        q = input("문제: ").strip()
        c = [input(f"보기{i}: ").strip() for i in range(1, 5)]
        a = self.get_valid_number("정답(1-4): ", 1, 4)
        return q, c, a

    def show_quiz_list(self, quizzes):
        if not quizzes:
            print("⚠ 등록된 퀴즈가 없습니다.")
            return
        for i, q in enumerate(quizzes, 1):
            print(f"{i}. {q.question}")

    def show_history(self, history):
        if not history:
            print("⚠ 기록이 없습니다.")
            return
        print("\n[게임 기록 히스토리]")
        for h in history:
            print(f"- {h['date']} | 점수: {h['score']}점 ({h['correct']}/{h['total']})")

### 4. `main.py` (전체 흐름 제어 컨트롤러)
# `QuizController`를 통해 전체 게임 루프를 실행하며 보너스 로직(랜덤 섞기 등)을 제어합니다.

import random
from datetime import datetime
from quizGame import QuizModel
from quiz import Quiz
from quizView import QuizView

class QuizController:
    def __init__(self):
        self.model = QuizModel()
        self.view = QuizView()

    def play_quiz(self):
        quizzes = self.model.quizzes[:] # 복사본 사용
        if not quizzes:
            self.view.show_message("⚠ 퀴즈가 없습니다.")
            return

        # 보너스: 수량 선택 및 랜덤 섞기
        count = self.view.get_valid_number(f"몇 문제를 푸시겠습니까? (1~{len(quizzes)}): ", 1, len(quizzes))
        random.shuffle(quizzes)
        quizzes = quizzes[:count]

        correct = 0
        for i, q in enumerate(quizzes, 1):
            self.view.show_message(f"\n[Q{i}] {q.question}")
            for idx, choice in enumerate(q.choices, 1):
                print(f"  {idx}. {choice}")
            
            ans = self.view.get_valid_number("정답: ", 1, 4)
            if q.is_correct(ans):
                self.view.show_message("✅ 정답!")
                correct += 1
            else:
                self.view.show_message(f"❌ 오답! 정답은 {q.answer}")

        score = int(correct / count * 100)
        self.view.show_message(f"\n🏁 종료! 점수: {score}점")
        
        # 기록 저장 및 최고점 경신
        self.model.add_history({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "score": score, "correct": correct, "total": count
        })
        if self.model.update_best_score(score):
            self.view.show_message("🎉 최고 점수 경신!")

    def run(self):
        try:
            while True:
                self.view.display_menu()
                choice = self.view.get_valid_number("선택: ", 1, 7)
                if choice == 1: self.play_quiz()
                elif choice == 2:
                    q_data = self.view.get_new_quiz_input()
                    self.model.add_quiz(Quiz(*q_data))
                elif choice == 3: self.view.show_quiz_list(self.model.quizzes)
                elif choice == 4: self.view.show_message(f"🔥 최고 점수: {self.model.best_score}점")
                elif choice == 5:
                    self.view.show_quiz_list(self.model.quizzes)
                    idx = self.view.get_valid_number("삭제할 번호: ", 1, len(self.model.quizzes))
                    self.model.delete_quiz(idx-1)
                elif choice == 6: self.view.show_history(self.model.history)
                elif choice == 7: break
        except (KeyboardInterrupt, EOFError):
            self.view.show_message("\n\n👋 안전하게 종료합니다.")

if __name__ == "__main__":
    QuizController().run()

    def run(self):
        try:
            while True:
                self.view.display_menu()
                choice = self.view.get_valid_number("선택: ", 1, 7)
                if choice == 1: self.play_quiz()
                elif choice == 2:
                    q_data = self.view.get_new_quiz_input()
                    self.model.add_quiz(Quiz(*q_data))
                elif choice == 3: self.view.show_quiz_list(self.model.quizzes)
                elif choice == 4: self.view.show_message(f"🔥 최고 점수: {self.model.best_score}점")
                elif choice == 5:
                    self.view.show_quiz_list(self.model.quizzes)
                    idx = self.view.get_valid_number("삭제할 번호: ", 1, len(self.model.quizzes))
                    self.model.delete_quiz(idx-1)
                elif choice == 6: self.view.show_history(self.model.history)
                elif choice == 7: break
        except (KeyboardInterrupt, EOFError):
            self.view.show_message("\n\n👋 안전하게 종료합니다.")

if __name__ == "__main__":
    QuizController().run()