from __future__ import annotations

import pandas as pd

from indicators.technicals import three_white_soldiers
from strategy_lab.config import StrategyConfig
from strategy_lab.data.base import MarketDataSlice
from strategy_lab.strategies.base import FactorPanels, MarketDataSlices, Strategy


class ThreeWhiteSoldiersStrategy(Strategy):
    """Generate signals from Three White Soldiers candlestick patterns."""

    def __init__(self, config: StrategyConfig | None = None, **kwargs):
        """Initialize strategy with config or parameters."""
        if config is None:
            config = StrategyConfig(
                name="three_white_soldiers",
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
        """Generate Three White Soldiers signals."""
        signals = {}

        for symbol, slice in data.items():
            df = slice.df.copy()
            three_white_soldiers(df)

            df["signal"] = 0
            df.loc[df["three_white_soldiers"], "signal"] = 1

            signals[symbol] = df["signal"]

        return signals
