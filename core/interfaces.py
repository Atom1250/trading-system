"""Core interfaces for framework-agnostic design.

This module defines abstract base classes that decouple the core trading
system logic from specific UI frameworks (Streamlit, FastAPI) and external
dependencies. This enables:

- Dependency injection for testing
- Framework-agnostic business logic
- Clear separation of concerns
- Easier migration between UI frameworks
"""

from abc import ABC, abstractmethod
from typing import Any, Optional

import pandas as pd


class DataProvider(ABC):
    """Abstract interface for data providers.
    
    Implementations can fetch data from various sources (FMP, Yahoo Finance,
    Kaggle, local cache) without the core logic needing to know the details.
    """
    
    @abstractmethod
    def get_prices(
        self,
        symbol: str,
        start_date: Optional[pd.Timestamp] = None,
        end_date: Optional[pd.Timestamp] = None,
    ) -> pd.DataFrame:
        """Fetch price data for a symbol.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            start_date: Optional start date for data range
            end_date: Optional end date for data range
            
        Returns:
            DataFrame with OHLCV data and DatetimeIndex
        """
        pass


class Strategy(ABC):
    """Abstract interface for trading strategies.
    
    All strategies (simple and advanced) should implement this interface
    to ensure consistent behavior across the system.
    """
    
    @abstractmethod
    def generate_signals(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate trading signals from price data.
        
        Args:
            df: DataFrame with OHLCV price data
            
        Returns:
            DataFrame with added 'signal' column:
                +1 = long signal
                -1 = short signal
                 0 = no position
        """
        pass
    
    @abstractmethod
    def get_parameters(self) -> dict[str, Any]:
        """Return strategy parameters.
        
        Returns:
            Dictionary of parameter names and values
        """
        pass


class BacktestRunner(ABC):
    """Abstract interface for backtest execution.
    
    Decouples backtest logic from specific backtesting libraries
    (e.g., backtesting.py, vectorbt, custom engine).
    """
    
    @abstractmethod
    def run(self, df: pd.DataFrame) -> dict[str, Any]:
        """Execute backtest and return results.
        
        Args:
            df: DataFrame with price data and signals
            
        Returns:
            Dictionary containing:
                - 'results': DataFrame with equity curve
                - 'cumulative_return': Final return as decimal
                - 'max_drawdown': Maximum drawdown as decimal
                - 'stats': Additional performance statistics
        """
        pass


class Reporter(ABC):
    """Abstract interface for result reporting.
    
    Enables different output formats (console, HTML, PDF, JSON)
    without changing core logic.
    """
    
    @abstractmethod
    def generate_report(self, results: dict[str, Any]) -> str:
        """Generate report from backtest results.
        
        Args:
            results: Dictionary from BacktestRunner.run()
            
        Returns:
            Formatted report as string (format depends on implementation)
        """
        pass
    
    @abstractmethod
    def save_report(self, report: str, output_path: str) -> None:
        """Save report to file.
        
        Args:
            report: Report content from generate_report()
            output_path: Path to save report
        """
        pass
