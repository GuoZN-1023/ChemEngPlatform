class DistillationSpec:
    def __init__(self, xF, q, xD, xW,
                 R=0.0,
                 consider_murphree=True,
                 EM_L=1.0,              # 液相效率
                 EM_V=None,             # 气相效率（优先级更高）
                 mode="basic",
                 tol=1e-6,
                 # ---- 可选高级参数 ----
                 n_effects=1,
                 pressures=None,
                 solvent=None,
                 solvent_ratio=0.0,
                 azeotrope_x=None,
                 azeotrope_y=None,
                 azeotrope_strength=0.0,
                 # ---- 物性参数 ----
                 feed_volume_L=0.0,
                 feed_density_kg_per_L=1.0,
                 MW_light=46.07,
                 MW_heavy=18.015):
        # 基本分离条件
        self.xF, self.q, self.xD, self.xW = xF, q, xD, xW
        self.R = R
        self.tol = tol

        # 效率控制
        self.consider_murphree = consider_murphree
        self.EM_L = EM_L
        self.EM_V = EM_V   # ✅ 新增：气相效率（若 <1 优先使用）

        # 模式控制
        self.mode = mode.lower()
        self.n_effects = n_effects
        self.pressures = pressures
        self.solvent = solvent
        self.solvent_ratio = solvent_ratio
        self.azeotrope_x = azeotrope_x
        self.azeotrope_y = azeotrope_y
        self.azeotrope_strength = azeotrope_strength

        # 物性
        self.feed_volume_L = feed_volume_L
        self.feed_density_kg_per_L = feed_density_kg_per_L
        self.MW_light = MW_light
        self.MW_heavy = MW_heavy