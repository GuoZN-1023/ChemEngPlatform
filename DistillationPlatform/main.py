import os
import csv
import json
import numpy as np
from core import VLEData, DistillationSpec, DistillationEngine
from core.special_models import azeotropic_modifier, extractive_modifier
from core.multiple_effect import MultiEffectSystem
from utils import create_result_folder, save_results, plot_mccabe_thiele


# ========== 1️⃣ 模式选择 ==========
print("🧪 请选择运行模式：")
print("1 - 基础精馏 (basic)")
print("2 - 共沸精馏 (azeotropic)")
print("3 - 萃取精馏 (extractive)")
print("4 - 多效精馏 (multiple)")
mode_choice = input("请输入数字选择模式 [1-4]: ").strip()

if mode_choice == "1":
    mode = "basic"
elif mode_choice == "2":
    mode = "azeotropic"
elif mode_choice == "3":
    mode = "extractive"
elif mode_choice == "4":
    mode = "multiple"
else:
    print("⚠️ 输入无效，默认使用基础精馏。")
    mode = "basic"


# ========== 2️⃣ 气液平衡输入方式 ==========
print("\n📊 请选择气液平衡数据来源：")
print("1 - 实验数据 (输入或读取 x-y 数据)")
print("2 - 理论模型 (仅输入相对挥发度 α；自动生成 y = αx / [1+(α−1)x])")
vle_choice = input("请输入数字选择 [1/2]: ").strip()

if vle_choice == "1":
    print("\n✅ 使用实验数据模式（默认样例数据）")
    x_data = np.array([0.000, 0.020, 0.040, 0.060, 0.080, 0.100, 0.120, 0.140, 0.160, 0.180,
                       0.200, 0.220, 0.240, 0.260, 0.280, 0.300, 0.320, 0.340, 0.360, 0.380,
                       0.400, 0.420, 0.440, 0.460, 0.480, 0.500, 0.520, 0.540, 0.560, 0.580,
                       0.600, 0.620, 0.640, 0.660, 0.680, 0.700, 0.720, 0.740, 0.760, 0.780,
                       0.800, 0.820, 0.840, 0.860, 0.880, 0.900, 0.920, 0.940, 0.960, 0.980])
    y_data = np.array([0.000, 0.135, 0.235, 0.311, 0.372, 0.421, 0.463, 0.499, 0.529, 0.556,
                       0.580, 0.602, 0.622, 0.640, 0.656, 0.672, 0.686, 0.700, 0.713, 0.725,
                       0.737, 0.748, 0.759, 0.769, 0.779, 0.789, 0.799, 0.808, 0.817, 0.826,
                       0.835, 0.844, 0.853, 0.861, 0.870, 0.878, 0.886, 0.895, 0.903, 0.911,
                       0.919, 0.927, 0.936, 0.944, 0.952, 0.960, 0.968, 0.976, 0.984, 0.992])
    vle = VLEData(x_data, y_data)
    vle_source = "experimental"

else:
    # 只输入 α 的理论 Raoult 形式： y = αx / [1+(α−1)x]
    print("\n🧠 理论气液平衡模型（Raoult 形式）：y = α·x / [1 + (α - 1)x]")
    alpha = float(input("请输入相对挥发度 α (默认 1.5): ") or 1.5)
    print(f"✅ 已选择 α = {alpha:.3f}")

    def y_theory(x):
        return alpha * x / (1.0 + (alpha - 1.0) * x)

    x_data = np.linspace(0.0, 1.0, 50)
    y_data = np.clip([y_theory(x) for x in x_data], 0.0, 1.0)
    vle = VLEData(x_data, y_data)
    vle_source = "theoretical"
    # 记录理论方程，便于写入 JSON
    eq_theory_str = f"y = {alpha:.6f}·x / [1 + ({alpha:.6f} - 1)·x]"


