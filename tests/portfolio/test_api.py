from datetime import datetime

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db.database import get_db
from backend.main import app
from portfolio.ledger.models import Trade

client = TestClient(app)


@pytest.fixture(scope="function")
def api_db():
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    from portfolio.ledger.models import Base as LedgerBase

    print("API_DB TABLES:", LedgerBase.metadata.tables.keys())
    LedgerBase.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    db = TestingSessionLocal()

    # Insert some dummy trades
    trades = [
        Trade(
            trade_id="api_1",
            timestamp=datetime(2025, 1, 1),
            symbol="AAPL",
            side="BUY",
            quantity=10,
            price=100,
            strategy_id="strat_1",
            run_id="run_test",
            execution_venue="B",
        ),
        Trade(
            trade_id="api_2",
            timestamp=datetime(2025, 1, 2),
            symbol="AAPL",
            side="SELL",
            quantity=10,
            price=150,
            strategy_id="strat_1",
            run_id="run_test",
            execution_venue="B",
        ),
    ]
    db.add_all(trades)
    db.commit()

    def override_get_db():
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield db
    app.dependency_overrides.clear()


def test_get_portfolio_trades_returns_200(api_db):
    response = client.get("/api/v1/portfolio/trades?run_id=run_test")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["symbol"] == "AAPL"


def test_get_portfolio_trades_404_if_not_found(api_db):
    response = client.get("/api/v1/portfolio/trades?run_id=invalid")
    assert response.status_code == 404


def test_get_portfolio_state_returns_200(api_db):
    response = client.get("/api/v1/portfolio/state?run_id=run_test")
    assert response.status_code == 200
    data = response.json()
    assert "cash" in data
    assert "equity" in data
    assert data["realized_pnl"] == 500.0  # 10 * (150 - 100)


def test_get_portfolio_equity_curve_returns_200(api_db):
    response = client.get("/api/v1/portfolio/equity?run_id=run_test")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert "equity" in data[0]


def test_get_portfolio_metrics_returns_200(api_db):
    response = client.get("/api/v1/portfolio/metrics?run_id=run_test")
    assert response.status_code == 200
    data = response.json()
    assert "total_return" in data
    assert data["winning_trades_count"] == 1


def test_get_portfolio_allocations_returns_200(api_db):
    response = client.get("/api/v1/portfolio/allocations?run_id=run_test")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["strategy_id"] == "strat_1"


def test_get_portfolio_positions_returns_200(api_db):
    response = client.get("/api/v1/portfolio/positions?run_id=run_test")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, dict)
    assert "AAPL" not in data


def test_create_and_get_trade_notes(api_db):
    note_payload = {"trade_id": "api_1", "note_text": "Good entry", "tags": ["buy"]}
    resp = client.post("/api/v1/portfolio/journal", json=note_payload)
    assert resp.status_code == 200
    data = resp.json()
    assert data["note_text"] == "Good entry"

    resp_get = client.get("/api/v1/portfolio/journal/api_1")
    assert resp_get.status_code == 200
    assert len(resp_get.json()) == 1
    assert resp_get.json()[0]["tags"] == ["buy"]
