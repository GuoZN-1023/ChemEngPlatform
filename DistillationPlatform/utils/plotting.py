import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

def _build_stair_xy_from_points(df_stages: pd.DataFrame, x0: float, y0: float,
                                x_col: str, y_col: str):
    """
    将逐级点表（每行是一个“到平衡线的 x、到操作线的 y”）转换为
    真正的 McCabe–Thiele 折线轨迹：每级两段（水平→竖直）。
    - 起点为 (x0, y0) = (xD, xD)
    - df_stages 需按 stage 升序
    - x_col/y_col 分别为该轨迹的 x/y 列名（理论：x_theory,y_theory；真实：x_real,y_real）
    返回：np.array(xs), np.array(ys)
    """
    xs_path = [x0]
    ys_path = [y0]
    for _, row in df_stages.sort_values("stage").iterrows():
        x_to_eq = float(row[x_col])       # 到平衡线的 x（理论：x_eq；真实：x_real）
        y_on_op = float(row[y_col])       # 对应操作线上的 y（理论/真实同一 y_op）

        # 1) 水平到平衡线端点：y 不变，x 变为 x_to_eq
        xs_path.append(x_to_eq)
        ys_path.append(ys_path[-1])

        # 2) 竖直到操作线：x 不变，y 变为 y_on_op
        xs_path.append(x_to_eq)
        ys_path.append(y_on_op)
    return np.array(xs_path), np.array(ys_path)


def plot_mccabe_thiele(result, vle, folder):
    """
    完整 McCabe–Thiele 图：
      - 平衡线、对角线
      - 精馏段/提馏段操作线
      - q 线（含 q=1 垂直线）
      - 进料交点
      - 理论阶梯（必有）
      - 真实阶梯（仅在 consider_murphree=True 且有列时）
    依赖：
      engine.run(...) 返回 result 中包含：
        - "data": DataFrame（合并后的表，含理论/真实列）
        - "lines": ((mr,br),(ms,bs),(mq,bq),(x_int,y_int))
        - "summary": 包含 xD、consider_murphree 等
    """
    df = result["data"]
    (mr, br), (ms, bs), (mq, bq), (x_int, y_int) = result["lines"]
    summary = result.get("summary", {})
    consider_murphree = bool(result.get("consider_murphree", summary.get("consider_murphree", False)))
    xD = float(summary.get("xD", 1.0))  # 若没提供，保守用 1.0
    yD = xD

    # 曲线与直线
    xs = np.linspace(0, 1, 1000)
    plt.figure(figsize=(8, 8))
    # 平衡线 & 对角线
    plt.plot(xs, [vle.y_star(x) for x in xs], color="C0", label="Equilibrium")
    plt.plot(xs, xs, "k--", label="y = x")

    # 操作线
    plt.plot(xs, mr * xs + br, color="C3", label="Rectifying line")
    plt.plot(xs, ms * xs + bs, color="C2", label="Stripping line")

    # q 线
    if mq is None:
        plt.axvline(x_int, color="0.5", linestyle="--", label="q line (q=1)")
    else:
        plt.plot(xs, mq * xs + bq, color="0.5", linestyle="--", label="q line")

    # 进料交点
    plt.scatter([x_int], [y_int], color="red", s=35, zorder=5, label="Feed intersection")

    # === 阶梯：严格“水平→竖直”的轨迹构造 ===
    # 理论阶梯
    if {"x_theory", "y_theory", "stage"}.issubset(df.columns):
        # 过滤掉 NaN 行，避免路径中断
        df_t = df[["stage", "x_theory", "y_theory"]].dropna().copy()
        if not df_t.empty:
            x_th, y_th = _build_stair_xy_from_points(df_t, x0=xD, y0=yD,
                                                     x_col="x_theory", y_col="y_theory")
            plt.plot(x_th, y_th, color="orange", linewidth=1.8, label="Theoretical stages")

    # 真实阶梯（仅当考虑 Murphree 且列存在）
    has_real_cols = {"x_real", "y_real", "stage"}.issubset(df.columns)
    if consider_murphree and has_real_cols:
        df_r = df[["stage", "x_real", "y_real"]].dropna().copy()
        if not df_r.empty:
            x_rl, y_rl = _build_stair_xy_from_points(df_r, x0=xD, y0=yD,
                                                     x_col="x_real", y_col="y_real")
            plt.plot(x_rl, y_rl, color="purple", linewidth=1.8, label="Real stages")

    # 轴、网格、保存
    plt.xlim(0, 1); plt.ylim(0, 1.05)
    plt.xlabel("x (liquid mole fraction)")
    plt.ylabel("y (vapor mole fraction)")
    plt.title("McCabe–Thiele Diagram")
    plt.grid(True, alpha=0.3)
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(f"{folder}/mccabe_thiele.png", dpi=300)
    plt.close()

def plot_optimization_results(opt_result, result_folder):
    """
    绘制经济优化结果图：
    - 回流比 R vs 塔板数 N
    - 回流比 R vs 总成本 C
    """
    Rs = opt_result["R_list"]
    Ns = opt_result["N_list"]
    Cs = opt_result["C_list"]

    # 图1: 回流比 vs 塔板数
    plt.figure(figsize=(6, 4))
    plt.plot(Rs, Ns, "o-", label="理论塔板数 N vs 回流比 R")
    plt.xlabel("回流比 R")
    plt.ylabel("理论塔板数 N")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{result_folder}/R_vs_N.png", dpi=300)
    plt.close()

    # 图2: 回流比 vs 成本
    plt.figure(figsize=(6, 4))
    plt.plot(Rs, Cs, "r-", label="总成本 C = aN + bQ(R)")
    plt.xlabel("回流比 R")
    plt.ylabel("相对成本 C")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(f"{result_folder}/economic_opt.png", dpi=300)
    plt.close()

    print(f"📊 已生成优化图：R_vs_N.png 与 economic_opt.png → {result_folder}")