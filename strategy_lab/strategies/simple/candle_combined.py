from __future__ import annotations

import pandas as pd

from indicators.technicals import morning_star, three_white_soldiers
from strategy_lab.config import StrategyConfig
from strategy_lab.data.base import MarketDataSlice
from strategy_lab.strategies.base import FactorPanels, MarketDataSlices, Strategy


class CandleCombinedStrategy(Strategy):
    """Combined strategy using Morning Star and Three White Soldiers patterns.

    Logic:
    - Long entry on Morning Star pattern.
    - Long entry on Three White Soldiers pattern.
    """

    def __init__(self, config: StrategyConfig | None = None, **kwargs):
        """Initialize strategy with config or parameters."""
        if config is None:
            config = StrategyConfig(
                name="candle_combined",
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
        """Generate combined signals."""
        signals = {}

        for symbol, slice in data.items():
            df = slice.df.copy()
            morning_star(df)
            three_white_soldiers(df)

            df["signal"] = 0
            # Combine signals (OR logic)
            df.loc[df["morning_star"] | df["three_white_soldiers"], "signal"] = 1

            signals[symbol] = df["signal"]

        return signals
