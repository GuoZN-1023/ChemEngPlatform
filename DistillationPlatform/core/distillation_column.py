import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from dataclasses import dataclass


@dataclass
class DistillationColumn:
    spec: any
    vle: any

    # ---------- q线 ----------
    def q_line(self):
        q = self.spec.q
        if abs(q - 1.0) < 1e-12:
            return None, None  # 垂直线
        return q / (q - 1.0), -self.spec.xF / (q - 1.0)

    # ---------- pinch点 ----------
    def _find_pinch(self):
        """
        寻找 q 线与平衡线的交点（pinch 点），提高精度：
        - q=1 时直接垂线；
        - 否则使用 scipy.optimize.minimize_scalar 精确最小化 |y*(x) - (mq*x + bq)|；
        - 若 scipy 不可用则自动回退为高密度扫描法。
        """
        eps = 1e-12
        q = float(self.spec.q)

        if abs(q - 1.0) < eps:
            # 饱和液体 → q 线垂直于 x=xF
            x_p = float(self.spec.xF)
            return x_p, float(self.vle.y_star(x_p))

        mq, bq = self.q_line()

        def diff(x):
            return abs(self.vle.y_star(x) - (mq * x + bq))

        # 优先使用 scipy 精确优化
        try:
            from scipy.optimize import minimize_scalar
            res = minimize_scalar(diff, bounds=(0.0, 1.0), method="bounded")
            x_p = float(res.x)
        except Exception:
            # 回退方案：高分辨率扫描 + 二次细化
            xs = np.linspace(0.0, 1.0, 5001)
            vals = np.abs([self.vle.y_star(x) - (mq * x + bq) for x in xs])
            i = int(np.argmin(vals))
            i0 = max(i - 5, 0)
            i1 = min(i + 5, len(xs) - 1)
            x_zoom = np.linspace(xs[i0], xs[i1], 2001)
            vals_zoom = np.abs([self.vle.y_star(x) - (mq * x + bq) for x in x_zoom])
            x_p = float(x_zoom[int(np.argmin(vals_zoom))])

        y_p = float(self.vle.y_star(x_p))
        return x_p, y_p

    # ---------- Rmin ----------
    def compute_Rmin(self):
        """
        根据 pinch 点和塔顶点计算最小回流比 Rmin。
        - 公式：m = (y_p - xD) / (x_p - xD)，Rmin = m / (1 - m)
        - 自动避免分母过小、m 越界
        """
        x_p, y_p = self._find_pinch()
        xD = float(self.spec.xD)

        denom = (x_p - xD)
        if abs(denom) < 1e-10:
            # 极端情况：pinch 点接近塔顶点 → 回流比趋于无穷
            m = 1.0 - 1e-8
        else:
            m = (y_p - xD) / denom

        # 限制 m 在合理范围 (0,1)
        m = float(np.clip(m, 1e-8, 1.0 - 1e-8))
        Rmin = m / (1.0 - m)
        return float(Rmin)

    # ---------- 操作线 ----------
    def operating_lines(self, R):
        m_rect = R / (R + 1.0)
        b_rect = self.spec.xD / (R + 1.0)
        mq, bq = self.q_line()
        if mq is None:
            x_int = self.spec.xF
            y_int = m_rect * x_int + b_rect
        else:
            x_int = (bq - b_rect) / (m_rect - mq)
            y_int = m_rect * x_int + b_rect
        m_strip = (y_int - self.spec.xW) / (x_int - self.spec.xW)
        b_strip = self.spec.xW - m_strip * self.spec.xW
        return (m_rect, b_rect), (m_strip, b_strip), (mq, bq), (x_int, y_int)

    # ---------- 单步理论计算 ----------
    def _theory_step(self, x_in, y_in, section, lines):
        (mr, br), (ms, bs), (_, _), (x_int, _) = lines
        x_eq = self.vle.x_star(y_in)
        sec = "rectifying" if (section == "rectifying" and x_eq > x_int + 1e-12) else "stripping"
        y_op = mr * x_eq + br if sec == "rectifying" else ms * x_eq + bs
        return x_eq, y_op, sec

    # ---------- 主运行 ----------
    def run(self):
        R = self.spec.R
        if R <= 0:
            R = 1.5 * self.compute_Rmin()
            self.spec.R = R

        lines = self.operating_lines(R)
        (mr, br), (ms, bs), (mq, bq), (x_int, y_int) = lines

        EM_L = getattr(self.spec, "EM_L", 1.0)
        EM_V = getattr(self.spec, "EM_V", None)
        use_gas = (EM_V is not None) and (EM_V < 1.0)
        tol = self.spec.tol

        # 初始化
        x_theory, y_theory = self.spec.xD, self.spec.xD
        x_real, y_real = self.spec.xD, self.spec.xD
        section = "rectifying"

        theory_pts, real_pts = [], []
        achieved = False

        for i in range(1, 2001):
            # ---------- 理论级 ----------
            x_eq, y_op, section = self._theory_step(x_theory, y_theory, section, lines)
            x_theory, y_theory = x_eq, y_op

            # ---------- 实际级 ----------
            if not self.spec.consider_murphree:
                x_real, y_real = x_eq, y_op
            elif use_gas:
                y_star = self.vle.y_star(x_eq)
                y_real = y_real + EM_V * (y_star - y_real)
                x_real = (y_real - br) / mr if section == "rectifying" else (y_real - bs) / ms
            else:
                x_real = x_real + EM_L * (x_eq - x_real)
                y_real = mr * x_real + br if section == "rectifying" else ms * x_real + bs

            # ---------- 判断是否达标 ----------
            if x_real <= self.spec.xW:
                theory_pts.append((i, x_eq, y_op, section))
                real_pts.append((i, x_real, y_real, section, x_eq, y_op))
                achieved = True
                break

            # ---------- 记录 ----------
            theory_pts.append((i, x_eq, y_op, section))
            real_pts.append((i, x_real, y_real, section, x_eq, y_op))

            # 防止数值发散
            if x_real < 0 or x_real > 1:
                print("⚠️ Numerical instability detected, aborting loop.")
                break

        # 输出 DataFrame
        df_theory = pd.DataFrame(theory_pts, columns=["stage", "x_theory", "y_theory", "section"])
        df_real = pd.DataFrame(real_pts, columns=["stage", "x_real", "y_real", "section",
                                                  "x_theory_ref", "y_theory_ref"])

        if not achieved:
            print(f"⚠️ Warning: target bottom composition not reached, last x_real = {x_real:.5f}")

        return {
            "R_used": R,
            "lines": lines,
            "theory": df_theory,
            "real": df_real,
            "achieved": achieved
        }

    # ---------- 绘图 ----------
    def plot(self, result, vle, folder):
        xs = np.linspace(0, 1, 1000)
        plt.figure(figsize=(8, 8))

        # 平衡线与对角线
        plt.plot(xs, [vle.y_star(x) for x in xs], "b", label="Equilibrium")
        plt.plot(xs, xs, "k--", label="y=x")

        # 操作线与 q 线
        (mr, br), (ms, bs), (mq, bq), (x_int, y_int) = result["lines"]
        plt.plot(xs, mr * xs + br, "r-", label="Rectifying line")
        plt.plot(xs, ms * xs + bs, "g-", label="Stripping line")
        if mq is None:
            plt.axvline(self.spec.xF, color="0.5", linestyle="--", label="q line (q=1)")
        else:
            plt.plot(xs, mq * xs + bq, color="0.5", linestyle="--", label="q line")
        plt.scatter([x_int], [y_int], color="red", s=35, label="Feed intersection")

        # 理论阶梯（橙色）
        df_t = result["theory"]
        if not df_t.empty:
            x_path, y_path = [self.spec.xD], [self.spec.xD]
            for _, r in df_t.iterrows():
                x_eq, y_op = r["x_theory"], r["y_theory"]
                x_path.append(x_eq)
                y_path.append(y_path[-1])
                x_path.append(x_eq)
                y_path.append(y_op)
            plt.plot(x_path, y_path, color="orange", lw=1.5, label="Theoretical")

        # 实际阶梯（紫色）
        df_r = result["real"]
        if df_r is not None and not df_r.empty:
            x_path_r, y_path_r = [self.spec.xD], [self.spec.xD]
            for _, r in df_r.iterrows():
                xr, yr = r["x_real"], r["y_real"]
                x_path_r.append(xr)
                y_path_r.append(y_path_r[-1])
                x_path_r.append(xr)
                y_path_r.append(yr)
            plt.plot(x_path_r, y_path_r, color="purple", lw=1.8, label="Real (Murphree)")

        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.xlabel("x (liquid mole fraction)")
        plt.ylabel("y (vapor mole fraction)")
        plt.title("McCabe–Thiele Diagram")
        plt.xlim(0, 1)
        plt.ylim(0, 1.05)
        plt.tight_layout()
        plt.savefig(f"{folder}/mccabe_thiele.png", dpi=300)
        plt.close()