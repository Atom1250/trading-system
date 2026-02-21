"""Reconciliation helpers for broker-vs-internal state alignment."""

from __future__ import annotations

from strategy_lab.execution.broker_adapter import BrokerAdapter
from strategy_lab.risk.portfolio_state import PortfolioState


def reconcile_with_broker(
    *,
    broker_adapter: BrokerAdapter,
    portfolio: PortfolioState,
) -> dict:
    """Fetch broker state and compare with internal portfolio state."""
    broker_positions = broker_adapter.get_positions()
    broker_by_symbol = {p.symbol: p for p in broker_positions}
    internal_by_symbol = portfolio.open_positions

    matched: list[str] = []
    missing_in_broker: list[str] = []
    missing_internal: list[str] = []
    mismatched: list[dict] = []

    for symbol, internal in internal_by_symbol.items():
        broker = broker_by_symbol.get(symbol)
        if broker is None:
            missing_in_broker.append(symbol)
            continue
        broker_qty = float(broker.quantity)
        internal_qty = float(internal.quantity)
        broker_side = broker.side
        internal_side = internal.side.value
        if broker_qty == internal_qty and broker_side == internal_side:
            matched.append(symbol)
        else:
            mismatched.append(
                {
                    "symbol": symbol,
                    "broker_quantity": broker_qty,
                    "internal_quantity": internal_qty,
                    "broker_side": broker_side,
                    "internal_side": internal_side,
                },
            )

    for symbol in broker_by_symbol:
        if symbol not in internal_by_symbol:
            missing_internal.append(symbol)

    return {
        "matched": matched,
        "missing_in_broker": missing_in_broker,
        "missing_internal": missing_internal,
        "mismatched": mismatched,
        "open_orders": [o.__dict__ for o in broker_adapter.get_open_orders()],
        "fills": [f.__dict__ for f in broker_adapter.get_fills()],
    }
