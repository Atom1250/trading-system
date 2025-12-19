"""Volume related factors."""

from dataclasses import dataclass

from strategy_lab.data.base import MarketDataSlice
from strategy_lab.factors.base import Factor, FactorRegistry


@FactorRegistry.register("avg_volume")
@dataclass
class AverageVolumeFactor(Factor):
    """Rolling Average Volume Factor."""

    window: int = 20

    def compute(self, data: MarketDataSlice) -> float:
        if len(data.df) < self.window:
            return 0.0
        return data.df["volume"].rolling(window=self.window).mean().iloc[-1]


@FactorRegistry.register("daily_return")
@dataclass
class DailyReturnFactor(Factor):
    """Daily Return Factor."""

    def compute(self, data: MarketDataSlice) -> float:
        if len(data.df) < 2:
            return 0.0
        return data.df["close"].pct_change().iloc[-1]
