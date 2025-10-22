import numpy as np
from core.distillation_column import DistillationColumn

class DistillationOptimizer:
    def __init__(self, spec, vle):
        self.spec = spec
        self.vle = vle

    # ---------- (1) 给定塔板数 N，求对应回流比 ----------
    def find_R_for_N(self, N_target, tol=1e-3, R_max=10.0):
        """
        迭代求解：给定理论塔板数 N_target，求对应回流比 R
        方法：二分搜索
        """
        column = DistillationColumn(self.spec, self.vle)
        Rmin = column.compute_Rmin()

        R_low = 1.05 * Rmin
        R_high = R_max
        iteration = 0
        best_result = None

        while iteration < 50:
            R_mid = 0.5 * (R_low + R_high)
            self.spec.R = R_mid
            col = DistillationColumn(self.spec, self.vle)
            result = col.run()
            N_now = len(result["theory"])

            if abs(N_now - N_target) < 1:
                return R_mid, result
            elif N_now > N_target:
                R_low = R_mid
            else:
                R_high = R_mid
            best_result = result
            iteration += 1

        return R_mid, best_result

    # ---------- (2) 给定回流比 R，求塔板数 ----------
    def plates_for_R(self, R):
        self.spec.R = R
        col = DistillationColumn(self.spec, self.vle)
        result = col.run()
        return len(result["theory"]), result

    # ---------- (3) 经济优化 ----------
    def economic_optimization(self, R_range=None, a=1.0, b=1.0):
        """
        能耗与塔板成本平衡：
            C = a * N + b * Q(R)
        """
        column = DistillationColumn(self.spec, self.vle)
        Rmin = column.compute_Rmin()

        if R_range is None:
            R_range = np.linspace(1.05 * Rmin, 3.0 * Rmin, 20)

        Rs, Ns, Cs = [], [], []

        for R in R_range:
            N, _ = self.plates_for_R(R)
            Q = R / (R + 1.0)
            C = a * N + b * Q
            Rs.append(R)
            Ns.append(N)
            Cs.append(C)

        idx = np.argmin(Cs)
        return {"R_opt": Rs[idx], "N_opt": Ns[idx],
                "C_opt": Cs[idx], "R_list": Rs,
                "N_list": Ns, "C_list": Cs}