class Model:
    def __init__(self):
        self.filter_a = None
        self.filter_b = None
        self.pattern = None
    
    def mac_simulation(self, filter, pattern, iterations):
        # MAC 시뮬레이션 로직
        result = 0
        for _ in range(iterations):
            for i in range(len(pattern)):
                for j in range(len(pattern[0])  if pattern else 0):
                    result += filter[i][j] * pattern[i][j]
        return result