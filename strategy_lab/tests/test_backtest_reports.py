from __future__ import annotations

from datetime import datetime

import pandas as pd

from strategy_lab.backtest.reports import (
    build_backtest_report,
    to_equity_df,
    to_summary_metrics,
    to_trades_df,
)
from strategy_lab.backtest.runner import StrategyLabBacktestRunner
from strategy_lab.config import StrategyConfig
from strategy_lab.data.base import MarketDataSlice
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
    idx = pd.date_range("2025-02-01", periods=5, freq="D")
    close = [100.0, 101.0, 102.0, 101.0, 103.0]
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


def test_backtest_reports_schema_and_shapes():
    symbol = "AAPL"
    df = _fixture_df()
    runner = StrategyLabBacktestRunner(_InMemoryProvider({symbol: df}))
    results = runner.run(
        strategy=_HardcodedLongStrategy(StrategyConfig(name="reports_test")),
        start_date=df.index.min().to_pydatetime(),
        end_date=df.index.max().to_pydatetime(),
        universe=[symbol],
    )

    equity_df = to_equity_df(results)
    trades_df = to_trades_df(results)
    summary = to_summary_metrics(results)
    report = build_backtest_report(results)

    assert set(["timestamp", "equity", "drawdown"]).issubset(set(equity_df.columns))
    assert set(["timestamp", "symbol", "type", "price", "quantity", "pnl"]).issubset(
        set(trades_df.columns),
    )
    assert "cumulative_return" in summary
    assert "max_drawdown" in summary

    assert set(["summary", "equity_curve", "trade_log"]).issubset(set(report.keys()))
    assert len(report["equity_curve"]) == len(equity_df)
    assert len(report["trade_log"]) == len(trades_df)
