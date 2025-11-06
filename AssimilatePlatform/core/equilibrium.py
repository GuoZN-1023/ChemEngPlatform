def y_star(m, x):
    """Linear equilibrium line Y*=mX"""
    return m * x

def operating_y(L, V, x, YN, X0):
    """Operating line: Y = (L/V)*X + (YN - (L/V)*X0)"""
    return (L / V) * x + (YN - (L / V) * X0)

def compute_Lmin(V, YF, YN, m, X0):
    """Minimum solvent rate from intersection of operating and equilibrium lines"""
    denom = (YF / m) - X0
    if denom <= 0:
        return float("inf")
    return V * (YF - YN) / denom