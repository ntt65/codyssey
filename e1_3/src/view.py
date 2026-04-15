class View:
    def __init__(self):
        # 뷰 초기화
        pass
    def load_view(self):        # 뷰 로드 로직
        print("=== Mini NPU Simulator ===")    
    def show_main_menu(self):
        # 메시지 출력
        print("[모드 선택]")
        print("1. 사용자 입력 (3x3)")
        print("2. data.json 분석")
        print("3. 종료")
    def show_user_input(self):        # 사용자 입력 모드 로직
        print("#----------------------------------------")
        print("# [1] 필터 입력")
        print("#----------------------------------------")
        print("필터 A 를 입력하세요 (3줄입력, 공백구분): ")
        filter_a = [list(map(int, input(f'line {i+1} : ').split())) for i in range(3)]
        print("필터 B 를 입력하세요 (3줄입력, 공백구분): ")
        filter_b = [list(map(int, input(f'line {i+1} : ').split())) for i in range(3)]
        print("#----------------------------------------")
        print("# [2] 패턴 입력")
        print("#----------------------------------------")
        print("패턴을 입력하세요 (3줄입력, 공백구분): ")
        pattern = [list(map(int, input(f'line {i+1} : ').split())) for i in range(3)]
        print("#----------------------------------------")
        print("입력된 필터 A:")
        for row in filter_a:
            print(row)
        print("입력된 필터 B:")
        for row in filter_b:
            print(row)
        print("입력된 패턴:")
        for row in pattern:
            print(row)
        return filter_a, filter_b, pattern

    def get_valid_number(self, prompt, min_val, max_val):
        """사용자로부터 유효한 숫자를 입력받음 (미션 요구 예외 처리 포함)
        
        처리:
        - 입력 앞뒤 공백 제거 (.strip())
        - 빈 입력 체크
        - 숫자 변환 실패 처리 (ValueError)
        - 범위 체크 (min_val ~ max_val)
        
        Args:
            prompt (str): 입력 프롬프트 메시지
            min_val (int): 허용 최소값
            max_val (int): 허용 최대값
            
        Returns:
            int: 검증된 숫자
        """
        while True:
            try:
                # 공백 제거
                user_input = input(prompt).strip()
                # 빈 입력 체크
                if not user_input:
                    print("⚠ 입력이 비어있습니다.")
                    continue
                # 숫자 변환
                num = int(user_input)
                # 범위 검증
                if min_val <= num <= max_val:
                    return num
                print(f"⚠ {min_val}~{max_val} 사이를 입력하세요.")
                # 숫자가 아닌 입력 처리
            except ValueError:
                print("⚠ 숫자를 입력해주세요.")