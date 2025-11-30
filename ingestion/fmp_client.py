"""Client for interacting with FinancialModelingPrep API."""
from __future__ import annotations

import logging
from typing import Any, Dict, Optional

import pandas as pd
import requests

from config import settings

logger = logging.getLogger(__name__)


class FMPClient:
    def __init__(
        self,
        api_key: str | None = None,
        *,
        base_url: str | None = None,
        fallback_base_url: str | None = None,
        session: Optional[requests.Session] = None,
    ) -> None:
        self.api_key = api_key or settings.FMP_API_KEY
        self.base_url = (base_url or settings.FMP_BASE_URL).rstrip("/")
        self.fallback_base_url = (fallback_base_url or settings.FMP_FALLBACK_BASE_URL).rstrip("/")
        self.session = session or requests.Session()

        self._candidate_base_urls = [self.base_url]
        if self.fallback_base_url and self.fallback_base_url not in self._candidate_base_urls:
            self._candidate_base_urls.append(self.fallback_base_url)

    def _get_json(self, path: str, params: dict | None = None) -> Any:
        if not self.api_key:
            raise RuntimeError("Missing FMP API key. Set config.settings.FMP_API_KEY or pass api_key.")

        query = dict(params or {})
        query["apikey"] = self.api_key

        last_error: RuntimeError | None = None
        for idx, base in enumerate(self._candidate_base_urls):
            url = f"{base}/{path.lstrip('/')}"
            if idx > 0:
                logger.info("Retrying FMP request via fallback base URL %s", base)

            response = self.session.get(url, params=query, timeout=30)
            try:
                response.raise_for_status()
            except requests.HTTPError as exc:
                last_error = RuntimeError(
                    f"FMP request failed [{response.status_code}] via {base}: {response.text}"
                )
                logger.warning("FMP request to %s failed [%s]: %s", url, response.status_code, response.text)
                continue

            try:
                payload = response.json()
            except ValueError as exc:
                last_error = RuntimeError("FMP response is not valid JSON")
                logger.warning("FMP response from %s was not valid JSON", url)
                continue

            if isinstance(payload, dict):
                message = payload.get("Error Message") or payload.get("error") or payload.get("message")
                if message:
                    last_error = RuntimeError(f"FMP error: {message}")
                    logger.warning("FMP returned an error from %s: %s", url, message)
                    continue

            return payload

        raise last_error or RuntimeError("FMP request failed without a specific error message")

    def get_daily(
        self,
        symbol: str,
        limit: int = 5000,
    ) -> pd.DataFrame:
        """
        Fetch historical daily OHLCV data for `symbol` from FMP.
        Use the 'historical-price-full' endpoint.
        Return a DataFrame with a DateTime index and columns:
        ['open', 'high', 'low', 'close', 'adj_close', 'volume'].
        """

        data = self._get_json(f"historical-price-full/{symbol}", params={"timeseries": limit})
        historical = data.get("historical") if isinstance(data, dict) else None

        if not historical:
            return pd.DataFrame(columns=["open", "high", "low", "close", "adj_close", "volume"])

        records = []
        for item in historical:
            try:
                record = {
                    "date": pd.to_datetime(item["date"]),
                    "open": float(item["open"]),
                    "high": float(item["high"]),
                    "low": float(item["low"]),
                    "close": float(item["close"]),
                    "adj_close": float(item.get("adjClose", item["close"])),
                    "volume": int(item["volume"]),
                }
            except (KeyError, TypeError, ValueError):
                continue

            if pd.isna(record["close"]):
                continue

            records.append(record)

        df = pd.DataFrame(records)
        if df.empty:
            return df

        df.set_index("date", inplace=True)
        if getattr(df.index, "tz", None) is not None:
            df.index = df.index.tz_localize(None)
        df.sort_index(inplace=True)

        return df[["open", "high", "low", "close", "adj_close", "volume"]]

    def get_fundamentals(self, symbol: str) -> Dict[str, Any]:
        """
        Fetch fundamental data for `symbol` (e.g. 'financial-statement-full-as-reported'
        or 'income-statement', 'balance-sheet-statement', 'cash-flow-statement' endpoints).
        Return a dictionary with the raw JSON payload.
        """

        data = self._get_json(f"financial-statement-full-as-reported/{symbol}")
        if not isinstance(data, dict):
            raise RuntimeError("Unexpected FMP fundamentals response format")
        return data
