import numpy as np

class VLEData:
    """存储气液平衡数据，提供插值方法"""
    def __init__(self, x_data, y_data):
        self.x = np.array(x_data)
        self.y = np.array(y_data)
        self.y_star_func = lambda x: np.interp(x, self.x, self.y)
        self.x_star_func = lambda y: np.interp(y, self.y, self.x)

    def y_star(self, x):
        return float(self.y_star_func(x))

    def x_star(self, y):
        return float(self.x_star_func(y))