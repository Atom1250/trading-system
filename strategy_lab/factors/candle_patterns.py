"""Candle pattern factors for the strategy lab."""

from dataclasses import dataclass

from indicators.technicals import morning_star, three_white_soldiers
from strategy_lab.data.base import MarketDataSlice
from strategy_lab.factors.base import Factor, FactorRegistry


@FactorRegistry.register("morning_star")
@dataclass
class MorningStarFactor(Factor):
    """Morning Star Candlestick Pattern Factor.

    Returns 1.0 if a Morning Star pattern is detected, 0.0 otherwise.
    """

    def compute(self, data: MarketDataSlice) -> float:
        """Compute the Morning Star signal.

        Args:
            data: Market data slice

        Returns:
            1.0 if pattern detected, 0.0 otherwise
        """
        if len(data.df) < 3:
            return 0.0

        # Run detection on the slice
        results = morning_star(data.df.copy())
        return 1.0 if results.iloc[-1] else 0.0


@FactorRegistry.register("three_white_soldiers")
@dataclass
class ThreeWhiteSoldiersFactor(Factor):
    """Three White Soldiers Candlestick Pattern Factor.

    Returns 1.0 if Three White Soldiers pattern is detected, 0.0 otherwise.
    """

    def compute(self, data: MarketDataSlice) -> float:
        """Compute the Three White Soldiers signal.

        Args:
            data: Market data slice

        Returns:
            1.0 if pattern detected, 0.0 otherwise
        """
        if len(data.df) < 3:
            return 0.0

        # Run detection on the slice
        results = three_white_soldiers(data.df.copy())
        return 1.0 if results.iloc[-1] else 0.0
