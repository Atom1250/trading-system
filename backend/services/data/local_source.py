"""Local repository data source implementation."""
from datetime import datetime
from typing import Optional
import pandas as pd


from repository.prices_repository import load_local_prices
from services.data.base import DataSource


class LocalDataSource(DataSource):
    """Local CSV repository data source."""
    
    def get_daily_prices(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> pd.DataFrame:
        """Get daily prices from local repository."""
        df = load_local_prices(symbol)
        
        if df.empty:
            return df
        
        # Filter by date range if provided
        if start:
            df = df[df.index >= start]
        if end:
            df = df[df.index <= end]
        
        return self._normalize_dataframe(df)
    
    def get_available_symbols(self) -> list[str]:
        """Get available symbols from local repository."""
        # Would need to list CSV files in data/prices directory
        return []
    
    @property
    def name(self) -> str:
        return "local"
    
    def _normalize_dataframe(self, df: pd.DataFrame) -> pd.DataFrame:
        """Normalize DataFrame to standard format."""
        if df.empty:
            return df
        
        required = ['open', 'high', 'low', 'close', 'volume']
        for col in required:
            if col not in df.columns:
                df[col] = None
        
        return df[required]
