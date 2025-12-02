"""Price data service with unified interface."""
from datetime import datetime
from typing import Optional
import pandas as pd

from services.data.base import DataSource
from services.data.fmp_source import FMPDataSource
from services.data.yahoo_source import YahooDataSource
from services.data.kaggle_source import KaggleDataSource
from services.data.local_source import LocalDataSource


class PriceDataService:
    """Unified price data service."""
    
    def __init__(self):
        self._sources: dict[str, DataSource] = {
            "fmp": FMPDataSource(),
            "yahoo": YahooDataSource(),
            "kaggle": KaggleDataSource(),
            "local": LocalDataSource(),
        }
        self._default_source = "local"
    
    def get_prices(
        self,
        symbol: str,
        source: str = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        validate: bool = True,
        use_cache: bool = True
    ) -> pd.DataFrame:
        """
        Get price data for a symbol.
        
        Args:
            symbol: Stock symbol
            source: Data source name (fmp, yahoo, kaggle, local)
            start: Start date
            end: End date
            validate: Whether to validate data
            use_cache: Whether to use cache
            
        Returns:
            DataFrame with OHLCV data
        """
        source_name = source or self._default_source
        
        if source_name not in self._sources:
            raise ValueError(f"Unknown data source: {source_name}")
        
        # Check cache
        if use_cache:
            from services.cache_service import cache
            cache_key = cache.make_key(
                "prices",
                symbol=symbol,
                source=source_name,
                start=str(start) if start else None,
                end=str(end) if end else None
            )
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data
        
        # Fetch from source
        data_source = self._sources[source_name]
        df = data_source.get_daily_prices(symbol, start=start, end=end)
        
        if validate and not df.empty:
            df = self._validate_and_clean(df, symbol)
        
        # Store in cache
        if use_cache and not df.empty:
            cache.set(cache_key, df)
        
        return df
    
    def get_available_sources(self) -> list[str]:
        """Get list of available data sources."""
        return list(self._sources.keys())
    
    def _validate_and_clean(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Validate and clean price data."""
        from utils.data_validation import validate_price_data, clean_price_data
        
        is_valid, warnings = validate_price_data(df, symbol)
        if not is_valid:
            df = clean_price_data(df, symbol)
        
        return df
