import json
import pandas as pd
from core.distillation_column import DistillationColumn

class DistillationEngine:
    def __init__(self, spec, vle):
        self.spec = spec
        self.vle = vle

    def run(self, result_folder):
        column = DistillationColumn(self.spec, self.vle)
        res = column.run()  # res 含 lines/theory/real 等完整信息

        df_theory = res["theory"]
        df_real = res.get("real", None)

        if df_real is None or not isinstance(df_real, pd.DataFrame) or df_real.empty:
            df_out = df_theory.copy()
            efficiency_type = "none"
            EM_val = 1.0
        else:
            # outer merge 保留理论/实际所有列
            df_out = df_theory.merge(df_real, on=["stage", "section"], how="outer")
            if self.spec.EM_V is not None and self.spec.EM_V < 1.0:
                efficiency_type = "gas"
                EM_val = self.spec.EM_V
            elif self.spec.consider_murphree and self.spec.EM_L < 1.0:
                efficiency_type = "liquid"
                EM_val = self.spec.EM_L
            else:
                efficiency_type = "none"
                EM_val = 1.0

        summary = {
            "R_used": float(res["R_used"]),
            "stages_theory": int(len(df_theory)),
            "stages_real": int(len(df_real)) if isinstance(df_real, pd.DataFrame) else 0,
            "consider_murphree": self.spec.consider_murphree,
            "efficiency_type": efficiency_type,
            "EM_value": EM_val,
            "achieved": res.get("achieved", True),
            "xF": self.spec.xF,
            "xD": self.spec.xD,
            "xW": self.spec.xW,
            "q": self.spec.q,
        }

        # 写文件
        df_out.to_csv(f"{result_folder}/results.csv", index=False)
        with open(f"{result_folder}/summary.json", "w") as f:
            json.dump(summary, f, indent=4)

        # ✅ 这里返回外层+内层数据一起
        return {
            "summary": summary,
            "data": df_out,
            "lines": res["lines"],
            "theory": res["theory"],
            "real": res["real"],
            "achieved": res["achieved"],
        }