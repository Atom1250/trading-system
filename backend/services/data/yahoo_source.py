"""Yahoo Finance data source implementation."""
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional
import pandas as pd

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from ingestion.yahoo_finance_client import YahooFinanceClient
from services.data.base import DataSource


class YahooDataSource(DataSource):
    """Yahoo Finance data source."""
    
    def __init__(self):
        self.client = YahooFinanceClient()
    
    def get_daily_prices(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Get daily prices from Yahoo Finance."""
        df = self.client.get_daily(symbol, start=start, end=end)
        return self._normalize_dataframe(df)
    
    def get_available_symbols(self) -> list[str]:
        """Get available symbols."""
        return []
    
    @property
    def name(self) -> str:
        return "yahoo"
    
    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize DataFrame to standard format."""
        if df.empty:
            return df
        
        # Yahoo returns adj_close, we'll use close
        required = ['open', 'high', 'low', 'close', 'volume']
        for col in required:
            if col not in df.columns:
                df[col] = None
        
        return df[required]
