from datetime import datetime, timezone

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.models import Base
from portfolio.ledger.repo import append_trade, list_trades
from portfolio.ledger.schemas import TradeEvent


@pytest.fixture
def db_session():
    # In-memory SQLite for testing
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    yield session
    session.close()


def test_append_trade(db_session):
    event = TradeEvent(
        timestamp=datetime.now(timezone.utc),
        symbol="AAPL",
        side="BUY",
        quantity=10.0,
        price=150.0,
        execution_venue="BACKTEST",
        run_id="test_run_1",
    )

    trade = append_trade(db_session, event)
    assert trade.trade_id is not None
    assert trade.symbol == "AAPL"

    # Read back inequality test
    trades = list_trades(db_session, run_id="test_run_1")
    assert len(trades) == 1
    assert trades[0].symbol == "AAPL"
    assert trades[0].quantity == 10.0
    assert trades[0].price == 150.0


def test_append_only_behavior_implied(db_session):
    # Test that no update or delete functions are exposed in the repo.
    import portfolio.ledger.repo as repo

    assert not hasattr(repo, "update_trade")
    assert not hasattr(repo, "delete_trade")
