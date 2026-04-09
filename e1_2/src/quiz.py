
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