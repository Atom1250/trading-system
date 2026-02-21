from __future__ import annotations

import pandas as pd

from indicators.technicals import morning_star
from strategy_lab.config import StrategyConfig
from strategy_lab.data.base import MarketDataSlice
from strategy_lab.strategies.base import FactorPanels, MarketDataSlices, Strategy


class MorningStarStrategy(Strategy):
    """Generate signals from Morning Star candlestick patterns."""

    def __init__(self, config: StrategyConfig | None = None, **kwargs):
        """Initialize strategy with config or parameters."""
        if config is None:
            config = StrategyConfig(
                name="morning_star",
                parameters=kwargs,
            )
        super().__init__(config)

    def run(self, df: pd.DataFrame) -> pd.DataFrame:
        """Legacy convenience runner returning DataFrame with signal column."""
        data = {"SYMBOL": MarketDataSlice(symbol="SYMBOL", df=df)}
        signals = self.generate_signals(data, {})
        result = df.copy()
        result["signal"] = signals["SYMBOL"]
        return result

    def generate_signals(
        self,
        data: MarketDataSlices,
        factor_panels: FactorPanels,
    ) -> dict[str, pd.Series]:
        """Generate Morning Star signals."""
        signals = {}

        for symbol, slice in data.items():
            df = slice.df.copy()
            morning_star(df)

            df["signal"] = 0
            df.loc[df["morning_star"], "signal"] = 1

            signals[symbol] = df["signal"]

        return signals
