#  `best_score`가 포함된 새로운 `default_data` 구조를 반영하여, 미션 요구사항인 **데이터 영속성, 예외 처리, 그리고 클래스 구조**를 모두 갖춘 통합 코드를 다시 구성해 드립니다.
# 이 코드는 `state.json`이라는 하나의 파일에 퀴즈 목록과 최고 점수를 함께 저장하며, 파일이 없거나 손상되었을 때 **도커 관련 기본 문제와 최고 점수 0점**으로 자동 복구하는 로직을 포함합니다.

### 🛠 주요 변경 및 반영 사항
# *   **통합 데이터 구조:** `default_state` 딕셔너리 안에 `quizzes` 리스트와 `best_score`를 함께 넣어 미션이 요구하는 **단일 파일 관리 체계**를 완성했습니다.
# *   **정수형 정답 관리:** 모든 정답은 `'1'`과 같은 문자열이 아닌 `1`과 같은 **정수(int)**로 처리하여 데이터 일관성을 높였습니다.
# *   **MVC 흐름 유지:** 퀴즈 객체(`Quiz`)가 스스로 정답을 체크하고(`is_correct`), 게임 클래스(`QuizGame`)가 전체 흐름과 파일 저장을 관리하도록 역할을 분리했습니다.
# *   **강력한 예외 처리:** `Ctrl+C` 비정상 종료와 `state.json` 파일 손상 시 기본값으로 복구하는 기능을 모두 포함했습니다.
import json
import os

# 1. 개별 퀴즈를 담당하는 클래스 (Quiz)
class Quiz:
    def __init__(self, question, choices, answer):
        self.question = question
        self.choices = choices
        self.answer = answer  # 정답 번호 (int)

    def is_correct(self, user_answer):
        """정답 여부 확인 (숫자 변환 및 비교)"""
        try:
            return int(user_answer) == self.answer
        except (ValueError, TypeError):
            return False

    def to_dict(self):
        """JSON 저장을 위한 딕셔너리 변환"""
        return {
            "question": self.question,
            "choices": self.choices,
            "answer": self.answer
        }

# 2. 게임 전체 흐름과 데이터(JSON)를 관리하는 클래스 (QuizGame)
class QuizGame:
    DATA_FILE = "state.json" # 미션 요구 파일명

    def __init__(self):
        self.quizzes = []
        self.best_score = 0
        self.load_data() # 시작 시 데이터 로드

    def load_data(self):
        """파일 로드 및 복구 로직"""
        if not os.path.exists(self.DATA_FILE):
            self.reset_to_default()
            return

        try:
            with open(self.DATA_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                # 필수 키(quizzes, best_score) 존재 여부 확인
                if "quizzes" not in data or "best_score" not in data:
                    raise ValueError("데이터 구조 손상")
                
                self.quizzes = [Quiz(q["question"], q["choices"], q["answer"]) for q in data["quizzes"]]
                self.best_score = int(data["best_score"])
        except (json.JSONDecodeError, ValueError, KeyError, TypeError):
            print("⚠ 데이터 파일이 손상되어 기본 데이터로 초기화합니다.")
            self.reset_to_default()

    def reset_to_default(self):
        """best_score가 포함된 새로운 default_data 구조로 초기화"""
        default_state = {
            "quizzes": [
                {"question": "컨테이너 내부(eth0)와 호스트 브리지를 연결하는 '가상 랜선'은?", "choices": ["veth pair", "Network Namespace", "iptables", "vmenet"], "answer": 1},
                {"question": "실행 중인 컨테이너에 새로운 프로세스를 띄워 접속하는 명령어는?", "choices": ["docker run", "docker attach", "docker exec", "docker start"], "answer": 3},
                {"question": "docker attach 사용 중 종료 없이 빠져나오는 키 조합은?", "choices": ["Ctrl + C", "Ctrl + Z", "exit", "Ctrl + P, Q"], "answer": 4},
                {"question": "macOS 도커 환경에서 호스트에 인터페이스가 직접 보이지 않는 이유는?", "choices": ["가상 NIC 누락", "VM 내부에서 실행되어서", "보안 설정", "포트 매핑 누락"], "answer": 2},
                {"question": "컨테이너 실행 시 호스트 포트를 중복 설정하면 발생하는 현상은?", "choices": ["자동 변경", "에러 발생 및 실행 실패", "덮어씌워짐", "성능 저하"], "answer": 2}
            ],
            "best_score": 0 # 최고 점수 초기값 포함
        }
        self.quizzes = [Quiz(q["question"], q["choices"], q["answer"]) for q in default_state["quizzes"]]
        self.best_score = default_state["best_score"]
        self.save_data()

    def save_data(self):
        """현재 상태(퀴즈+점수)를 JSON에 저장"""
        state = {
            "quizzes": [q.to_dict() for q in self.quizzes],
            "best_score": self.best_score
        }
        with open(self.DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(state, f, ensure_ascii=False, indent=4)

    def run(self):
        """게임 실행 메인 루프"""
        try:
            while True:
                print(f"\n--- 도커 퀴즈 챌린지 (최고점: {self.best_score}점) ---")
                print("1. 퀴즈 풀기  2. 최고 점수 확인  3. 종료")
                choice = input("선택: ").strip()

                if choice == '1':
                    self.play()
                elif choice == '2':
                    print(f"\n🔥 현재 기록된 최고 점수는 {self.best_score}점입니다.")
                elif choice == '3':
                    print("👋 프로그램을 종료합니다.")
                    break
                else:
                    print("⚠ 1, 2, 3번 중에서 선택해주세요.")
        except (KeyboardInterrupt, EOFError): # 비정상 종료 대응
            print("\n\n👋 프로그램을 안전하게 종료합니다.")

    def play(self):
        """퀴즈 풀기 및 점수 갱신"""
        if not self.quizzes:
            print("⚠ 풀 수 있는 퀴즈가 없습니다.")
            return

        correct_count = 0
        for idx, q in enumerate(self.quizzes, 1):
            print(f"\n[Q{idx}] {q.question}")
            for i, c in enumerate(q.choices, 1):
                print(f"  {i}) {c}")
            
            ans = input("정답 번호: ").strip()
            if q.is_correct(ans):
                print("✅ 정답입니다!")
                correct_count += 1
            else:
                print(f"❌ 틀렸습니다. 정답은 {q.answer}번입니다.")

        # 최종 점수 계산 및 최고 점수 비교
        final_score = int((correct_count / len(self.quizzes)) * 100)
        print(f"\n🏁 종료! 점수: {final_score}점")
        
        if final_score > self.best_score:
            print("🎉 최고 점수 경신!")
            self.best_score = final_score
            self.save_data()

# 3. 메인 실행부
if __name__ == "__main__":
    game = QuizGame()
    game.run()