# ========== 3️⃣ 参数输入 ==========
if mode != "multiple":
    xF = float(input("请输入进料摩尔分数 xF (默认 0.48): ") or 0.48)
    xD = float(input("请输入塔顶摩尔分数 xD (默认 0.90): ") or 0.90)
    xW = float(input("请输入塔釜摩尔分数 xW (默认 0.01): ") or 0.01)
    q = float(input("请输入进料热状态参数 q (默认 1.0): ") or 1.0)
    R = float(input("请输入回流比 R (输入 0 则自动计算，默认 0.6): ") or 0.6)

    feed_volume_L = float(input("请输入进料体积 (L) (默认 100): ") or 100)
    feed_density_kg_per_L = float(input("请输入进料密度 (kg/L) (默认 0.95): ") or 0.95)

    # （已按你的要求删除轻/重组分摩尔体积输入）
    murphree_choice = input("是否考虑Murphree效率? (y/n, 默认 n): ").strip().lower() or "n"
    if murphree_choice == "y":
        consider_murphree = True
        em_type = input("请输入效率类型 ('L' 表示液相, 'V' 表示气相, 默认 'L'): ").strip().upper() or "L"
        em_value = float(input(f"请输入{'液相' if em_type == 'L' else '气相'}Murphree效率 (0~1, 默认 0.7): ") or 0.7)
        EM_L = em_value if em_type == "L" else None
        EM_V = em_value if em_type == "V" else None
    else:
        consider_murphree = False
        EM_L = EM_V = None
else:
    print("\n多效精馏模式：自动构建两个串联塔参数。\n")


# ========== 4️⃣ 模式分支处理 ==========
result_folder = create_result_folder("./results")

def compute_operating_lines(xF, xD, xW, q, R, x_for_fit, y_for_fit, vle_source, alpha=None):
    """
    返回：操作线/平衡线方程（斜率+截距+字符串），以及 q 线交点
    """
    # 精馏段 (rectifying): y = (R/(R+1)) x + xD/(R+1)
    m_rect = R / (R + 1.0)
    b_rect = xD / (R + 1.0)

    # ——几何点法：求 q 线与精馏段交点，再与 (xW, xW) 确定提馏段——
    eps = 1e-12
    if abs(q - 1.0) < eps:
        x_q = xF
        y_q = m_rect * x_q + b_rect
    else:
        m_q = q / (q - 1.0)
        b_q = -xF / (q - 1.0)
        if abs(m_rect - m_q) < eps:
            x_q = xF
            y_q = m_rect * x_q + b_rect
        else:
            x_q = (b_q - b_rect) / (m_rect - m_q)
            y_q = m_rect * x_q + b_rect

    if abs(x_q - xW) < eps:
        m_strip = 1.0
        b_strip = 0.0
    else:
        m_strip = (y_q - xW) / (x_q - xW)
        b_strip = y_q - m_strip * x_q

    # 平衡线摘要（实验拟合或理论式）
    if vle_source == "theoretical" and alpha is not None:
        eq_label = f"y = {alpha:.6f}·x / [1 + ({alpha:.6f} - 1)·x]"
        m_eq = None
        b_eq = None
    else:
        coeff = np.polyfit(x_for_fit, y_for_fit, 1)
        m_eq, b_eq = float(coeff[0]), float(coeff[1])
        eq_label = f"y = {m_eq:.6f} x + {b_eq:.6f}"

    return {
        "rectifying": {"m": m_rect, "b": b_rect, "eq": f"y = {m_rect:.6f} x + {b_rect:.6f}"},
        "stripping":  {"m": m_strip, "b": b_strip, "eq": f"y = {m_strip:.6f} x + {b_strip:.6f}"},
        "equilibrium":{"m": m_eq, "b": b_eq, "eq": eq_label},
        "q_intersection": {"xq": x_q, "yq": y_q}
    }

def write_streams_table_csv(folder, xF, xD, xW, basis_F=1.0):
    """
    以 F=basis_F (kmol/h) 为基准输出进料/塔顶/塔釜的总量与组分（横向格式）。
    """
    F = float(basis_F)
    if abs(xD - xW) < 1e-12:
        raise ValueError("xD 与 xW 过于接近，无法解出 D/B。")

    D = (xF - xW) / (xD - xW) * F
    B = F - D

    light = {"F": xF * F, "D": xD * D, "B": xW * B}
    heavy = {"F": (1 - xF) * F, "D": (1 - xD) * D, "B": (1 - xW) * B}

    path = os.path.join(folder, "streams_table.csv")
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["", "进料", "塔顶采出", "塔釜采出"])
        w.writerow(["总流量 (kmol/h)", f"{F:.6f}", f"{D:.6f}", f"{B:.6f}"])
        w.writerow(["轻组分 (kmol/h)", f"{light['F']:.6f}", f"{light['D']:.6f}", f"{light['B']:.6f}"])
        w.writerow(["重组分 (kmol/h)", f"{heavy['F']:.6f}", f"{heavy['D']:.6f}", f"{heavy['B']:.6f}"])

    return {"F": F, "D": D, "B": B, "light": light, "heavy": heavy, "csv": path}

