"""Paper trading execution backend with simulated fills."""

from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from typing import Optional

from strategy_lab.core.types import (
    ExecutionReport,
    ExecutionStatus,
    OrderIntent,
    OrderSide,
    OrderType,
)
from strategy_lab.execution.base import ExecutionEngine
from strategy_lab.risk.portfolio_state import (
    PortfolioState,
    PositionSide,
    PositionState,
)


class PaperExecutionEngine(ExecutionEngine):
    """Paper execution engine using quote bars for simulated fills."""

    def __init__(self):
        self._pending_market_orders: dict[str, list[OrderIntent]] = {}
        self._position_stops: dict[str, float] = {}

    def submit_order_intent(self, order_intent: OrderIntent) -> None:
        if order_intent.order_type != OrderType.MARKET:
            raise ValueError("PaperExecutionEngine currently supports MARKET intents")
        self._pending_market_orders.setdefault(order_intent.symbol, []).append(
            order_intent
        )

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
        reports: list[ExecutionReport] = []
        reports.extend(
            self._fill_pending_market_orders(
                symbol=symbol,
                timestamp=timestamp,
                fill_price=close_price,
                portfolio=portfolio,
            ),
        )
        stop_report = self._apply_stop_if_triggered(
            symbol=symbol,
            timestamp=timestamp,
            high_price=high_price,
            low_price=low_price,
            portfolio=portfolio,
        )
        if stop_report is not None:
            reports.append(stop_report)

        position = portfolio.get_position(symbol)
        if position is not None:
            position.update_unrealized_pnl(Decimal(str(close_price)))
        portfolio.update_equity()
        return reports

    def _fill_pending_market_orders(
        self,
        *,
        symbol: str,
        timestamp,
        fill_price: float,
        portfolio: PortfolioState,
    ) -> list[ExecutionReport]:
        orders = self._pending_market_orders.get(symbol, [])
        if not orders:
            return []

        reports: list[ExecutionReport] = []
        self._pending_market_orders[symbol] = []
        for intent in orders:
            side = (
                PositionSide.LONG
                if intent.side == OrderSide.BUY
                else PositionSide.SHORT
            )
            price = Decimal(str(fill_price))
            qty = Decimal(str(intent.quantity))
            portfolio.cash -= qty * price
            position = PositionState(
                symbol=symbol,
                side=side,
                quantity=qty,
                avg_price=price,
                entry_timestamp=int(self._to_datetime(timestamp).timestamp()),
                last_update_timestamp=int(self._to_datetime(timestamp).timestamp()),
            )
            portfolio.add_position(position)
            if intent.stop_price is not None:
                self._position_stops[symbol] = float(intent.stop_price)
            reports.append(
                ExecutionReport(
                    status=ExecutionStatus.FILLED,
                    symbol=symbol,
                    side=intent.side,
                    order_type=intent.order_type,
                    requested_quantity=float(intent.quantity),
                    filled_quantity=float(intent.quantity),
                    submitted_at=intent.timestamp,
                    filled_at=self._to_datetime(timestamp),
                    avg_fill_price=float(fill_price),
                    metadata={"fill_rule": "paper_quote_close"},
                ),
            )
        return reports

    def _apply_stop_if_triggered(
        self,
        *,
        symbol: str,
        timestamp,
        high_price: float,
        low_price: float,
        portfolio: PortfolioState,
    ) -> Optional[ExecutionReport]:
        position = portfolio.get_position(symbol)
        stop_price = self._position_stops.get(symbol)
        if position is None or stop_price is None:
            return None

        trigger = (position.side == PositionSide.LONG and low_price <= stop_price) or (
            position.side == PositionSide.SHORT and high_price >= stop_price
        )
        if not trigger:
            return None

        closed = portfolio.remove_position(symbol)
        if closed is None:
            return None

        stop_fill = Decimal(str(stop_price))
        if closed.side == PositionSide.LONG:
            pnl = (stop_fill - closed.avg_price) * closed.quantity
            returned_capital = closed.quantity * stop_fill
            report_side = OrderSide.SELL
        else:
            pnl = (closed.avg_price - stop_fill) * closed.quantity
            returned_capital = (closed.quantity * closed.avg_price) + pnl
            report_side = OrderSide.BUY
        portfolio.cash += returned_capital
        portfolio.total_realized_pnl += pnl
        self._position_stops.pop(symbol, None)

        return ExecutionReport(
            status=ExecutionStatus.FILLED,
            symbol=symbol,
            side=report_side,
            order_type=OrderType.STOP,
            requested_quantity=float(closed.quantity),
            filled_quantity=float(closed.quantity),
            submitted_at=self._to_datetime(timestamp),
            filled_at=self._to_datetime(timestamp),
            avg_fill_price=float(stop_price),
            metadata={"fill_rule": "paper_stop"},
        )

    @staticmethod
    def _to_datetime(timestamp) -> datetime:
        if isinstance(timestamp, datetime):
            return timestamp
        return timestamp.to_pydatetime()
