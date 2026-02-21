from datetime import datetime, timedelta, timezone

from portfolio.accounting.schemas import (
    PortfolioSnapshot,
    PortfolioTimeline,
    PositionSnapshot,
)
from portfolio.ledger.models import Trade
from portfolio.metrics.aggregation import aggregate_strategy_metrics
from portfolio.metrics.exposure import calculate_snapshot_exposure
from portfolio.metrics.performance import calculate_performance_metrics


def test_performance_metrics():
    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t1 = t0 + timedelta(days=1)
    t2 = t0 + timedelta(days=2)

    # 1. Equity: 100 -> 110 -> 105 (Peak 110, DD (110-105)/110 = 0.04545)
    snapshots = [
        PortfolioSnapshot(
            timestamp=t0,
            cash=100.0,
            equity=100.0,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            positions={},
        ),
        PortfolioSnapshot(
            timestamp=t1,
            cash=110.0,
            equity=110.0,
            realized_pnl=10.0,
            unrealized_pnl=0.0,
            positions={},
        ),  # Win jump: 10.0
        PortfolioSnapshot(
            timestamp=t2,
            cash=105.0,
            equity=105.0,
            realized_pnl=5.0,
            unrealized_pnl=0.0,
            positions={},
        ),  # Loss jump: -5.0
    ]
    timeline = PortfolioTimeline(snapshots=snapshots, final_state=snapshots[-1])

    metrics = calculate_performance_metrics(timeline)
    assert metrics.total_return == 0.05
    assert abs(metrics.max_drawdown - 0.04545) < 0.001
    assert metrics.winning_trades_count == 1
    assert metrics.losing_trades_count == 1
    assert metrics.total_trades_count == 2
    assert metrics.win_rate == 50.0


def test_exposure_metrics():
    t0 = datetime.now()
    pos_long = PositionSnapshot(
        symbol="AAPL", quantity=10, avg_cost=100, market_price=150, unrealized_pnl=500
    )
    pos_short = PositionSnapshot(
        symbol="TSLA", quantity=-5, avg_cost=200, market_price=250, unrealized_pnl=-250
    )

    snap = PortfolioSnapshot(
        timestamp=t0,
        cash=1000,
        equity=1250,  # 1000 + 1500 + (-1250)
        realized_pnl=0,
        unrealized_pnl=250,
        positions={"AAPL": pos_long, "TSLA": pos_short},
    )

    exposure = calculate_snapshot_exposure(snap)
    assert exposure.long_exposure == 1500.0
    assert exposure.short_exposure == 1250.0
    assert exposure.gross_exposure == 2750.0
    assert exposure.net_exposure == 250.0

    assert exposure.concentration["AAPL"] == 1500.0 / 2750.0
    assert exposure.concentration["TSLA"] == 1250.0 / 2750.0


def test_strategy_aggregation():
    t0 = datetime(2025, 1, 1, tzinfo=timezone.utc)
    t1 = t0 + timedelta(days=1)

    trades = [
        Trade(
            trade_id="1",
            timestamp=t0,
            symbol="AAPL",
            side="BUY",
            quantity=10,
            price=100,
            strategy_id="strat_a",
            execution_venue="B",
        ),
        Trade(
            trade_id="2",
            timestamp=t1,
            symbol="AAPL",
            side="SELL",
            quantity=10,
            price=150,
            strategy_id="strat_a",
            execution_venue="B",
        ),
        Trade(
            trade_id="3",
            timestamp=t0,
            symbol="TSLA",
            side="BUY",
            quantity=5,
            price=200,
            strategy_id="strat_b",
            execution_venue="B",
        ),
        Trade(
            trade_id="4",
            timestamp=t1,
            symbol="TSLA",
            side="SELL",
            quantity=5,
            price=100,
            strategy_id="strat_b",
            execution_venue="B",
        ),
        Trade(
            trade_id="5",
            timestamp=t1,
            symbol="MSFT",
            side="BUY",
            quantity=10,
            price=50,
            strategy_id="strat_a",
            execution_venue="B",
        ),
    ]

    metrics = aggregate_strategy_metrics(trades)

    strat_a = next(m for m in metrics if m.strategy_id == "strat_a")
    strat_b = next(m for m in metrics if m.strategy_id == "strat_b")

    # strat_a: bought 10@100, sold 10@150 => 500 PnL
    # MSFT bought 10@50 (no realized yet)
    assert strat_a.realized_pnl == 500.0

    # strat_b: bought 5@200, sold 5@100 => -500 PnL
    assert strat_b.realized_pnl == -500.0
