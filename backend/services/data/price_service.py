"""Price data service with unified interface."""

import logging
import sys
from datetime import datetime
from typing import Optional

import pandas as pd

from services.data.base import DataSource

# Expose concrete data source classes at module level so unit tests can patch them.
try:
    from services.data.fmp_source import FMPDataSource
    from services.data.kaggle_source import KaggleDataSource
    from services.data.local_source import LocalDataSource
    from services.data.yahoo_source import YahooDataSource
except Exception:
    # Provide lightweight fallbacks so tests can patch these attributes even if the
    # concrete implementations are not importable in the current environment.
    class FMPDataSource:  # pragma: no cover - fallback for tests
        def __init__(self, *args, **kwargs):
            raise RuntimeError("FMPDataSource is not available in this environment")

    class YahooDataSource:  # pragma: no cover - fallback for tests
        def __init__(self, *args, **kwargs):
            raise RuntimeError("YahooDataSource is not available in this environment")

    class KaggleDataSource:  # pragma: no cover - fallback for tests
        def __init__(self, *args, **kwargs):
            raise RuntimeError("KaggleDataSource is not available in this environment")

    class LocalDataSource:  # pragma: no cover - fallback for tests
        def __init__(self, *args, **kwargs):
            raise RuntimeError("LocalDataSource is not available in this environment")


logger = logging.getLogger(__name__)


class PriceDataService:
    """Unified price data service with lazy data source initialization."""

    def __init__(self):
        # Map logical name to the symbol name we expect in this module so tests can patch the class
        self._factory_symbols: dict[str, str] = {
            "fmp": "FMPDataSource",
            "yahoo": "YahooDataSource",
            "kaggle": "KaggleDataSource",
            "local": "LocalDataSource",
        }
        self._sources: dict[str, DataSource] = {}
        self._default_source = "local"

    def _get_source_instance(self, name: str) -> DataSource:
        if name in self._sources:
            return self._sources[name]
        symbol = self._factory_symbols.get(name)
        if symbol is None:
            raise ValueError(f"Unknown data source: {name}")

        # Ensure the class symbol is available on this module; if not, try a dynamic import.
        factory = getattr(sys.modules[__name__], symbol, None)
        if factory is None:
            try:
                import importlib

                module_name = f"services.data.{name}_source"
                mod = importlib.import_module(module_name)
                factory = getattr(mod, symbol)
                # Cache it on this module for easier patching in tests
                setattr(sys.modules[__name__], symbol, factory)
            except Exception as exc:  # pragma: no cover - environment-dependent
                logger.warning(
                    "Failed to import data source %s from %s: %s",
                    name,
                    module_name,
                    exc,
                )
                raise

        try:
            inst = factory()
        except Exception as exc:  # pragma: no cover - environment-dependent
            logger.warning("Data source %s initialization failed: %s", name, exc)
            raise
        self._sources[name] = inst
        return inst

    def get_prices(
        self,
        symbol: str,
        source: Optional[str] = None,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
        validate: bool = True,
        use_cache: bool = True,
    ) -> pd.DataFrame:
        """Get price data for a symbol.

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

        # Validate source exists (we allow lazy instantiation via factory symbols)
        if source_name not in self._factory_symbols:
            raise ValueError(f"Unknown data source: {source_name}")

        # Check cache
        if use_cache:
            from services.cache_service import cache

            cache_key = cache.make_key(
                "prices",
                symbol=symbol,
                source=source_name,
                start=str(start) if start else None,
                end=str(end) if end else None,
            )
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data

        # Fetch from source
        data_source = self._get_source_instance(source_name)
        if hasattr(data_source, "fetch_prices"):
            # Backwards-compatibility for mocks/tests that use fetch_prices
            df = data_source.fetch_prices(symbol, start=start, end=end)
        elif hasattr(data_source, "get_daily_prices"):
            df = data_source.get_daily_prices(symbol, start=start, end=end)
        else:
            raise RuntimeError(
                f"Data source {source_name} does not implement price fetch method",
            )

        if validate and not df.empty:
            df = self._validate_and_clean(df, symbol)

        # Store in cache
        if use_cache and not df.empty:
            cache.set(cache_key, df)

        return df

    def get_available_sources(self) -> list[str]:
        """Get list of available data sources."""
        return list(self._factory_symbols.keys())

    def _validate_and_clean(self, df: pd.DataFrame, symbol: str) -> pd.DataFrame:
        """Validate and clean price data."""
        from utils.data_validation import clean_price_data, validate_price_data

        is_valid, warnings = validate_price_data(df, symbol)
        if not is_valid:
            df = clean_price_data(df, symbol)

        return df
