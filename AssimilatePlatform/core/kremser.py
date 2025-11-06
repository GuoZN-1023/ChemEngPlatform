from .stagewise import stepwise_stairs

def kremser_search(L, V, m, YF, YN, X0, cap=2000):
    """整数级数搜索"""
    for N in range(1, cap):
        stairs, n_calc, X1 = stepwise_stairs(L, V, m, YF, YN, X0, cap=N)
        if stairs[-1]["Y"] >= YF - 1e-8:
            return N
    return float("inf")