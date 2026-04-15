import model, view
class Controller:
    def __init__(self):
        # 컨트롤러 초기화
        self.model = model.Model()
        self.view = view.View()

    def run(self):
        # 프로그램 실행 로직
        try:
            while True:
                # 메뉴 표시 및 사용자 선택 입력
                self.view.show_main_menu()
                choice = self.view.get_valid_number("선택: ", 1, 3)
                if choice == 1:
                    # 사용자 입력 모드
                    filter_a, filter_b, pattern = self.view.show_user_input()

                elif choice == 2:
                    # data.json 분석 모드
                    self.view.show_data_analysis()
                    
                elif choice == 3:
                    # 종료
                    print("프로그램을 종료합니다.")
                    break
        except (KeyboardInterrupt, EOFError):
            print("\n\n👋 프로그램이 종료되었습니다.")

if __name__ == "__main__":
    # 프로그램 진입점
    Controller().run()
