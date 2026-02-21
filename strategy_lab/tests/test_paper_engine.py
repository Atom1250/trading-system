from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from strategy_lab.core.types import OrderIntent, OrderSide, OrderType
from strategy_lab.execution.paper_engine import PaperExecutionEngine
from strategy_lab.risk.portfolio_state import PortfolioState


def test_paper_engine_fills_market_on_quote_close():
    engine = PaperExecutionEngine()
    portfolio = PortfolioState(
        initial_equity=Decimal("100000"),
        current_equity=Decimal("100000"),
    )
    intent = OrderIntent(
        symbol="AAPL",
        side=OrderSide.BUY,
        order_type=OrderType.MARKET,
        quantity=10.0,
        timestamp=datetime(2025, 1, 1),
        stop_price=98.5,
    )
    engine.submit_order_intent(intent)
    reports = engine.on_bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, 1, 9, 30),
        open_price=100.0,
        high_price=101.0,
        low_price=99.0,
        close_price=100.5,
        portfolio=portfolio,
    )
    assert len(reports) == 1
    assert reports[0].avg_fill_price == 100.5
    assert portfolio.has_position("AAPL")


def test_paper_engine_stop_triggers_intrabar():
    engine = PaperExecutionEngine()
    portfolio = PortfolioState(
        initial_equity=Decimal("100000"),
        current_equity=Decimal("100000"),
    )
    engine.submit_order_intent(
        OrderIntent(
            symbol="AAPL",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10.0,
            timestamp=datetime(2025, 1, 1),
            stop_price=98.5,
        ),
    )
    engine.on_bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, 1, 9, 30),
        open_price=100.0,
        high_price=101.0,
        low_price=99.0,
        close_price=100.0,
        portfolio=portfolio,
    )
    reports = engine.on_bar(
        symbol="AAPL",
        timestamp=datetime(2025, 1, 1, 9, 31),
        open_price=99.0,
        high_price=99.5,
        low_price=98.0,
        close_price=98.3,
        portfolio=portfolio,
    )
    assert len(reports) == 1
    assert reports[0].order_type == OrderType.STOP
    assert reports[0].avg_fill_price == 98.5
    assert not portfolio.has_position("AAPL")
