"""Deterministic backtest execution backend."""

from __future__ import annotations

from dataclasses import dataclass
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


@dataclass
class _PendingOrder:
    order_intent: OrderIntent
    stop_price: Optional[float]


class BacktestExecutionEngine(ExecutionEngine):
    """Backtest engine with next-bar-open fills and intrabar stop triggering."""

    def __init__(self):
        self._pending_market_orders: dict[str, list[_PendingOrder]] = {}
        self._position_stops: dict[str, float] = {}

    def submit_order_intent(self, order_intent: OrderIntent) -> None:
        if order_intent.order_type != OrderType.MARKET:
            raise ValueError(
                "BacktestExecutionEngine currently supports MARKET intents"
            )
        bucket = self._pending_market_orders.setdefault(order_intent.symbol, [])
        bucket.append(
            _PendingOrder(
                order_intent=order_intent,
                stop_price=order_intent.stop_price,
            ),
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
                open_price=open_price,
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
        # Mark-to-market at close after fills/stop checks.
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
        open_price: float,
        portfolio: PortfolioState,
    ) -> list[ExecutionReport]:
        pending = self._pending_market_orders.get(symbol, [])
        if not pending:
            return []

        reports: list[ExecutionReport] = []
        self._pending_market_orders[symbol] = []
        for item in pending:
            intent = item.order_intent
            side = (
                PositionSide.LONG
                if intent.side == OrderSide.BUY
                else PositionSide.SHORT
            )
            fill_price = Decimal(str(open_price))
            qty = Decimal(str(intent.quantity))
            portfolio.cash -= qty * fill_price
            position = PositionState(
                symbol=symbol,
                side=side,
                quantity=qty,
                avg_price=fill_price,
                entry_timestamp=self._to_epoch_seconds(timestamp),
                last_update_timestamp=self._to_epoch_seconds(timestamp),
            )
            portfolio.add_position(position)
            if item.stop_price is not None:
                self._position_stops[symbol] = float(item.stop_price)

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
                    avg_fill_price=float(open_price),
                    metadata={"fill_rule": "next_bar_open"},
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

        should_stop = False
        if position.side == PositionSide.LONG and low_price <= stop_price:
            should_stop = True
        if position.side == PositionSide.SHORT and high_price >= stop_price:
            should_stop = True
        if not should_stop:
            return None

        closed = portfolio.remove_position(symbol)
        if closed is None:
            return None

        stop_fill = Decimal(str(stop_price))
        if closed.side == PositionSide.LONG:
            pnl = (stop_fill - closed.avg_price) * closed.quantity
            returned_capital = closed.quantity * stop_fill
        else:
            pnl = (closed.avg_price - stop_fill) * closed.quantity
            returned_capital = (closed.quantity * closed.avg_price) + pnl

        portfolio.cash += returned_capital
        portfolio.total_realized_pnl += pnl
        self._position_stops.pop(symbol, None)

        return ExecutionReport(
            status=ExecutionStatus.FILLED,
            symbol=symbol,
            side=OrderSide.SELL if closed.side == PositionSide.LONG else OrderSide.BUY,
            order_type=OrderType.STOP,
            requested_quantity=float(closed.quantity),
            filled_quantity=float(closed.quantity),
            submitted_at=self._to_datetime(timestamp),
            filled_at=self._to_datetime(timestamp),
            avg_fill_price=float(stop_price),
            metadata={"fill_rule": "intrabar_stop"},
        )

    @staticmethod
    def _to_epoch_seconds(timestamp) -> int:
        return int(BacktestExecutionEngine._to_datetime(timestamp).timestamp())

    @staticmethod
    def _to_datetime(timestamp) -> datetime:
        if isinstance(timestamp, datetime):
            return timestamp
        return timestamp.to_pydatetime()
