from __future__ import annotations

import pandas as pd

from indicators.technicals import rsi
from strategy_lab.strategies.base import FactorPanels, MarketDataSlices, Strategy


class RSIMeanReversionStrategy(Strategy):
    """Enter long when RSI is oversold and short when overbought."""

    def generate_signals(
        self,
        data: MarketDataSlices,
        factor_panels: FactorPanels,
    ) -> dict[str, pd.Series]:
        """Generate RSI mean-reversion signals."""
        signals = {}

        # Get parameters from config
        period = int(self.config.parameters.get("period", 14))
        lower_threshold = float(self.config.parameters.get("lower_threshold", 30.0))
        upper_threshold = float(self.config.parameters.get("upper_threshold", 70.0))

        for symbol, slice in data.items():
            df = slice.df.copy()
            rsi(df, period=period, column="close")

            rsi_col = f"RSI_{period}"
            df["signal"] = 0
            df.loc[df[rsi_col] < lower_threshold, "signal"] = 1
            df.loc[df[rsi_col] > upper_threshold, "signal"] = -1

            signals[symbol] = df["signal"]

        return signals
