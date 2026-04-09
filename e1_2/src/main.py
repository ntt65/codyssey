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

    def play_quiz(self):
        """퀴즈 풀기 기능 실행
        
        1. 풀 문제 수 선택 (보너스: 랜덤)
        2. 선택된 문제 수만큼 퀴즈 출제
        3. 정답 확인 및 점수 계산
        4. 최고 점수 업데이트
        5. 기록 저장
        """
        quizzes = self.model.quizzes[:]  # 복사본 사용 - 원본 리스트 보호
        if not quizzes:
            self.view.show_message("⚠ 퀴즈가 없습니다.")
            return

        # 사용자가 풀 문제 수 선택 (보너스 기능)
        count = self.view.get_valid_number(f"몇 문제를 푸시겠습니까? (1~{len(quizzes)}): ", 1, len(quizzes))
        
        # 퀴즈 순서 랜덤 섞기 (보너스 기능)
        random.shuffle(quizzes)
        quizzes = quizzes[:count]

        correct = 0
        # 각 퀴즈 출제 및 채점
        for i, q in enumerate(quizzes, 1):
            self.view.show_message(f"\n[Q{i}] {q.question}")
            # 4개 선택지 출력
            for idx, choice in enumerate(q.choices, 1):
                print(f"  {idx}. {choice}")

            # 사용자 입력 받기 (1~4 범위 검증)
            ans = self.view.get_valid_number("정답: ", 1, 4)
            # 정답 확인 및 점수 누적
            if q.is_correct(ans):
                self.view.show_message("✅ 정답!")
                correct += 1
            else:
                self.view.show_message(f"❌ 오답! 정답은 {q.answer}")

        # 최종 점수 계산 (정답률 %)
        score = int(correct / count * 100)
        self.view.show_message(f"\n🏁 종료! 점수: {score}점")

        # 게임 기록 저장 (보너스 기능)
        self.model.add_history({
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "score": score, "correct": correct, "total": count
        })
        # 최고 점수 업데이트 및 사용자 피드백
        if self.model.update_best_score(score):
            self.view.show_message("🎉 최고 점수 경신!")