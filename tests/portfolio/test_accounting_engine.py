from datetime import datetime, timedelta, timezone

from portfolio.accounting.engine import rebuild_portfolio
from portfolio.ledger.models import Trade


def create_trade(timestamp, trade_id, symbol, side, qty, price):
    return Trade(
        trade_id=trade_id,
        timestamp=timestamp,
        symbol=symbol,
        side=side,
        quantity=qty,
        price=price,
        execution_venue="BACKTEST",
    )


def test_deterministic_reconstruction_simple_long():
    t0 = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(days=1)
    t2 = t0 + timedelta(days=2)
    t3 = t0 + timedelta(days=3)

    # buy 10 @100, sell 5 @110, mark 5 @105
    trades = [
        create_trade(t0, "1", "AAPL", "BUY", 10.0, 100.0),
        create_trade(t1, "2", "AAPL", "SELL", 5.0, 110.0),
    ]

    price_marks = {
        t0: {"AAPL": 100.0},
        t1: {"AAPL": 110.0},
        t2: {"AAPL": 105.0},
        t3: {"AAPL": 108.0},
    }

    timeline = rebuild_portfolio(trades, price_marks, initial_cash=1000.0)

    assert len(timeline.snapshots) == 4

    # At t0: Bought 10 @ 100
    snap0 = timeline.snapshots[0]
    assert snap0.cash == 0.0  # 1000 - 1000
    assert snap0.positions["AAPL"].quantity == 10.0
    assert snap0.positions["AAPL"].avg_cost == 100.0
    assert snap0.realized_pnl == 0.0
    assert snap0.unrealized_pnl == 0.0
    assert snap0.equity == 1000.0  # 0 cash + 10*100 pos

    # At t1: Sold 5 @ 110
    snap1 = timeline.snapshots[1]
    assert snap1.cash == 550.0  # 0 + 550
    assert snap1.positions["AAPL"].quantity == 5.0
    assert snap1.positions["AAPL"].avg_cost == 100.0
    assert snap1.realized_pnl == 50.0  # (110 - 100) * 5
    assert snap1.unrealized_pnl == 50.0  # (110 - 100) * 5 remaining
    assert snap1.equity == 1100.0  # 550 cash + 5*110 pos

    # At t2: Mark 5 @ 105
    snap2 = timeline.snapshots[2]
    assert snap2.cash == 550.0
    assert snap2.positions["AAPL"].quantity == 5.0
    assert snap2.realized_pnl == 50.0
    assert snap2.unrealized_pnl == 25.0  # (105 - 100) * 5
    assert snap2.equity == 1075.0  # 550 + 5*105


def test_short_selling_reconstruction():
    t0 = datetime(2025, 1, 1, 10, 0, tzinfo=timezone.utc)
    t1 = t0 + timedelta(days=1)

    trades = [
        create_trade(t0, "1", "TSLA", "SELL", 10.0, 200.0),  # Short 10
        create_trade(t1, "2", "TSLA", "BUY", 10.0, 150.0),  # Cover 10
    ]

    price_marks = {
        t0: {"TSLA": 200.0},
        t1: {"TSLA": 150.0},
    }

    timeline = rebuild_portfolio(trades, price_marks, initial_cash=10000.0)

    # At t0: Shorted 10 @ 200
    snap0 = timeline.snapshots[0]
    assert snap0.cash == 12000.0  # 10000 + 2000
    assert snap0.positions["TSLA"].quantity == -10.0
    assert snap0.positions["TSLA"].avg_cost == 200.0
    assert snap0.realized_pnl == 0.0
    assert snap0.unrealized_pnl == 0.0  # (200 - 200) * -10
    assert snap0.equity == 10000.0  # 12000 cash - 2000 position liability

    # At t1: Covered 10 @ 150
    snap1 = timeline.snapshots[1]
    assert snap1.cash == 10500.0  # 12000 - 1500
    assert "TSLA" not in snap1.positions
    assert snap1.realized_pnl == 500.0  # (200 - 150) * 10
    assert snap1.unrealized_pnl == 0.0
    assert snap1.equity == 10500.0  # 10500 cash + 0 pos
