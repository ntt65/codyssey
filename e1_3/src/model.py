"""
================================================================================
모듈명: Model (Mini NPU Simulator)
개요: NPU 시뮬레이터의 핵심 연산 엔진입니다. 
      MAC(Multiply-Accumulate) 연산 구현, 실행 시간 측정, 
      그리고 부동소수점 오차를 고려한 판정 로직을 포함합니다.
작성일: 2026-04-18
================================================================================
"""

import json
import time

class Model:
    """
    데이터 처리 및 수치 연산을 담당하는 모델 클래스
    """
    
    def __init__(self):
        """
        모델 인스턴스를 초기화합니다.
        부동소수점 비교를 위한 허용 오차(epsilon) 값을 설정합니다.
        """
        self.epsilon = 1e-9 # 10의 -9승까지는 같은 값으로 간주 (동점 처리 기준)

    def mac_simulation(self, filter_mat, pattern_mat):
        """
        입력 패턴과 필터 간의 MAC(Multiply-Accumulate) 연산을 수행합니다.
        
        Args:
            filter_mat (list): N x N 크기의 필터 행렬
            pattern_mat (list): N x N 크기의 입력 패턴 행렬
            
        Returns:
            float: 각 원소의 곱을 모두 합산한 최종 점수
        """
        result = 0.0 # 누적 합계를 저장할 변수 초기화
        # 2차원 배열(행렬)을 순회하며 연산 수행
        for i in range(len(filter_mat)): # 행 반복
            for j in range(len(filter_mat[0])): # 열 반복
                # 동일 위치의 값을 곱하여 누적 합산 (MAC의 핵심)
                result += filter_mat[i][j] * pattern_mat[i][j] 
        return result

    def get_average_mac_time(self, filter_mat, pattern_mat, iterations=10):
        """
        MAC 연산의 성능을 측정하기 위해 지정된 횟수만큼 반복 실행하여 평균 시간을 계산합니다.
        
        Args:
            filter_mat, pattern_mat: 연산에 사용될 행렬
            iterations (int): 반복 측정 횟수 (기본값 10회)
            
        Returns:
            float: 1회 연산당 평균 소요 시간 (ms 단위)
        """
        start = time.time() # 전체 측정 시작 시간 기록
        for _ in range(iterations): # 정해진 횟수만큼 반복
            _ = self.mac_simulation(filter_mat, pattern_mat) # 순수 연산 수행
        end = time.time() # 측정 종료 시간 기록
        
        # (전체 소요 시간 / 반복 횟수) 계산 후 초(s) 단위를 밀리초(ms)로 변환
        return ((end - start) / iterations) * 1000 

    def normalize_label(self, label):
        """
        다양한 형식의 입력 라벨을 프로그램 표준 라벨(Cross, X)로 통합합니다.
        
        Args:
            label: JSON 등에서 읽어온 원본 라벨 ('+', 'x', 'cross' 등)
            
        Returns:
            str: 'Cross', 'X', 또는 'UNDECIDED'
        """
        label = str(label).lower().strip() # 소문자 변환 및 공백 제거로 전처리
        if label in ['cross', '+']: return 'Cross' # '+' 기호나 'cross' 문자열 처리
        if label in ['x']: return 'X' # 'x' 문자열 처리
        return 'UNDECIDED' # 정의되지 않은 라벨인 경우

    def judge(self, score_a, score_b):
        """
        두 필터의 점수를 비교하여 최종 판정을 내립니다. 
        설정된 epsilon보다 차이가 작으면 동점으로 처리합니다.
        
        Args:
            score_a (float): 첫 번째 필터(보통 Cross)의 점수
            score_b (float): 두 번째 필터(보통 X)의 점수
            
        Returns:
            str: 'Cross', 'X', 또는 'UNDECIDED'
        """
        # 두 점수의 절대 차이가 허용 오차 미만인지 확인 (부동소수점 오차 대응)
        if abs(score_a - score_b) < self.epsilon: 
            return "UNDECIDED" # 판정 불가 (동점)
        
        # 더 높은 점수를 받은 필터의 이름을 반환
        return "Cross" if score_a > score_b else "X"
    
    def judge_user_input(self, score_a, score_b):
        # 두 점수의 절대 차이가 허용 오차 미만인지 확인 (부동소수점 오차 대응)
        if abs(score_a - score_b) < self.epsilon: 
            return "UNDECIDED" # 판정 불가 (동점)
        
        # 더 높은 점수를 받은 필터의 이름을 반환
        return "A" if score_a > score_b else "B"
    
    def load_json_data(self, file_path):
        """
        지정된 경로의 JSON 파일을 읽어 Python 딕셔너리로 반환합니다.
        
        Args:
            file_path (str): 읽어올 파일의 경로
            
        Returns:
            dict: 파싱된 JSON 데이터
        """
        with open(file_path, 'r') as f: # 읽기 모드로 파일 열기
            return json.load(f) # JSON 라이브러리를 사용하여 역직렬화