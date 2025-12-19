"""Data validation utilities for price data.

Refactored to reduce complexity by extracting smaller helper
functions and adding clearer, testable logic paths.
"""

from __future__ import annotations

import logging
from typing import List, Tuple

import pandas as pd

logger = logging.getLogger(__name__)

EXTREME_RETURN_THRESHOLD: float = 0.5


def _required_columns() -> List[str]:
    return ["open", "high", "low", "close", "volume"]


def _log_warnings(symbol: str, warnings: List[str]) -> None:
    for warning in warnings:
        if "corruption" in warning.lower():
            logger.error(warning)
        else:
            logger.warning(warning)


def _check_required_columns(df: pd.DataFrame, symbol: str) -> Tuple[bool, List[str]]:
    required = _required_columns()
    missing = [c for c in required if c not in df.columns]
    if missing:
        return False, [f"Missing required columns for {symbol}: {missing}"]
    return True, []


def _check_nulls(df: pd.DataFrame, symbol: str) -> List[str]:
    warnings: List[str] = []
    cols = [c for c in _required_columns() if c in df.columns]
    null_counts = df[cols].isna().sum()
    for col, count in null_counts[null_counts > 0].items():
        pct = count / len(df) * 100
        warnings.append(f"{symbol}: Column '{col}' has {count} null values ({pct:.1f}%)")
    return warnings


def _check_ohlc_relationships(df: pd.DataFrame, symbol: str) -> Tuple[bool, List[str]]:
    warnings: List[str] = []
    is_valid = True

    high_lt_low = (df["high"] < df["low"]).sum()
    if high_lt_low:
        warnings.append(f"{symbol}: {high_lt_low} rows where high < low (data corruption)")
        is_valid = False

    # Non-fatal anomalies
    checks = [
        ("high < close", (df["high"] < df["close"]).sum()),
        ("low > close", (df["low"] > df["close"]).sum()),
        ("high < open", (df["high"] < df["open"]).sum()),
        ("low > open", (df["low"] > df["open"]).sum()),
    ]

    for desc, count in checks:
        if count:
            warnings.append(f"{symbol}: {count} rows where {desc}")

    return is_valid, warnings


def _check_prices_and_volume(df: pd.DataFrame, symbol: str) -> Tuple[bool, List[str]]:
    warnings: List[str] = []
    is_valid = True

    if any(c in df.columns for c in ["open", "high", "low", "close"]):
        negative_prices = (df[["open", "high", "low", "close"]] < 0).any(axis=1).sum()
        if negative_prices:
            warnings.append(f"{symbol}: {negative_prices} rows with negative prices (data corruption)")
            is_valid = False

        zero_prices = (df[["open", "high", "low", "close"]] == 0).any(axis=1).sum()
        if zero_prices:
            warnings.append(f"{symbol}: {zero_prices} rows with zero prices")

    if "volume" in df.columns:
        neg_vol = (df["volume"] < 0).sum()
        if neg_vol:
            warnings.append(f"{symbol}: {neg_vol} rows with negative volume")
            is_valid = False

    return is_valid, warnings


def _check_duplicates_and_gaps(df: pd.DataFrame, symbol: str) -> List[str]:
    warnings: List[str] = []
    if isinstance(df.index, pd.DatetimeIndex):
        duplicates = df.index.duplicated().sum()
        if duplicates:
            warnings.append(f"{symbol}: {duplicates} duplicate dates found")

        if len(df) > 1:
            date_diffs = df.index.to_series().diff()
            max_gap = date_diffs.max()
            if max_gap and max_gap > pd.Timedelta(days=30):
                warnings.append(f"{symbol}: Maximum gap in data is {getattr(max_gap, 'days', max_gap)} days")

    return warnings


