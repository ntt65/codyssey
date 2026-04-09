"""
quizView.py - 사용자 인터페이스 및 입력 처리

개요:
    사용자와의 상호작용을 담당하는 View 클래스입니다.
    메뉴 표시, 메시지 출력, 사용자 입력을 처리합니다.
    미션 요구 예외 처리 (공백 제거, 숫자 검증, 범위 체크 등)를 포함합니다.
"""

class QuizView:
    """사용자 인터페이스를 담당하는 View 클래스
    
    기능:
        - 메뉴 표시
        - 메시지 출력
        - 사용자 입력 검증 (공백 제거, 숫자 변환, 범위 체크)
        - 퀴즈 관련 정보 표시
    """

    def display_menu(self):
        """메인 메뉴를 콘솔에 출력"""
        print("\n" + "="*30)
        print("   파이썬 퀴즈 챌린지")
        print("="*30)
        print("1. 퀴즈 풀기 (랜덤/수량)")
        print("2. 새로운 퀴즈 추가")
        print("3. 퀴즈 목록 보기")
        print("4. 최고 점수 확인")
        print("5. 퀴즈 삭제하기 (보너스)")
        print("6. 전체 기록 보기 (보너스)")
        print("7. 게임 종료")
        print("="*30)

    def show_message(self, msg):
        """메시지 출력
        
        Args:
            msg (str): 출력할 메시지
        """
        print(msg)

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
