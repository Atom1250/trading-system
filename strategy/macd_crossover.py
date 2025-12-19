"""MACD signal-line crossover trading strategy."""

from __future__ import annotations

import pandas as pd

from indicators.technicals import macd
from strategy.trade_management import apply_position_management


class MACDCrossoverStrategy:
    """Generate signals from MACD line and signal line crosses."""

    def __init__(
        self,
        fast_span: int = 12,
        slow_span: int = 26,
        signal_span: int = 9,
        *,
        initial_capital: float = 100_000.0,
        risk_per_trade: float = 0.01,
        atr_window: int = 14,
        stop_atr_multiple: float = 1.5,
        take_profit_multiple: float = 2.0,
        max_drawdown_pct: float = 0.2,
    ) -> None:
        if fast_span <= 0 or slow_span <= 0 or signal_span <= 0:
            raise ValueError("MACD spans must be positive integers.")
        if fast_span >= slow_span:
            raise ValueError("fast_span must be smaller than slow_span for MACD.")

        self.fast_span = fast_span
        self.slow_span = slow_span
        self.signal_span = signal_span
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.atr_window = atr_window
        self.stop_atr_multiple = stop_atr_multiple
        self.take_profit_multiple = take_profit_multiple
        self.max_drawdown_pct = max_drawdown_pct

    def run(self, df: pd.DataFrame, price_column: str = "close") -> pd.DataFrame:
        """Run the MACD crossover strategy and return the annotated DataFrame."""
        if price_column not in df.columns:
            raise KeyError(f"Column '{price_column}' not found in DataFrame.")

        macd(
            df,
            fast_span=self.fast_span,
            slow_span=self.slow_span,
            signal_span=self.signal_span,
            column=price_column,
        )

        df["signal"] = 0
        df.loc[df["MACD_line"] > df["MACD_signal"], "signal"] = 1
        df.loc[df["MACD_line"] < df["MACD_signal"], "signal"] = -1

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
