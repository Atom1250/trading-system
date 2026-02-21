"""Technical indicator calculations for trading strategies."""

from __future__ import annotations

import pandas as pd

__all__ = [
    "average_true_range",
    "bollinger_bands",
    "ema",
    "macd",
    "rsi",
    "sma",
    "morning_star",
    "three_white_soldiers",
]


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
    df: pd.DataFrame,
    window: int = 20,
    num_std: float = 2.0,
    column: str = "close",
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


def average_true_range(
    df: pd.DataFrame,
    window: int = 14,
    *,
    high_column: str = "high",
    low_column: str = "low",
    close_column: str = "close",
) -> pd.Series:
    """Calculate the Average True Range (ATR) for volatility-aware sizing.

    Args:
        df: DataFrame containing high, low, and close columns.
        window: Lookback window for the ATR smoothing period.
        high_column: Column name for session highs.
        low_column: Column name for session lows.
        close_column: Column name for session closes.

    Returns:
        The ATR series, also attached to the provided DataFrame with an
        ``ATR_<window>`` column name.

    """
    missing = [
        name
        for name in (high_column, low_column, close_column)
        if name not in df.columns
    ]
    if missing:
        raise KeyError(
            "Missing required columns for ATR calculation: " + ", ".join(missing),
        )

    high = df[high_column]
    low = df[low_column]
    close = df[close_column]
    previous_close = close.shift(1)

    true_range = pd.concat(
        [
            high - low,
            (high - previous_close).abs(),
            (low - previous_close).abs(),
        ],
        axis=1,
    ).max(axis=1)

    col_name = f"ATR_{window}"
    df[col_name] = true_range.rolling(window=window, min_periods=window).mean()
    return df[col_name]


def morning_star(df: pd.DataFrame) -> pd.Series:
    """Detect the Morning Star candlestick pattern.

    A three-candle bullish reversal pattern:
    1. Long bearish candle.
    2. Small body candle (star) that gaps down.
    3. Long bullish candle that closes above the midpoint of the first candle.

    Args:
        df: DataFrame with open, high, low, close columns.

    Returns:
        Boolean series indicating the presence of a Morning Star pattern.
    """
    required = ["open", "high", "low", "close"]
    if not all(col in df.columns for col in required):
        raise KeyError(
            f"Missing required columns: {[c for c in required if c not in df.columns]}"
        )

    body = (df["close"] - df["open"]).abs()
    candle_range = df["high"] - df["low"]
    is_bearish = df["close"] < df["open"]
    is_bullish = df["close"] > df["open"]

    # Condition 1: First candle is long and bearish
    cond1 = is_bearish.shift(2) & (body.shift(2) > 0.6 * candle_range.shift(2))

    # Condition 2: Second candle has a small body
    cond2 = body.shift(1) < 0.3 * candle_range.shift(1)

    # Condition 3: Third candle is bullish and closes above midpoint of first candle
    midpoint_first = (df["open"].shift(2) + df["close"].shift(2)) / 2
    cond3 = is_bullish & (df["close"] > midpoint_first)

    df["morning_star"] = cond1 & cond2 & cond3
    return df["morning_star"]


def three_white_soldiers(df: pd.DataFrame) -> pd.Series:
    """Detect the Three White Soldiers candlestick pattern.

    Three consecutive long-bodied bullish candles with increasing volume.

    Args:
        df: DataFrame with open, high, low, close, volume columns.

    Returns:
        Boolean series indicating the presence of Three White Soldiers.
    """
    required = ["open", "high", "low", "close", "volume"]
    if not all(col in df.columns for col in required):
        raise KeyError(
            f"Missing required columns: {[c for c in required if c not in df.columns]}"
        )

    is_bullish = df["close"] > df["open"]
    body = (df["close"] - df["open"]).abs()
    candle_range = df["high"] - df["low"]
    is_long_body = body > 0.5 * candle_range
    vol_increasing = df["volume"] > df["volume"].shift(1)

    # Each soldier must be bullish, have a long body, and increasing volume
    soldier = is_bullish & is_long_body & vol_increasing

    df["three_white_soldiers"] = soldier & soldier.shift(1) & soldier.shift(2)
    return df["three_white_soldiers"]
