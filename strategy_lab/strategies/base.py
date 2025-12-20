"""Base strategy classes and interfaces.

This module defines the abstract base classes for strategies and
signal generation.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any

import pandas as pd

from ..config import StrategyConfig
from ..data.base import MarketDataSlice

# Type aliases
MarketDataSlices = dict[str, MarketDataSlice]
FactorPanels = dict[str, pd.DataFrame]


class SignalType(Enum):
    """Signal types for trading strategies."""

    LONG = 1
    SHORT = -1
    FLAT = 0
    CLOSE = 2  # Close existing position


@dataclass
class Signal:
    """Trading signal.

    Attributes:
        timestamp: Signal timestamp
        symbol: Trading symbol
        signal_type: Type of signal (LONG, SHORT, FLAT, CLOSE)
        strength: Signal strength (0 to 1)
        metadata: Additional signal metadata

    """

    timestamp: pd.Timestamp
    symbol: str
    signal_type: SignalType
    strength: float = 1.0
    metadata: dict[str, Any] = None

    def __post_init__(self):
        """Validate signal."""
        if not 0 <= self.strength <= 1:
            raise ValueError(
                f"Signal strength must be between 0 and 1, got {self.strength}",
            )
        if self.metadata is None:
            self.metadata = {}


class Strategy(ABC):
    """Abstract base class for trading strategies.

    A strategy generates trading signals based on market data and factors.
    """

    def __init__(self, config: StrategyConfig):
        """Initialize strategy.

        Args:
            config: Strategy configuration

        """
        self.config = config
        self.name = config.name

    @abstractmethod
    def generate_signals(
        self,
        data: MarketDataSlices,
        factor_panels: FactorPanels,
    ) -> dict[str, pd.Series]:
        """Generate trading signals.

        Args:
            data: Dictionary of MarketDataSlice per symbol
            factor_panels: Dictionary of factor DataFrames per symbol

        Returns:
            Dictionary of signal Series per symbol (1 for long, -1 for short, 0 for flat)

        """

    def get_params(self) -> dict[str, Any]:
        """Get strategy parameters from config.

        Returns:
            Dictionary of strategy parameters

        """
        return self.config.parameters

    def __repr__(self) -> str:
        """String representation of the strategy."""
        return f"{self.__class__.__name__}(name='{self.name}')"
