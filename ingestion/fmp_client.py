"""FMP client for historical and EOD price data.

This module is designed for use in the trading-system app as a drop-in
replacement for previous Alpha Vantage clients. It pulls configuration
from environment variables (typically via a .env file) and exposes a
simple Python interface for Codex and other orchestrators to call.

Environment variables expected:
    FMP_API_KEY      - Your FMP API key
    FMP_BASE_URL     - Base URL for FMP stable API
                       (default: https://financialmodelingprep.com/stable)

Typical usage:
    from ingestion.fmp_client import FMPClient

    client = FMPClient()
    df = client.get_historical_eod("AAPL", start_date="2010-01-01", end_date="2025-11-30")

"""

from __future__ import annotations

import logging
import os
from typing import Any, Optional

import pandas as pd
import requests

logger = logging.getLogger(__name__)


class FMPClient:
    """Thin wrapper around FMP stable API endpoints for historical prices.
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        session: Optional[requests.Session] = None,
        timeout: int = 30,
    ) -> None:
        """Initialize the FMPClient.

        Args:
            api_key: FMP API key. If not provided, will use FMP_API_KEY env var.
            base_url: Base URL for FMP. If not provided, will use FMP_BASE_URL env var
                      or default to "https://financialmodelingprep.com/stable".
            session: Optional shared requests.Session for connection pooling.
            timeout: Request timeout in seconds.

        """
        self.api_key = api_key or os.getenv("FMP_API_KEY")
        if not self.api_key:
            raise ValueError(
                "FMP_API_KEY is not set.\n\n"
                "To fix this:\n"
                "  1. Get a free API key at: https://financialmodelingprep.com/developer/docs/\n"
                "  2. Add it to your .env file:\n"
                "     FMP_API_KEY=your_key_here\n"
                "  3. Or set the environment variable:\n"
                "     export FMP_API_KEY=your_key_here\n\n"
                "Alternatively, use Yahoo Finance (no API key required):\n"
                "  - Set TS_PRICE_DATA_SOURCE=yahoo_finance in your .env file\n"
                "  - Or select Yahoo Finance when prompted in the console",
            )

        # Ensure we have a concrete string before calling rstrip to satisfy type checkers
        self.base_url = str(
            base_url
            or os.getenv("FMP_BASE_URL", "https://financialmodelingprep.com/stable"),
        ).rstrip("/")
        self.session = session or requests.Session()
        self.timeout = timeout

        logger.info("Initialized FMPClient with base_url=%s", self.base_url)

    # ---------------------------------------------------------------------
    # Low-level request helper
    # ---------------------------------------------------------------------
    def _get(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> Any:
        """Internal GET wrapper handling base URL, API key, and error handling.

        Args:
            endpoint: Path starting with "/" (e.g. "/historical-price-eod/full").
            params: Optional dict of query parameters.

        Returns:
            Parsed JSON response.

        Raises:
            RuntimeError: For non-200 responses or API error payloads.

        """
        if not endpoint.startswith("/"):
            endpoint = "/" + endpoint

        url = f"{self.base_url}{endpoint}"

        params = params.copy() if params else {}
        params["apikey"] = self.api_key

        logger.debug("Requesting FMP URL=%s params=%s", url, params)

        try:
            resp = self.session.get(url, params=params, timeout=self.timeout)
        except requests.RequestException as exc:
            logger.error("Network error while calling FMP: %s", exc)
            raise RuntimeError(f"Network error while calling FMP: {exc}") from exc

        if resp.status_code != 200:
            logger.error("FMP HTTP error %s: %s", resp.status_code, resp.text[:500])
            raise RuntimeError(f"FMP HTTP error {resp.status_code}: {resp.text[:500]}")

        try:
            data = resp.json()
        except ValueError as exc:
            logger.error("Failed to parse JSON from FMP response: %s", exc)
            raise RuntimeError("Failed to parse JSON from FMP response") from exc

        if isinstance(data, dict) and data.get("error"):
            logger.error("FMP API error: %s", data["error"])
            raise RuntimeError(f"FMP API error: {data['error']}")

        return data

    # ---------------------------------------------------------------------
    # Public methods
    # ---------------------------------------------------------------------
    def get_historical_eod(
        self,
        symbol: str,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch full historical end-of-day prices for a single symbol.

        This uses the stable FMP endpoint:
            /historical-price-eod/full?symbol={SYMBOL}&from=YYYY-MM-DD&to=YYYY-MM-DD

        Args:
            symbol: Ticker symbol, e.g. "AAPL".
            start_date: Optional start date in "YYYY-MM-DD" format.
            end_date: Optional end date in "YYYY-MM-DD" format.

        Returns:
            DataFrame with columns typically including:
                date, open, high, low, close, adjClose, volume, etc.
            Indexed by datetime (date).

        """
        params: dict[str, Any] = {"symbol": symbol.upper()}
        if start_date:
            params["from"] = start_date
        if end_date:
            params["to"] = end_date

        raw = self._get("/historical-price-eod/full", params=params)

        if isinstance(raw, dict) and "historical" in raw:
            records: list[dict[str, Any]] = raw["historical"]
        elif isinstance(raw, list):
            records = raw
        else:
            logger.error("Unexpected FMP historical EOD payload shape: %s", type(raw))
            raise RuntimeError("Unexpected FMP historical EOD payload shape")

        if not records:
            logger.warning("No historical data returned for symbol=%s", symbol)
            return pd.DataFrame()

        df = pd.DataFrame(records)

        if "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"])
            df.set_index("date", inplace=True)
            df.sort_index(inplace=True)

        return df

    def get_intraday(
        self,
        symbol: str,
        interval: str = "1min",
        limit: Optional[int] = None,
    ) -> pd.DataFrame:
        """Fetch intraday historical data for a symbol.

        This uses the stable intraday endpoint (pattern; adjust to actual doc
        if you extend intraday support in the app):

            /historical-chart/{interval}?symbol={SYMBOL}

        Args:
            symbol: Ticker symbol, e.g. "AAPL".
            interval: Interval string, e.g. "1min", "5min", "15min", "30min", "1hour".
            limit: Optional number of bars to return.

        Returns:
            DataFrame indexed by datetime. Currently unused in the app and safe
            to ignore if you have not implemented intraday analytics.

        """
        endpoint = f"/historical-chart/{interval}"
        params: dict[str, Any] = {"symbol": symbol.upper()}
        if limit is not None:
            params["limit"] = limit

        raw = self._get(endpoint, params=params)

        if not isinstance(raw, list):
            logger.error("Unexpected FMP intraday payload shape: %s", type(raw))
            raise RuntimeError("Unexpected FMP intraday payload shape")

        if not raw:
            logger.warning("No intraday data returned for symbol=%s", symbol)
            return pd.DataFrame()

        df = pd.DataFrame(raw)

        date_col = "date" if "date" in df.columns else "datetime"
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col])
            df.set_index(date_col, inplace=True)
            df.sort_index(inplace=True)

        return df

    # ------------------------------------------------------------------
    # Compatibility helpers for existing callers in the app
    # ------------------------------------------------------------------
    def get_daily(
        self,
        symbol: str,
        limit: int = 5000,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """Fetch historical daily OHLCV data for ``symbol`` using the stable EOD endpoint.

        The ``limit`` parameter is retained for backward compatibility but is applied
        by trimming the returned DataFrame rather than altering the API request.
        """
        df = self.get_historical_eod(symbol, start_date=start_date, end_date=end_date)
        if df.empty:
            return pd.DataFrame(
                columns=["open", "high", "low", "close", "adj_close", "volume"],
            )

        column_mapping = {"adjClose": "adj_close", "adj_close": "adj_close"}
        normalized = df.rename(columns=column_mapping)

        for col in ("open", "high", "low", "close", "adj_close", "volume"):
            if col not in normalized.columns:
                normalized[col] = pd.NA

        normalized = normalized[["open", "high", "low", "close", "adj_close", "volume"]]

        if limit and len(normalized) > limit:
            normalized = normalized.tail(limit)

        return normalized
