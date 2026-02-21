import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.models import Base


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Automatically patch SessionLocal to use an in-memory SQLite DB for all tests."""
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Patch the backend SessionLocal
    monkeypatch.setattr("backend.db.database.SessionLocal", TestingSessionLocal)

    # Also patch where it's explicitly imported
    try:
        monkeypatch.setattr(
            "strategy_lab.backtest.runner.SessionLocal", TestingSessionLocal
        )
    except AttributeError:
        pass
