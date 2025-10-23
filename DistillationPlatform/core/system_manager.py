# -*- coding: utf-8 -*-
"""
system_manager.py
-----------------
多塔精馏系统管理器（串联模式）
每一塔计算完成后，将塔底液相或塔顶气相作为下一塔的进料。
"""

from core.distillation_column import DistillationColumn
from utils import create_result_folder, save_results, plot_mccabe_thiele


class DistillationSystem:
    """
    多塔精馏系统
    支持多级串联操作，每一级塔的结果会单独输出。
    """

    def __init__(self, specs, vles, mode="series", handoff="bottoms", default_q=1.0):
        """
        参数：
            specs : list[DistillationSpec] 每塔的规格对象
            vles  : list[VLEData]          对应的 VLE 数据
            mode  : str                    'series' 串联（默认）
            handoff : str                  'bottoms'（塔底→下一塔）或 'distillate'（塔顶→下一塔）
            default_q : float              下一塔的进料 q 值（默认 1.0 饱和液体）
        """
        self.specs = specs
        self.vles = vles
        self.mode = mode
        self.handoff = handoff
        self.default_q = default_q
        self.columns = [DistillationColumn(spec, vle) for spec, vle in zip(specs, vles)]
        self.results = []

    def run(self, result_folder="./results"):
        """
        运行多塔系统
        每一塔计算后输出独立文件，并自动更新下一塔进料。
        """
        print(f"🚀 启动多塔系统计算，模式：{self.mode}，衔接方式：{self.handoff}")
        result_folder = create_result_folder(result_folder)
        self.results = []

        for i, column in enumerate(self.columns):
            print(f"\n🧱 正在计算第 {i+1} 塔...")

            res = column.run()
            self.results.append(res)

            # 保存每一塔结果
            prefix = f"Tower_{i+1}"
            save_results(res, result_folder, prefix=prefix)
            plot_mccabe_thiele(res, self.vles[i], result_folder, filename=f"{prefix}.png")

            # 若为串联模式，则更新下一塔的进料
            if self.mode == "series" and i < len(self.columns) - 1:
                next_spec = self.specs[i+1]
                # 提取当前塔的产品组成
                xD = res["summary"].get("achieved_xD", res["summary"].get("xD", None))
                xW = res["summary"].get("achieved_xW", res["summary"].get("xW", None))

                if self.handoff == "bottoms":
                    x_feed_next = xW
                    source = "塔底"
                else:
                    x_feed_next = xD
                    source = "塔顶"

                if x_feed_next is None:
                    print(f"⚠️ 第 {i+1} 塔的产品组成未找到，无法更新下一塔进料。")
                else:
                    next_spec.xF = max(0.0, min(1.0, x_feed_next))
                    next_spec.q = self.default_q
                    print(f"➡️ 将第 {i+1} 塔的 {source} 产品 xF(next)={x_feed_next:.4f}, q={self.default_q:.2f} 作为第 {i+2} 塔进料。")

        print(f"\n✅ 多塔系统计算完成，结果已保存至：{result_folder}")
        return self.results