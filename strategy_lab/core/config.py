"""Canonical configuration contracts for Strategy Lab.

This module contains stable config objects for strategy, risk, backtest, and
execution flows. Legacy imports should re-export from here.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class EntryMode(str, Enum):
    """Entry mode for trading strategies."""

    FIRST_SIGNAL = "first_signal"
    PYRAMID = "pyramid"
    SCALE_IN = "scale_in"


class CapitalAllocationMode(str, Enum):
    """Mode for allocating capital to trades."""

    FIXED = "fixed"
    COMPOUNDING = "compounding"


class PyramidingMode(str, Enum):
    """Pyramiding strategy modes."""

    FIXED_SIZE = "fixed_size"
    DECREASING = "decreasing"
    INCREASING = "increasing"
    RISK_BASED = "risk_based"


@dataclass
class PyramidingConfig:
    """Configuration for pyramiding strategies."""

    mode: PyramidingMode = PyramidingMode.FIXED_SIZE
    max_entries: int = 3
    entry_spacing: float = 0.02
    size_multiplier: float = 1.0


@dataclass
class RiskConfig:
    """Comprehensive risk management configuration."""

    entry_mode: EntryMode = EntryMode.FIRST_SIGNAL
    pyramiding_config: Optional[PyramidingConfig] = None
    max_position_size: float = 0.2
    max_portfolio_risk: float = 0.1
    stop_loss_atr_multiple: float = 1.5
    take_profit_atr_multiple: float = 2.0
    stop_loss_pct: Optional[float] = None  # Exit if price drops by this %
    take_profit_pct: Optional[float] = None  # Exit if price rises by this %
    max_drawdown_pct: float = 0.2
    risk_per_trade: float = 0.01
    use_trailing_stop: bool = False
    trailing_stop_atr_multiple: float = 2.0
    capital_allocation_mode: CapitalAllocationMode = CapitalAllocationMode.COMPOUNDING


@dataclass
class RiskConstraintConfig:
    """Risk constraint parameters for strategy execution."""

    max_leverage: float = 1.0
    max_concentration: float = 0.25
    max_sector_exposure: float = 0.4
    max_correlation: float = 0.7
    min_liquidity: float = 1_000_000.0
    max_volatility: float = 0.5


@dataclass
class ParameterBound:
    """Parameter boundary definition for optimization."""

    name: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    param_type: str = "float"
    categorical_values: Optional[list[Any]] = None

    def __post_init__(self) -> None:
        """Validate parameter bounds."""
        if self.param_type == "categorical":
            if not self.categorical_values:
                raise ValueError(
                    f"categorical_values required for categorical parameter {self.name}",
                )
            return

        if self.min_value is None or self.max_value is None:
            raise ValueError(
                f"min_value and max_value required for {self.param_type} parameter {self.name}",
            )
        if self.min_value >= self.max_value:
            raise ValueError(f"min_value must be less than max_value for {self.name}")


@dataclass
class BacktestConfig:
    """Backtest runtime configuration."""

    initial_capital: float = 100_000.0
    commission: float = 0.001
    slippage: float = 0.0005
    seed: int = 42
    market_order_fill: str = "next_bar_open"
    stop_fill_model: str = "stop_price"


@dataclass
class ExecutionConfig:
    """Execution runtime configuration shared by paper/live paths."""

    mode: str = "backtest"
    allow_partial_fills: bool = False
    reconcile_interval_seconds: int = 30
    heartbeat_seconds: int = 5


@dataclass
class StrategyConfig:
    """Strategy configuration settings."""

    name: str
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    risk_config: RiskConfig = field(default_factory=RiskConfig)
    risk_constraints: RiskConstraintConfig = field(default_factory=RiskConstraintConfig)
    universe: list[str] = field(default_factory=list)
    rebalance_frequency: str = "daily"
    initial_capital: float = 100_000.0
    commission: float = 0.001
    slippage: float = 0.0005


@dataclass
class OptimizationConfig:
    """Optimization run configuration."""

    method: str = "bayesian"
    parameter_bounds: list[ParameterBound] = field(default_factory=list)
    objective: str = "sharpe"
    n_trials: int = 100
    n_jobs: int = -1
    cv_folds: int = 5
    train_test_split: float = 0.7
    random_seed: Optional[int] = 42
    direction: str = "maximize"
    timeout: Optional[int] = None
    early_stopping_rounds: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate optimization configuration."""
        valid_methods = ["grid", "random", "bayesian", "monte_carlo"]
        if self.method not in valid_methods:
            raise ValueError(
                f"method must be one of {valid_methods}, got {self.method}",
            )

        valid_objectives = ["sharpe", "returns", "sortino", "calmar", "max_drawdown"]
        if self.objective not in valid_objectives:
            raise ValueError(
                f"objective must be one of {valid_objectives}, got {self.objective}",
            )

        valid_directions = ["maximize", "minimize"]
        if self.direction not in valid_directions:
            raise ValueError(
                f"direction must be one of {valid_directions}, got {self.direction}",
            )

        if self.train_test_split <= 0 or self.train_test_split >= 1:
            raise ValueError(
                f"train_test_split must be between 0 and 1, got {self.train_test_split}",
            )
