


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
        quizzes = self.model.quizzes[:]  # 복사본 사용
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