"""Base classes and interfaces for data providers.

This module defines the abstract base classes and common data structures
used throughout the data module.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Protocol, runtime_checkable

import pandas as pd


@dataclass
class OHLCVData:
    """OHLCV (Open, High, Low, Close, Volume) data structure.

    Attributes:
        symbol: Trading symbol
        data: DataFrame with OHLCV data (columns: open, high, low, close, volume)
        start_date: Start date of data
        end_date: End date of data
        source: Data source identifier

    """

    symbol: str
    data: pd.DataFrame
    start_date: datetime
    end_date: datetime
    source: str = "unknown"

    def __post_init__(self):
        """Validate OHLCV data structure."""
        required_columns = ["open", "high", "low", "close", "volume"]
        missing_columns = [
            col for col in required_columns if col not in self.data.columns
        ]
        if missing_columns:
            raise ValueError(f"Missing required columns: {missing_columns}")

        if self.data.empty:
            raise ValueError("Data cannot be empty")


@dataclass
class MarketDataSlice:
    """A slice of market data for a specific symbol.

    Attributes:
        symbol: Trading symbol
        df: DataFrame containing the market data (index: datetime, columns: open, high, low, close, volume, etc.)

    """

    symbol: str
    df: pd.DataFrame


@runtime_checkable
class HistoricalDataProvider(Protocol):
    """Protocol for historical data providers."""

    def get_history(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> MarketDataSlice:
        """Get historical data for a symbol.

        Args:
            symbol: Trading symbol
            start: Start date
            end: End date

        Returns:
            MarketDataSlice containing the history

        """
        ...


class DataProvider(ABC):
    """Abstract base class for data providers.

    All data providers must implement the fetch_ohlcv method to retrieve
    historical price data.
    """

    @abstractmethod
    def fetch_ohlcv(
        self,
        symbol: str,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs,
    ) -> OHLCVData:
        """Fetch OHLCV data for a given symbol.

        Args:
            symbol: Trading symbol
            start_date: Start date for data retrieval
            end_date: End date for data retrieval
            **kwargs: Additional provider-specific parameters

        Returns:
            OHLCVData object containing the requested data

        Raises:
            ValueError: If symbol is invalid or data cannot be retrieved

        """

    @abstractmethod
    def get_available_symbols(self) -> list[str]:
        """Get list of available symbols from this provider.

        Returns:
            List of available trading symbols

        """

    def validate_symbol(self, symbol: str) -> bool:
        """Validate if a symbol is available from this provider.

        Args:
            symbol: Trading symbol to validate

        Returns:
            True if symbol is available, False otherwise

        """
        return symbol in self.get_available_symbols()
