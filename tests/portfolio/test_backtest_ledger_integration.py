from datetime import datetime

import pandas as pd
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.models import Base
from portfolio.ledger.repo import list_trades
from strategy_lab.backtest.runner import StrategyLabBacktestRunner
from strategy_lab.config import StrategyConfig
from strategy_lab.data.base import MarketDataSlice
from strategy_lab.risk.engine import RiskEngine
from strategy_lab.strategies.base import FactorPanels, MarketDataSlices, Strategy


class InMemoryHistoricalDataProvider:
    def __init__(self, payload: dict[str, pd.DataFrame]):
        self._payload = payload

    def get_history(
        self, symbol: str, start: datetime, end: datetime
    ) -> MarketDataSlice:
        df = self._payload[symbol]
        df = df.loc[(df.index >= start) & (df.index <= end)]
        return MarketDataSlice(symbol=symbol, df=df.copy())


class HardcodedBuyStrategy(Strategy):
    def generate_signals(
        self, data: MarketDataSlices, factor_panels: FactorPanels
    ) -> dict[str, pd.Series]:
        signals = {}
        for symbol, market_slice in data.items():
            signals[symbol] = pd.Series(
                data=1, index=market_slice.df.index, dtype=float
            )
        return signals


def _tiny_ohlcv_fixture() -> pd.DataFrame:
    idx = pd.date_range("2026-01-01", periods=3, freq="D")
    prices = [100.0, 105.0, 110.0]
    return pd.DataFrame(
        {
            "open": prices,
            "high": [p + 1.0 for p in prices],
            "low": [p - 1.0 for p in prices],
            "close": prices,
            "volume": [1000] * len(prices),
        },
        index=idx,
    )


@pytest.fixture
def test_db_session(monkeypatch):
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Patch SessionLocal in runner
    monkeypatch.setattr(
        "strategy_lab.backtest.runner.SessionLocal", TestingSessionLocal
    )

    session = TestingSessionLocal()
    yield session
    session.close()


def test_backtest_writes_ledger(test_db_session):
    symbol = "TEST"
    fixture = _tiny_ohlcv_fixture()
    provider = InMemoryHistoricalDataProvider({symbol: fixture})
    risk_engine = RiskEngine()

    strategy = HardcodedBuyStrategy(
        StrategyConfig(
            name="test_ledger_strategy",
            parameters={},
            universe=[symbol],
            initial_capital=100_000.0,
        )
    )

    runner = StrategyLabBacktestRunner(
        data_provider=provider,
        risk_engine=risk_engine,
    )

    start = fixture.index.min().to_pydatetime()
    end = fixture.index.max().to_pydatetime()

    runner.run(
        strategy=strategy,
        start_date=start,
        end_date=end,
        universe=[symbol],
        initial_capital=100_000.0,
    )

    # Verify that trades were written to the ledger
    trades = list_trades(test_db_session, strategy_id="test_ledger_strategy")

    assert len(trades) > 0, "No trades were written to the ledger"

    # Check invariant: run_id is attached to all trades
    run_ids = {trade.run_id for trade in trades}
    assert len(run_ids) == 1, "All trades in a run should share the same run_id"

    # Verify execution_venue
    assert all(t.execution_venue == "BACKTEST" for t in trades)
