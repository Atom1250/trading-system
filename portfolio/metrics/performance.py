"""Performance metric calculations."""

import math

from portfolio.accounting.schemas import PortfolioTimeline

from .schemas import PerformanceMetrics


def calculate_performance_metrics(
    timeline: PortfolioTimeline, risk_free_rate: float = 0.0
) -> PerformanceMetrics:
    """Computes basic performance metrics from a portfolio timeline."""

    if not timeline.snapshots:
        return PerformanceMetrics(
            total_return=0.0,
            max_drawdown=0.0,
            sharpe_ratio=0.0,
            win_rate=0.0,
            total_trades_count=0,
            winning_trades_count=0,
            losing_trades_count=0,
        )

    snapshots = timeline.snapshots
    initial_equity = snapshots[0].equity
    final_equity = snapshots[-1].equity

    total_return = (
        (final_equity - initial_equity) / initial_equity if initial_equity > 0 else 0.0
    )

    # Drawdown
    peak = initial_equity
    max_dd = 0.0
    for snap in snapshots:
        if snap.equity > peak:
            peak = snap.equity

        if peak > 0:
            dd = (peak - snap.equity) / peak
            if dd > max_dd:
                max_dd = dd

    # Sharpe Ratio
    # We'll calculate period-over-period returns.
    # To annualize properly we'd need exact time deltas, but basic Sharpe assumes daily periods.
    # Let's compute average period return.
    returns = []
    prev_eq = initial_equity
    for snap in snapshots[1:]:
        if prev_eq > 0:
            returns.append((snap.equity - prev_eq) / prev_eq)
        else:
            returns.append(0.0)
        prev_eq = snap.equity

    mean_ret = sum(returns) / len(returns) if returns else 0.0

    variance = (
        sum((r - mean_ret) ** 2 for r in returns) / len(returns)
        if len(returns) > 1
        else 0.0
    )
    std_ret = math.sqrt(variance)

    # Assume ~252 trading days for basic annualization scaling
    sharpe = 0.0
    if std_ret > 0:
        sharpe = math.sqrt(252) * (mean_ret - (risk_free_rate / 252)) / std_ret

    # Win Rate based on Realized PnL jumps between snapshots
    wins = 0
    losses = 0
    prev_realized = snapshots[0].realized_pnl

    for snap in snapshots[1:]:
        jump = snap.realized_pnl - prev_realized
        if jump > 1e-6:
            wins += 1
        elif jump < -1e-6:
            losses += 1
        prev_realized = snap.realized_pnl

    total_closed = wins + losses
    win_rate = (wins / total_closed) * 100.0 if total_closed > 0 else 0.0

    return PerformanceMetrics(
        total_return=total_return,
        max_drawdown=max_dd,
        sharpe_ratio=sharpe,
        win_rate=win_rate,
        total_trades_count=total_closed,
        winning_trades_count=wins,
        losing_trades_count=losses,
    )
