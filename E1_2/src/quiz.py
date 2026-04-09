
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
