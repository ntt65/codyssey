class View:
    def __init__(self):
        print("=== Mini NPU Simulator ===")

    def show_main_menu(self): 
        print("\n[모드 선택]") 
        print("1. 사용자 입력 (3x3)") 
        print("2. data.json 분석") 
        print("3. 종료")

    def show_user_input(self, size):
        def get_fixed_matrix(name, size):
            print(f"{name}를 입력하세요 ({size}줄 입력, 공백 구분):")
            matrix = []
            i = 0
            while i < size:
                try:
                    line = input(f'line {i+1} : ').strip()
                    if not line: continue
                    row = [float(x) for x in line.split()] # 정수/실수 모두 대응
                    
                    if len(row) > size:
                        row = row[:size]
                    elif len(row) < size:
                        row += [0] * (size - len(row)) # [수정 완료]
                    
                    matrix.append(row)
                    i += 1
                except ValueError:
                    print(f"⚠ 입력 형식 오류: 숫자가 아닌 값이 있습니다. 다시 입력하세요.")
            return matrix

        print("\n" + "-"*40)
        filter_a = get_fixed_matrix("필터 A", size)
        filter_b = get_fixed_matrix("필터 B", size)
        print("-"*40)
        pattern = get_fixed_matrix("패턴", size)
        return filter_a, filter_b, pattern

    def show_mac_result(self, res_a, res_b, exec_time, decision):
        print("\n" + "-"*40)
        print("# [3] MAC 결과")
        print("-"*40)
        print(f"필터 A 점수: {res_a:.10f}")
        print(f"필터 B 점수: {res_b:.10f}")
        print(f"연산 시간(평균 10회): {exec_time:.4f} ms")
        print(f"판정: {decision}")

    def show_analysis_header(self):
        print("\n# [2] 패턴 분석 (라벨 정규화 적용)")

    def show_case_result(self, case_id, score_cross, score_x, decision, expected, is_pass):
        status = "PASS" if is_pass else "FAIL"
        print(f"--- {case_id} ---")
        print(f"Cross 점수: {score_cross:.10f}")
        print(f"X 점수: {score_x:.10f}")
        print(f"판정: {decision} | expected: {expected} | {status}")

    def show_performance_table(self, perf_data):
        print("\n# [3] 성능 분석 (평균/10회)")
        print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수(N²)'}")
        print("-" * 40)
        for item in perf_data:
            print(f"{item['size']:<10} {item['avg_time']:<15.4f} {item['ops']}")

    def show_summary(self, total, passed, failed, fail_list):
        print("\n# [4] 결과 요약")
        print(f"총 테스트: {total}개 | 통과: {passed}개 | 실패: {failed}개")
        if fail_list:
            print("\n실패 케이스:")
            for case in fail_list:
                print(f"- {case['id']}: {case['reason']}")

    def get_valid_number(self, prompt, min_val, max_val):
        while True:
            try:
                user_input = input(prompt).strip()
                if not user_input: continue
                num = int(user_input)
                if min_val <= num <= max_val: return num
                print(f"⚠ {min_val}~{max_val} 사이를 입력하세요.")
            except ValueError:
                print("⚠ 숫자를 입력해주세요.")