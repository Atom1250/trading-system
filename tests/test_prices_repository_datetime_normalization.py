from __future__ import annotations

import pandas as pd

from config.settings import PriceDataSource
from repository import prices_repository as repo


def _naive_prices_df() -> pd.DataFrame:
    idx = pd.to_datetime(["2024-01-02", "2024-01-03"])
    return pd.DataFrame(
        {
            "open": [100.0, 101.0],
            "high": [101.0, 102.0],
            "low": [99.0, 100.0],
            "close": [100.5, 101.5],
            "volume": [1000, 1200],
        },
        index=idx,
    )


def test_get_prices_for_backtest_cache_miss_normalizes_returned_index(monkeypatch):
    monkeypatch.setattr(repo, "load_local_prices", lambda symbol: pd.DataFrame())
    monkeypatch.setattr(
        repo, "_fetch_with_fallback", lambda *args, **kwargs: _naive_prices_df()
    )
    monkeypatch.setattr(repo, "save_local_prices", lambda symbol, df: None)

    df = repo.get_prices_for_backtest(
        symbol="AAPL",
        use_local_repository=True,
        data_source=PriceDataSource.YAHOO_FINANCE,
    )

    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.tz is not None
    assert str(df.index.tz) == "UTC"


def test_get_prices_for_backtest_no_cache_normalizes_returned_index(monkeypatch):
    monkeypatch.setattr(
        repo, "_fetch_with_fallback", lambda *args, **kwargs: _naive_prices_df()
    )

    df = repo.get_prices_for_backtest(
        symbol="MSFT",
        use_local_repository=False,
        data_source=PriceDataSource.YAHOO_FINANCE,
    )

    assert isinstance(df.index, pd.DatetimeIndex)
    assert df.index.tz is not None
    assert str(df.index.tz) == "UTC"
