"""Route-level tests for Phase 7 backtest run/fetch endpoints."""

from __future__ import annotations

from datetime import datetime

import pandas as pd

from backend.schemas.backtests_v2 import BacktestRunRequest
from backend.services.backtest_service import BacktestService
from strategy_lab.data.base import MarketDataSlice
from strategy_lab.persistence.repo import BacktestRepository


class _InMemoryProvider:
    def __init__(self, payload: dict[str, pd.DataFrame]):
        self.payload = payload

    def get_history(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> MarketDataSlice:
        df = self.payload[symbol]
        df = df.loc[(df.index >= start) & (df.index <= end)]
        return MarketDataSlice(symbol=symbol, df=df.copy())


def _fixture_df() -> pd.DataFrame:
    idx = pd.date_range("2025-04-01", periods=5, freq="D")
    close = [100.0, 101.0, 102.0, 103.0, 104.0]
    return pd.DataFrame(
        {
            "open": close,
            "high": [p + 1.0 for p in close],
            "low": [p - 1.0 for p in close],
            "close": close,
            "volume": [1_000_000] * len(close),
        },
        index=idx,
    )


def test_backtests_run_and_fetch_route_handlers(monkeypatch, tmp_path):
    from backend.api.routes_backtest import (
        get_backtest_equity,
        get_backtest_summary,
        get_backtest_trades,
        run_backtest,
    )

    symbol = "AAPL"
    data_provider = _InMemoryProvider({symbol: _fixture_df()})
    repo = BacktestRepository(db_path=tmp_path / "phase7.sqlite")
    monkeypatch.setattr(
        "backend.api.routes_backtest.backtest_service",
        BacktestService(data_provider=data_provider, repository=repo),
    )

    request = BacktestRunRequest(
        strategy_name="MovingAverageCrossover",
        symbol=symbol,
        start_date=datetime(2025, 4, 1).date(),
        end_date=datetime(2025, 4, 5).date(),
        initial_capital=100000.0,
        parameters={"short_window": 2, "long_window": 3},
    )
    run_payload = run_backtest(request)
    run_id = run_payload["run_id"]
    assert run_id
    assert run_payload["summary"] is not None

    summary_payload = get_backtest_summary(run_id)
    assert summary_payload["run_id"] == run_id

    trades_payload = get_backtest_trades(run_id)
    assert trades_payload["run_id"] == run_id
    assert isinstance(trades_payload["trades"], list)

    equity_payload = get_backtest_equity(run_id)
    assert equity_payload["run_id"] == run_id
    assert len(equity_payload["equity"]) > 0
