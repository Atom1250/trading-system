"""Compatibility config module.

Canonical configuration contracts now live in ``strategy_lab.core.config``.
This module remains for backward-compatible imports.
"""

from strategy_lab.core.config import (
    BacktestConfig,
    CapitalAllocationMode,
    EntryMode,
    ExecutionConfig,
    OptimizationConfig,
    ParameterBound,
    PyramidingConfig,
    PyramidingMode,
    RiskConfig,
    RiskConstraintConfig,
    StrategyConfig,
)

__all__ = [
    "BacktestConfig",
    "CapitalAllocationMode",
    "EntryMode",
    "ExecutionConfig",
    "OptimizationConfig",
    "ParameterBound",
    "PyramidingConfig",
    "PyramidingMode",
    "RiskConfig",
    "RiskConstraintConfig",
    "StrategyConfig",
]
