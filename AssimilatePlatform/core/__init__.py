"""Core algorithms for the Absorption Platform."""

from .equilibrium import compute_Lmin, y_star, operating_y
from .stagewise import stepwise_stairs
from .kremser import kremser_search
from .streams import material_balance
from .runner import run_absorption

__all__ = [
    "compute_Lmin",
    "y_star",
    "operating_y",
    "stepwise_stairs",
    "kremser_search",
    "material_balance",
    "run_absorption",
]

__version__ = "0.1.0"