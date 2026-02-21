"""Canonical backtest report serializers for Strategy Lab."""

from __future__ import annotations

from datetime import datetime
from typing import Any

import pandas as pd

from strategy_lab.backtest.results import BacktestResults


def to_equity_df(results: BacktestResults) -> pd.DataFrame:
    """Return canonical equity curve DataFrame."""
    if results.portfolio_history is not None and not results.portfolio_history.empty:
        df = results.portfolio_history.copy()
        if "timestamp" not in df.columns:
            df = df.reset_index().rename(columns={"index": "timestamp"})
        cols = [c for c in ["timestamp", "equity", "drawdown"] if c in df.columns]
        return df[cols]

    equity = results.get_equity_curve(initial_capital=results.config.initial_capital)
    drawdown = ((equity - equity.cummax()) / equity.cummax().replace(0, pd.NA)).fillna(
        0.0
    )
    return pd.DataFrame(
        {
            "timestamp": equity.index,
            "equity": equity.values,
            "drawdown": drawdown.values,
        },
    )


def to_trades_df(results: BacktestResults) -> pd.DataFrame:
    """Return canonical trade log DataFrame."""
    trades = results.get_trade_log_df().copy()
    if trades.empty:
        return pd.DataFrame(
            columns=["timestamp", "symbol", "type", "price", "quantity", "pnl"]
        )
    if "timestamp" not in trades.columns and trades.index.name is not None:
        trades = trades.reset_index().rename(columns={trades.index.name: "timestamp"})
    expected = ["timestamp", "symbol", "type", "price", "quantity", "pnl"]
    for col in expected:
        if col not in trades.columns:
            trades[col] = None
    return trades[expected]


def to_summary_metrics(results: BacktestResults) -> dict[str, float]:
    """Return canonical summary metrics."""
    metrics = results.get_metrics()
    equity = results.get_equity_curve(initial_capital=results.config.initial_capital)
    cumulative_return = 0.0
    if len(equity) > 1 and float(equity.iloc[0]) != 0.0:
        cumulative_return = float(equity.iloc[-1] / equity.iloc[0] - 1.0)

    return {
        "total_return": float(metrics.get("total_return", 0.0)),
        "cumulative_return": cumulative_return,
        "max_drawdown": float(metrics.get("max_drawdown", 0.0)),
        "sharpe_ratio": float(metrics.get("sharpe_ratio", 0.0)),
        "num_trades": float(metrics.get("num_trades", 0.0)),
        "win_rate": float(metrics.get("win_rate", 0.0)),
    }


def build_backtest_report(results: BacktestResults) -> dict[str, Any]:
    """Build canonical report payload for UI/API consumption."""
    equity_df = to_equity_df(results)
    trades_df = to_trades_df(results)
    report = {
        "strategy_name": results.strategy_name,
        "generated_at": datetime.utcnow().isoformat(),
        "summary": to_summary_metrics(results),
        "equity_curve": [
            {
                "timestamp": _to_iso(row["timestamp"]),
                "equity": float(row["equity"]),
                "drawdown": float(row.get("drawdown", 0.0)),
            }
            for _, row in equity_df.iterrows()
        ],
        "trade_log": [
            {
                "timestamp": _to_iso(row["timestamp"]),
                "symbol": row["symbol"],
                "type": row["type"],
                "price": _safe_float(row["price"]),
                "quantity": _safe_float(row["quantity"]),
                "pnl": _safe_float(row["pnl"]),
            }
            for _, row in trades_df.iterrows()
        ],
    }
    return report


def _to_iso(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _safe_float(value: Any) -> float:
    try:
        if pd.isna(value):
            return 0.0
    except Exception:
        pass
    return float(value)
