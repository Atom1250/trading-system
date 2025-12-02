"""Data validation utilities for price data."""
from __future__ import annotations

import logging
from typing import List

import pandas as pd

logger = logging.getLogger(__name__)


def validate_price_data(df: pd.DataFrame, symbol: str = "Unknown") -> tuple[bool, List[str]]:
    """
    Validate price data DataFrame for common issues.
    
    Args:
        df: DataFrame to validate
        symbol: Symbol name for logging
        
    Returns:
        Tuple of (is_valid, list_of_warnings)
    """
    warnings = []
    is_valid = True
    
    if df.empty:
        warnings.append(f"DataFrame is empty for {symbol}")
        return False, warnings
    
    # Check required columns
    required_cols = ['open', 'high', 'low', 'close', 'volume']
    missing_cols = [col for col in required_cols if col not in df.columns]
    
    if missing_cols:
        warnings.append(f"Missing required columns for {symbol}: {missing_cols}")
        is_valid = False
    
    if not is_valid:
        return is_valid, warnings
    
    # Check for null values
    null_counts = df[required_cols].isnull().sum()
    if null_counts.any():
        for col, count in null_counts[null_counts > 0].items():
            warnings.append(f"{symbol}: Column '{col}' has {count} null values ({count/len(df)*100:.1f}%)")
    
    # Check for invalid OHLC relationships
    invalid_high_low = (df['high'] < df['low']).sum()
    if invalid_high_low > 0:
        warnings.append(f"{symbol}: {invalid_high_low} rows where high < low (data corruption)")
        is_valid = False
    
    invalid_high_close = (df['high'] < df['close']).sum()
    if invalid_high_close > 0:
        warnings.append(f"{symbol}: {invalid_high_close} rows where high < close")
    
    invalid_low_close = (df['low'] > df['close']).sum()
    if invalid_low_close > 0:
        warnings.append(f"{symbol}: {invalid_low_close} rows where low > close")
    
    invalid_high_open = (df['high'] < df['open']).sum()
    if invalid_high_open > 0:
        warnings.append(f"{symbol}: {invalid_high_open} rows where high < open")
    
    invalid_low_open = (df['low'] > df['open']).sum()
    if invalid_low_open > 0:
        warnings.append(f"{symbol}: {invalid_low_open} rows where low > open")
    
    # Check for negative prices
    negative_prices = (df[['open', 'high', 'low', 'close']] < 0).any(axis=1).sum()
    if negative_prices > 0:
        warnings.append(f"{symbol}: {negative_prices} rows with negative prices (data corruption)")
        is_valid = False
    
    # Check for zero prices
    zero_prices = (df[['open', 'high', 'low', 'close']] == 0).any(axis=1).sum()
    if zero_prices > 0:
        warnings.append(f"{symbol}: {zero_prices} rows with zero prices")
    
    # Check for negative volume
    if 'volume' in df.columns:
        negative_volume = (df['volume'] < 0).sum()
        if negative_volume > 0:
            warnings.append(f"{symbol}: {negative_volume} rows with negative volume")
            is_valid = False
    
    # Check for duplicate dates
    if isinstance(df.index, pd.DatetimeIndex):
        duplicates = df.index.duplicated().sum()
        if duplicates > 0:
            warnings.append(f"{symbol}: {duplicates} duplicate dates found")
    
    # Check for large gaps in data
    if isinstance(df.index, pd.DatetimeIndex) and len(df) > 1:
        date_diffs = df.index.to_series().diff()
        max_gap = date_diffs.max()
        if max_gap > pd.Timedelta(days=30):
            warnings.append(f"{symbol}: Maximum gap in data is {max_gap.days} days")
    
    # Check for extreme price movements (potential data errors)
    if len(df) > 1:
        returns = df['close'].pct_change()
        extreme_returns = returns[abs(returns) > 0.5]  # >50% daily move
        if len(extreme_returns) > 0:
            warnings.append(
                f"{symbol}: {len(extreme_returns)} days with >50% price movement "
                f"(max: {extreme_returns.abs().max():.1%})"
            )
    
    # Log warnings
    for warning in warnings:
        if "corruption" in warning.lower():
            logger.error(warning)
        else:
            logger.warning(warning)
    
    return is_valid, warnings


def clean_price_data(df: pd.DataFrame, symbol: str = "Unknown") -> pd.DataFrame:
    """
    Clean price data by removing or fixing common issues.
    
    Args:
        df: DataFrame to clean
        symbol: Symbol name for logging
        
    Returns:
        Cleaned DataFrame
    """
    if df.empty:
        return df
    
    df_clean = df.copy()
    
    # Remove rows with null values in critical columns
    critical_cols = ['open', 'high', 'low', 'close']
    before_count = len(df_clean)
    df_clean = df_clean.dropna(subset=critical_cols)
    removed = before_count - len(df_clean)
    if removed > 0:
        logger.info(f"{symbol}: Removed {removed} rows with null values")
    
    # Remove duplicate dates
    if isinstance(df_clean.index, pd.DatetimeIndex):
        before_count = len(df_clean)
        df_clean = df_clean[~df_clean.index.duplicated(keep='last')]
        removed = before_count - len(df_clean)
        if removed > 0:
            logger.info(f"{symbol}: Removed {removed} duplicate dates")
    
    # Remove rows with invalid OHLC relationships
    before_count = len(df_clean)
    df_clean = df_clean[df_clean['high'] >= df_clean['low']]
    removed = before_count - len(df_clean)
    if removed > 0:
        logger.warning(f"{symbol}: Removed {removed} rows where high < low")
    
    # Remove rows with negative or zero prices
    before_count = len(df_clean)
    df_clean = df_clean[
        (df_clean['open'] > 0) &
        (df_clean['high'] > 0) &
        (df_clean['low'] > 0) &
        (df_clean['close'] > 0)
    ]
    removed = before_count - len(df_clean)
    if removed > 0:
        logger.warning(f"{symbol}: Removed {removed} rows with non-positive prices")
    
    # Fix negative volume
    if 'volume' in df_clean.columns:
        negative_vol = (df_clean['volume'] < 0).sum()
        if negative_vol > 0:
            df_clean.loc[df_clean['volume'] < 0, 'volume'] = 0
            logger.warning(f"{symbol}: Set {negative_vol} negative volume values to 0")
    
    # Sort by date
    if isinstance(df_clean.index, pd.DatetimeIndex):
        df_clean = df_clean.sort_index()
    
    return df_clean
