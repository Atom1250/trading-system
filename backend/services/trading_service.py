"""Paper trading session service with deterministic tick loop."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Protocol
from uuid import uuid4

from strategy_lab.core.types import ExecutionReport, OrderIntent
from strategy_lab.execution.paper_engine import PaperExecutionEngine
from strategy_lab.risk.portfolio_state import PortfolioState


class QuoteProvider(Protocol):
    def get_quote(self, symbol: str) -> dict:
        """Return quote dict with timestamp/open/high/low/close for symbol."""


@dataclass
class TradingSession:
    session_id: str
    symbols: list[str]
    initial_capital: float
    state: str
    created_at: datetime
    started_at: datetime
    stopped_at: datetime | None = None
    last_tick_at: datetime | None = None
    tick_count: int = 0
    reports_count: int = 0
    latest_reports: list[ExecutionReport] = field(default_factory=list)


class TradingService:
    """Manage paper trading sessions and polling ticks."""

    def __init__(self, quote_provider: QuoteProvider):
        self.quote_provider = quote_provider
        self.sessions: dict[str, TradingSession] = {}
        self.engines: dict[str, PaperExecutionEngine] = {}
        self.portfolios: dict[str, PortfolioState] = {}

    def start_session(
        self,
        *,
        symbols: list[str],
        initial_capital: float = 100000.0,
    ) -> TradingSession:
        now = datetime.utcnow()
        session_id = str(uuid4())
        session = TradingSession(
            session_id=session_id,
            symbols=sorted(set(symbols)),
            initial_capital=initial_capital,
            state="running",
            created_at=now,
            started_at=now,
        )
        self.sessions[session_id] = session
        self.engines[session_id] = PaperExecutionEngine()
        self.portfolios[session_id] = PortfolioState(
            initial_equity=Decimal(str(initial_capital)),
            current_equity=Decimal(str(initial_capital)),
        )
        return session

    def stop_session(self, session_id: str) -> TradingSession:
        session = self._require_session(session_id)
        if session.state != "stopped":
            session.state = "stopped"
            session.stopped_at = datetime.utcnow()
        return session

    def get_session_status(self, session_id: str) -> TradingSession:
        return self._require_session(session_id)

    def submit_order_intent(self, session_id: str, order_intent: OrderIntent) -> None:
        session = self._require_session(session_id)
        if session.state != "running":
            raise ValueError("Cannot submit orders to stopped session")
        self.engines[session_id].submit_order_intent(order_intent)

    def tick(self, session_id: str) -> list[ExecutionReport]:
        session = self._require_session(session_id)
        if session.state != "running":
            return []

        portfolio = self.portfolios[session_id]
        engine = self.engines[session_id]
        reports: list[ExecutionReport] = []
        for symbol in session.symbols:
            quote = self.quote_provider.get_quote(symbol)
            quote_ts = quote.get("timestamp", datetime.utcnow())
            reports.extend(
                engine.on_bar(
                    symbol=symbol,
                    timestamp=quote_ts,
                    open_price=float(quote["open"]),
                    high_price=float(quote["high"]),
                    low_price=float(quote["low"]),
                    close_price=float(quote["close"]),
                    portfolio=portfolio,
                ),
            )
        session.latest_reports = reports
        session.reports_count += len(reports)
        session.tick_count += 1
        session.last_tick_at = datetime.utcnow()
        return reports

    def _require_session(self, session_id: str) -> TradingSession:
        session = self.sessions.get(session_id)
        if session is None:
            raise KeyError(session_id)
        return session
