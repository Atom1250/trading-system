"""Strategies module - Strategy implementations for the lab environment."""

from strategy_lab.strategies.base import Signal, Strategy
from strategy_lab.strategies.model_strategy import ModelScoreStrategy
from strategy_lab.strategies.simple.candle_combined import CandleCombinedStrategy
from strategy_lab.strategies.simple.morning_star import MorningStarStrategy
from strategy_lab.strategies.simple.three_white_soldiers import (
    ThreeWhiteSoldiersStrategy,
)

__all__ = [
    "ModelScoreStrategy",
    "Signal",
    "Strategy",
    "MorningStarStrategy",
    "ThreeWhiteSoldiersStrategy",
    "CandleCombinedStrategy",
]
