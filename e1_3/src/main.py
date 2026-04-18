import model, view

class Controller:
    def __init__(self):
        self.model = model.Model()
        self.view = view.View()

    def run(self):
        try:
            while True:
                self.view.show_main_menu()
                choice = self.view.get_valid_number("선택: ", 1, 3)
                if choice == 1: self.mode_user_input()
                elif choice == 2: self.mode_json_analysis()
                else: break
        except (KeyboardInterrupt, EOFError):
            print("\n👋 프로그램을 종료합니다.")

    def mode_user_input(self):
        f_a, f_b, pattern = self.view.show_user_input(3)
        res_a = self.model.mac_simulation(f_a, pattern)
        res_b = self.model.mac_simulation(f_b, pattern)
        avg_time = self.model.get_average_mac_time(f_a, pattern)
        decision = self.model.judge(res_a, res_b)
        self.view.show_mac_result(res_a, res_b, avg_time, decision)

    def mode_json_analysis(self):
        try:
            data = self.model.load_json_data('data.json')
        except FileNotFoundError:
            print("⚠ data.json 파일이 없습니다.")
            return

        filters = data.get('filters', {})
        patterns = data.get('patterns', {})
        
        results = []
        perf_summary = {} # 크기별 성능 데이터 저장

        self.view.show_analysis_header()
        
        for p_key, p_val in patterns.items():
            # 키에서 사이즈 추출 (size_5_1 -> 5)
            size_str = p_key.split('_')[1]
            f_key = f"size_{size_str}"
            
            target_filters = filters.get(f_key, {})
            # 필터 라벨 정규화 로드
            f_cross = target_filters.get('cross')
            f_x = target_filters.get('x')
            
            input_pattern = p_val.get('input')
            expected = self.model.normalize_label(p_val.get('expected'))
            
            # 검증: 크기 불일치 등
            if not f_cross or len(f_cross) != int(size_str):
                results.append({'id': p_key, 'pass': False, 'reason': '필터 스키마 오류'})
                continue

            score_cross = self.model.mac_simulation(f_cross, input_pattern)
            score_x = self.model.mac_simulation(f_x, input_pattern)
            decision = self.model.judge(score_cross, score_x)
            
            is_pass = (decision == expected)
            self.view.show_case_result(p_key, score_cross, score_x, decision, expected, is_pass)
            
            results.append({'id': p_key, 'pass': is_pass, 'reason': f'판정 {decision} != 기대 {expected}' if not is_pass else ''})

            # 성능 기록용 (크기별로 한 번씩만 측정)
            if size_str not in perf_summary:
                avg_t = self.model.get_average_mac_time(f_cross, input_pattern)
                perf_summary[size_str] = {'avg_time': avg_t, 'ops': int(size_str)**2}

        # 요약 출력
        passed = sum(1 for r in results if r['pass'])
        fails = [r for r in results if not r['pass']]
        
        perf_list = [{'size': f"{k}x{k}", 'avg_time': v['avg_time'], 'ops': v['ops']} for k, v in sorted(perf_summary.items(), key=lambda x: int(x[0]))]
        self.view.show_performance_table(perf_list)
        self.view.show_summary(len(results), passed, len(fails), fails)

if __name__ == "__main__":
    Controller().run()