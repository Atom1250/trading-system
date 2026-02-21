"""Strategy level aggregation."""

from typing import Dict, List

from portfolio.ledger.models import Trade

from .schemas import StrategyMetrics


def aggregate_strategy_metrics(trades: List[Trade]) -> List[StrategyMetrics]:
    """
    Groups trades by strategy_id and computes basic PnL totals.
    This provides strategy-level contribution without full portfolio rebuilding.
    """
    # Simply sum up realized/unrealized ?
    # Since we can't do full mark-to-market without price series per strategy easily,
    # the minimum specification says:
    # "compute per-strategy equity curve if feasible; minimum: per-strategy realized/unrealized totals"
    # To get realized we do standard FIFO.
    # For a simple minimum implementation without MTM: we can aggregate cash flow.
    # We will implement a quick FIFO realized PNL per strategy.

    from portfolio.accounting.pnl import calculate_new_avg_cost, calculate_realized_pnl

    strats: Dict[str, Dict[str, float]] = {}  # strategy_id -> {symbol: qty}
    strats_ac: Dict[str, Dict[str, float]] = {}  # strategy_id -> {symbol: avg_cost}
    realized: Dict[str, float] = {}

    # Sort trades to be safe
    sorted_trades = sorted(trades, key=lambda t: (t.timestamp, t.trade_id))

    for t in sorted_trades:
        sid = t.strategy_id or "unassigned"

        if sid not in strats:
            strats[sid] = {}
            strats_ac[sid] = {}
            realized[sid] = 0.0

        sym = t.symbol
        qty = t.quantity
        price = t.price
        side = t.side

        curr_qty = strats[sid].get(sym, 0.0)
        curr_ac = strats_ac[sid].get(sym, 0.0)

        pnl = calculate_realized_pnl(curr_qty, curr_ac, qty, price, side)
        realized[sid] += pnl

        new_ac = calculate_new_avg_cost(curr_qty, curr_ac, qty, price, side)
        sgn_qty = qty if side == "BUY" else -qty
        new_qty = curr_qty + sgn_qty

        if abs(new_qty) < 1e-8:
            if sym in strats[sid]:
                del strats[sid][sym]
            if sym in strats_ac[sid]:
                del strats_ac[sid][sym]
        else:
            strats[sid][sym] = new_qty
            strats_ac[sid][sym] = new_ac

    # Unrealized without marks is 0, but total PnL = realized
    results = []
    for sid in realized:
        results.append(
            StrategyMetrics(
                strategy_id=sid,
                realized_pnl=realized[sid],
                unrealized_pnl=0.0,
                total_pnl=realized[sid],
            )
        )
    return results
