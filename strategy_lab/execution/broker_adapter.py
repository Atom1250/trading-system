"""Broker adapter contracts and mock implementation (no secrets required)."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

from strategy_lab.core.types import OrderIntent, OrderSide


@dataclass
class BrokerOrder:
    order_id: str
    symbol: str
    side: str
    quantity: float
    status: str
    submitted_at: datetime
    avg_fill_price: float | None = None


@dataclass
class BrokerFill:
    fill_id: str
    order_id: str
    symbol: str
    side: str
    quantity: float
    price: float
    timestamp: datetime


@dataclass
class BrokerPosition:
    symbol: str
    quantity: float
    side: str
    avg_price: float


class BrokerAdapter(ABC):
    """Abstract broker adapter interface."""

    @abstractmethod
    def place_order(self, order_intent: OrderIntent) -> BrokerOrder:
        """Place an order at the broker."""

    @abstractmethod
    def get_positions(self) -> list[BrokerPosition]:
        """Fetch broker positions."""

    @abstractmethod
    def get_open_orders(self) -> list[BrokerOrder]:
        """Fetch open orders."""

    @abstractmethod
    def get_fills(self) -> list[BrokerFill]:
        """Fetch fills."""

    @abstractmethod
    def cancel_order(self, order_id: str) -> bool:
        """Cancel an open order."""


class MockBrokerAdapter(BrokerAdapter):
    """Deterministic in-memory broker adapter for tests and scaffolding."""

    def __init__(self):
        self._orders: list[BrokerOrder] = []
        self._fills: list[BrokerFill] = []
        self._positions: dict[str, BrokerPosition] = {}

    def place_order(self, order_intent: OrderIntent) -> BrokerOrder:
        now = datetime.utcnow()
        order_id = str(uuid4())
        fill_price = (
            float(order_intent.limit_price)
            if order_intent.limit_price is not None
            else float(order_intent.metadata.get("reference_price", 100.0))
        )
        order = BrokerOrder(
            order_id=order_id,
            symbol=order_intent.symbol,
            side=order_intent.side.value,
            quantity=float(order_intent.quantity),
            status="filled",
            submitted_at=now,
            avg_fill_price=fill_price,
        )
        self._orders.append(order)
        fill = BrokerFill(
            fill_id=str(uuid4()),
            order_id=order_id,
            symbol=order_intent.symbol,
            side=order_intent.side.value,
            quantity=float(order_intent.quantity),
            price=fill_price,
            timestamp=now,
        )
        self._fills.append(fill)
        self._apply_position_update(
            symbol=order_intent.symbol,
            side=order_intent.side,
            quantity=float(order_intent.quantity),
            price=fill_price,
        )
        return order

    def get_positions(self) -> list[BrokerPosition]:
        return list(self._positions.values())

    def get_open_orders(self) -> list[BrokerOrder]:
        return [o for o in self._orders if o.status in {"new", "pending"}]

    def get_fills(self) -> list[BrokerFill]:
        return list(self._fills)

    def cancel_order(self, order_id: str) -> bool:
        for order in self._orders:
            if order.order_id == order_id and order.status in {"new", "pending"}:
                order.status = "cancelled"
                return True
        return False

    def _apply_position_update(
        self,
        *,
        symbol: str,
        side: OrderSide,
        quantity: float,
        price: float,
    ) -> None:
        signed_qty = quantity if side == OrderSide.BUY else -quantity
        existing = self._positions.get(symbol)
        if existing is None:
            pos_side = "long" if signed_qty >= 0 else "short"
            self._positions[symbol] = BrokerPosition(
                symbol=symbol,
                quantity=abs(signed_qty),
                side=pos_side,
                avg_price=price,
            )
            return

        current_signed = (
            existing.quantity if existing.side == "long" else -existing.quantity
        )
        new_signed = current_signed + signed_qty
        if new_signed == 0:
            self._positions.pop(symbol, None)
            return
        new_side = "long" if new_signed > 0 else "short"
        existing.quantity = abs(new_signed)
        existing.side = new_side
        existing.avg_price = price
