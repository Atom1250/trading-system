"""Paper trading session routes."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, HTTPException

from backend.schemas.trading_sessions import (
    StartTradingSessionRequest,
    StartTradingSessionResponse,
    StopTradingSessionResponse,
    TradingSessionStatusResponse,
)
from backend.services.trading_service import TradingService


class _DefaultQuoteProvider:
    """Deterministic fallback quote provider for session scaffolding."""

    def get_quote(self, symbol: str) -> dict:
        now = datetime.utcnow()
        base = float(len(symbol) * 10)
        return {
            "timestamp": now,
            "open": base,
            "high": base + 1.0,
            "low": base - 1.0,
            "close": base + 0.5,
        }


router = APIRouter()
trading_service = TradingService(quote_provider=_DefaultQuoteProvider())


@router.post(
    "/trading/sessions/start",
    response_model=StartTradingSessionResponse,
)
def start_session(request: StartTradingSessionRequest):
    if not request.symbols:
        raise HTTPException(status_code=400, detail="symbols must not be empty")
    session = trading_service.start_session(
        symbols=request.symbols,
        initial_capital=request.initial_capital,
    )
    return {"session_id": session.session_id, "state": session.state}


@router.post(
    "/trading/sessions/stop",
    response_model=StopTradingSessionResponse,
)
def stop_session(session_id: str):
    try:
        session = trading_service.stop_session(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return {"session_id": session.session_id, "state": session.state}


@router.get(
    "/trading/sessions/{session_id}/status",
    response_model=TradingSessionStatusResponse,
)
def get_session_status(session_id: str):
    try:
        session = trading_service.get_session_status(session_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found")
    return {
        "session_id": session.session_id,
        "state": session.state,
        "symbols": session.symbols,
        "initial_capital": session.initial_capital,
        "tick_count": session.tick_count,
        "reports_count": session.reports_count,
        "created_at": session.created_at.isoformat(),
        "started_at": session.started_at.isoformat(),
        "stopped_at": session.stopped_at.isoformat() if session.stopped_at else None,
        "last_tick_at": (
            session.last_tick_at.isoformat() if session.last_tick_at else None
        ),
    }
