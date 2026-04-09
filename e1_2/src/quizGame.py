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

    def _load_data(self):
        """state.json에서 데이터 로드
        
        처리:
        - 파일 없음: 기본 데이터로 초기화 및 저장
        - 파일 손상: 필수 키 검증 후 손상 시 복구
        - 예외 처리: JSON, 키, 타입 에러 등 모두 처리
        """
        # 파일이 없으면 기본 데이터로 초기화
        if not os.path.exists(self.DATA_FILE):
            self._reset_to_default()
            self._save_data()
            return

        try:
            # state.json 파일 읽기 (UTF-8 인코딩)
            with open(self.DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                # 필수 키 검증
                if "quizzes" not in raw or "best_score" not in raw:
                    raise ValueError("필수 키 누락")
                # 데이터 로드
                self.quizzes = [Quiz.from_dict(q) for q in raw["quizzes"]]
                self.best_score = int(raw["best_score"])
                # 히스토리 로드 (없으면 빈 리스트)
                self.history = raw.get("history", [])
        # 데이터 손상 시 기본값으로 복구
        except (json.JSONDecodeError, ValueError, KeyError, TypeError):
            self._reset_to_default()
            self._save_data()
    
    def _load_data(self):
        """state.json에서 데이터 로드
        
        처리:
        - 파일 없음: 기본 데이터로 초기화 및 저장
        - 파일 손상: 필수 키 검증 후 손상 시 복구
        - 예외 처리: JSON, 키, 타입 에러 등 모두 처리
        """
        # 파일이 없으면 기본 데이터로 초기화
        if not os.path.exists(self.DATA_FILE):
            self._reset_to_default()
            self._save_data()
            return

        try:
            # state.json 파일 읽기 (UTF-8 인코딩)
            with open(self.DATA_FILE, "r", encoding="utf-8") as f:
                raw = json.load(f)
                # 필수 키 검증
                if "quizzes" not in raw or "best_score" not in raw:
                    raise ValueError("필수 키 누락")
                # 데이터 로드
                self.quizzes = [Quiz.from_dict(q) for q in raw["quizzes"]]
                self.best_score = int(raw["best_score"])
                # 히스토리 로드 (없으면 빈 리스트)
                self.history = raw.get("history", [])
        # 데이터 손상 시 기본값으로 복구
        except (json.JSONDecodeError, ValueError, KeyError, TypeError):
            self._reset_to_default()
            self._save_data()

    def _save_data(self):
        """현재 상태를 state.json에 저장
        
        저장 형식:
        {
            "quizzes": [...],
            "best_score": int,
            "history": [...]
        }
        
        인코딩: UTF-8, ensure_ascii=False (한글 저장 가능)
        """
        try:
            # 저장할 데이터 구성
            data = {
                "quizzes": [q.to_dict() for q in self.quizzes],
                "best_score": self.best_score,
                "history": self.history  # 히스토리 저장
            }
            # JSON 파일 작성
            with open(self.DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except IOError:
            # 저장 실패 시 먹음 처리 (프로그램 중단 없음)
            pass