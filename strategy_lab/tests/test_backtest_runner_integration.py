from __future__ import annotations

from datetime import datetime

import pandas as pd
from pandas.testing import assert_frame_equal

from strategy_lab.backtest.reports import build_backtest_report
from strategy_lab.backtest.runner import StrategyLabBacktestRunner
from strategy_lab.config import StrategyConfig
from strategy_lab.data.base import MarketDataSlice
from strategy_lab.risk.engine import RiskEngine
from strategy_lab.strategies.base import FactorPanels, MarketDataSlices, Strategy


class InMemoryHistoricalDataProvider:
    """Deterministic in-memory provider for integration tests."""

    def __init__(self, payload: dict[str, pd.DataFrame]):
        self._payload = payload

    def get_history(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> MarketDataSlice:
        df = self._payload[symbol]
        df = df.loc[(df.index >= start) & (df.index <= end)]
        return MarketDataSlice(symbol=symbol, df=df.copy())


class HardcodedSignalStrategy(Strategy):
    """Strategy that emits deterministic long signals on all bars."""

    def generate_signals(
        self,
        data: MarketDataSlices,
        factor_panels: FactorPanels,
    ) -> dict[str, pd.Series]:
        signals: dict[str, pd.Series] = {}
        for symbol, market_slice in data.items():
            signals[symbol] = pd.Series(
                data=1,
                index=market_slice.df.index,
                dtype=float,
            )
        return signals


class RecordingRiskEngine(RiskEngine):
    """RiskEngine that tracks how many trade proposals were evaluated."""

    def __init__(self):
        super().__init__()
        self.propose_calls = 0

    def propose_trade(self, *args, **kwargs):  # noqa: ANN002, ANN003
        self.propose_calls += 1
        return super().propose_trade(*args, **kwargs)


def _tiny_ohlcv_fixture() -> pd.DataFrame:
    idx = pd.date_range("2025-01-01", periods=5, freq="D")
    prices = [100.0, 102.0, 101.0, 103.0, 104.0]
    return pd.DataFrame(
        {
            "open": prices,
            "high": [p + 1.0 for p in prices],
            "low": [p - 1.0 for p in prices],
            "close": prices,
            "volume": [1_000_000] * len(prices),
        },
        index=idx,
    )


def test_backtest_runner_v1_deterministic_integration():
    symbol = "AAPL"
    fixture = _tiny_ohlcv_fixture()
    provider = InMemoryHistoricalDataProvider({symbol: fixture})
    risk_engine = RecordingRiskEngine()

    strategy = HardcodedSignalStrategy(
        StrategyConfig(
            name="hardcoded_signal",
            parameters={},
            universe=[symbol],
            initial_capital=100_000.0,
        ),
    )

    runner = StrategyLabBacktestRunner(
        data_provider=provider,
        risk_engine=risk_engine,
    )

    start = fixture.index.min().to_pydatetime()
    end = fixture.index.max().to_pydatetime()

    first = runner.run(
        strategy=strategy,
        start_date=start,
        end_date=end,
        universe=[symbol],
        initial_capital=100_000.0,
    )
    second = runner.run(
        strategy=strategy,
        start_date=start,
        end_date=end,
        universe=[symbol],
        initial_capital=100_000.0,
    )

    assert first.portfolio_history is not None
    assert second.portfolio_history is not None
    assert not first.portfolio_history.empty
    assert len(first.portfolio_history) == len(fixture)

    assert first.trade_log is not None
    assert second.trade_log is not None
    assert not first.trade_log.empty
    assert len(first.trade_log) >= 1

    assert_frame_equal(first.portfolio_history, second.portfolio_history)
    assert_frame_equal(first.trade_log, second.trade_log)

    assert risk_engine.propose_calls >= 1

    report = build_backtest_report(first)
    assert "summary" in report
    assert "equity_curve" in report
    assert "trade_log" in report
