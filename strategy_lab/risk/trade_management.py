"""Trade management helpers for P&L tracking and risk controls."""

from __future__ import annotations

import pandas as pd

from indicators.technicals import average_true_range


def apply_position_management(
    df: pd.DataFrame,
    price_column: str = "close",
    *,
    initial_capital: float = 100_000.0,
    risk_per_trade: float = 0.01,
    atr_window: int = 14,
    stop_atr_multiple: float = 1.5,
    take_profit_multiple: float = 2.0,
    max_drawdown_pct: float = 0.2,
    high_column: str = "high",
    low_column: str = "low",
) -> pd.DataFrame:
    """Annotate a strategy frame with P&L, sizing, and risk overlays.

    The helper expects a ``signal`` column where +1 denotes long, -1 denotes
    short, and 0 denotes flat. It computes position-aware returns, notional
    exposure, ATR-based sizing guidance, and risk stops (stop loss, take
    profit, and drawdown halts).
    """
    if price_column not in df.columns:
        raise KeyError(f"Column '{price_column}' not found in DataFrame.")

    working = df.copy()

    atr = average_true_range(
        working,
        window=atr_window,
        high_column=high_column,
        low_column=low_column,
        close_column=price_column,
    )
    working["atr"] = atr

    working["position"] = working["signal"].shift().fillna(0)
    working["price_return"] = working[price_column].pct_change().fillna(0)
    working["strategy_return"] = working["position"] * working["price_return"]
    working["equity"] = (1 + working["strategy_return"]).cumprod() * initial_capital
    working["pnl"] = working["equity"].diff().fillna(0)
    working["cumulative_pnl"] = working["pnl"].cumsum()

    risk_capital = initial_capital * risk_per_trade
    stop_distance = working["atr"] * stop_atr_multiple
    stop_distance = stop_distance.replace(0, pd.NA)
    working["position_size_units"] = (risk_capital / stop_distance).fillna(0)
    working.loc[stop_distance <= 0, "position_size_units"] = 0

    working["position_size_units_signed"] = working["position_size_units"] * working[
        "signal"
    ].fillna(0)
    working["notional_exposure"] = (
        working["position_size_units_signed"] * working[price_column]
    )

    direction = working["signal"].fillna(0)
    stop_offset = stop_atr_multiple * working["atr"]
    tp_offset = take_profit_multiple * stop_offset

    working["stop_loss_price"] = working[price_column] - stop_offset.where(
        direction >= 0,
        -stop_offset,
    )
    working["take_profit_price"] = working[price_column] + tp_offset.where(
        direction >= 0,
        -tp_offset,
    )

    peak_equity = working["equity"].cummax()
    working["drawdown_pct"] = (working["equity"] - peak_equity) / peak_equity.replace(
        0,
        pd.NA,
    )
    working["halt_trading"] = working["drawdown_pct"] <= -max_drawdown_pct
    working["risk_adjusted_signal"] = working["signal"].where(
        ~working["halt_trading"],
        0,
    )

    return working
