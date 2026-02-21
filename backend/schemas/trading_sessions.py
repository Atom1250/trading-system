"""Schemas for paper trading session endpoints."""

from __future__ import annotations

from pydantic import BaseModel, Field


class StartTradingSessionRequest(BaseModel):
    symbols: list[str] = Field(default_factory=list)
    initial_capital: float = 100000.0


class TradingSessionStatusResponse(BaseModel):
    session_id: str
    state: str
    symbols: list[str]
    initial_capital: float
    tick_count: int
    reports_count: int
    created_at: str
    started_at: str
    stopped_at: str | None
    last_tick_at: str | None


class StartTradingSessionResponse(BaseModel):
    session_id: str
    state: str


class StopTradingSessionResponse(BaseModel):
    session_id: str
    state: str
