"""Client for downloading historical data from Alpha Vantage."""
from __future__ import annotations

import logging
import time
from typing import Any, Dict, Optional

import pandas as pd
import requests


logger = logging.getLogger(__name__)


class AlphaVantageInformation(RuntimeError):
    """Raised when Alpha Vantage returns an informational response."""

    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


class AlphaVantageClient:
    """Simple Alpha Vantage client using the TIME_SERIES_DAILY endpoint."""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str, session: Optional[requests.Session] = None) -> None:
        self.api_key = api_key
        self.session = session or requests.Session()

    def _get(self, params: Dict[str, str]) -> Dict[str, Any]:
        response = self.session.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()

        # Explicit Alpha Vantage error formats
        if "Error Message" in data:
            # Invalid API call, bad symbol, or similar
            raise ValueError(f"Alpha Vantage error: {data['Error Message']}")

        if "Note" in data:
            # Typically rate limit / quota issues
            raise RuntimeError(f"Alpha Vantage note (likely rate limit): {data['Note']}")

        if "Information" in data:
            # Other informational response (often related to API key usage)
            message = data["Information"]
            logger.error("Alpha Vantage message: %s", message)
            raise AlphaVantageInformation(message)

        return data

    def _get_with_retry(
        self,
        params: Dict[str, str],
        *,
        max_retries: int = 3,
        backoff_seconds: float = 60.0,
    ) -> Dict[str, Any]:
        """Call Alpha Vantage with basic backoff for rate-limit responses."""

        last_exc: Exception | None = None

        for attempt in range(1, max_retries + 1):
            try:
                return self._get(params)
            except (RuntimeError, AlphaVantageInformation) as exc:
                last_exc = exc
                if attempt == max_retries:
                    break

                logger.warning(
                    "Alpha Vantage responded with %s. Sleeping %.1fs before retry %s/%s.",
                    exc,
                    backoff_seconds,
                    attempt,
                    max_retries,
                )
                time.sleep(backoff_seconds)

        assert last_exc  # for type checkers; code above always sets it before breaking
        raise last_exc

    def get_daily(
        self,
        symbol: str,
        output_size: str = "compact",
        *,
        outputsize: Optional[str] = None,
        fallback_to_free_tier: bool = True,
    ) -> pd.DataFrame:
        """Fetch daily time series for the given symbol.

        Args:
            symbol: Ticker symbol to request.
            output_size: Alpha Vantage output size parameter ("compact" or "full").
            outputsize: Deprecated alias for ``output_size`` to preserve compatibility.
            fallback_to_free_tier: Reserved for compatibility with earlier callers;
                TIME_SERIES_DAILY is already free-tier.

        Returns:
            A pandas DataFrame indexed by date with OHLCV columns.
        """

        effective_outputsize = outputsize or output_size

        params = {
            "function": "TIME_SERIES_DAILY",
            "symbol": symbol,
            "apikey": self.api_key,
            "datatype": "json",
            "outputsize": effective_outputsize,
        }

        data = self._get_with_retry(params)
        time_series_key = "Time Series (Daily)"

        if time_series_key not in data:
            raise ValueError("Unexpected response format from Alpha Vantage")

        records = []
        for date_str, values in data[time_series_key].items():
            records.append(
                {
                    "date": pd.to_datetime(date_str),
                    "open": float(values["1. open"]),
                    "high": float(values["2. high"]),
                    "low": float(values["3. low"]),
                    "close": float(values["4. close"]),
                    "volume": int(values["5. volume"]),
                }
            )

        df = pd.DataFrame(records)
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)
        return df

    def get_daily_multiple(
        self,
        symbols: list[str],
        output_size: str = "compact",
        *,
        pause_seconds: float = 12.0,
    ) -> dict[str, pd.DataFrame]:
        """Fetch daily data for multiple symbols.

        Loops over each symbol, reusing :meth:`get_daily` and aggregating results
        while respecting Alpha Vantage free-tier limits. The client pauses
        between each request and enforces no more than five calls per minute.

        Args:
            symbols: Iterable of ticker symbols to fetch sequentially.
            output_size: Alpha Vantage output size parameter ("compact" or "full").
            pause_seconds: Number of seconds to sleep after each request to avoid
                tripping the free-tier rate limit. Default of 12 seconds yields
                at most five calls per minute.
        """

        results: dict[str, pd.DataFrame] = {}
        window_start = time.monotonic()
        calls_in_window = 0

        for index, symbol in enumerate(symbols):
            now = time.monotonic()
            elapsed = now - window_start
            if elapsed >= 60:
                window_start = now
                calls_in_window = 0

            if calls_in_window >= 5:
                sleep_duration = max(0.0, 60 - elapsed)
                if sleep_duration:
                    logger.info(
                        "Sleeping %.1fs to respect Alpha Vantage rate limits", sleep_duration
                    )
                    time.sleep(sleep_duration)
                window_start = time.monotonic()
                calls_in_window = 0

            try:
                results[symbol] = self.get_daily(symbol, output_size=output_size)
                calls_in_window += 1
            except Exception as exc:  # noqa: BLE001 - surface per-symbol errors
                logger.error("Failed to fetch %s: %s", symbol, exc)

            if index < len(symbols) - 1:
                time.sleep(pause_seconds)

        return results
