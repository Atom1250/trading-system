"""FMP data source implementation."""

import sys
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd

# Add parent directory to path to import from existing codebase
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ingestion.fmp_client import FMPClient
from services.data.base import DataSource


class FMPDataSource(DataSource):
    """Financial Modeling Prep data source."""

    def __init__(self):
        self.client = FMPClient()

    def get_daily_prices(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """Get daily prices from FMP."""
        df = self.client.get_daily(symbol, start_date=start, end_date=end)
        return self._normalize_dataframe(df)

    def get_available_symbols(self) -> list[str]:
        """Get available symbols from FMP."""
        # FMP doesn't have a simple list endpoint, return empty for now
        return []

    @property
    def name(self) -> str:
        return "fmp"

    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize DataFrame to standard format."""
        if df.empty:
            return df

        # Ensure required columns exist
        required = ["open", "high", "low", "close", "volume"]
        for col in required:
            if col not in df.columns:
                df[col] = None

        return df[required]
