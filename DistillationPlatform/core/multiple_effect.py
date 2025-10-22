from core.distillation_column import DistillationColumn
import numpy as np

class MultiEffectSystem:
    def __init__(self, specs, vles, heat_efficiency=0.9):
        """
        参数：
            specs : list[DistillationSpec]   每个塔的参数对象
            vles : list[VLEData]             对应的气液平衡数据
            heat_efficiency : float          热耦合效率（默认 0.9）
        """
        assert len(specs) == len(vles), "每个塔必须有对应的 VLE 数据"
        self.specs = specs
        self.vles = vles
        self.heat_eff = heat_efficiency
        self.columns = [DistillationColumn(spec, vle) for spec, vle in zip(specs, vles)]

    def run(self, result_folder):
        """
        串联运行多效精馏塔：
        - 前一塔的冷凝热部分供给下一塔再沸
        - 能量平衡为简化版：Q_next = η * Q_prev
        """
        results = []
        Q_prev = None  # 前一塔冷凝热

        for i, column in enumerate(self.columns):
            print(f"\n🚀 正在计算第 {i+1} 效精馏塔...")
            result = column.run()

            # 估算热负荷（简化为与蒸汽流量 ~ R/(R+1) 成正比）
            R_used = result["R_used"]
            Q_current = R_used / (R_used + 1.0)

            # 若有前一塔，则按热效率调整其再沸热需求
            if Q_prev is not None:
                Q_saved = self.heat_eff * Q_prev
                effective_Q = Q_current - Q_saved
                print(f"  ↳ 利用前一塔冷凝热：节能约 {Q_saved:.3f}，实际需热量 {effective_Q:.3f}")
            else:
                effective_Q = Q_current
                print(f"  ↳ 第一效塔，无上级供热，需热量 {effective_Q:.3f}")

            results.append({
                "tower_index": i + 1,
                "R_used": R_used,
                "energy_load": effective_Q,
                "data": result
            })

            Q_prev = Q_current  # 下一塔用

        print("\n✅ 多效精馏系统计算完成。")
        return results