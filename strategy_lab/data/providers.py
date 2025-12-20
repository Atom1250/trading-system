"""Concrete data provider implementations.

This module provides concrete implementations of data providers that integrate
with the existing trading system's data ingestion modules.
"""

import os
import sys
from datetime import datetime
from typing import Optional

# Add parent directory to path to import from existing modules
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from config.settings import DEFAULT_PRICE_DATA_SOURCE, PriceDataSource
from repository.prices_repository import get_prices_for_backtest
from strategy_lab.data.base import (
    DataProvider,
    HistoricalDataProvider,
    MarketDataSlice,
    OHLCVData,
)


class TradingSystemDataProvider(DataProvider):
    """Data provider that integrates with the existing trading system.

    This provider uses the existing repository layer to fetch data from
    FMP, Yahoo Finance, or local repository based on configuration.

    Attributes:
        source: Data source to use (from PriceDataSource enum)
        force_refresh: Whether to force refresh data from source

    """

    def __init__(
        self,
        source: Optional[PriceDataSource] = None,
        force_refresh: bool = False,
    ):
        """Initialize the trading system data provider.

        Args:
            source: Data source to use (defaults to DEFAULT_PRICE_DATA_SOURCE)
            force_refresh: Whether to force refresh data from source

        """
        self.source = source or DEFAULT_PRICE_DATA_SOURCE
        self.force_refresh = force_refresh

    def fetch_ohlcv(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs,
    ) -> OHLCVData:
        """Fetch OHLCV data using the existing repository layer.

        Args:
            symbol: Trading symbol
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            **kwargs: Additional parameters (force_refresh, etc.)

        Returns:
            OHLCVData object containing the requested data

        Raises:
            ValueError: If data cannot be retrieved

        """
        force_refresh = kwargs.get("force_refresh", self.force_refresh)

        # Fetch data using existing repository
        df = get_prices_for_backtest(
            symbol=symbol,
            use_local_repository=not force_refresh,
            data_source=self.source,
        )

        if df is None or df.empty:
            raise ValueError(f"No data available for symbol {symbol}")

        # Standardize column names to lowercase
        df.columns = df.columns.str.lower()

        # Filter by date range if provided
        if start_date is not None:
            df = df[df.index >= start_date]
        if end_date is not None:
            df = df[df.index <= end_date]

        if df.empty:
            raise ValueError(f"No data available for {symbol} in date range")

        # Create OHLCVData object
        return OHLCVData(
            symbol=symbol,
            data=df,
            start_date=df.index.min(),
            end_date=df.index.max(),
            source=self.source.value,
        )

    def get_available_symbols(self) -> list[str]:
        """Get list of available symbols.

        Note: This is a placeholder implementation. In practice, you would
        query the data source for available symbols.

        Returns:
            List of common symbols (placeholder)

        """
        # Placeholder - return common symbols
        # In production, this would query the actual data source
        return [
            "AAPL",
            "MSFT",
            "GOOGL",
            "AMZN",
            "META",
            "TSLA",
            "NVDA",
            "JPM",
            "V",
            "WMT",
        ]


class YahooFinanceProvider(DataProvider):
    """Yahoo Finance data provider.

    Convenience wrapper for Yahoo Finance data source.
    """

    def __init__(self, force_refresh: bool = False):
        """Initialize Yahoo Finance provider."""
        self.provider = TradingSystemDataProvider(
            source=PriceDataSource.YAHOO_FINANCE,
            force_refresh=force_refresh,
        )

    def fetch_ohlcv(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs,
    ) -> OHLCVData:
        """Fetch OHLCV data from Yahoo Finance."""
        return self.provider.fetch_ohlcv(symbol, start_date, end_date, **kwargs)

    def get_available_symbols(self) -> list[str]:
        """Get available symbols from Yahoo Finance."""
        return self.provider.get_available_symbols()


class FMPProvider(DataProvider):
    """FinancialModelingPrep data provider.

    Convenience wrapper for FMP data source.
    """

    def __init__(self, force_refresh: bool = False):
        """Initialize FMP provider."""
        self.provider = TradingSystemDataProvider(
            source=PriceDataSource.FMP,
            force_refresh=force_refresh,
        )

    def fetch_ohlcv(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs,
    ) -> OHLCVData:
        """Fetch OHLCV data from FMP."""
        return self.provider.fetch_ohlcv(symbol, start_date, end_date, **kwargs)

    def get_available_symbols(self) -> list[str]:
        """Get available symbols from FMP."""
        return self.provider.get_available_symbols()


class YFinanceHistoricalProvider(HistoricalDataProvider):
    """Yahoo Finance implementation of HistoricalDataProvider.

    Uses standard yahoo finance data ingestion.
    """

    def __init__(self, force_refresh: bool = False):
        self.provider = YahooFinanceProvider(force_refresh=force_refresh)

    def get_history(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> MarketDataSlice:
        try:
            ohlcv = self.provider.fetch_ohlcv(symbol, start_date=start, end_date=end)
            return MarketDataSlice(symbol=symbol, df=ohlcv.data)
        except Exception as e:
            # For now, return empty DF if fails, or re-raise.
            # Protocol return type implies we should succeed or raise exception.
            # We will rely on underlying provider raising ValueError.
            raise e


class FMPHistoricalProvider(HistoricalDataProvider):
    """FMP implementation of HistoricalDataProvider.

    Uses standard FMP data ingestion.
    """

    def __init__(self, force_refresh: bool = False):
        self.provider = FMPProvider(force_refresh=force_refresh)

    def get_history(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> MarketDataSlice:
        try:
            ohlcv = self.provider.fetch_ohlcv(symbol, start_date=start, end_date=end)
            return MarketDataSlice(symbol=symbol, df=ohlcv.data)
        except Exception as e:
            raise e
