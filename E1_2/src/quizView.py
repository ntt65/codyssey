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