"""Configuration dataclasses for strategy_lab module.

This module defines all configuration classes used throughout the strategy_lab
package, including risk management, strategy parameters, and optimization settings.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional

# ============================================================================
# Risk Configuration Classes
# ============================================================================


class EntryMode(str, Enum):
    """Entry mode for trading strategies."""

    FIRST_SIGNAL = "first_signal"  # Enter only on first signal
    PYRAMID = "pyramid"  # Allow pyramiding (multiple entries)
    SCALE_IN = "scale_in"  # Scale into position over time


class CapitalAllocationMode(str, Enum):
    """Mode for allocating capital to trades."""

    FIXED = "fixed"  # Use initial capital for sizing
    COMPOUNDING = "compounding"  # Use current equity for sizing


class PyramidingMode(str, Enum):
    """Pyramiding strategy modes."""

    FIXED_SIZE = "fixed_size"  # Fixed position size for each entry
    DECREASING = "decreasing"  # Decreasing position size
    INCREASING = "increasing"  # Increasing position size
    RISK_BASED = "risk_based"  # Size based on risk per entry


@dataclass
class PyramidingConfig:
    """Configuration for pyramiding strategies.

    Attributes:
        mode: Pyramiding mode to use
        max_entries: Maximum number of entries allowed
        entry_spacing: Minimum spacing between entries (in price percentage or ATR multiples)
        size_multiplier: Multiplier for position sizing (mode-dependent)

    """

    mode: PyramidingMode = PyramidingMode.FIXED_SIZE
    max_entries: int = 3
    entry_spacing: float = 0.02  # 2% or 2 ATR
    size_multiplier: float = 1.0


@dataclass
class RiskConfig:
    """Comprehensive risk management configuration.

    Attributes:
        entry_mode: Entry mode for the strategy
        pyramiding_config: Pyramiding configuration (if entry_mode is PYRAMID)
        max_position_size: Maximum position size as fraction of portfolio
        max_portfolio_risk: Maximum portfolio risk as fraction
        stop_loss_atr_multiple: Stop loss distance in ATR multiples
        take_profit_atr_multiple: Take profit distance in ATR multiples
        max_drawdown_pct: Maximum allowed drawdown before halting
        risk_per_trade: Risk per trade as fraction of capital
        use_trailing_stop: Whether to use trailing stops
        trailing_stop_atr_multiple: Trailing stop distance in ATR multiples

    """

    entry_mode: EntryMode = EntryMode.FIRST_SIGNAL
    pyramiding_config: Optional[PyramidingConfig] = None
    max_position_size: float = 0.2  # 20% of portfolio
    max_portfolio_risk: float = 0.1  # 10% total portfolio risk
    stop_loss_atr_multiple: float = 1.5
    take_profit_atr_multiple: float = 2.0
    max_drawdown_pct: float = 0.2  # 20% max drawdown
    risk_per_trade: float = 0.01  # 1% risk per trade
    use_trailing_stop: bool = False
    trailing_stop_atr_multiple: float = 2.0
    capital_allocation_mode: CapitalAllocationMode = CapitalAllocationMode.COMPOUNDING


# ============================================================================
# Strategy Configuration Classes
# ============================================================================


@dataclass
class RiskConstraintConfig:
    """Risk constraint parameters for strategy execution.

    Attributes:
        max_leverage: Maximum leverage allowed
        max_concentration: Maximum concentration in single position
        max_sector_exposure: Maximum exposure to single sector
        max_correlation: Maximum correlation between positions
        min_liquidity: Minimum liquidity requirement (avg daily volume)
        max_volatility: Maximum volatility threshold (annualized)

    """

    max_leverage: float = 1.0
    max_concentration: float = 0.25  # 25% max in single position
    max_sector_exposure: float = 0.4  # 40% max in single sector
    max_correlation: float = 0.7  # Max 0.7 correlation
    min_liquidity: float = 1_000_000.0  # $1M avg daily volume
    max_volatility: float = 0.5  # 50% annualized volatility


@dataclass
class ParameterBound:
    """Parameter boundary definition for optimization.

    Attributes:
        name: Parameter name
        min_value: Minimum value
        max_value: Maximum value
        step: Step size for discrete parameters (None for continuous)
        param_type: Parameter type ('int', 'float', 'categorical')
        categorical_values: List of values for categorical parameters

    """

    name: str
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    step: Optional[float] = None
    param_type: str = "float"  # 'int', 'float', 'categorical'
    categorical_values: Optional[list[Any]] = None

    def __post_init__(self):
        """Validate parameter bounds."""
        if self.param_type == "categorical":
            if not self.categorical_values:
                raise ValueError(
                    f"categorical_values required for categorical parameter {self.name}",
                )
        else:
            if self.min_value is None or self.max_value is None:
                raise ValueError(
                    f"min_value and max_value required for {self.param_type} parameter {self.name}",
                )
            if self.min_value >= self.max_value:
                raise ValueError(
                    f"min_value must be less than max_value for {self.name}",
                )


@dataclass
class StrategyConfig:
    """Strategy configuration settings.

    Attributes:
        name: Strategy name
        description: Strategy description
        parameters: Strategy-specific parameters
        risk_config: Risk management configuration
        risk_constraints: Risk constraint configuration
        universe: List of symbols to trade
        rebalance_frequency: Rebalancing frequency ('daily', 'weekly', 'monthly')
        initial_capital: Initial capital for backtesting
        commission: Commission per trade (fraction)
        slippage: Slippage per trade (fraction)

    """

    name: str
    description: str = ""
    parameters: dict[str, Any] = field(default_factory=dict)
    risk_config: RiskConfig = field(default_factory=RiskConfig)
    risk_constraints: RiskConstraintConfig = field(default_factory=RiskConstraintConfig)
    universe: list[str] = field(default_factory=list)
    rebalance_frequency: str = "daily"
    initial_capital: float = 100_000.0
    commission: float = 0.001  # 0.1%
    slippage: float = 0.0005  # 0.05%


# ============================================================================
# Optimization Configuration Classes
# ============================================================================


@dataclass
class OptimizationConfig:
    """Optimization run configuration.

    Attributes:
        method: Optimization method ('grid', 'random', 'bayesian', 'monte_carlo')
        parameter_bounds: List of parameter bounds to optimize
        objective: Optimization objective ('sharpe', 'returns', 'sortino', 'calmar')
        n_trials: Number of trials for random/bayesian/monte_carlo methods
        n_jobs: Number of parallel jobs (-1 for all cores)
        cv_folds: Number of cross-validation folds
        train_test_split: Train/test split ratio
        random_seed: Random seed for reproducibility
        direction: Optimization direction ('maximize' or 'minimize')
        timeout: Timeout in seconds (None for no timeout)
        early_stopping_rounds: Early stopping rounds (None to disable)

    """

    method: str = "bayesian"  # 'grid', 'random', 'bayesian', 'monte_carlo'
    parameter_bounds: list[ParameterBound] = field(default_factory=list)
    objective: str = "sharpe"  # 'sharpe', 'returns', 'sortino', 'calmar'
    n_trials: int = 100
    n_jobs: int = -1  # Use all cores
    cv_folds: int = 5
    train_test_split: float = 0.7
    random_seed: Optional[int] = 42
    direction: str = "maximize"
    timeout: Optional[int] = None
    early_stopping_rounds: Optional[int] = None

    def __post_init__(self):
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
