def material_balance(YF, YN, X0, V, L):
    """
    Ratio basis:
      Y = n_A / n_I,  V = inert gas molar flow (kmol/h)
      X = n_A / n_S,  L = solvent molar flow   (kmol/h)

    Returns dict including totals and a 'rows' list for CSV/back-compat.
    """
    # Solute transferred to liquid
    absorbed = V * (YF - YN)                # kmol_A/h

    # Outlet liquid solute ratio on solvent basis
    X1 = X0 + absorbed / L

    # Totals
    gas_in_total  = V * (1.0 + YF)
    gas_out_total = V * (1.0 + YN)
    liq_in_total  = L * (1.0 + X0)
    liq_out_total = L * (1.0 + X1)

    rows = [
        {
            "stream": "Gas_in",
            "total_kmol_h": gas_in_total,
            "inert_kmol_h": V,
            "solvent_kmol_h": 0.0,
            "solute_kmol_h": V * YF,
            "ratio": YF,         # Y_F
        },
        {
            "stream": "Gas_out",
            "total_kmol_h": gas_out_total,
            "inert_kmol_h": V,
            "solvent_kmol_h": 0.0,
            "solute_kmol_h": V * YN,
            "ratio": YN,         # Y_N
        },
        {
            "stream": "Liq_in",
            "total_kmol_h": liq_in_total,
            "inert_kmol_h": 0.0,
            "solvent_kmol_h": L,
            "solute_kmol_h": L * X0,
            "ratio": X0,         # X_0
        },
        {
            "stream": "Liq_out",
            "total_kmol_h": liq_out_total,
            "inert_kmol_h": 0.0,
            "solvent_kmol_h": L,
            "solute_kmol_h": L * X1,
            "ratio": X1,         # X_1
        },
    ]

    return {
        "absorbed": absorbed,
        "X1": X1,
        "gas_in_total":  gas_in_total,
        "gas_out_total": gas_out_total,
        "liq_in_total":  liq_in_total,
        "liq_out_total": liq_out_total,
        "components": {
            "gas_in":  {"inert": V, "solute": V*YF},
            "gas_out": {"inert": V, "solute": V*YN},
            "liq_in":  {"solvent": L, "solute": L*X0},
            "liq_out": {"solvent": L, "solute": L*X1},
        },
        # ✅ 提供 CSV/旧代码兼容用的行列表
        "rows": rows,
        "streams": rows,   # 兼容更早的键名
    }