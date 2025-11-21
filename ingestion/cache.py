"""Simple local cache for daily OHLCV data."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

import pandas as pd

CACHE_DIR = Path("data_cache")


def _normalized_outputsize(outputsize: Optional[str]) -> str:
    return (outputsize or "compact").lower()


def _parquet_path(symbol: str, outputsize: Optional[str]) -> Path:
    suffix = _normalized_outputsize(outputsize)
    return CACHE_DIR / f"{symbol.upper()}_{suffix}.parquet"


def _csv_path(symbol: str, outputsize: Optional[str]) -> Path:
    suffix = _normalized_outputsize(outputsize)
    return CACHE_DIR / f"{symbol.upper()}_{suffix}.csv"


def load_cached_daily(symbol: str, outputsize: Optional[str] = "compact") -> Optional[pd.DataFrame]:
    """Load cached daily OHLCV data for the given symbol and output size.

    Returns a DataFrame indexed by date or ``None`` if no matching cache exists.
    """

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    parquet_file = _parquet_path(symbol, outputsize)
    csv_file = _csv_path(symbol, outputsize)

    if parquet_file.exists():
        try:
            df = pd.read_parquet(parquet_file)
            df.sort_index(inplace=True)
            return df
        except Exception:
            # Fall through to CSV if parquet cannot be read
            pass

    if csv_file.exists():
        try:
            df = pd.read_csv(csv_file, parse_dates=["date"], index_col="date")
            df.sort_index(inplace=True)
            return df
        except Exception:
            return None

    return None


def save_cached_daily(symbol: str, df: pd.DataFrame, outputsize: Optional[str] = "compact") -> None:
    """Save the given daily OHLCV DataFrame to a local cache for the symbol/output size."""

    CACHE_DIR.mkdir(parents=True, exist_ok=True)

    parquet_file = _parquet_path(symbol, outputsize)
    csv_file = _csv_path(symbol, outputsize)

    try:
        df.to_parquet(parquet_file)
    except Exception:
        df.to_csv(csv_file, index_label="date")
