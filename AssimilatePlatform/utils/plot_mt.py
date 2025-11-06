import matplotlib.pyplot as plt

def draw_mt(out_png, m, L, V, YN, X0, YF, stairs):
    """
    教材式 McCabe–Thiele 吸收图。
    - 平衡线: Y = mX
    - 操作线: Y = (L/V)X + (YN - (L/V)X0)
    - 阶梯: 按 stairs 逐级绘制
    """

    r = L / V
    intercept = YN - r * X0

    # ==== 基础设定 ====
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.set_title("McCabe–Thiele Diagram for Gas Absorption", fontsize=13)
    ax.set_xlabel("X (solute in liquid)", fontsize=11)
    ax.set_ylabel("Y (solute in gas)", fontsize=11)
    ax.grid(True, linestyle="--", alpha=0.4)

    # ==== 平衡线 ====
    x_eq = [0, max(0.02, max(s["X"] for s in stairs)) * 1.1]
    y_eq = [m * x for x in x_eq]
    ax.plot(x_eq, y_eq, "r-", lw=1.8,
            label=f"Equilibrium line  Y = {m:.3f}·X")

    # ==== 操作线 ====
    y_op = [r * x + intercept for x in x_eq]
    ax.plot(x_eq, y_op, "b-", lw=1.8,
            label=f"Operating line  Y = {r:.3f}·X + {intercept:.4f}")

    # ==== 阶梯 ====
    for i in range(1, len(stairs), 2):
        h1, v1 = stairs[i - 1], stairs[i]
        ax.plot([h1["X"], v1["X"]], [h1["Y"], h1["Y"]], "k-", lw=1)
        if i + 1 < len(stairs):
            v2 = stairs[i + 1]
            ax.plot([v1["X"], v2["X"]], [v1["Y"], v2["Y"]], "k-", lw=1)

    # ==== 起点/终点 ====
    ax.scatter(X0, YN, c="g", s=40, label="Top  (X₀, Y_N)")
    ax.scatter(stairs[-1]["X"], stairs[-1]["Y"], c="orange", s=40, label="Bottom (X₁, Y_F)")

    # ==== 坐标范围与图例 ====
    ax.set_xlim(0, max(x_eq) * 1.05)
    ax.set_ylim(0, max(y_eq[-1], y_op[-1]) * 1.05)
    ax.legend(loc="upper left", fontsize=9, frameon=False)

    plt.tight_layout()
    plt.savefig(out_png, dpi=300, bbox_inches="tight")
    plt.close()
    return True