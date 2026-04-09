
"""
quiz.py - 개별 퀴즈 데이터 모델

개요:
    각 퀴즈를 나타내는 Quiz 클래스를 정의합니다.
    기본 데이터 5개를 DEFAULT_QUIZZES로 제공합니다.
"""

class Quiz:
    """개별 퀴즈를 나타내는 클래스
    
    속성:
        question (str): 퀴즈 문제
        choices (list): 4개의 선택지
        answer (int): 정답 번호 (1~4)
    """
    
    def __init__(self, question, choices, answer):
        """퀴즈 초기화"""
        self.question = question  # 문제 (str)
        self.choices = choices    # 선택지 4개 (list)
        self.answer = answer      # 정답 번호 (int, 1~4)
    
    def is_correct(self, user_answer):
        """사용자의 정답과 정확한 정답을 비교
        
        Args:
            user_answer (int): 사용자가 입력한 정답 번호
            
        Returns:
            bool: 정답 여부
        """
        return user_answer == self.answer
    
    def to_dict(self):
        """Quiz 객체를 JSON 저장 가능한 딕셔너리로 변환
        
        Returns:
            dict: {\"question\": str, \"choices\": list, \"answer\": int}
        """
        return {
            "question": self.question,
            "choices": self.choices,
            "answer": self.answer,
        }
    
    @staticmethod
    def from_dict(data):
        """JSON 데이터에서 Quiz 객체 생성
        
        Args:
            data (dict): {\"question\": str, \"choices\": list, \"answer\": int} 형식
            
        Returns:
            Quiz: 생성된 Quiz 객체
        """
        return Quiz(data["question"], data["choices"], data["answer"])

# 파이썬 문법 기본 퀴즈 데이터 (미션 요구: 5개 이상)
DEFAULT_QUIZZES = [
    Quiz("파이썬에서 함수를 정의할 때 사용하는 키워드는 무엇인가요", ["func", "define", "def", "function"], 3),
    Quiz("다음 중 파이썬의 기본 데이터 타입이 아닌 것은 무엇인가요", ["int", "str", "bool", "char"], 4),
    Quiz("화면에 값을 출력하기 위해 사용하는 함수는 무엇인가요", ["input", "print", "write", "show"], 2),
    Quiz("리스트의 맨 끝에 새로운 요소를 추가하는 메서드는 무엇인가요", ["add", "push", "append", "insert"], 3),
    Quiz("조건에 따라 코드를 실행할지 결정하는 키워드는 무엇인가요", ["if", "for", "while", "def"], 1)
]