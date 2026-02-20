from __future__ import annotations
import pandas as pd
from indicators.technicals import sma
from strategy_lab.strategies.base import Strategy, MarketDataSlices, FactorPanels

class MovingAverageCrossoverStrategy(Strategy):
    """Generate buy and sell signals when SMAs cross over."""

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
