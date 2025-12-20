from __future__ import annotations

import datetime
import logging
import sqlite3
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from dateutil import parser

from config import settings
from config.settings import (
    DEFAULT_PRICE_DATA_SOURCE,
    KAGGLE_DB_PATH,
    PRICE_DATA_DIR,
    PriceDataSource,
    ensure_data_directories,
)
from ingestion.fmp_client import FMPClient
from ingestion.yahoo_finance_client import YahooFinanceClient
from utils.data_validation import clean_price_data, validate_price_data

logger = logging.getLogger(__name__)

# Ensure data directories exist on import so load/save calls work.
ensure_data_directories()


def price_file_path(symbol: str) -> Path:
    return PRICE_DATA_DIR / f"{symbol.upper()}.csv"


def _normalize_index(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return df

    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = df.index.map(
            lambda value: (
                value
                if isinstance(value, datetime.datetime)
                else parser.parse(str(value))
            ),
        )

    if getattr(df.index, "tz", None) is not None:
        try:
            # If index is timezone-aware, prefer tz_convert to remove tz information.
            df.index = df.index.tz_convert(None)
        except Exception:
            # Fallback for older pandas versions or unexpected index types
            df.index = df.index.tz_localize(None)

    df.sort_index(inplace=True)
    return df


def load_local_prices(symbol: str) -> pd.DataFrame:
    """Load local price history for a symbol from CSV, if it exists.
    Return an empty DataFrame if the file is missing.
    """
    ensure_data_directories()
    path = price_file_path(symbol)

    if not path.exists():
        logger.info("Local price file for %s not found at %s", symbol, path)
        return pd.DataFrame()

    try:
        df = pd.read_csv(path, parse_dates=["date"], index_col="date")
    except FileNotFoundError:
        return pd.DataFrame()
    except Exception as exc:  # noqa: BLE001 - log and return empty on read issues
        logger.error("Failed to load local prices for %s: %s", symbol, exc)
        return pd.DataFrame()

    return _normalize_index(df)


def load_kaggle_prices(symbol: str) -> pd.DataFrame:
    """Load historical prices for a symbol from the Kaggle SQLite database."""
    if not KAGGLE_DB_PATH.exists():
        logger.warning(
            "Kaggle DB not found at %s. Run scripts/build_kaggle_price_db.py first.",
            KAGGLE_DB_PATH,
        )
        return pd.DataFrame()

    try:
        with sqlite3.connect(KAGGLE_DB_PATH) as conn:
            query = "SELECT date, open, high, low, close, volume FROM prices WHERE symbol = ?"
            df = pd.read_sql_query(
                query,
                conn,
                params=(symbol,),
                parse_dates=["date"],
                index_col="date",
            )

        if df.empty:
            logger.info("No Kaggle data found for %s", symbol)
            return pd.DataFrame()

        return _normalize_index(df)
    except Exception as exc:
        logger.error("Failed to load Kaggle prices for %s: %s", symbol, exc)
        return pd.DataFrame()


def save_local_prices(symbol: str, df: pd.DataFrame) -> None:
    """Save the given price DataFrame to the local repository as CSV.
    Overwrite existing file.
    """
    ensure_data_directories()
    path = price_file_path(symbol)

    cleaned = _normalize_index(df.copy())
    cleaned.to_csv(path, index_label="date")
    logger.info("Saved %s rows for %s to %s", len(cleaned), symbol, path)


def append_new_rows(symbol: str, new_data: pd.DataFrame) -> None:
    """Append new rows to an existing local CSV, avoiding duplicate dates."""
    if new_data.empty:
        logger.info("No new price data to append for %s", symbol)
        return

    existing = load_local_prices(symbol)
    combined = (
        _normalize_index(new_data.copy())
        if existing.empty
        else pd.concat([existing, _normalize_index(new_data.copy())])
    )

    combined = combined[~combined.index.duplicated(keep="last")]
    combined.sort_index(inplace=True)

    save_local_prices(symbol, combined)


def _source_to_value(data_source: Optional[Any]) -> str:
    source = data_source or DEFAULT_PRICE_DATA_SOURCE
    return getattr(source, "value", str(source)).lower()


def _resolve_source_for_symbol(
    symbol: str,
    preferred_source: Optional[Any],
) -> str:
    """Return a usable source name, falling back when configuration is missing.

    If FMP is requested but the API key is absent, automatically fall back to
    Yahoo Finance so backtests can still run without manual reconfiguration.
    """
    source_value = _source_to_value(preferred_source)

    if source_value == PriceDataSource.FMP.value and not settings.FMP_API_KEY:
        logger.warning(
            "FMP_API_KEY is not configured; falling back to Yahoo Finance for %s",
            symbol,
        )
        return PriceDataSource.YAHOO_FINANCE.value

    return source_value


def _fetch_with_fallback(
    symbol: str,
    primary_source: str,
    fallback_source: Optional[str],
) -> pd.DataFrame:
    """Fetch prices from ``primary_source`` and optionally fall back if empty/errors."""

    def _attempt(source_value: str) -> pd.DataFrame:
        try:
            return _fetch_prices_from_source(symbol, source_value)
        except Exception as exc:  # noqa: BLE001 - log and allow fallback
            logger.error(
                "Fetching %s prices from %s failed: %s",
                symbol,
                source_value,
                exc,
            )
            return pd.DataFrame()

    df = _attempt(primary_source)
    if (
        (df is None or df.empty)
        and fallback_source
        and fallback_source != primary_source
    ):
        logger.info(
            "Primary source %s returned no data for %s; trying fallback %s",
            primary_source,
            symbol,
            fallback_source,
        )
        df = _attempt(fallback_source)

    return df


def _fetch_prices_from_source(symbol: str, source_value: str) -> pd.DataFrame:
    if source_value == PriceDataSource.YAHOO_FINANCE.value:
        logger.info("Fetching %s prices from Yahoo Finance", symbol)
        df = YahooFinanceClient().get_daily(symbol)
    elif source_value == PriceDataSource.FMP.value:
        logger.info("Fetching %s prices from FinancialModelingPrep", symbol)
        df = FMPClient().get_daily(symbol)
    elif source_value == PriceDataSource.LOCAL_REPOSITORY.value:
        logger.info("Loading %s prices from local repository", symbol)
        df = load_local_prices(symbol)
    elif source_value == PriceDataSource.KAGGLE.value:
        logger.info("Loading %s prices from Kaggle DB", symbol)
        df = load_kaggle_prices(symbol)
    else:
        raise ValueError(f"Unsupported data source: {source_value}")

    # Validate and clean the data
    if not df.empty:
        is_valid, warnings = validate_price_data(df, symbol)
        if not is_valid:
            logger.warning("Data validation failed for %s, attempting to clean", symbol)
            df = clean_price_data(df, symbol)
            # Re-validate after cleaning
            is_valid, warnings = validate_price_data(df, symbol)
            if not is_valid:
                logger.error("Data still invalid after cleaning for %s", symbol)

    return df


def fetch_and_cache_prices(
    symbol: str,
    data_source: Optional[PriceDataSource] = None,
) -> pd.DataFrame:
    """Fetch full historical prices for `symbol` from the chosen data source
    (Yahoo Finance or FMP), then save to the local repository.
    Returns the full DataFrame.
    """
    source_value = _source_to_value(data_source)
    df = _fetch_prices_from_source(symbol, source_value)

    if df.empty:
        logger.warning("No price data fetched for %s from %s", symbol, source_value)
        return df

    save_local_prices(symbol, df)
    return df


def get_prices_for_backtest(
    symbol: str,
    use_local_repository: bool,
    data_source: Optional[PriceDataSource] = None,
) -> pd.DataFrame:
    """High-level entrypoint used by the strategy/backtest layer.
    If use_local_repository is True:
        - Try to load local prices.
        - If file does not exist or is empty, fetch_and_cache_prices and then return.
    If use_local_repository is False:
        - Use the given data_source (or DEFAULT_PRICE_DATA_SOURCE if None) to fetch data,
          but do not necessarily save it.
    """
    if use_local_repository:
        local_df = load_local_prices(symbol)
        if not local_df.empty:
            return local_df

        logger.info("Local prices missing for %s; fetching and caching.", symbol)
        fallback_source = data_source
        if fallback_source in (None, PriceDataSource.LOCAL_REPOSITORY):
            fallback_source = DEFAULT_PRICE_DATA_SOURCE

        primary_value = _resolve_source_for_symbol(symbol, fallback_source)
        secondary_value = None
        if primary_value != PriceDataSource.YAHOO_FINANCE.value:
            secondary_value = PriceDataSource.YAHOO_FINANCE.value

        df = _fetch_with_fallback(symbol, primary_value, secondary_value)
        if df.empty:
            return df

        save_local_prices(symbol, df)
        return df

    source_value = _resolve_source_for_symbol(symbol, data_source)
    fallback_value = None
    if source_value != PriceDataSource.YAHOO_FINANCE.value:
        fallback_value = PriceDataSource.YAHOO_FINANCE.value

    logger.info(
        "Fetching %s prices from %s for backtest (no cache).",
        symbol,
        source_value,
    )
    return _fetch_with_fallback(symbol, source_value, fallback_value)