def _check_extreme_returns(df: pd.DataFrame, symbol: str) -> List[str]:
    warnings: List[str] = []
    if len(df) <= 1 or "close" not in df.columns:
        return warnings

    returns = df["close"].pct_change()
    extreme = returns[returns.abs() > EXTREME_RETURN_THRESHOLD]
    if len(extreme) > 0:
        max_ret = extreme.abs().max()
        warnings.append(
            f"{symbol}: {len(extreme)} days with >{int(EXTREME_RETURN_THRESHOLD * 100)}% price movement (max: {max_ret:.1%})"
        )
    return warnings


def validate_price_data(df: pd.DataFrame, symbol: str = "Unknown") -> Tuple[bool, List[str]]:
    """Validate price data and return (is_valid, warnings).

    This function inspects an OHLCV DataFrame for common issues
    such as missing columns, nulls, negative prices, duplicates,
    and extreme returns. It returns a boolean validity flag and
    a list of human-readable warnings.
    """
    warnings: List[str] = []

    if df.empty:
        warnings.append(f"DataFrame is empty for {symbol}")
        _log_warnings(symbol, warnings)
        return False, warnings

    ok, missing_warnings = _check_required_columns(df, symbol)
    if not ok:
        warnings.extend(missing_warnings)
        _log_warnings(symbol, warnings)
        return False, warnings

    warnings.extend(_check_nulls(df, symbol))

    ohlc_ok, ohlc_warnings = _check_ohlc_relationships(df, symbol)
    warnings.extend(ohlc_warnings)

    prices_ok, price_warnings = _check_prices_and_volume(df, symbol)
    warnings.extend(price_warnings)

    warnings.extend(_check_duplicates_and_gaps(df, symbol))
    warnings.extend(_check_extreme_returns(df, symbol))

    # Determine overall validity
    is_valid = ohlc_ok and prices_ok

    _log_warnings(symbol, warnings)
    return is_valid, warnings


def clean_price_data(df: pd.DataFrame, symbol: str = "Unknown") -> pd.DataFrame:
    """Clean price data and return the cleaned DataFrame.

    The function removes rows with missing critical OHLC values,
    duplicates, invalid OHLC relationships, out-of-range prices,
    and fixes negative volumes where applicable.
    """
    if df.empty:
        return df

    df_clean = df.copy()

    # Drop rows missing critical OHLC
    critical_cols = ["open", "high", "low", "close"]
    before = len(df_clean)
    df_clean = df_clean.dropna(subset=critical_cols)
    removed = before - len(df_clean)
    if removed:
        logger.info("%s: Removed %d rows with null values", symbol, removed)

    # Remove duplicate dates (keep last)
    if isinstance(df_clean.index, pd.DatetimeIndex):
        before = len(df_clean)
        df_clean = df_clean[~df_clean.index.duplicated(keep="last")]
        removed = before - len(df_clean)
        if removed:
            logger.info("%s: Removed %d duplicate dates", symbol, removed)

    # Keep only valid OHLC rows
    before = len(df_clean)
    df_clean = df_clean[df_clean["high"] >= df_clean["low"]]
    removed = before - len(df_clean)
    if removed:
        logger.warning("%s: Removed %d rows where high < low", symbol, removed)

    # Remove non-positive prices
    before = len(df_clean)
    df_clean = df_clean[(df_clean["open"] > 0) & (df_clean["high"] > 0) & (df_clean["low"] > 0) & (df_clean["close"] > 0)]
    removed = before - len(df_clean)
    if removed:
        logger.warning("%s: Removed %d rows with non-positive prices", symbol, removed)

    # Fix negative volume
    if "volume" in df_clean.columns:
        neg = (df_clean["volume"] < 0).sum()
        if neg:
            df_clean.loc[df_clean["volume"] < 0, "volume"] = 0
            logger.warning("%s: Set %d negative volume values to 0", symbol, neg)

    # Sort by date if index is datetime
    if isinstance(df_clean.index, pd.DatetimeIndex):
        df_clean = df_clean.sort_index()

    return df_clean
