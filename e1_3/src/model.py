import json
import time

class Model:
    def __init__(self):
        self.epsilon = 1e-9

    def mac_simulation(self, filter_mat, pattern_mat):
        # 10회 반복 측정 후 평균값 반환을 위해 연산부 분리
        result = 0.0
        for i in range(len(filter_mat)):
            for j in range(len(filter_mat[0])):
                result += filter_mat[i][j] * pattern_mat[i][j]
        return result

    def get_average_mac_time(self, filter_mat, pattern_mat, iterations=10):
        start = time.time()
        for _ in range(iterations):
            _ = self.mac_simulation(filter_mat, pattern_mat)
        end = time.time()
        return ((end - start) / iterations) * 1000  # ms 변환

    def normalize_label(self, label):
        # 라벨 정규화: '+' -> Cross, 'x' -> X
        label = str(label).lower().strip()
        if label in ['cross', '+']: return 'Cross'
        if label in ['x']: return 'X'
        return 'UNDECIDED'

    def judge(self, score_a, score_b):
        if abs(score_a - score_b) < self.epsilon:
            return "UNDECIDED"
        return "Cross" if score_a > score_b else "X"

    def load_json_data(self, file_path):
        with open(file_path, 'r') as f:
            return json.load(f)