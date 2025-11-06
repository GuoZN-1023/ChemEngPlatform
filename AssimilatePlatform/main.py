import argparse, json
from utils.io_utils import load_config_any
from core import run_absorption  # ✅ 改为从 core 包导入（更简洁）

def parse_args():
    p = argparse.ArgumentParser(
        description="Absorption Platform (main). "
                    "No --config & no --interactive will enter interactive mode."
    )
    p.add_argument("--config", type=str, help="YAML/JSON config file path")
    p.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    return p.parse_args()

def interactive_input():
    def ask_float(prompt, default):
        s = input(f"{prompt} (default {default}): ").strip()
        if s == "": return float(default)
        try:
            return float(s)
        except Exception:
            print("  ⚠️ invalid number, using default.")
            return float(default)

    print("\n=== Interactive Absorption Inputs ===")
    m = ask_float("▶ 平衡线斜率 m (Y*=mX)", 0.4)
    YF = ask_float("▶ 气体入口溶质摩尔比 YF", 0.04)
    YN = ask_float("▶ 气体出口目标摩尔比 YN_target", 0.002)
    X0 = ask_float("▶ 吸收剂入口摩尔比 X0", 0.002)
    V  = ask_float("▶ 气体流量 V (kmol/h)", 100.0)
    L  = ask_float("▶ 吸收剂流量 L (kmol/h, 0 表示自动 = 1.5×Lmin)", 0.0)
    L_factor = ask_float("▶ L_factor (L=Lmin×factor)", 1.5)
    HETP = ask_float("▶ HETP (m/理论级)", 0.5)
    cap  = int(ask_float("▶ 最大步数上限 max_stages_cap", 300))
    case_name = input("▶ 案例名称 case_name (默认 interactive_case): ").strip() or "interactive_case"
    notes = input("▶ 备注 notes: ").strip()
    plot_ans = input("▶ 是否绘制 M–T 图？(y/n, 默认 y): ").strip().lower()
    plot = (plot_ans != "n")

    return {
        "m": m, "YF": YF, "YN_target": YN, "X0": X0,
        "V": V, "L": L, "L_factor": L_factor, "HETP": HETP,
        "max_stages_cap": cap, "case_name": case_name, "notes": notes, "plot": plot
    }

def main():
    args = parse_args()
    if args.interactive or not args.config:
        cfg = interactive_input()
    else:
        cfg = load_config_any(args.config)

    outdir, summary = run_absorption(cfg, config_path=args.config)
    print("\n✅ Absorption complete. Results saved to:", outdir)
    print(json.dumps(summary, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()