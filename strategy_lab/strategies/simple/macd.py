from __future__ import annotations

import pandas as pd

from indicators.technicals import macd
from strategy_lab.strategies.base import FactorPanels, MarketDataSlices, Strategy


class MACDCrossoverStrategy(Strategy):
    """Generate signals from MACD line and signal line crosses."""

    def generate_signals(
        self,
        data: MarketDataSlices,
        factor_panels: FactorPanels,
    ) -> dict[str, pd.Series]:
        """Generate MACD crossover signals."""
        signals = {}

        # Get parameters from config
        fast_span = int(self.config.parameters.get("fast_span", 12))
        slow_span = int(self.config.parameters.get("slow_span", 26))
        signal_span = int(self.config.parameters.get("signal_span", 9))

        for symbol, slice in data.items():
            df = slice.df.copy()
            macd(
                df,
                fast_span=fast_span,
                slow_span=slow_span,
                signal_span=signal_span,
                column="close",
            )

            df["signal"] = 0
            df.loc[df["MACD_line"] > df["MACD_signal"], "signal"] = 1
            df.loc[df["MACD_line"] < df["MACD_signal"], "signal"] = -1

            signals[symbol] = df["signal"]

        return signals
