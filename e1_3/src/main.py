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
        decision = self.model.judge(res_a, res_b)
        
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

        self.view.show_analysis_header() # 분석 시작 헤더 출력
        
        for p_key, p_val in patterns.items():
            # 패턴 키 이름에서 크기 정보 추출 (예: 'size_5_1' -> '5')
            size_str = p_key.split('_')[1] 
            f_key = f"size_{size_str}" # 대응되는 필터 그룹 키 생성
            
            target_filters = filters.get(f_key, {})
            # 각 필터 타입 로드 및 정규화
            f_cross = target_filters.get('cross')
            f_x = target_filters.get('x')
            
            input_pattern = p_val.get('input') # 입력된 이미지 패턴
            # 기대값(expected)을 표준 라벨('Cross' 또는 'X')로 정규화
            expected = self.model.normalize_label(p_val.get('expected'))
            
            # 스키마 검증: 필터 존재 여부 및 행 크기 일치 확인
            if not f_cross or len(f_cross) != int(size_str):
                results.append({'id': p_key, 'pass': False, 'reason': '필터 스키마 오류'})
                continue

            # MAC 연산 수행 (Cross 필터 vs X 필터)
            score_cross = self.model.mac_simulation(f_cross, input_pattern)
            score_x = self.model.mac_simulation(f_x, input_pattern)
            
            # 수치 비교를 통한 최종 판정
            decision = self.model.judge(score_cross, score_x)
            
            # 실제 판정과 기대값이 일치하는지 확인
            is_pass = (decision == expected)
            self.view.show_case_result(p_key, score_cross, score_x, decision, expected, is_pass)
            
            # 결과 리스트에 기록
            results.append({
                'id': p_key, 
                'pass': is_pass, 
                'reason': f'판정 {decision} != 기대 {expected}' if not is_pass else ''
            })

            # 크기별 성능 데이터 기록 (동일 크기는 한 번만 측정하여 효율성 제고)
            if size_str not in perf_summary:
                avg_t = self.model.get_average_mac_time(f_cross, input_pattern)
                perf_summary[size_str] = {'avg_time': avg_t, 'ops': int(size_str)**2}

        # 결과 집계: 통과 개수 및 실패 케이스 추출
        passed = sum(1 for r in results if r['pass'])
        fails = [r for r in results if not r['pass']]
        
        # 성능 분석 표 작성을 위한 데이터 정렬 (크기순)
        perf_list = [
            {'size': f"{k}x{k}", 'avg_time': v['avg_time'], 'ops': v['ops']} 
            for k, v in sorted(perf_summary.items(), key=lambda x: int(x[0]))
        ]
        
        # 최종 통계 및 테이블 출력
        self.view.show_performance_table(perf_list)
        self.view.show_summary(len(results), passed, len(fails), fails)

if __name__ == "__main__":
    # 엔트리 포인트: 컨트롤러 인스턴스 생성 및 실행
    Controller().run()