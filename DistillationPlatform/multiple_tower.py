# -*- coding: utf-8 -*-
"""
多塔串联精馏（最终版，无编号，补全首尾线）
----------------------------------------------------
特性：
- 完整的 McCabe–Thiele 理论阶梯（首尾都补全）
- q=1 情形（竖直 q 线）
- 上一塔塔底 → 下一塔进料
- 每塔独立输出 CSV / JSON / 图像
----------------------------------------------------
Author: AI4ChemEng
"""

import os, json, datetime
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d


# ==========================================================
# 工具函数
# ==========================================================
def create_result_folder(base="./results"):
    """创建带时间戳的输出文件夹"""
    t = datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    path = os.path.join(base, t)
    os.makedirs(path, exist_ok=True)
    return path


def make_interp_xy(x_data, y_data):
    """返回互为反函数的插值器 y*(x), x*(y)"""
    x_data = np.asarray(x_data)
    y_data = np.asarray(y_data)
    fy = interp1d(x_data, y_data, kind="cubic", fill_value="extrapolate")
    fx = interp1d(y_data, x_data, kind="cubic", fill_value="extrapolate")
    return fy, fx  # y* = fy(x), x* = fx(y)


def rectifying_line(R, xD):
    """精馏段操作线"""
    m = R / (R + 1.0)
    b = xD / (R + 1.0)
    return m, b


def stripping_line_from_intersection(xW, x_int, y_int):
    """提馏段操作线"""
    m = (y_int - xW) / (x_int - xW + 1e-12)
    b = xW - m * xW
    return m, b


# ==========================================================
# 理论阶梯（补全顶部和底部）
# ==========================================================
def step_off_theory(xD, xW_target, xF, R, fy, fx, consider_switch=True):
    """
    修正版 McCabe–Thiele 阶梯：
      - 水平段：x = fx(y)
      - 竖直段：y = 操作线(x)
      - 塔顶起点 (xD,xD)
      - 塔底补到 y=x 交点（不再画水平回勾）
    """
    mr, br = rectifying_line(R, xD)
    x_int = xF
    y_int = mr * x_int + br
    ms, bs = stripping_line_from_intersection(xW_target, x_int, y_int)

    X, Y = [], []
    y_curr = xD
    x_curr = fx(y_curr)
    X.append(x_curr)
    Y.append(y_curr)

    max_iter = 500
    count = 0

    while x_curr > xW_target + 1e-6 and count < max_iter:
        # 竖直段
        if (not consider_switch) or (x_curr >= x_int):
            y_next = mr * x_curr + br
        else:
            y_next = ms * x_curr + bs
        X.append(x_curr)
        Y.append(y_next)

        # 水平段
        x_next = float(fx(y_next))
        X.append(x_next)
        Y.append(y_next)

        x_curr, y_curr = x_next, y_next
        count += 1
        if x_curr <= xW_target + 1e-6:
            break

    # ✅ 只补竖直段到 y=x 交点（不再水平延伸）
    X.append(x_curr)
    Y.append(x_curr)

    # ✅ 塔顶补全
    X.insert(0, xD)
    Y.insert(0, xD)

    lines = (mr, br), (ms, bs), (None, None), (x_int, y_int)
    return np.array(X), np.array(Y), lines

# ==========================================================
# 绘图函数
# ==========================================================
def plot_MT(x_data, y_data, X_theory, Y_theory, lines, xF, save_path, title="McCabe–Thiele Diagram"):
    (mr, br), (ms, bs), (_, _), (x_int, y_int) = lines

    plt.figure(figsize=(7, 7))
    plt.title(title, fontsize=13)

    # 平衡线
    plt.plot(x_data, y_data, color="blue", lw=2.0, label="Equilibrium")
    # 对角线
    plt.plot([0, 1], [0, 1], "--", color="black", lw=1.0, label="y = x")
    # q=1竖线
    plt.axvline(x=xF, color="gray", ls="--", lw=1.2, label="q line (q=1)")
    # 精馏操作线
    xr = np.linspace(x_int, 1, 200)
    yr = mr * xr + br
    plt.plot(xr, yr, color="red", lw=1.6, label="Rectifying line")
    # 提馏操作线
    xs = np.linspace(0, x_int, 200)
    ys = ms * xs + bs
    plt.plot(xs, ys, color="green", lw=1.6, label="Stripping line")

    # 阶梯线
    plt.step(X_theory, Y_theory, where="post", color="orange", lw=2.0, label="Theoretical stages")

    # Feed交点
    plt.scatter([x_int], [y_int], color="red", s=35, zorder=5, label="Feed intersection")

    plt.xlabel("x (liquid mole fraction)")
    plt.ylabel("y (vapor mole fraction)")
    plt.xlim(0, 1)
    plt.ylim(0, 1)
    plt.legend(loc="upper left", fontsize=9)
    plt.grid(alpha=0.3)
    plt.tight_layout()
    plt.savefig(save_path, dpi=300)
    plt.close()
    print(f"📊 图已保存：{save_path}")


