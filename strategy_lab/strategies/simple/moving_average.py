from __future__ import annotations

import pandas as pd

from indicators.technicals import sma
from strategy_lab.config import StrategyConfig
from strategy_lab.data.base import MarketDataSlice
from strategy_lab.strategies.base import FactorPanels, MarketDataSlices, Strategy


class MovingAverageCrossoverStrategy(Strategy):
    """Generate buy and sell signals when SMAs cross over."""

    def __init__(
        self,
        config: StrategyConfig | None = None,
        short_window: int = 50,
        long_window: int = 200,
    ):
        """Initialize strategy with config or legacy constructor kwargs."""
        if config is None:
            config = StrategyConfig(
                name="moving_average_crossover",
                parameters={
                    "short_window": short_window,
                    "long_window": long_window,
                },
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
        """Generate MA crossover signals."""
        signals = {}

        # Get parameters from config
        short_window = int(self.config.parameters.get("short_window", 50))
        long_window = int(self.config.parameters.get("long_window", 200))

        for symbol, slice in data.items():
            df = slice.df.copy()
            sma(df, window=short_window, column="close")
            sma(df, window=long_window, column="close")

            short_col = f"SMA_{short_window}"
            long_col = f"SMA_{long_window}"

            df["signal"] = 0
            df.loc[df[short_col] > df[long_col], "signal"] = 1
            df.loc[df[short_col] < df[long_col], "signal"] = -1

            signals[symbol] = df["signal"]

        return signals
