import numpy as np
from core import VLEData, DistillationSpec
from core.optimizer import DistillationOptimizer
from core.distillation_column import DistillationColumn
from utils import create_result_folder, plot_optimization_results

# ========== 1️⃣ 数据输入 ==========
print("🧪 精馏系统优化分析")
print("-----------------------------------------------------")

# 基础物性与组成数据（可换为文件输入）
x_data = np.linspace(0, 0.98, 50)
y_data = np.array([0.000,0.135,0.235,0.311,0.372,0.421,0.463,0.499,0.529,0.556,
                   0.580,0.602,0.622,0.640,0.656,0.672,0.686,0.700,0.713,0.725,
                   0.737,0.748,0.759,0.769,0.779,0.789,0.799,0.808,0.817,0.826,
                   0.835,0.844,0.853,0.861,0.870,0.878,0.886,0.895,0.903,0.911,
                   0.919,0.927,0.936,0.944,0.952,0.960,0.968,0.976,0.984,0.992])

vle = VLEData(x_data, y_data)

# ========== 2️⃣ 用户输入基础规格 ==========
xF = float(input("请输入进料摩尔分数 xF (默认 0.48): ") or 0.48)
xD = float(input("请输入塔顶摩尔分数 xD (默认 0.90): ") or 0.90)
xW = float(input("请输入塔釜摩尔分数 xW (默认 0.01): ") or 0.01)
q = float(input("请输入进料热状态参数 q (默认 1.0): ") or 1.0)

# --- 新增部分：进料条件与Murphree效率设置 ---
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

# 构建规格对象
spec = DistillationSpec(
    xF=xF, q=q, xD=xD, xW=xW, R=0.0,
    consider_murphree=consider_murphree,
    EM_L=EM_L, EM_V=EM_V,
    mode="basic",
    feed_volume_L=feed_volume_L,
    feed_density_kg_per_L=feed_density_kg_per_L,
    MW_light=46.07, MW_heavy=18.015
)

# 创建结果文件夹
result_folder = create_result_folder("./results")

# 创建优化器对象
opt = DistillationOptimizer(spec, vle)

# ========== 3️⃣ 选择优化类型 ==========
print("\n请选择优化类型：")
print("1 - 计算最小回流比 Rmin")
print("2 - 给定塔板数求所需回流比 R")
print("3 - 经济优化（最优 Ropt 与 Nopt）")
print("4 - 全部执行")
choice = input("请输入编号 [1-4]: ").strip()

# ========== 4️⃣ 优化执行 ==========
if choice in ("1", "4"):
    # ---- 计算最小回流比 ----
    column = DistillationColumn(spec, vle)
    Rmin = column.compute_Rmin()
    print(f"\n📘 最小回流比 Rmin = {Rmin:.4f}")

if choice in ("2", "4"):
    # ---- 给定塔板数求 R ----
    N_target = int(input("\n请输入目标理论塔板数 N (默认 8): ") or 8)
    R_target, result_N = opt.find_R_for_N(N_target=N_target)
    print(f"🎯 当理论塔板数 N={N_target} 时，对应回流比 R = {R_target:.3f}")

if choice in ("3", "4"):
    # ---- 经济优化 ----
    a = float(input("\n请输入塔板成本系数 a (默认 1.0): ") or 1.0)
    b = float(input("请输入能耗成本系数 b (默认 5.0): ") or 5.0)
    opt_result = opt.economic_optimization(a=a, b=b)
    print(f"💰 最优经济操作点: R_opt={opt_result['R_opt']:.3f}, N_opt={opt_result['N_opt']}")
    plot_optimization_results(opt_result, result_folder)

print("\n✅ 优化分析完成，结果已保存至：", result_folder)