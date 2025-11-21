"""Client for downloading historical data from Alpha Vantage."""
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import requests


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
            print(f"Alpha Vantage message: {message}")
            raise AlphaVantageInformation(message)

        return data

    def get_daily(
        self,
        symbol: str,
        output_size: str = "compact",
        *,
        outputsize: Optional[str] = None,
        *,
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

        data = self._get(params)
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
