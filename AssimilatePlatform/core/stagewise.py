from .equilibrium import y_star

def stepwise_stairs(L, V, m, YF, YN, X0, cap=500, tol=1e-12):
    """
    McCabe–Thiele 逐级（吸收） —— 严格遵循教材/7-2.py 逻辑：
      起点：塔顶 (X0, YN)
      每级：先 “水平到平衡线”  X_eq = Y / m
            再 “竖直到操作线”  Y_new = (L/V) * X_eq + (YN - (L/V) * X0)
      终止：竖直到操作线后的 Y_new >= YF
    说明：
      - 允许首级 Y 先下降（若顶端操作线高于平衡线）；这在吸收是正常的。
      - 对 X 做物理约束（非负、不回退）；若回退，提示参数矛盾。
      - L < Lmin 的不可行情况由 runner 预先拦截；本函数不做“跑满 cap”的假收敛。
    返回：
      stairs: 节点列表（start/horizontal/vertical）
      N: 理论级数
      X1: 塔底液相溶质摩尔比（最后一次水平段的 X_eq）
    """
    if L <= 0 or V <= 0:
        raise ValueError("L 和 V 必须为正。")

    r = L / V
    intercept = YN - r * X0  # 操作线：Y = r*X + (YN - r*X0)

    # 起点（塔顶）
    Y = float(YN)
    X = float(X0)
    stairs = [{"stage": 0, "type": "start", "X": X, "Y": Y}]
    N = 0

    for _ in range(max(1, int(cap))):
        # 1) 水平到平衡线：在当前 Y 下，X_eq = Y / m
        #    （教材/7-2 的标准做法：横向到平衡线）
        if m <= 0:
            raise RuntimeError("m 必须为正。请检查平衡式 Y* = m X 的 m。")
        X_eq = Y / m

        # 物理/数值保护：X 非负 & 不回退
        if X_eq < 0:
            X_eq = 0.0
        if X_eq + tol < X:
            # 若出现回退，说明 (X0, YN) 与 m 的关系不自洽，或单位/定义（摩尔比/分率）混用
            raise RuntimeError(
                f"逐级计算检测到 X 回退：X_eq({X_eq:.6g}) < 当前 X({X:.6g})。"
                "请核对起点 (X0, YN) 与 m（以及 X/Y 的定义是否为摩尔比而非分率）。"
            )

        stairs.append({"stage": N + 1, "type": "horizontal", "X": X_eq, "Y": Y})

        # 2) 竖直到操作线：Y_new = r * X_eq + intercept
        Y_new = r * X_eq + intercept
        stairs.append({"stage": N + 1, "type": "vertical", "X": X_eq, "Y": Y_new})

        # 更新状态
        X, Y = X_eq, Y_new
        N += 1

        # 3) 停止条件：竖直到操作线后的 Y 达到/超过底部气相入口 YF
        if Y >= YF - tol:
            break

        # 额外保护：防止异常大 X（定义/单位错误）
        if X > 1.0 + 1e-6:
            raise RuntimeError(
                f"X 已超过 1（X={X:.6g}），不合物理。请检查输入定义/单位（是否以摩尔分率而非摩尔比）。"
            )

    return stairs, N, X