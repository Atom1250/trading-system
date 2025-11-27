"""Moving Average Crossover trading strategy implementation."""
from __future__ import annotations

import logging
import pandas as pd

from indicators.technicals import sma
from strategy.trade_management import apply_position_management


logger = logging.getLogger(__name__)


class MovingAverageCrossoverStrategy:
    """Generate buy and sell signals when SMAs cross over.

    Attributes:
        short_window: Window length for the fast SMA.
        long_window: Window length for the slow SMA.
    """

    def __init__(
        self,
        short_window: int = 50,
        long_window: int = 200,
        *,
        initial_capital: float = 100_000.0,
        risk_per_trade: float = 0.01,
        atr_window: int = 14,
        stop_atr_multiple: float = 1.5,
        take_profit_multiple: float = 2.0,
        max_drawdown_pct: float = 0.2,
        fundamentals: dict | None = None,
    ) -> None:
        if short_window <= 0 or long_window <= 0:
            raise ValueError("Window lengths must be positive integers.")
        if short_window >= long_window:
            raise ValueError("short_window must be smaller than long_window for a crossover strategy.")

        self.short_window = short_window
        self.long_window = long_window
        self.initial_capital = initial_capital
        self.risk_per_trade = risk_per_trade
        self.atr_window = atr_window
        self.stop_atr_multiple = stop_atr_multiple
        self.take_profit_multiple = take_profit_multiple
        self.max_drawdown_pct = max_drawdown_pct
        self.fundamentals = fundamentals or {}

        if self.fundamentals:
            logger.debug("Loaded fundamentals for strategy: keys=%s", list(self.fundamentals.keys()))

    def run(self, df: pd.DataFrame, price_column: str = "close") -> pd.DataFrame:
        """Run the strategy and return the DataFrame with signals.

        Args:
            df: DataFrame containing price data with a ``price_column`` column.
            price_column: Column name to use for SMA calculations. Defaults to ``close``.

        Returns:
            The input DataFrame with added SMA and signal columns.
        """
        if price_column not in df.columns:
            raise KeyError(f"Column '{price_column}' not found in DataFrame.")

        short_col = f"SMA_{self.short_window}"
        long_col = f"SMA_{self.long_window}"

        sma(df, window=self.short_window, column=price_column)
        sma(df, window=self.long_window, column=price_column)

        df["signal"] = 0
        df.loc[df[short_col] > df[long_col], "signal"] = 1
        df.loc[df[short_col] < df[long_col], "signal"] = -1

        df["positions"] = df["signal"].diff().fillna(0)

        band_columns = {"bb_middle", "bb_upper", "bb_lower"}
        if band_columns.issubset(df.columns):
            df["price_above_upper_band"] = (
                df[price_column].gt(df["bb_upper"]).fillna(False)
            )
            df["price_below_lower_band"] = (
                df[price_column].lt(df["bb_lower"]).fillna(False)
            )

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
