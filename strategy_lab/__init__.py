"""Strategy Lab - Advanced strategy research and backtesting framework.

This package provides comprehensive tools for strategy development, backtesting,
risk management, and optimization.
"""
from strategy_lab.config import (
    EntryMode,
    PyramidingMode,
    PyramidingConfig,
    RiskConfig,
    RiskConstraintConfig,
    ParameterBound,
    StrategyConfig,
    OptimizationConfig,
)

__version__ = "0.1.0"

__all__ = [
    "EntryMode",
    "PyramidingMode",
    "PyramidingConfig",
    "RiskConfig",
    "RiskConstraintConfig",
    "ParameterBound",
    "StrategyConfig",
    "OptimizationConfig",
]
