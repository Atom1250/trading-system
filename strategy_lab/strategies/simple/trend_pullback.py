from __future__ import annotations
import pandas as pd
from indicators.technicals import ema, rsi
from strategy_lab.strategies.base import Strategy, MarketDataSlices, FactorPanels

class TrendPullbackStrategy(Strategy):
    """
    Trade pullbacks in a strong trend.
    Rules:
    - Long entry: Close > EMA(50) AND RSI(14) > 40 AND RSI(14) > RSI(14)[1]
    """

    def generate_signals(
        self,
        data: MarketDataSlices,
        factor_panels: FactorPanels,
    ) -> dict[str, pd.Series]:
        """Generate trend pullback signals."""
        signals = {}
        
        # Get parameters from config
        ema_period = int(self.config.parameters.get("ema_period", 50))
        rsi_period = int(self.config.parameters.get("rsi_period", 14))
        rsi_threshold = float(self.config.parameters.get("rsi_threshold", 40.0))
        
        for symbol, slice in data.items():
            df = slice.df.copy()
            
            # Calculate indicators
            ema(df, span=ema_period, column="close")
            rsi(df, period=rsi_period, column="close")
            
            ema_col = f"EMA_{ema_period}"
            rsi_col = f"RSI_{rsi_period}"
            
            df["signal"] = 0
            
            # Long Rules
            # 1. Price is above the EMA
            # 2. RSI stays above threshold
            # 3. RSI turns up (momentum confirmation)
            df.loc[
                (df["close"] > df[ema_col]) & 
                (df[rsi_col] > rsi_threshold) & 
                (df[rsi_col] > df[rsi_col].shift(1)), 
                "signal"
            ] = 1
            
            signals[symbol] = df["signal"]
            
        return signals
