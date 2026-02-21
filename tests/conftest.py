"""Test configuration and fixtures."""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import pytest  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402
from sqlalchemy.pool import StaticPool  # noqa: E402

from backend.db.models import Base  # noqa: E402


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Automatically patch SessionLocal to use an in-memory SQLite DB for all tests."""

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
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
