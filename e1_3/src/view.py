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

def show_user_input(self, size):
    """사용자 입력 모드에서 필터와 패턴을 입력받는 로직
    동적 사이즈 대응: 기존 코드에 하드코딩되어 있던 range(3)를 매개변수 size로 변경하여, 
    3×3뿐만 아니라 소스에서 요구하는 5×5, 13×13 등의 크기도 처리할 수 있도록 확장성을 높였습니다
    데이터 정제(Trimming & Padding):
    제거: row[:size]를 통해 입력된 숫자가 지정된 크기보다 많을 경우 뒷부분을 잘라냅니다.
    0으로 채우기: row +=  * (size - len(row))를 통해 입력된 숫자가 적을 경우 부족한 만큼 0을 
    채워 넣습니다.
    예외 처리: try-except 문을 추가하여 사용자가 숫자가 아닌 문자 등을 입력했을 때 프로그램이 비정상 종료되지 
    않도록 하였으며, 이는 소스의 "프로그램이 비정상 종료되면 안 된다"는 지침과 일치합니다.
    입력 검증 안내: 숫자 파싱 실패 시 안내 문구를 출력하도록 하여 소스의 기능 요구 사항을 충족했습니다
    사용자가 1 0 1 1과 같이 4개의 값을 입력해도 3×3 모드라면 앞의 1 0 1만 저장되고, 1 0만 입력하면 
    1 0 0으로 자동 보정되어 MAC 연산 단계에서 오류가 발생하는 것을 방지할 수 있습니다.
    """
    # 행렬 입력을 처리하는 내부 보조 함수
    def get_fixed_matrix(name, size):
        print(f"{name} 를 입력하세요 ({size}줄 입력, 공백 구분):")
        matrix = []
        for i in range(size):
            try:
                line = input(f'line {i+1} : ').split()
                # 1. 숫자 파싱 (소스 5번 요구사항 반영)
                row = [int(x) for x in line]
                
                # 2. 열(Column) 처리: 크면 제거, 작으면 0으로 패딩
                if len(row) > size:
                    row = row[:size]  # 정해진 사이즈만큼 슬라이싱
                elif len(row) < size:
                    row +=  * (size - len(row))  # 부족한 만큼 0 추가
                
                matrix.append(row)
            except ValueError:
                # 숫자 파싱 실패 시 안내 문구 출력 후 해당 줄을 0으로 채움 [1, 2]
                print(f"입력 형식 오류: 숫자가 아닌 값이 있어 line {i+1}을 0으로 채웁니다.")
                matrix.append( * size)
        return matrix

    print("#----------------------------------------")
    print("# [5] 필터 입력")
    print("#----------------------------------------")
    # 하드코딩된 '3' 대신 매개변수 'size'를 사용하도록 수정
    filter_a = get_fixed_matrix("필터 A", size)
    filter_b = get_fixed_matrix("필터 B", size)

    print("#----------------------------------------")
    print("# [6] 패턴 입력")
    print("#----------------------------------------")
    pattern = get_fixed_matrix("패턴", size)

    print("#----------------------------------------")
    print(f"입력된 필터 A ({size}x{size}):")
    for row in filter_a:
        print(row)
    print(f"입력된 필터 B ({size}x{size}):")
    for row in filter_b:
        print(row)
    print(f"입력된 패턴 ({size}x{size}):")
    for row in pattern:
        print(row)

    return filter_a, filter_b, pattern
    
    def show_mac_result(self, result_a, result_b, time):        # MAC 결과 출력 로직
        print("#----------------------------------------")
        print("# [3] MAC 결과")
        print("#----------------------------------------")
        print(f"필터 A의 MAC 결과: {result_a}")
        print(f"필터 B의 MAC 결과: {result_b}")
        print(f"실행 시간: {time} ms")
        print(f"판정: {'A' if result_a > result_b else 'B'}")

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