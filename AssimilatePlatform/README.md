# AssimilatePlatform — 气体吸收计算与可视化平台

> **AI4ChemEng Submodule**  
> 一款基于 Python 的自动化气体吸收计算平台，支持 McCabe–Thiele 图形化分析、气液流量计算与数据导出。  
> 可应用于化工原理课程、传递过程实验及工业吸收塔初步设计。

---

## 🚀 功能概述 / Features Overview

| 模块类型 | 模块路径 | 功能描述 |
|-----------|-----------|-----------|
| 主程序入口 | `main.py` | 参数输入、结果输出、可视化与数据导出 |
| 核心计算模块 | `core/runner.py` | 逐级吸收过程模拟、气液平衡计算 |
| 数据处理 | `utils/io_utils.py` | CSV 与 JSON 文件读写 |
| 可视化模块 | `utils/plot_mt.py` | McCabe–Thiele 吸收图绘制 |
| 文件管理 | `utils/logger.py` | 自动创建结果文件夹（带时间戳） |
| 输出文件 | `results/[timestamp]/` | 含 log.txt, mt_plot.png, stage_data.csv, stage_table.csv, streams_table.csv, streams.csv, summary.json |

---

## 📁 文件结构 / Directory Layout

```text
AssimilatePlatform/
├── main.py

├── core/
│   ├── __init__.py
│   ├── runner.py
│   ├── streams.py
│   ├── equilibrium.py
│   ├── stagewise.py
│   ├── kremser.py

├── utils/
│   ├── __init__.py
│   ├── io_utils.py
│   ├── logger.py
│   ├── plot_mt.py
│
├── results/
│   └── 2025-11-07_10-30-00/     # 自动生成的实验结果
│       ├── stage_table.csv
│       ├── streams_table.csv
│       ├── summary.json
│       └── absorption_plot.png
│
└── requirements.txt
```

---

## ⚙️ 安装环境 / Installation

推荐使用 Python ≥ 3.10 环境：

```bash
conda create -n assimilate python=3.10
conda activate assimilate
pip install -r requirements.txt
```

### 🧾 requirements.txt 内容

```text
numpy>=1.26.0
scipy>=1.11.0
matplotlib>=3.8.0
pandas>=2.1.0
seaborn>=0.13.0
plotly>=5.20.0
openpyxl>=3.1.2
python-docx>=1.1.0
PyYAML>=6.0.1
```

---

## 📈 可视化结果 / Visualization

程序自动绘制 **McCabe–Thiele 吸收图**：
生成文件示例：

```text
results/2025-11-07_10-30-00/
├── stage_table.csv        # 各级板气液浓度与流量数据
├── streams_table.csv      # 进气、出气、吸收液物流汇总表
├── summary.json           # 吸收过程摘要（平衡参数、操作线方程等）
└── absorption_plot.png    # McCabe–Thiele 吸收图
```

---

## 🧠 运行说明 / How to Run

在终端运行主程序：

```bash
python main.py
```

根据提示依次输入：

```
=== Interactive Absorption Inputs ===
▶ 平衡线斜率 m (Y*=mX) (default 0.4): 1
▶ 气体入口溶质摩尔比 YF (default 0.04): 0.04
▶ 气体出口目标摩尔比 YN_target (default 0.002): 0.002
▶ 吸收剂入口摩尔比 X0 (default 0.002): 0.001
▶ 气体流量 V (kmol/h) (default 100.0): 100
▶ 吸收剂流量 L (kmol/h, 0 表示自动 = 1.5×Lmin) (default 0.0): 150
▶ L_factor (L=Lmin×factor) (default 1.5): 
▶ HETP (m/理论级) (default 0.5): 
▶ 最大步数上限 max_stages_cap (default 300): 
▶ 案例名称 case_name (默认 interactive_case): 
▶ 备注 notes: 
▶ 是否绘制 M–T 图？(y/n, 默认 y): y
```

随后输入进气与液体流量、进出口浓度等参数，程序会自动：

1. 计算各级气液平衡与操作线；
2. 输出 CSV 与 JSON 文件；
3. 绘制吸收曲线图；
4. 自动创建结果文件夹。

---

## 📘 示例输出 / Example Output

```
✅ Absorption complete. Results saved to: results/20251107-153222_interactive_case
{
  "case_name": "interactive_case",
  "inputs": {
    "m": 1.0,
    "YF": 0.04,
    "YN": 0.002,
    "X0": 0.001,
    "V": 100.0,
    "L": 150.0,
    "L_factor": 1.5,
    "HETP": 0.5,
    "max_stages_cap": 300,
    "plot": true
  },
  "results": {
    "Lmin": 97.43589743589743,
    "L_used": 150.0,
    "N_stair": 7,
    "N_kremser": 7,
    "N_used": 7,
    "H_total_m": 3.5,
    "absorbed_kmol_h": 3.8,
    "X1": 0.026333333333333334,
    "gas_in_total_kmol_h": 104.0,
    "gas_out_total_kmol_h": 100.2,
    "liq_in_total_kmol_h": 150.14999999999998,
    "liq_out_total_kmol_h": 153.95,
    "components": {
      "gas_in": {
        "inert": 100.0,
        "solute": 4.0
      },
      "gas_out": {
        "inert": 100.0,
        "solute": 0.2
      },
      "liq_in": {
        "solvent": 150.0,
        "solute": 0.15
      },
      "liq_out": {
        "solvent": 150.0,
        "solute": 3.95
      }
    }
  },
  "artifacts": {
    "stage_data_csv": "stage_data.csv",
    "stage_table_csv": "stage_table.csv",
    "streams_csv": "streams.csv",
    "streams_table_csv": "streams_table.csv",
    "mt_plot": "mt_plot.png",
    "log": "log.txt"
  }
}
```

---

## 🧩 理论背景 / Theoretical Basis

| 概念 | 说明 |
|------|------|
| **操作线** | 表示气液间传质的整体物料平衡 |
| **平衡线** | 由实验或模型得到的 y\* = f(x) 关系 |
| **McCabe–Thiele 图** | 逐级构建气液浓度变化的几何解法 |
| **级板效率** | 实际吸收板与理论板的效率比，可扩展 Murphree 模型 |
| **平衡数据插值** | 使用三次样条提高 y\* 与 x\* 精度，避免线性插值误差 |

---

## 🧱 可扩展方向 / Future Extensions

- ✅ 增加 **非理想体系** 支持（使用 UNIFAC / NRTL 计算活度系数）  
- ✅ 扩展 **多组分吸收** 处理逻辑  
- ✅ 实现 **图形化界面 GUI**（基于 PyQt 或 Tkinter）  
- ✅ 引入 **AI 模型预测参数**（机器学习吸收效率）  
- ✅ 提供 **JSON/Excel 批量计算模式**

---

## 👨‍🔬 作者与项目背景 / Author & Acknowledgment

**Author:** Zhen-Ning Guo  
**Affiliation:** AI4ChemEng Project  
**Year:** 2025  

> 本项目旨在构建开放、透明的气体吸收教学与科研计算平台，  
> 为化工原理课程提供可复现、可验证的数值计算工具。

---

## 📜 License

本项目遵循 **MIT License**，可自由使用、修改与扩展。  
引用格式如下：

> Zhen-Ning Guo. *AssimilatePlatform: Gas Absorption Simulation and Visualization Platform (2025).*