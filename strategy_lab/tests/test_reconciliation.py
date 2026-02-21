from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from strategy_lab.core.types import OrderIntent, OrderSide, OrderType
from strategy_lab.execution.broker_adapter import MockBrokerAdapter
from strategy_lab.execution.reconciliation import reconcile_with_broker
from strategy_lab.risk.portfolio_state import (
    PortfolioState,
    PositionSide,
    PositionState,
)


def test_reconciliation_detects_matches_and_mismatches():
    adapter = MockBrokerAdapter()
    adapter.place_order(
        OrderIntent(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10.0,
            timestamp=datetime(2025, 1, 1),
            metadata={"reference_price": 100.0},
        ),
    )
    adapter.place_order(
        OrderIntent(
            symbol="TSLA",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=3.0,
            timestamp=datetime(2025, 1, 1),
            metadata={"reference_price": 200.0},
        ),
    )

    portfolio = PortfolioState(
        initial_equity=Decimal("100000"),
        current_equity=Decimal("100000"),
    )
    portfolio.add_position(
        PositionState(
            symbol="AAPL",
            side=PositionSide.LONG,
            quantity=Decimal("10"),
            avg_price=Decimal("100"),
        ),
    )
    portfolio.add_position(
        PositionState(
            symbol="MSFT",
            side=PositionSide.LONG,
            quantity=Decimal("2"),
            avg_price=Decimal("150"),
        ),
    )

    summary = reconcile_with_broker(broker_adapter=adapter, portfolio=portfolio)
    assert "AAPL" in summary["matched"]
    assert "MSFT" in summary["missing_in_broker"]
    assert "TSLA" in summary["missing_internal"]
    assert isinstance(summary["fills"], list)
