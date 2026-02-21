"""Tests for paper trading session routes and service flow."""

from __future__ import annotations

from datetime import datetime

from backend.api.routes_trading import get_session_status, start_session, stop_session
from backend.schemas.trading_sessions import StartTradingSessionRequest
from backend.services.trading_service import TradingService


class _MockQuoteProvider:
    def __init__(self):
        self.calls = 0

    def get_quote(self, symbol: str) -> dict:
        self.calls += 1
        base = 100.0 + self.calls
        return {
            "timestamp": datetime(2025, 5, 1, 9, 30),
            "open": base,
            "high": base + 1.0,
            "low": base - 1.0,
            "close": base + 0.5,
        }


def test_trading_session_start_tick_status_stop(monkeypatch):
    from backend.api import routes_trading

    service = TradingService(quote_provider=_MockQuoteProvider())
    monkeypatch.setattr(routes_trading, "trading_service", service)

    started = start_session(
        StartTradingSessionRequest(symbols=["AAPL"], initial_capital=100000.0),
    )
    session_id = started["session_id"]
    assert started["state"] == "running"

    reports = service.tick(session_id)
    assert isinstance(reports, list)

    status = get_session_status(session_id)
    assert status["session_id"] == session_id
    assert status["tick_count"] == 1

    stopped = stop_session(session_id=session_id)
    assert stopped["state"] == "stopped"
