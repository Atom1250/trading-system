from __future__ import annotations

from datetime import datetime

import pandas as pd

from strategy_lab.backtest.runner import StrategyLabBacktestRunner
from strategy_lab.config import StrategyConfig
from strategy_lab.data.base import MarketDataSlice
from strategy_lab.persistence.repo import BacktestRepository
from strategy_lab.strategies.base import FactorPanels, MarketDataSlices, Strategy


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


class _HardcodedLongStrategy(Strategy):
    def generate_signals(
        self,
        data: MarketDataSlices,
        factor_panels: FactorPanels,
    ) -> dict[str, pd.Series]:
        del factor_panels
        out: dict[str, pd.Series] = {}
        for symbol, market_slice in data.items():
            out[symbol] = pd.Series(1.0, index=market_slice.df.index)
        return out


def _fixture_df() -> pd.DataFrame:
    idx = pd.date_range("2025-03-01", periods=5, freq="D")
    close = [100.0, 101.0, 102.0, 101.5, 103.0]
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


def test_persistence_repo_inserts_run_trades_and_equity_idempotently(tmp_path):
    symbol = "AAPL"
    df = _fixture_df()
    runner = StrategyLabBacktestRunner(_InMemoryProvider({symbol: df}))
    results = runner.run(
        strategy=_HardcodedLongStrategy(StrategyConfig(name="persistence_test")),
        start_date=df.index.min().to_pydatetime(),
        end_date=df.index.max().to_pydatetime(),
        universe=[symbol],
        initial_capital=100_000.0,
    )

    repo = BacktestRepository(db_path=tmp_path / "backtests.sqlite")
    run_id = "run-persistence-001"

    first = repo.save_backtest_results(run_id=run_id, results=results)
    second = repo.save_backtest_results(run_id=run_id, results=results)

    assert first["run_inserted"] is True
    assert first["trades_inserted"] >= 1
    assert first["equity_inserted"] == len(results.get_equity_curve())
    assert len(first["config_hash"]) == 64

    assert second["run_inserted"] is False
    assert second["trades_inserted"] == 0
    assert second["equity_inserted"] == 0
    assert second["config_hash"] == first["config_hash"]

    summary = repo.get_run_summary(run_id)
    assert summary is not None
    assert summary["run_id"] == run_id
    assert summary["config_hash"] == first["config_hash"]

    trades_df = repo.get_run_trades(run_id)
    equity_df = repo.get_run_equity_history(run_id)
    assert not trades_df.empty
    assert len(equity_df) == len(results.get_equity_curve())
