"""Client for downloading historical data from Alpha Vantage."""
from __future__ import annotations

from typing import Any, Dict, Optional

import pandas as pd
import requests


class AlphaVantageClient:
    """Simple Alpha Vantage client using the TIME_SERIES_DAILY_ADJUSTED endpoint."""

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self, api_key: str, session: Optional[requests.Session] = None) -> None:
        self.api_key = api_key
        self.session = session or requests.Session()

    def _get(self, params: Dict[str, str]) -> Dict[str, Any]:
        response = self.session.get(self.BASE_URL, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        if "Error Message" in data:
            raise ValueError(data["Error Message"])
        return data

    def get_daily(self, symbol: str, outputsize: str = "compact") -> pd.DataFrame:
        """Fetch daily adjusted time series for the given symbol.

        Args:
            symbol: Ticker symbol to request.
            outputsize: Alpha Vantage outputsize parameter ("compact" or "full").

        Returns:
            A pandas DataFrame indexed by date with OHLCV and adjusted close columns.
        """

        params = {
            "function": "TIME_SERIES_DAILY_ADJUSTED",
            "symbol": symbol,
            "apikey": self.api_key,
            "datatype": "json",
            "outputsize": outputsize,
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
                    "adjusted_close": float(values["5. adjusted close"]),
                    "volume": int(values["6. volume"]),
                    "dividend_amount": float(values["7. dividend amount"]),
                    "split_coefficient": float(values["8. split coefficient"]),
                }
            )

        df = pd.DataFrame(records)
        df.set_index("date", inplace=True)
        df.sort_index(inplace=True)
        return df
