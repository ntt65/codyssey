import model, view
import time
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
                    filter_a, filter_b, pattern = self.view.show_user_input(3)
                    start_time = time.time()  # 시작 시간 기록  
                    mac_result_a = self.model.mac_simulation(filter_a, pattern,10)
                    mac_result_b = self.model.mac_simulation(filter_b, pattern,10)
                    end_time = time.time()  # 종료 시간 기록
                    execution_time = (end_time - start_time) * 1000  # 밀리초로 변환
                    self.view.show_mac_result(mac_result_a, mac_result_b, execution_time)

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
