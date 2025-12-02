"""Data source abstraction layer."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional
import pandas as pd


class DataSource(ABC):
    """Abstract base class for data sources."""
    
    @abstractmethod
    def get_daily_prices(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None
    ) -> pd.DataFrame:
        """
        Get daily OHLCV data for a symbol.
        
        Returns DataFrame with columns: open, high, low, close, volume
        and DatetimeIndex.
        """
        pass
    
    @abstractmethod
    def get_available_symbols(self) -> list[str]:
        """Get list of available symbols from this data source."""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Data source name."""
        pass
