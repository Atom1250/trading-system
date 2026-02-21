"""Simple trading strategies (MA, MACD, RSI).

This module contains simple, single-indicator strategies that were
migrated from the legacy `strategy/` module. These strategies are
now part of the unified `strategy_lab` framework.

Strategies:
- MovingAverageCrossoverStrategy: MA crossover signals
- MACDCrossoverStrategy: MACD crossover signals
- RSIMeanReversionStrategy: RSI mean reversion signals
"""

from .candle_combined import CandleCombinedStrategy
from .macd import MACDCrossoverStrategy
from .morning_star import MorningStarStrategy
from .moving_average import MovingAverageCrossoverStrategy
from .rsi import RSIMeanReversionStrategy
from .three_white_soldiers import ThreeWhiteSoldiersStrategy
from .trend_pullback import TrendPullbackStrategy

__all__ = [
    "MovingAverageCrossoverStrategy",
    "MACDCrossoverStrategy",
    "RSIMeanReversionStrategy",
    "TrendPullbackStrategy",
    "MorningStarStrategy",
    "ThreeWhiteSoldiersStrategy",
    "CandleCombinedStrategy",
]
