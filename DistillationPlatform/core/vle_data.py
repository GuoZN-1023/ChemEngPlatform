import numpy as np
from scipy.interpolate import CubicSpline

class VLEData:
    """存储气液平衡数据，提供三次样条插值方法"""
    def __init__(self, x_data, y_data):
        self.x = np.array(x_data)
        self.y = np.array(y_data)

        # 使用 SciPy 三次样条插值（自然边界）
        self.y_star_func = CubicSpline(self.x, self.y, bc_type='natural')
        self.x_star_func = CubicSpline(self.y, self.x, bc_type='natural')

    def y_star(self, x):
        return float(self.y_star_func(x))

    def x_star(self, y):
        return float(self.x_star_func(y))