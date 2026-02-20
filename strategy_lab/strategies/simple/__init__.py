"""Simple trading strategies (MA, MACD, RSI).

This module contains simple, single-indicator strategies that were
migrated from the legacy `strategy/` module. These strategies are
now part of the unified `strategy_lab` framework.

Strategies:
- MovingAverageCrossoverStrategy: MA crossover signals
- MACDCrossoverStrategy: MACD crossover signals
- RSIMeanReversionStrategy: RSI mean reversion signals
"""

from .macd import MACDCrossoverStrategy
from .moving_average import MovingAverageCrossoverStrategy
from .rsi import RSIMeanReversionStrategy
from .trend_pullback import TrendPullbackStrategy

__all__ = [
    'MovingAverageCrossoverStrategy',
    'MACDCrossoverStrategy',
    'RSIMeanReversionStrategy',
    'TrendPullbackStrategy',
]
