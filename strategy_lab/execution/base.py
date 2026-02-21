"""Execution engine interfaces for Strategy Lab."""

from __future__ import annotations

from abc import ABC, abstractmethod

from strategy_lab.core.types import ExecutionReport, OrderIntent
from strategy_lab.risk.portfolio_state import PortfolioState


class ExecutionEngine(ABC):
    """Abstract execution backend contract."""

    @abstractmethod
    def submit_order_intent(self, order_intent: OrderIntent) -> None:
        """Submit an approved order intent for execution."""

    @abstractmethod
    def on_bar(
        self,
        *,
        symbol: str,
        timestamp,
        open_price: float,
        high_price: float,
        low_price: float,
        close_price: float,
        portfolio: PortfolioState,
    ) -> list[ExecutionReport]:
        """Process one symbol/bar and return execution reports."""
