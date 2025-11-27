"""Client for downloading historical data from Yahoo Finance."""
from datetime import datetime
from typing import Optional

import pandas as pd
import yfinance as yf


class YahooFinanceClient:
    def get_daily(
        self,
        symbol: str,
        start: Optional[datetime] = None,
        end: Optional[datetime] = None,
    ) -> pd.DataFrame:
        """
        Download daily OHLCV data for `symbol` from Yahoo Finance.
        Return a DataFrame with a DateTime index and columns:
        ['open', 'high', 'low', 'close', 'adj_close', 'volume'].
        If start/end are None, default to a long history (e.g. 'max').
        """

        download_kwargs = {
            "interval": "1d",
            "progress": False,
            "auto_adjust": False,
        }

        if start is None and end is None:
            raw = yf.download(symbol, period="max", **download_kwargs)
        else:
            raw = yf.download(symbol, start=start, end=end, **download_kwargs)

        if raw.empty:
            return raw

        if getattr(raw.index, "tz", None) is not None:
            raw.index = raw.index.tz_localize(None)

        data = raw.rename(
            columns={
                "Open": "open",
                "High": "high",
                "Low": "low",
                "Close": "close",
                "Adj Close": "adj_close",
                "Volume": "volume",
            }
        )

        data = data.dropna(subset=["close"])

        return data[["open", "high", "low", "close", "adj_close", "volume"]]
