"""Deterministic portfolio accounting engine."""

from datetime import datetime
from typing import Dict, List

from portfolio.ledger.models import Trade

from .pnl import calculate_new_avg_cost, calculate_realized_pnl
from .schemas import PortfolioSnapshot, PortfolioTimeline, PositionSnapshot


def rebuild_portfolio(
    trades: List[Trade],
    price_marks: Dict[datetime, Dict[str, float]],
    initial_cash: float,
) -> PortfolioTimeline:
    """
    Rebuilds the portfolio state deterministically from an append-only ledger of trades.
    Trades must be sorted by timestamp. MTM is evaluated at each mark timestamp via price_marks.
    """

    cash = initial_cash
    realized_pnl = 0.0
    positions: Dict[str, float] = {}  # symbol -> qty
    avg_costs: Dict[str, float] = {}  # symbol -> avg_cost

    snapshots: List[PortfolioSnapshot] = []

    sorted_trades = sorted(trades, key=lambda t: (t.timestamp, t.trade_id))

    trade_times = {t.timestamp for t in sorted_trades}
    mark_times = set(price_marks.keys())
    all_times = sorted(list(trade_times | mark_times))

    trade_idx = 0
    trade_count = len(sorted_trades)

    for current_time in all_times:
        # Process trades occurring exactly at current_time
        while (
            trade_idx < trade_count
            and sorted_trades[trade_idx].timestamp == current_time
        ):
            trade = sorted_trades[trade_idx]
            symbol = trade.symbol
            qty = trade.quantity
            price = trade.price
            side = trade.side
            commission = trade.commission or 0.0

            cash -= commission

            current_qty = positions.get(symbol, 0.0)
            current_ac = avg_costs.get(symbol, 0.0)

            pnl = calculate_realized_pnl(current_qty, current_ac, qty, price, side)
            realized_pnl += pnl

            new_ac = calculate_new_avg_cost(current_qty, current_ac, qty, price, side)
            sgn_qty = qty if side == "BUY" else -qty

            cash -= sgn_qty * price
            new_qty = current_qty + sgn_qty

            if abs(new_qty) < 1e-8:
                if symbol in positions:
                    del positions[symbol]
                if symbol in avg_costs:
                    del avg_costs[symbol]
            else:
                positions[symbol] = new_qty
                avg_costs[symbol] = new_ac

            trade_idx += 1

        marks = price_marks.get(current_time, {})

        unrealized_pnl = 0.0
        pos_snapshots: Dict[str, PositionSnapshot] = {}
        positions_value = 0.0

        for symbol, qty in positions.items():
            ac = avg_costs[symbol]
            m_price = marks.get(symbol, ac)

            val = qty * m_price
            positions_value += val

            pos_unrealized = (m_price - ac) * qty
            unrealized_pnl += pos_unrealized

            pos_snapshots[symbol] = PositionSnapshot(
                symbol=symbol,
                quantity=qty,
                avg_cost=ac,
                market_price=m_price,
                unrealized_pnl=pos_unrealized,
            )

        equity = cash + positions_value

        snap = PortfolioSnapshot(
            timestamp=current_time,
            cash=cash,
            equity=equity,
            realized_pnl=realized_pnl,
            unrealized_pnl=unrealized_pnl,
            positions=pos_snapshots,
        )
        snapshots.append(snap)

    final_state = (
        snapshots[-1]
        if snapshots
        else PortfolioSnapshot(
            timestamp=datetime.now(),
            cash=initial_cash,
            equity=initial_cash,
            realized_pnl=0.0,
            unrealized_pnl=0.0,
            positions={},
        )
    )

    return PortfolioTimeline(snapshots=snapshots, final_state=final_state)
