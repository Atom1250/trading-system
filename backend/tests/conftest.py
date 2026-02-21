"""Pytest conftest to ensure repository root is on sys.path for imports.

Some tests run with the test directory as sys.path[0], which can prevent
top-level shim packages from being importable. Add the project root to
sys.path at collection time so `import services` resolves correctly.
"""

import os
import sys

_repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _repo_root not in sys.path:
    sys.path.insert(0, _repo_root)

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.db.models import Base


@pytest.fixture(autouse=True)
def setup_test_db(monkeypatch):
    """Patch SessionLocal with a fully initialised in-memory SQLite database.

    Ensures all ORM tables (including portfolio_trades) are created before
    any test that triggers the Strategy Lab backtest runner.
    """
    from portfolio.ledger.models import Trade  # noqa: F401 — registers the model

    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    monkeypatch.setattr("backend.db.database.SessionLocal", TestingSessionLocal)

    try:
        monkeypatch.setattr("strategy_lab.backtest.runner.SessionLocal", TestingSessionLocal)
    except AttributeError:
        pass

