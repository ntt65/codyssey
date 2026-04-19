"""
================================================================================
프로그램명: Mini NPU Simulator (v1.0)
개요: NPU의 핵심 연산인 MAC(Multiply-Accumulate)을 시뮬레이션하고,
      2차원 패턴(Cross, X) 인식 성능 및 정확도를 분석하는 도구입니다.
구조: MVC 패턴 (Model-View-Controller) 중 제어 로직을 담당하는 Controller부
작성일: 2026-04-18
================================================================================
"""

import model
import view

class Controller:
    """
    사용자의 입력을 처리하고 Model(연산)과 View(UI)를 중재하는 메인 컨트롤러 클래스
    """
    
    def __init__(self):
        """프로그램 실행에 필요한 모델과 뷰 인스턴스를 초기화합니다."""
        self.model = model.Model() # 데이터 연산 및 비즈니스 로직 담당
        self.view = view.View()    # 콘솔 출력 및 사용자 입력 담당

    def run(self):
        """메인 루프를 실행하여 메뉴를 표시하고 사용자 선택에 따른 모드를 수행합니다."""
        try:
            while True:
                self.view.show_main_menu() # 메인 메뉴 출력
                choice = self.view.get_valid_number("선택: ", 1, 3) # 1~3 사이 정수 입력 보장
                
                if choice == 1: 
                    self.mode_user_input() # 1번: 3x3 수동 입력 모드
                elif choice == 2: 
                    self.mode_json_analysis() # 2번: JSON 데이터 일괄 분석 모드
                else: 
                    break # 3번: 루프 탈출 및 종료
        except (KeyboardInterrupt, EOFError):
            print("\n👋 프로그램을 종료합니다.")

    def mode_user_input(self):
        """사용자로부터 3x3 행렬 데이터를 직접 입력받아 MAC 점수를 비교하고 판정합니다."""
        # View를 통해 필터 2개와 패턴 1개를 입력받음 (기본 3x3)
        f_a, f_b, pattern = self.view.show_user_input(3) 

        # Model을 이용해 각 필터별 MAC 결과값 계산
        res_a = self.model.mac_simulation(f_a, pattern) 
        res_b = self.model.mac_simulation(f_b, pattern)
        
        # 10회 반복 연산을 통한 평균 수행 시간(ms) 측정
        avg_time = self.model.get_average_mac_time(f_a, pattern)
        
        # 두 점수를 비교하여 판정 결과(A, B, 또는 UNDECIDED) 도출
        decision = self.model.judge_user_input(res_a, res_b)
        
        # 결과 화면 출력
        self.view.show_mac_result(res_a, res_b, avg_time, decision)

    def mode_json_analysis(self):
        """data.json 파일을 로드하여 다수의 패턴 케이스에 대한 정확도와 성능을 분석합니다."""
        try:
            # JSON 데이터 로드
            data = self.model.load_json_data('data.json')
        except FileNotFoundError:
            print("⚠ data.json 파일이 없습니다.")
            return

        filters = data.get('filters', {})   # 크기별 정의된 필터 세트
        patterns = data.get('patterns', {}) # 테스트용 패턴 데이터 세트
        
        results = []       # 개별 테스트 통과/실패 결과 저장 리스트
        perf_summary = {}  # 크기별(5, 13, 25) 성능 지표 저장 딕셔너리

        self.view.show_title(2, "JSON 분석") # 분석 시작 헤더 출력
        
        for p_key, p_data in patterns.items():
            try:
                # 1. 키에서 사이즈 정보 추출 (예: size_5_1_Normal -> 5)
                parts = p_key.split('_')
                if len(parts) < 2:
                    raise ValueError("잘못된 키 형식")
                
                size_str = parts[1] # '5', '13', '25' 추출
                f_key = f"size_{size_str}"
                filter_set = filters.get(f_key)

                if not filter_set:
                    raise ValueError(f"{f_key}에 해당하는 필터가 없습니다.")

                # 2. 필터 및 패턴 데이터 가져오기
                f_cross = filter_set.get('cross')
                f_x = filter_set.get('x')
                input_pattern = p_data.get('input')
                expected_raw = p_data.get('expected')

                ### 🛡️ 시스템 안정성 (Error Handling)
                # 데이터 분석 과정에서 발생할 수 있는 잠재적 오류를 방지하기 위해 2단계 검증 로직을 구축했습니다.

                # 1. **데이터 무결성 검사 (Integrity Check)**: 
                # - `mac_simulation` 연산 수행 전, 필터와 입력 패턴이 비어있지는 않은지(`None` 또는 빈 리스트) 체크합니다.
                # - 데이터 누락 시 `ValueError`를 발생시켜 잘못된 연산 결과가 산출되는 것을 원천 차단했습니다.

                # 2. **개별 케이스 격리 (Case Isolation)**:
                # - 특정 패턴 데이터(`size_N_idx`)에 오류가 있더라도 프로그램 전체가 종료되지 않고, 해당 케이스만 'ERROR'로 표시한 뒤 다음 테스트를 계속 진행하도록 `try-except` 블록을 구성했습니다.

                # 데이터 유효성 검사
                if not f_cross or not f_x or not input_pattern:
                    raise ValueError("필터 또는 입력 패턴 데이터가 누락되었습니다.")

                # 3. 라벨 정규화 및 MAC 연산
                expected = self.model.normalize_label(expected_raw)
                score_cross = self.model.mac_simulation(f_cross, input_pattern)
                score_x = self.model.mac_simulation(f_x, input_pattern)
                
                # 4. 판정 및 결과 기록
                decision = self.model.judge(score_cross, score_x)
                is_pass = (decision == expected)
                
                self.view.show_case_result(p_key, score_cross, score_x, decision, expected, is_pass)
                
                results.append({
                    'id': p_key, 
                    'pass': is_pass, 
                    'reason': f'판정 {decision} != 기대 {expected}' if not is_pass else ''
                })

                # 5. 성능 데이터 기록 (크기별로 한 번씩만 측정)
                if size_str not in perf_summary:
                    avg_t = self.model.get_average_mac_time(f_cross, input_pattern)
                    perf_summary[size_str] = {'avg_time': avg_t, 'ops': int(size_str)**2}

            except Exception as e:
                # 예기치 못한 데이터 오류 발생 시 해당 케이스만 FAIL 처리
                self.view.show_case_result(p_key, 0, 0, "ERROR", "UNKNOWN", False)
                results.append({
                    'id': p_key, 
                    'pass': False, 
                    'reason': f"오류: {str(e)}"
                })
                continue

        # 결과 집계 및 출력
        passed = sum(1 for r in results if r['pass'])
        fails = [r for r in results if not r['pass']]
        
        perf_list = [
            {'size': f"{k}x{k}", 'avg_time': v['avg_time'], 'ops': v['ops']} 
            for k, v in sorted(perf_summary.items(), key=lambda x: int(x[0]))
        ]
        
        self.view.show_performance_table(perf_list)
        self.view.show_summary(len(results), passed, len(fails), fails)
if __name__ == "__main__":
    # 엔트리 포인트: 컨트롤러 인스턴스 생성 및 실행
    Controller().run()