import json

class Quiz:
    def __init__(self, question, choices, answer):
        self.question = question
        self.choices = choices
        self.answer = answer

class QuizGame:
    def __init__(self):
        self.data_file = "state.json"
        self.quizzes = []
        self.best_score = 0
        self.load_data()

    def load_data(self):
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                self.best_score = data.get("best_score", 0)
                self.quizzes = [Quiz(**q) for q in data.get("quizzes", [])]
        except (FileNotFoundError, json.JSONDecodeError): # 파일이 없거나 손상된 경우 [1, 2]
            self.quizzes = [
                Quiz("Python의 창시자는?", ["Guido", "Linus", "Bjarne", "James"], 1),
                Quiz("출력 함수는?", ["input", "print", "write", "show"], 2),
                Quiz("함수 정의 키워드는?", ["func", "def", "define", "function"], 2),
                Quiz("리스트 요소 추가 메서드는?", ["add", "push", "append", "insert"], 3),
                Quiz("조건문 키워드는?", ["if", "for", "while", "def"], 1)
            ]

    def save_data(self):
        data = {"best_score": self.best_score, "quizzes": [q.__dict__ for q in self.quizzes]}
        with open(self.data_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

    def get_input(self, prompt, min_val, max_val):
        while True:
            try:
                val = int(input(prompt).strip())
                if min_val <= val <= max_val: return val
                print(f"{min_val}~{max_val} 사이 숫자를 입력하세요.")
            except ValueError: print("숫자만 입력 가능합니다.")

    def play(self):
        score = 0
        for q in self.quizzes:
            print(f"\n[문제] {q.question}")
            for i, choice in enumerate(q.choices, 1): print(f"{i}. {choice}")
            if self.get_input("정답: ", 1, 4) == q.answer:
                print("✅ 정답!"); score += 1
            else: print("❌ 오답!")
        if score > self.best_score: self.best_score = score
        self.save_data()
        print(f"\n최종 점수: {score}/{len(self.quizzes)}")

    def run(self):
        while True:
            try:
                print(f"\n--- 퀴즈 게임 (최고점: {self.best_score}) ---")
                print("1.풀기 2.추가 3.목록 4.종료")
                menu = self.get_input("선택: ", 1, 4)
                if menu == 1: self.play()
                elif menu == 2:
                    q = input("문제: ")
                    c = [input(f"선택지 {i}: ") for i in range(1, 5)]
                    a = self.get_input("정답(1-4): ", 1, 4)
                    self.quizzes.append(Quiz(q, c, a))
                    self.save_data()
                elif menu == 3:
                    for i, q in enumerate(self.quizzes, 1): print(f"[{i}] {q.question}")
                elif menu == 4: break
            except (KeyboardInterrupt, EOFError): break # 비정상 종료 방지 [1, 3]
        print("\n안전하게 종료합니다.")

if __name__ == "__main__":
    QuizGame().run()