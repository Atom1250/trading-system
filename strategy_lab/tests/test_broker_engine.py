from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from strategy_lab.core.types import OrderIntent, OrderSide, OrderType
from strategy_lab.execution.broker_adapter import MockBrokerAdapter
from strategy_lab.execution.broker_engine import BrokerExecutionEngine
from strategy_lab.risk.portfolio_state import PortfolioState


def test_broker_engine_submits_order_and_returns_execution_report():
    adapter = MockBrokerAdapter()
    engine = BrokerExecutionEngine(adapter)
    portfolio = PortfolioState(
        initial_equity=Decimal("100000"),
        current_equity=Decimal("100000"),
    )
    intent = OrderIntent(
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=5.0,
        timestamp=datetime(2025, 1, 1),
        metadata={"reference_price": 101.25},
    )

    engine.submit_order_intent(intent)
    reports = engine.on_bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, 1, 9, 30),
        open_price=100.0,
        high_price=102.0,
        low_price=99.0,
        close_price=101.0,
        portfolio=portfolio,
    )

    assert len(reports) == 1
    report = reports[0]
    assert report.symbol == "AAPL"
    assert report.side == OrderSide.BUY
    assert report.order_type == OrderType.MARKET
    assert report.filled_quantity == 5.0
    assert report.avg_fill_price == 101.25
    assert "broker_order_id" in report.metadata
