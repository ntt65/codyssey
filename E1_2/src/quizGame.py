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