"""RSI mean-reversion trading strategy implementation."""
from __future__ import annotations

import pandas as pd

from indicators.technicals import rsi
from strategy.trade_management import apply_position_management


class RSIMeanReversionStrategy:
    """Enter long when RSI is oversold and short when overbought."""

    def __init__(
        self,
        period: int = 14,
        lower_threshold: float = 30.0,
        upper_threshold: float = 70.0,
        *,
        initial_capital: float = 100_000.0,
        risk_per_trade: float = 0.01,
        atr_window: int = 14,
        stop_atr_multiple: float = 1.5,
        take_profit_multiple: float = 2.0,
        max_drawdown_pct: float = 0.2,
    ) -> None:
        if period <= 0:
            raise ValueError("RSI period must be a positive integer.")
        if lower_threshold >= upper_threshold:
            raise ValueError("lower_threshold must be less than upper_threshold.")

        self.period = period
        self.lower_threshold = lower_threshold
        self.upper_threshold = upper_threshold
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.atr_window = atr_window
        self.stop_atr_multiple = stop_atr_multiple
        self.take_profit_multiple = take_profit_multiple
        self.max_drawdown_pct = max_drawdown_pct

    def run(self, df: pd.DataFrame, price_column: str = "close") -> pd.DataFrame:
        """Run the RSI mean-reversion strategy and return the annotated DataFrame."""

        if price_column not in df.columns:
            raise KeyError(f"Column '{price_column}' not found in DataFrame.")

        rsi(df, period=self.period, column=price_column)

        rsi_col = f"RSI_{self.period}"
        df["signal"] = 0
        df.loc[df[rsi_col] < self.lower_threshold, "signal"] = 1
        df.loc[df[rsi_col] > self.upper_threshold, "signal"] = -1

        df["positions"] = df["signal"].diff().fillna(0)

        managed = apply_position_management(
            df,
            price_column=price_column,
            initial_capital=self.initial_capital,
            risk_per_trade=self.risk_per_trade,
            atr_window=self.atr_window,
            stop_atr_multiple=self.stop_atr_multiple,
            take_profit_multiple=self.take_profit_multiple,
            max_drawdown_pct=self.max_drawdown_pct,
        )

        return managed