# ==========================================================
# 单塔计算
# ==========================================================
def run_one_column(name, xF, q, xD, xW, R, x_data, y_data, out_dir):
    assert abs(q - 1.0) < 1e-9, "当前脚本仅支持 q=1 情形（竖直 q 线）"

    fy, fx = make_interp_xy(x_data, y_data)

    Xth, Yth, lines = step_off_theory(
        xD=xD, xW_target=xW, xF=xF, R=R, fy=fy, fx=fx, consider_switch=True
    )

    df = pd.DataFrame({"x_theory": Xth, "y_theory": Yth})
    df.to_csv(os.path.join(out_dir, f"{name}_results.csv"), index=False)

    (mr, br), (ms, bs), (_, _), (x_int, y_int) = lines
    summary = {
        "name": name,
        "xF": xF, "xD": xD, "xW_target": xW,
        "R": R,
        "feed_intersection": {"x": x_int, "y": y_int},
        "stages_theory": int(len(Xth) // 2),
        "achieved_xW": float(Xth[-1]),
    }
    with open(os.path.join(out_dir, f"{name}_summary.json"), "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    plot_MT(
        x_data, y_data, Xth, Yth, lines, xF,
        save_path=os.path.join(out_dir, f"{name}.png"),
        title=f"McCabe–Thiele Diagram - {name}"
    )

    return summary


# ==========================================================
# 多塔串联主流程
# ==========================================================
if __name__ == "__main__":
    # VLE 数据
    x_data = np.linspace(0, 0.98, 50)
    y_data = np.array([
        0.000, 0.135, 0.235, 0.311, 0.372, 0.421, 0.463, 0.499, 0.529, 0.556,
        0.580, 0.602, 0.622, 0.640, 0.656, 0.672, 0.686, 0.700, 0.713, 0.725,
        0.737, 0.748, 0.759, 0.769, 0.779, 0.789, 0.799, 0.808, 0.817, 0.826,
        0.835, 0.844, 0.853, 0.861, 0.870, 0.878, 0.886, 0.895, 0.903, 0.911,
        0.919, 0.927, 0.936, 0.944, 0.952, 0.960, 0.968, 0.976, 0.984, 0.992
    ])

    out_dir = create_result_folder("./results")
    print(f"🚀 启动多塔串联精馏计算，结果保存至：{out_dir}")

    towers = [
        dict(name="Tower_1", xF=0.48, q=1.0, xD=0.90, xW=0.3, R=0.6),
        dict(name="Tower_2", xF=0.00, q=1.0, xD=0.90, xW=0.15, R=0.9),
        dict(name="Tower_3", xF=0.00, q=1.0, xD=0.90, xW=0.01, R=2.5),
    ]

    for i, T in enumerate(towers):
        print(f"\n🧱 正在计算第 {i+1} 塔：{T['name']} ...")
        summ = run_one_column(
            name=T["name"], xF=T["xF"], q=T["q"], xD=T["xD"], xW=T["xW"], R=T["R"],
            x_data=x_data, y_data=y_data, out_dir=out_dir
        )

        # 串联：塔底 -> 下一塔进料
        if i < len(towers) - 1:
            towers[i + 1]["xF"] = summ["achieved_xW"]
            print(f"➡️ 塔底组成传递：{T['name']} → {towers[i+1]['name']}，xF(next) = {summ['achieved_xW']:.4f}")

    print("\n✅ 全部塔计算完成！输出文件夹：", out_dir)

        # ==========================================================
    # 🧭 多塔系统优化建议（基于相平衡数据）
    # ==========================================================
    print("\n🧭 多塔系统优化建议分析（基于相平衡与操作参数）")
    print("--------------------------------------------------")

    # 曲线形态分析
    dy_dx = np.gradient(y_data, x_data)
    curvature = np.gradient(dy_dx, x_data)
    curvature_mean = np.mean(np.abs(curvature))
    equilibrium_steepness = np.mean(dy_dx)

    fy, fx = make_interp_xy(x_data, y_data)

    # 分析曲线难分离程度
    if equilibrium_steepness > 0.85:
        sep_difficulty = "hard"
        curve_msg = "相平衡曲线接近 y=x，属于难分离体系。"
    elif equilibrium_steepness < 0.6:
        sep_difficulty = "easy"
        curve_msg = "相平衡曲线弯曲明显，为易分离体系。"
    else:
        sep_difficulty = "moderate"
        curve_msg = "体系分离中等。"

    print(f"📈 {curve_msg} 平均斜率 = {equilibrium_steepness:.3f}")

    # 汇总各塔信息
    summaries = []
    for T in towers:
        try:
            with open(os.path.join(out_dir, f"{T['name']}_summary.json"), "r", encoding="utf-8") as f:
                summaries.append(json.load(f))
        except Exception as e:
            print(f"⚠️ 无法读取 {T['name']} 结果：{e}")

    for i, s in enumerate(summaries):
        name = s["name"]
        xF = s["xF"]
        xD = s["xD"]
        xW_target = s["xW_target"]
        xW_actual = s.get("achieved_xW", xW_target)
        R = s["R"]
        N = s["stages_theory"]

        Δx = xD - xW_actual
        purity_ratio = (xD - xW_actual) / max(1e-6, (xD - xF))

        print(f"\n🔹 {name} 分析：")
        print(f"   ➤ 回流比 R = {R:.2f}, 理论板数 = {N}, Δx = {Δx:.3f}")

        # 1️⃣ 回流比建议
        # 估算 Rmin（基于平衡线交点近似）
        yF = fy(xF)
        Rmin_est = (xD - yF) / (yF - xF + 1e-8)
        if R < 1.2 * Rmin_est:
            print(f"   ⚠️ 当前回流比低于 1.2×Rmin ({R:.2f} < {1.2*Rmin_est:.2f})，建议适当提高回流比以确保分离。")
        elif R > 2.0 * Rmin_est:
            print(f"   💡 当前回流比远高于需求 ({R:.2f} > {2.5*Rmin_est:.2f})，建议降低回流比以节能。")
        else:
            print("   ✅ 回流比适中，能量利用合理。")

        # 2️⃣ 分离效率分析
        if Δx < 0.2 and N > 30:
            print("   ⚠️ 分离效果偏弱，体系难分离或塔板效率低，考虑提高回流或采用萃取精馏。")
        elif Δx > 0.4 and R > 1.0:
            print("   💡 分离强度较高，可尝试小幅降低 R 以节能。")
        else:
            print("   ✅ 分离效果与操作条件匹配。")

        # 3️⃣ 相平衡特性结合
        if sep_difficulty == "hard" and R < 1.5 * Rmin_est:
            print("   ⚠️ 难分离体系但回流比偏低，建议增加 R 或采用中间冷凝器。")
        elif sep_difficulty == "easy" and R > 2.0 * Rmin_est:
            print("   💡 易分离体系可降低回流比，减少能耗。")

        # 4️⃣ 塔间衔接分析
        if i < len(summaries) - 1:
            next_xF = summaries[i+1]["xF"]
            diff = abs(xW_actual - next_xF)
            if diff > 0.05:
                print(f"   ⚠️ 与下一塔衔接差值较大 (Δx={diff:.3f})，建议调整中间取样点或再沸比。")
            else:
                print("   ✅ 塔间衔接平稳。")

    print("\n--------------------------------------------------")
    print("💡 提示：以上建议综合考虑了相平衡数据曲线形态与回流操作参数，")
    print("         可作为优化精馏系统（R值、塔板数、能耗）的初步依据。")