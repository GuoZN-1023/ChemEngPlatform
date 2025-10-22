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

# ========== 2️⃣ 数据输入 ==========
x_data = np.linspace(0, 0.98, 50)
y_data = np.array([0.000, 0.135, 0.235, 0.311, 0.372, 0.421, 0.463, 0.499, 0.529, 0.556,
                   0.580, 0.602, 0.622, 0.640, 0.656, 0.672, 0.686, 0.700, 0.713, 0.725,
                   0.737, 0.748, 0.759, 0.769, 0.779, 0.789, 0.799, 0.808, 0.817, 0.826,
                   0.835, 0.844, 0.853, 0.861, 0.870, 0.878, 0.886, 0.895, 0.903, 0.911,
                   0.919, 0.927, 0.936, 0.944, 0.952, 0.960, 0.968, 0.976, 0.984, 0.992])

vle = VLEData(x_data, y_data)

# ========== 3️⃣ 参数输入 ==========
if mode != "multiple":
    xF = float(input("请输入进料摩尔分数 xF (默认 0.48): ") or 0.48)
    xD = float(input("请输入塔顶摩尔分数 xD (默认 0.90): ") or 0.90)
    xW = float(input("请输入塔釜摩尔分数 xW (默认 0.01): ") or 0.01)
    q = float(input("请输入进料热状态参数 q (默认 1.0): ") or 1.0)
    R = float(input("请输入回流比 R (输入 0 则自动计算，默认 0.6): ") or 0.6)

    # --- 新增部分：进料体积、密度、Murphree效率输入 ---
    feed_volume_L = float(input("请输入进料体积 (L) (默认 100): ") or 100)
    feed_density_kg_per_L = float(input("请输入进料密度 (kg/L) (默认 0.95): ") or 0.95)

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