# === 新增：生成精馏塔物流表（与截图一致） ===
# === 新版：精馏塔物流表（与截图一致；仅用进料体积与浓度） ===
def write_distillation_mass_table(folder, xF, xD, xW, feed_volume_L, feed_density_kg_per_L):
    """
    仅基于进料体积 feed_volume_L（直接视为总摩尔流量 F, 单位 kmol/h）与 xF/xD/xW，
    自动计算 D/B 及各股甲醇/CO2/水的摩尔流量，并输出 distillation_mass_table.csv。
    说明：为与示例保持一致，忽略密度，不做质量到摩尔的换算。
    """
    # 1) 以“进料体积”直接作为 F（kmol/h 基准）
    F = float(feed_volume_L)

    # 2) 由摩尔守恒解出 D/B
    eps = 1e-12
    if abs(xD - xW) < eps:
        raise ValueError("xD 与 xW 过于接近，无法解出 D/B。")
    D = (xF - xW) / (xD - xW) * F
    B = F - D

    # 3) 组分分配（按你的示例：甲醇为轻组分，水为重组分；精馏塔不含惰性 CO2）
    methanol = {"F": xF * F, "D": xD * D, "B": xW * B}
    water    = {"F": (1 - xF) * F, "D": (1 - xD) * D, "B": (1 - xW) * B}
    co2      = {"F": 0.0, "D": 0.0, "B": 0.0}  # 精馏塔场景无惰性

    # 4) 写出与截图完全一致的横向表格
    path = os.path.join(folder, "distillation_mass_table.csv")
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["精馏塔", "进料", "塔顶采出", "塔釜采出"])
        w.writerow(["总流量 (kmol/h)",      f"{F:.2f}",           f"{D:.2f}",           f"{B:.2f}"])
        w.writerow(["甲醇流量 (kmol/h)",    f"{methanol['F']:.2f}", f"{methanol['D']:.2f}", f"{methanol['B']:.2f}"])
        w.writerow(["CO₂流量 (kmol/h)",     f"{co2['F']:.2f}",     f"{co2['D']:.2f}",     f"{co2['B']:.2f}"])
        w.writerow(["水流量 (kmol/h)",      f"{water['F']:.2f}",   f"{water['D']:.2f}",   f"{water['B']:.2f}"])

    print(f"📘 已生成精馏塔物流表: {path}")
    return {"F": F, "D": D, "B": B, "methanol": methanol, "water": water, "co2": co2, "path": path}


if mode == "basic":
    spec = DistillationSpec(
        xF=xF, q=q, xD=xD, xW=xW, R=R,
        consider_murphree=consider_murphree,
        EM_L=EM_L, EM_V=EM_V,
        mode="basic",
        feed_volume_L=feed_volume_L,
        feed_density_kg_per_L=feed_density_kg_per_L,
        MW_light=46.07, MW_heavy=18.015
    )
    engine = DistillationEngine(spec, vle)
    result = engine.run(result_folder)
    save_results(result, result_folder)
    plot_mccabe_thiele(result, vle, result_folder)

    # 方程&物流摘要
    alpha_used = alpha if vle_choice == "2" else None
    oplines = compute_operating_lines(xF, xD, xW, q, R, vle.x, vle.y, vle_source, alpha_used)
    streams_meta = write_streams_table_csv(result_folder, xF, xD, xW, basis_F=1.0)

    with open(os.path.join(result_folder, "summary_oplines.json"), "w", encoding="utf-8") as f:
        json.dump({
            "vle_source": vle_source,
            "theoretical_alpha": alpha_used,
            "operating_lines": oplines,
            "streams_basis_F": streams_meta
        }, f, indent=2, ensure_ascii=False)

    # 新增：生成与截图一致的精馏物流表（由进料体积/浓度自动计算）
    write_distillation_mass_table(result_folder, xF, xD, xW, feed_volume_L, feed_density_kg_per_L)

    print(f"✅ 基础精馏计算完成，结果已保存至：{result_folder}")

