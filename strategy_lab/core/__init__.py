"""Canonical core contracts for Strategy Lab.

This package hosts stable shared contracts and configuration schemas that are
reused across backtest, paper, and live execution paths.
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
from strategy_lab.core.types import (
    ExecutionReport,
    ExecutionStatus,
    OrderIntent,
    OrderSide,
    OrderType,
    RiskDecision,
    RiskViolation,
    Signal,
    SignalType,
)

__all__ = [
    "BacktestConfig",
    "CapitalAllocationMode",
    "EntryMode",
    "ExecutionConfig",
    "ExecutionReport",
    "ExecutionStatus",
    "OptimizationConfig",
    "OrderIntent",
    "OrderSide",
    "OrderType",
    "ParameterBound",
    "PyramidingConfig",
    "PyramidingMode",
    "RiskConfig",
    "RiskConstraintConfig",
    "RiskDecision",
    "RiskViolation",
    "Signal",
    "SignalType",
    "StrategyConfig",
]
