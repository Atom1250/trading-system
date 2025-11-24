"""Technical indicator calculations for trading strategies."""
from __future__ import annotations

import pandas as pd


__all__ = ["sma", "ema", "rsi", "macd", "bollinger_bands"]


def sma(df: pd.DataFrame, window: int = 14, column: str = "close") -> pd.Series:
    """Calculate the Simple Moving Average (SMA).

    Args:
        df: DataFrame containing price data with a ``column`` column.
        window: Window length for the rolling mean.
        column: Column name to use for calculation.

    Returns:
        The SMA series, also attached to the provided DataFrame with a
        ``SMA_<window>`` column name.
    """
    col_name = f"SMA_{window}"
    df[col_name] = df[column].rolling(window=window, min_periods=window).mean()
    return df[col_name]


def ema(df: pd.DataFrame, span: int = 14, column: str = "close") -> pd.Series:
    """Calculate the Exponential Moving Average (EMA).

    Args:
        df: DataFrame containing price data with a ``column`` column.
        span: Span for the exponential weighted average.
        column: Column name to use for calculation.

    Returns:
        The EMA series, also attached to the provided DataFrame with an
        ``EMA_<span>`` column name.
    """
    col_name = f"EMA_{span}"
    df[col_name] = df[column].ewm(span=span, adjust=False).mean()
    return df[col_name]


def rsi(df: pd.DataFrame, period: int = 14, column: str = "close") -> pd.Series:
    """Calculate the Relative Strength Index (RSI).

    Args:
        df: DataFrame containing price data with a ``column`` column.
        period: Lookback period for RSI calculation.
        column: Column name to use for calculation.

    Returns:
        The RSI series, also attached to the provided DataFrame with an
        ``RSI_<period>`` column name.
    """
    delta = df[column].diff()
    gain = delta.where(delta > 0, 0.0)
    loss = -delta.where(delta < 0, 0.0)

    avg_gain = gain.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()
    avg_loss = loss.ewm(alpha=1 / period, adjust=False, min_periods=period).mean()

    rs = avg_gain / avg_loss
    rsi_series = 100 - (100 / (1 + rs))

    col_name = f"RSI_{period}"
    df[col_name] = rsi_series
    return df[col_name]


def macd(
    df: pd.DataFrame,
    fast_span: int = 12,
    slow_span: int = 26,
    signal_span: int = 9,
    column: str = "close",
) -> pd.Series:
    """Calculate the Moving Average Convergence Divergence (MACD).

    Args:
        df: DataFrame containing price data with a ``column`` column.
        fast_span: Span for the fast EMA.
        slow_span: Span for the slow EMA.
        signal_span: Span for the signal line EMA.
        column: Column name to use for calculation.

    Returns:
        The MACD histogram series, also attached to the DataFrame as
        ``MACD_hist``. Additional columns ``MACD_line`` and ``MACD_signal``
        are included for reference.
    """
    fast_ema = df[column].ewm(span=fast_span, adjust=False).mean()
    slow_ema = df[column].ewm(span=slow_span, adjust=False).mean()

    macd_line = fast_ema - slow_ema
    signal_line = macd_line.ewm(span=signal_span, adjust=False).mean()
    macd_hist = macd_line - signal_line

    df["MACD_line"] = macd_line
    df["MACD_signal"] = signal_line
    df["MACD_hist"] = macd_hist

    return df["MACD_hist"]


def bollinger_bands(
    df: pd.DataFrame, window: int = 20, num_std: float = 2.0, column: str = "close"
) -> pd.DataFrame:
    """Calculate Bollinger Bands on the ``column`` price.

    Adds ``bb_middle``, ``bb_upper``, and ``bb_lower`` columns to the DataFrame and
    returns the DataFrame.
    """
    if column not in df.columns:
        raise KeyError(f"Column '{column}' not found in DataFrame.")

    rolling = df[column].rolling(window=window, min_periods=window)
    rolling_mean = rolling.mean()
    rolling_std = rolling.std()

    df["bb_middle"] = rolling_mean
    df["bb_upper"] = rolling_mean + num_std * rolling_std
    df["bb_lower"] = rolling_mean - num_std * rolling_std

    df[["bb_middle", "bb_upper", "bb_lower"]] = df[
        ["bb_middle", "bb_upper", "bb_lower"]
    ].astype(float)

    return df
