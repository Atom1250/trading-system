"""Kaggle SQLite data source implementation."""

import sys
from datetime import datetime
from typing import Optional
from pathlib import Path

import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from repository.prices_repository import load_kaggle_prices
from services.data.base import DataSource


class KaggleDataSource(DataSource):
    """Kaggle SQLite database data source."""

    def get_daily_prices(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Get daily prices from Kaggle DB."""
        df = load_kaggle_prices(symbol)

        if df.empty:
            return df

        # Filter by date range if provided
        if start:
            df = df[df.index >= start]
        if end:
            df = df[df.index <= end]

        return self._normalize_dataframe(df)

    def get_available_symbols(self) -> list[str]:
        """Get available symbols from Kaggle DB."""
        # Would need to query the DB for distinct symbols
        return []

    @property
    def name(self) -> str:
        return "kaggle"

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize DataFrame to standard format."""
        if df.empty:
            return df

        required = ["open", "high", "low", "close", "volume"]
        for col in required:
            if col not in df.columns:
                df[col] = None

        return df[required]
