"""
main.py - 파이썬 퀴즈 게임 메인 컨트롤러

개요:
    사용자 입력을 받아 퀴즈 게임의 전체 흐름을 관리합니다.
    MVC 패턴에서 Controller 역할을 하며, Model(QuizModel)과 View(QuizView)를 연결합니다.
    
주요 기능:
    - 게임 메뉴 제어
    - 퀴즈 풀기 (랜덤 지원)
    - 퀴즈 추가/삭제
    - 최고 점수 관리
    - 게임 기록 히스토리 (보너스)
    - 키보드 인터럽트(Ctrl+C) 안전 처리
"""

import random
from datetime import datetime
from quizGame import QuizModel
from quiz import Quiz
from quizView import QuizView

class QuizController:
    """퀴즈 게임의 전체 플로우를 관리하는 컨트롤러 클래스
    
    QuizModel(데이터 관리)과 QuizView(UI)를 연결하여 게임 로직을 실행합니다.
    """
    def __init__(self):
        """QuizController 초기화. Model과 View 인스턴스 생성"""
        self.model = QuizModel()
        self.view = QuizView()