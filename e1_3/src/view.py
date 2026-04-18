"""
================================================================================
모듈명: View (Mini NPU Simulator)
개요: 사용자 인터페이스(UI)를 담당하는 모듈입니다.
      콘솔 출력 양식을 정의하고, 사용자의 입력을 유효성 검사하여 
      정제된 데이터를 Controller로 전달합니다.
작성일: 2026-04-18
================================================================================
"""

class View:
    """
    콘솔 화면 출력 및 사용자 입력을 관리하는 뷰 클래스
    """
    
    def __init__(self):
        """View 인스턴스 생성 시 초기 환영 메시지를 출력합니다."""
        print("=== Mini NPU Simulator ===")

    def show_main_menu(self): 
        """사용자가 선택할 수 있는 프로그램 메인 메뉴를 출력합니다."""
        print("\n[모드 선택]") 
        print("1. 사용자 입력 (3x3)") 
        print("2. data.json 분석") 
        print("3. 종료")

    def show_user_input(self, size):
        """
        사용자로부터 지정된 크기(N x N)의 행렬 데이터를 입력받습니다.
        
        Args:
            size (int): 행렬의 가로/세로 크기 (예: 3)
        Returns:
            tuple: (filter_a, filter_b, pattern) 형태의 2차원 리스트 묶음
        """
        def get_fixed_matrix(name, size):
            """내부 함수: 개별 행렬(필터 또는 패턴)을 입력받고 검증합니다."""
            print(f"{name}를 입력하세요 ({size}줄 입력, 공백 구분):")
            matrix = []
            i = 0
            while i < size:
                try:
                    line = input(f'line {i+1} : ').strip()
                    if not line: continue # 빈 줄 입력 시 스킵
                    
                    # 공백 기준 분리 후 숫자로 변환
                    row = [float(x) for x in line.split()] 
                    
                    # 입력 데이터 길이 조정 (요구사항: 부족하면 0으로 채움)
                    if len(row) > size:
                        row = row[:size] # 초과 입력 시 잘라냄
                    elif len(row) < size:
                        row += [0] * (size - len(row)) # 부족할 경우 0으로 패딩
                    
                    matrix.append(row)
                    i += 1 # 정상 입력 시 다음 행으로 이동
                except ValueError:
                    # 숫자가 아닌 값이 포함된 경우 에러 메시지 출력 후 재입력
                    print(f"⚠ 입력 형식 오류: 숫자가 아닌 값이 있습니다. 다시 입력하세요.")
            return matrix

        # 필터 A, 필터 B, 입력 패턴을 순차적으로 입력받음
        print("\n" + "-"*40)
        filter_a = get_fixed_matrix("필터 A", size)
        filter_b = get_fixed_matrix("필터 B", size)
        print("-"*40)
        pattern = get_fixed_matrix("패턴", size)
        return filter_a, filter_b, pattern

    def show_mac_result(self, res_a, res_b, exec_time, decision):
        """
        수동 입력 모드의 MAC 연산 결과를 화면에 출력합니다.
        
        Args:
            res_a, res_b (float): 각 필터별 연산 점수
            exec_time (float): 평균 연산 시간 (ms)
            decision (str): 최종 판정 결과
        """
        print("\n" + "-"*40)
        print("# [3] MAC 결과")
        print("-"*40)
        print(f"필터 A 점수: {res_a:.10f}") # 소수점 10자리까지 출력
        print(f"필터 B 점수: {res_b:.10f}")
        print(f"연산 시간(평균 10회): {exec_time:.4f} ms")
        print(f"판정: {decision}")

    def show_analysis_header(self):
        """JSON 분석 모드 시작 시 헤더 문구를 출력합니다."""
        print("\n# [2] 패턴 분석 (라벨 정규화 적용)")

    def show_case_result(self, case_id, score_cross, score_x, decision, expected, is_pass):
        """
        JSON 내 개별 테스트 케이스의 분석 결과를 출력합니다.
        """
        status = "PASS" if is_pass else "FAIL"
        print(f"--- {case_id} ---")
        print(f"Cross 점수: {score_cross:.10f}")
        print(f"X 점수: {score_x:.10f}")
        print(f"판정: {decision} | expected: {expected} | {status}")

    def show_performance_table(self, perf_data):
        """
        크기별 연산 성능(평균 시간 및 연산 횟수)을 표 형식으로 출력합니다.
        
        Args:
            perf_data (list): {'size', 'avg_time', 'ops'} 구조의 딕셔너리 리스트
        """
        print("\n# [3] 성능 분석 (평균/10회)")
        print(f"{'크기':<10} {'평균 시간(ms)':<15} {'연산 횟수(N²)'}")
        print("-" * 40)
        for item in perf_data:
            # 정렬된 간격으로 데이터 출력
            print(f"{item['size']:<10} {item['avg_time']:<15.4f} {item['ops']}")

    def show_summary(self, total, passed, failed, fail_list):
        """
        전체 테스트 결과에 대한 통계와 실패 케이스 요약을 출력합니다.
        """
        print("\n# [4] 결과 요약")
        print(f"총 테스트: {total}개 | 통과: {passed}개 | 실패: {failed}개")
        if fail_list:
            print("\n실패 케이스:")
            for case in fail_list:
                # 실패 원인(판정 불일치 또는 스키마 오류) 함께 표시
                print(f"- {case['id']}: {case['reason']}")

    def get_valid_number(self, prompt, min_val, max_val):
        """
        사용자로부터 범위 내의 유효한 정수를 입력받을 때까지 반복합니다.
        
        Args:
            prompt (str): 입력 안내 문구
            min_val, max_val (int): 허용되는 최소/최대 숫자 범위
        """
        while True:
            try:
                user_input = input(prompt).strip()
                if not user_input: continue
                num = int(user_input)
                if min_val <= num <= max_val: return num
                print(f"⚠ {min_val}~{max_val} 사이를 입력하세요.")
            except ValueError:
                print("⚠ 숫자를 입력해주세요.")