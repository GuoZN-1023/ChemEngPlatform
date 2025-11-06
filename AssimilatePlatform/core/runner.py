import os
import math

from utils.io_utils import ensure_dir, now, write_json, copy_file
from utils.logger import Logger
from utils.plot_mt import draw_mt

from .equilibrium import compute_Lmin
from .stagewise import stepwise_stairs
from .kremser import kremser_search
from .streams import material_balance


def _bottom_up_stage_table(m, L, V, YF, YN, X0, N_cap):
    """自底向上计算级板表"""
    r = L / V
    b = YN - r * X0
    X = (YF - b) / r
    if not math.isfinite(X) or X < 0:
        raise RuntimeError("计算底部 X1 失败：请检查参数。")

    table = []
    k = 1
    while k <= max(1, int(N_cap)):
        Y = m * X
        table.append({"stage": k, "X": X, "Y": Y})
        if Y <= YN + 1e-12:
            break
        X_next = (Y - b) / r
        if X_next > X + 1e-12:
            break
        X = X_next
        k += 1
    return table


def run_absorption(cfg, config_path=None):
    """吸收塔主运行逻辑"""
    results_root = ensure_dir("results")
    outdir = ensure_dir(os.path.join(results_root, f"{now()}_{cfg.get('case_name', 'case')}"))
    logger = Logger(os.path.join(outdir, "log.txt"))
    logger.info("=== Absorption calculation started ===")
    logger.info(f"Config: {cfg}")

    # --- 1️⃣ 读取输入参数 ---
    m   = float(cfg["m"])
    YF  = float(cfg["YF"])
    YN  = float(cfg["YN_target"])
    X0  = float(cfg["X0"])
    V   = float(cfg["V"])
    L_in = float(cfg["L"])
    L_factor = float(cfg.get("L_factor", 1.5))
    HETP = float(cfg.get("HETP", 0.5))
    cap  = int(cfg.get("max_stages_cap", 300))
    plot = bool(cfg.get("plot", True))

    solute_name  = cfg.get("solute_name",  "溶质")
    inert_name   = cfg.get("inert_name",   "惰性气体")
    solvent_name = cfg.get("solvent_name", "溶剂")

    # --- 2️⃣ Lmin 与 L_used ---
    Lmin = compute_Lmin(V, YF, YN, m, X0)
    if not math.isfinite(Lmin) or Lmin <= 0:
        raise RuntimeError("L_min 计算无效。")
    if L_in <= 0:
        L_used = Lmin * L_factor
        logger.info(f"自动 L = {Lmin:.6f}×{L_factor:.2f} = {L_used:.6f}")
    else:
        L_used = L_in
        if L_used < Lmin * (1.0 - 1e-9):
            raise RuntimeError(f"L={L_used:.4g} < Lmin={Lmin:.4g}")
        logger.info(f"输入 L = {L_used:.6f}, L/Lmin={L_used/Lmin:.3f}")

    # --- 3️⃣ 顶→底 阶梯数据 ---
    stairs, N_stair, _ = stepwise_stairs(L_used, V, m, YF, YN, X0, cap=cap)
    N_int = kremser_search(L_used, V, m, YF, YN, X0, cap=max(cap, 2000))
    N_used = int(round(N_int)) if math.isfinite(N_int) else N_stair
    H_total = N_used * HETP

    # --- 4️⃣ 保存 stage_data.csv ---
    stage_data_csv = os.path.join(outdir, "stage_data.csv")
    with open(stage_data_csv, "w", encoding="utf-8") as f:
        f.write("stage,type,X,Y\n")
        for node in stairs:
            f.write(f"{node['stage']},{node['type']},{node['X']:.8f},{node['Y']:.8f}\n")
    logger.info("stage_data.csv saved.")

    # --- 5️⃣ 保存 stage_table.csv ---
    table = _bottom_up_stage_table(m, L_used, V, YF, YN, X0, N_cap=N_used + 5)
    stage_table_csv = os.path.join(outdir, "stage_table.csv")
    with open(stage_table_csv, "w", encoding="utf-8") as f:
        f.write("Stage,X(%),Y(%)\n")
        for row in table:
            f.write(f"{row['stage']},{row['X']*100:.2f},{row['Y']*100:.2f}\n")
    logger.info("stage_table.csv saved.")

    # --- 6️⃣ 物料衡算 + 流程表 ---
    streams = material_balance(YF, YN, X0, V, L_used)

    # 6.1 明细版
    streams_csv = os.path.join(outdir, "streams.csv")
    with open(streams_csv, "w", encoding="utf-8") as f:
        f.write("stream,total_kmol_h,inert_kmol_h,solvent_kmol_h,solute_kmol_h,ratio\n")
        for r in streams["rows"]:
            f.write(f"{r['stream']},{r['total_kmol_h']:.8f},{r['inert_kmol_h']:.8f},"
                    f"{r['solvent_kmol_h']:.8f},{r['solute_kmol_h']:.8f},{r['ratio']:.8f}\n")
    logger.info("streams.csv saved.")

    # 6.2 表格版（教学展示）
    cols = ["气体进", "气体出", "吸收液进", "吸收液出"]
    total_row = [
        streams["gas_in_total"], streams["gas_out_total"],
        streams["liq_in_total"], streams["liq_out_total"]
    ]
    solute_row = [
        streams["components"]["gas_in"]["solute"],
        streams["components"]["gas_out"]["solute"],
        streams["components"]["liq_in"]["solute"],
        streams["components"]["liq_out"]["solute"],
    ]
    inert_row = [
        streams["components"]["gas_in"]["inert"],
        streams["components"]["gas_out"]["inert"], 0.0, 0.0
    ]
    solvent_row = [
        0.0, 0.0,
        streams["components"]["liq_in"]["solvent"],
        streams["components"]["liq_out"]["solvent"],
    ]
    streams_table_csv = os.path.join(outdir, "streams_table.csv")
    with open(streams_table_csv, "w", encoding="utf-8") as f:
        f.write("," + ",".join(cols) + "\n")
        f.write(f"总流量 (kmol/h),{total_row[0]:.4f},{total_row[1]:.4f},{total_row[2]:.4f},{total_row[3]:.4f}\n")
        f.write(f"{solute_name}流量 (kmol/h),{solute_row[0]:.4f},{solute_row[1]:.4f},{solute_row[2]:.4f},{solute_row[3]:.4f}\n")
        f.write(f"{inert_name}流量 (kmol/h),{inert_row[0]:.4f},{inert_row[1]:.4f},{inert_row[2]:.4f},{inert_row[3]:.4f}\n")
        f.write(f"{solvent_name}流量 (kmol/h),{solvent_row[0]:.4f},{solvent_row[1]:.4f},{solvent_row[2]:.4f},{solvent_row[3]:.4f}\n")
    logger.info("streams_table.csv saved.")

    # --- 7️⃣ summary.json ---
    summary = {
        "case_name": cfg.get("case_name", "case"),
        "inputs": {
            "m": m, "YF": YF, "YN": YN, "X0": X0,
            "V": V, "L": L_in, "L_factor": L_factor,
            "HETP": HETP, "max_stages_cap": cap, "plot": plot
        },
        "results": {
            "Lmin": Lmin, "L_used": L_used,
            "N_stair": N_stair, "N_kremser": N_int,
            "N_used": N_used, "H_total_m": H_total,
            "absorbed_kmol_h": streams["absorbed"], "X1": streams["X1"],
            "gas_in_total_kmol_h":  streams["gas_in_total"],
            "gas_out_total_kmol_h": streams["gas_out_total"],
            "liq_in_total_kmol_h":  streams["liq_in_total"],
            "liq_out_total_kmol_h": streams["liq_out_total"],
            "components": streams["components"]
        },
        "artifacts": {
            "stage_data_csv": "stage_data.csv",
            "stage_table_csv": "stage_table.csv",
            "streams_csv": "streams.csv",
            "streams_table_csv": "streams_table.csv",
            "mt_plot": "mt_plot.png" if plot else None,
            "log": "log.txt"
        }
    }
    write_json(os.path.join(outdir, "summary.json"), summary)
    logger.info("summary.json saved.")

    # --- 8️⃣ 绘图 ---
    if plot:
        fig_path = os.path.join(outdir, "mt_plot.png")
        draw_mt(fig_path, m, L_used, V, YN, X0, YF, stairs)
        logger.info(f"McCabe–Thiele plot saved: {fig_path}")

    # --- 9️⃣ 复制配置文件 ---
    if config_path:
        try:
            copy_file(config_path, outdir)
            logger.info(f"config copied: {config_path} -> {outdir}")
        except Exception as e:
            logger.info(f"config copy skipped: {e!r}")

    logger.info("=== Absorption calculation completed ===")
    return outdir, summary