elif mode == "azeotropic":
    azeo_x = float(input("请输入共沸点液相组成 azeo_x (默认 0.65): ") or 0.65)
    azeo_y = float(input("请输入共沸点气相组成 azeo_y (默认 0.65): ") or 0.65)
    strength = float(input("请输入扰动强度（负值打破共沸，默认 -0.05）: ") or -0.05)
    vle = azeotropic_modifier(vle, azeo_x, azeo_y, strength)

    spec = DistillationSpec(
        xF=xF, q=q, xD=xD, xW=xW, R=R,
        consider_murphree=consider_murphree,
        EM_L=EM_L, EM_V=EM_V,
        mode="azeotropic",
        feed_volume_L=feed_volume_L,
        feed_density_kg_per_L=feed_density_kg_per_L
    )
    engine = DistillationEngine(spec, vle)
    result = engine.run(result_folder)
    save_results(result, result_folder)
    plot_mccabe_thiele(result, vle, result_folder)

    alpha_used = alpha if (vle_choice == "2") else None
    oplines = compute_operating_lines(xF, xD, xW, q, R, vle.x, vle.y, vle_source, alpha_used)
    streams_meta = write_streams_table_csv(result_folder, xF, xD, xW, basis_F=1.0)
    with open(os.path.join(result_folder, "summary_oplines.json"), "w", encoding="utf-8") as f:
        json.dump({
            "vle_source": vle_source,
            "theoretical_alpha": alpha_used,
            "operating_lines": oplines,
            "streams_basis_F": streams_meta
        }, f, indent=2, ensure_ascii=False)

    write_distillation_mass_table(result_folder, xF, xD, xW, feed_volume_L, feed_density_kg_per_L)

    print(f"✅ 共沸精馏计算完成，结果已保存至：{result_folder}")

elif mode == "extractive":
    solvent_ratio = float(input("请输入溶剂比例 S/F (默认 0.2): ") or 0.2)
    alpha_factor = float(input("请输入挥发度放大系数 (默认 1.3): ") or 1.3)
    vle = extractive_modifier(vle, solvent_ratio=solvent_ratio, alpha_factor=alpha_factor)

    spec = DistillationSpec(
        xF=xF, q=q, xD=xD, xW=xW, R=R,
        consider_murphree=consider_murphree,
        EM_L=EM_L, EM_V=EM_V,
        mode="extractive",
        feed_volume_L=feed_volume_L,
        feed_density_kg_per_L=feed_density_kg_per_L
    )
    engine = DistillationEngine(spec, vle)
    result = engine.run(result_folder)
    save_results(result, result_folder)
    plot_mccabe_thiele(result, vle, result_folder)

    alpha_used = alpha if (vle_choice == "2") else None
    oplines = compute_operating_lines(xF, xD, xW, q, R, vle.x, vle.y, vle_source, alpha_used)
    streams_meta = write_streams_table_csv(result_folder, xF, xD, xW, basis_F=1.0)
    with open(os.path.join(result_folder, "summary_oplines.json"), "w", encoding="utf-8") as f:
        json.dump({
            "vle_source": vle_source,
            "theoretical_alpha": alpha_used,
            "operating_lines": oplines,
            "streams_basis_F": streams_meta
        }, f, indent=2, ensure_ascii=False)

    write_distillation_mass_table(result_folder, xF, xD, xW, feed_volume_L, feed_density_kg_per_L)

    print(f"✅ 萃取精馏计算完成，结果已保存至：{result_folder}")

elif mode == "multiple":
    from core.vle_data import VLEData
    print("👉 构建两个串联塔：第一效高压，第二效低压。")

    spec1 = DistillationSpec(xF=0.48, q=1.0, xD=0.90, xW=0.05, R=1.5, consider_murphree=True, EM_L=0.75)
    spec2 = DistillationSpec(xF=0.30, q=1.0, xD=0.85, xW=0.02, R=1.2, consider_murphree=True, EM_L=0.75)

    vle1 = VLEData(x_data, y_data)
    vle2 = VLEData(x_data, y_data)
    system = MultiEffectSystem([spec1, spec2], [vle1, vle2], heat_efficiency=0.85)
    results = system.run(result_folder)

    for r in results:
        print(f"塔 {r['tower_index']}: R={r['R_used']:.2f}, 有效热负荷={r['energy_load']:.3f}")

    print(f"✅ 多效精馏系统计算完成，结果已保存至：{result_folder}")

else:
    print("⚠️ 模式未识别，程序结束。")