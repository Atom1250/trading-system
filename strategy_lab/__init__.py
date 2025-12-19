"""Strategy Lab - Advanced strategy research and backtesting framework.

This package provides comprehensive tools for strategy development, backtesting,
risk management, and optimization.
"""

from strategy_lab.config import (
    EntryMode,
    OptimizationConfig,
    ParameterBound,
    PyramidingConfig,
    PyramidingMode,
    RiskConfig,
    RiskConstraintConfig,
    StrategyConfig,
)

__version__ = "0.1.0"

__all__ = [
    "EntryMode",
    "OptimizationConfig",
    "ParameterBound",
    "PyramidingConfig",
    "PyramidingMode",
    "RiskConfig",
    "RiskConstraintConfig",
    "StrategyConfig",
]
