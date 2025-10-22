import numpy as np

# ---------------- 共沸精馏 ----------------
def azeotropic_modifier(vle, azeo_x=0.6, azeo_y=0.6, strength=-0.05, width=0.05):
    """
    修改平衡曲线以模拟共沸精馏。
    参数：
        vle : VLEData 对象
        azeo_x : 共沸点液相组成
        azeo_y : 共沸点气相组成
        strength : 扰动强度（<0 表示打破共沸；>0 表示增强共沸）
        width : 扰动宽度（决定影响区域）
    返回：
        修改后的 VLEData 对象（浅拷贝）
    """
    orig_func = vle.y_star
    def new_y_star(x):
        base = orig_func(x)
        perturb = strength * np.exp(-((x - azeo_x) ** 2) / (2 * width ** 2))
        return np.clip(base + perturb, 0.0, 1.0)
    vle.y_star = new_y_star
    return vle


# ---------------- 萃取精馏 ----------------
def extractive_modifier(vle, solvent_ratio=0.1, alpha_factor=1.5):
    """
    修改平衡曲线以模拟萃取精馏（通过改变相对挥发度）。
    参数：
        vle : VLEData 对象
        solvent_ratio : 溶剂/进料摩尔比
        alpha_factor : 溶剂引起的挥发度放大系数 (>1 增强分离)
    返回：
        修改后的 VLEData 对象
    """
    orig_func = vle.y_star
    factor = 1 + (alpha_factor - 1) * solvent_ratio
    def new_y_star(x):
        base = orig_func(x)
        return np.clip(base * factor, 0.0, 1.0)
    vle.y_star = new_y_star
    return vle