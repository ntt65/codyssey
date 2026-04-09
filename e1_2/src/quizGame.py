"""
quizGame.py - 데이터 관리 및 퀴즈 모델

개요:
    state.json 파일을 관리하는 QuizModel 클래스입니다.
    퀴즈 목록, 최고 점수, 게임 기록 히스토리를 관리합니다.
    
주요 기능:
    - 데이터 로드/저장 (JSON, UTF-8 인코딩)
    - 파일 손상 시 기본 데이터로 복구
    - 퀴즈 추가/삭제
    - 최고 점수 업데이트
    - 게임 기록 관리 (보너스 기능)
"""

import json
import os
from quiz import Quiz, DEFAULT_QUIZZES

class QuizModel:
    """퀴즈 데이터와 게임 상태를 관리하는 모델 클래스
    
    속성:
        quizzes (list): Quiz 객체 리스트
        best_score (int): 최고 점수
        history (list): 게임 기록 (보너스 기능)
        DATA_FILE (str): state.json 파일 경로
    """
    
    DATA_FILE = "state.json"  # 프로젝트 루트의 상태 저장 파일

    def __init__(self):
        """QuizModel 초기화 및 데이터 로드"""
        self.quizzes = []
        self.best_score = 0
        self.history = []  # 보너스: 게임 기록 히스토리
        self._load_data()

