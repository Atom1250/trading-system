"""Broker execution engine scaffolding backed by BrokerAdapter (mock-ready)."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from strategy_lab.core.types import ExecutionReport, ExecutionStatus, OrderIntent
from strategy_lab.execution.base import ExecutionEngine
from strategy_lab.execution.broker_adapter import BrokerAdapter
from strategy_lab.risk.portfolio_state import PortfolioState


class BrokerExecutionEngine(ExecutionEngine):
    """Execution engine that forwards orders to a broker adapter."""

    def __init__(self, broker_adapter: BrokerAdapter):
        self.broker_adapter = broker_adapter
        self._pending_reports: list[ExecutionReport] = []

    def submit_order_intent(self, order_intent: OrderIntent) -> None:
        broker_order = self.broker_adapter.place_order(order_intent)
        status = (
            ExecutionStatus.FILLED
            if broker_order.status == "filled"
            else ExecutionStatus.PENDING
        )
        report = ExecutionReport(
            status=status,
            symbol=order_intent.symbol,
            side=order_intent.side,
            order_type=order_intent.order_type,
            requested_quantity=float(order_intent.quantity),
            filled_quantity=(
                float(order_intent.quantity)
                if status == ExecutionStatus.FILLED
                else 0.0
            ),
            submitted_at=order_intent.timestamp,
            filled_at=datetime.utcnow() if status == ExecutionStatus.FILLED else None,
            avg_fill_price=broker_order.avg_fill_price,
            metadata={"broker_order_id": broker_order.order_id},
        )
        self._pending_reports.append(report)

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
        del symbol, timestamp, open_price, high_price, low_price
        for position in portfolio.open_positions.values():
            position.update_unrealized_pnl(Decimal(str(close_price)))
        portfolio.update_equity()
        reports = self._pending_reports[:]
        self._pending_reports = []
        return reports

    def reconcile(self, portfolio: PortfolioState) -> dict:
        """Return reconciliation summary between broker and internal portfolio."""
        broker_positions = self.broker_adapter.get_positions()
        internal_positions = [
            {
                "symbol": p.symbol,
                "side": p.side.value,
                "quantity": float(p.quantity),
            }
            for p in portfolio.open_positions.values()
        ]
        return {
            "broker_positions": [p.__dict__ for p in broker_positions],
            "internal_positions": internal_positions,
            "open_orders": [o.__dict__ for o in self.broker_adapter.get_open_orders()],
            "fills": [f.__dict__ for f in self.broker_adapter.get_fills()],
            "status": "ok",
        }
