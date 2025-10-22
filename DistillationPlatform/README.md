# DistillationPlatform

> **AI4ChemEng 精馏设计与优化平台**  
> 一款用于化工原理教学与工业流程设计的精馏计算与优化平台。  
> 支持普通精馏、共沸精馏、萃取精馏、多效精馏，以及塔设计优化。

---

## 功能概述

| 模块类型 | 模块名称 | 功能 |
|-----------|-----------|------|
| 基础精馏 | `core/distillation_column.py` | 逐级计算理论与实际塔板，输出 McCabe–Thiele 图 |
| 共沸/萃取精馏 | `core/special_models.py` | 修改气液平衡 (VLE) 模拟共沸或萃取体系 |
| 多效精馏 | `core/multiple_effect.py` | 模拟多塔串联的热耦合精馏过程 |
| 优化分析 | `core/optimizer.py` | 提供最小回流比、给定塔板数求回流比、经济优化等 |
| 可视化 | `utils/plotting.py` | 绘制 McCabe–Thiele 图与经济优化曲线 |
| 文件管理 | `utils/file_utils.py` | 自动创建时间戳结果文件夹 |
| 主程序入口 | `main.py` | 选择运行普通、共沸、萃取或多效精馏 |
| 优化入口 | `optimize.py` | 交互式优化主程序，支持 Rmin、R(N)、经济优化分析 |

---

## 文件结构

```text
DistillationPlatform/
│
├── main.py                         # 主入口：普通/共沸/萃取/多效精馏
├── optimize.py                     # 设计优化入口（交互式）
├── requirements.txt                # 依赖包声明
│
├── core/
│   ├── __init__.py
│   ├── spec.py                     # 精馏参数对象（DistillationSpec）
│   ├── vle_data.py                 # 气液平衡数据插值
│   ├── distillation_column.py      # 精馏塔逐级计算
│   ├── engine.py                   # 运行与结果导出控制
│   ├── special_models.py           # 共沸/萃取模型修饰
│   ├── multiple_effect.py          # 多效精馏模型
│   └── optimizer.py                # 设计与优化算法
│
├── utils/
│   ├── __init__.py
│   ├── plotting.py                 # 绘图（McCabe–Thiele、经济优化）
│   ├── file_utils.py               # 结果目录创建
│   ├── export.py                   # 结果导出工具
│
└── results/
    └── [timestamp]/
        ├── results.csv
        ├── summary.json
        ├── mccabe_thiele.png
        ├── R_vs_N.png
        └── economic_opt.png
```

---

## 安装环境

```bash
# 创建虚拟环境（推荐使用 conda）
conda create -n AI4ChemEng python=3.9
conda activate AI4ChemEng

# 安装依赖
pip install -r requirements.txt
```

**requirements.txt**

```text
numpy>=1.24
pandas>=2.0
matplotlib>=3.7
```

---

## 快速开始

### 运行基础精馏

```bash
python main.py
```

运行后在终端中交互输入：

```
🧪 请选择运行模式：
1 - 基础精馏 (basic)
2 - 共沸精馏 (azeotropic)
3 - 萃取精馏 (extractive)
4 - 多效精馏 (multiple)
```

根据提示输入参数（如 xF, q, R 等），程序将自动：

- 计算操作线、理论与实际塔板；
- 输出表格结果；
- 绘制 McCabe–Thiele 图；
- 保存结果至 `results/` 文件夹。

生成结果示例：

```
results/2025-10-22_16-45-12/
├── results.csv
├── summary.json
└── mccabe_thiele.png
```

---

### 运行设计优化

```bash
python optimize.py
```

终端交互：

```
精馏系统优化分析
-----------------------------------------------------
请输入进料摩尔分数 xF (默认 0.48):
请输入塔顶摩尔分数 xD (默认 0.90):
请输入塔釜摩尔分数 xW (默认 0.01):
请输入进料热状态 q (默认 1.0):

请选择优化类型：
1 - 计算最小回流比 Rmin
2 - 给定塔板数求所需回流比
3 - 经济优化（最优 Ropt 与 Nopt）
4 - 全部执行
```

输出示例：

```
最小回流比 Rmin = 0.4047
当理论塔板数 N=8 时，对应回流比 R = 0.982
最优经济操作点: R_opt=1.233, N_opt=10
已生成优化图：R_vs_N.png 与 economic_opt.png
优化分析完成，结果已保存至 ./results/2025-10-22_16-45-12
```

---

## 输出文件说明

| 文件名 | 说明 |
|--------|------|
| **results.csv** | 各级理论与实际塔板的浓度、操作线段信息 |
| **summary.json** | 汇总计算参数（R、效率类型、板数、达标情况） |
| **mccabe_thiele.png** | McCabe–Thiele 精馏图 |
| **R_vs_N.png** | 回流比与理论塔板数关系图 |
| **economic_opt.png** | 总成本与回流比关系图 |

---

## 工程背景与设计原理

| 模块 | 理论依据 | 说明 |
|------|-----------|------|
| **Rmin 计算** | McCabe–Thiele 图法与操作线交点 | 自动求最小回流比 |
| **Murphree 效率** | 实际塔板与理论塔板修正关系 | 支持液相与气相效率 |
| **多效精馏** | 热力学第二定律：能量梯级利用 | 多塔串联节能模型 |
| **经济优化** | 成本函数 \$begin:math:text$C = aN + bQ(R)\\$end:math:text$ | 平衡塔板数与能耗，求最优 R |
| **共沸/萃取精馏** | 改变相对挥发度或扰动平衡曲线 | 修改 VLE 模型实现 |

---

## 可扩展方向

- **Gilliland 经验关联图**：绘制 \$begin:math:text$N/N_{min}\\$end:math:text$ 与 \$begin:math:text$R/R_{min}\\$end:math:text$ 的经验曲线  
- **自动调节回流比**：迭代使产品纯度达到指定要求  
- **多目标优化**：同时最小化能耗与设备成本  
- **图形界面 GUI**：通过 PyQt / Tkinter 实现可视化操作  
- **批量参数运行**：读取配置文件自动化运行多组计算  

---

## 理论图示

**McCabe–Thiele Diagram**

![McCabe–Thiele Diagram](docs/mccabe_thiele_example.png)

**Economic Optimization**

![Economic Optimization](docs/economic_opt_example.png)

> 注：如无 `docs/` 文件夹，可忽略以上图示。

---

## 示例运行日志

```text
精馏系统优化分析
-----------------------------------------------------
请输入进料摩尔分数 xF (默认 0.48):
请输入塔顶摩尔分数 xD (默认 0.90):
请输入塔釜摩尔分数 xW (默认 0.01):
请输入进料热状态 q (默认 1.0):
最小回流比 Rmin = 0.4047
当理论塔板数 N=8 时，对应回流比 R = 0.982
最优经济操作点: R_opt=1.233, N_opt=10
已生成优化图：R_vs_N.png 与 economic_opt.png
优化分析完成，结果已保存至 ./results/2025-10-22_16-45-12
```

---

## 👨作者与项目背景

**Author:** Zhen-Ning Guo, Kun Xu, Yu-Kai Liang
**Organization:** AI4ChemEng Project  
**Year:** 2025  

本项目旨在为化工原理课程与科研提供开源、透明、可扩展的精馏计算与优化平台。

> *“Engineering is not just calculation — it’s design thinking.”*

---

## License

本项目遵循 **MIT License**，可自由使用、修改与扩展。  
若在科研或教学中使用，请引用：

> Zhen-Ning Guo, Kun Xu, Yu-Kai Liang. *AI4ChemEng: An Open Distillation Design and Optimization Platform (2025)*.