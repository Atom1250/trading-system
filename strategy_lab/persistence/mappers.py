"""Mappers from Strategy Lab domain objects to persistence records."""

from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, is_dataclass
from enum import Enum
from typing import Any

from strategy_lab.backtest.results import BacktestResults


def config_to_canonical_dict(config: Any) -> dict[str, Any]:
    """Convert config dataclass/object to canonical JSON-serializable dict."""
    if is_dataclass(config):
        payload = asdict(config)
    elif isinstance(config, dict):
        payload = dict(config)
    else:
        payload = vars(config)
    return _normalize(payload)


def compute_config_hash(config: Any) -> str:
    """Compute stable SHA256 hash for backtest configuration."""
    canonical = config_to_canonical_dict(config)
    raw = json.dumps(canonical, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def map_run_row(run_id: str, results: BacktestResults) -> dict[str, Any]:
    """Map BacktestResults metadata to backtest_runs row."""
    config_dict = config_to_canonical_dict(results.config)
    return {
        "run_id": run_id,
        "strategy_name": results.strategy_name,
        "config_hash": compute_config_hash(results.config),
        "config_json": json.dumps(config_dict, sort_keys=True),
    }


def map_trade_rows(run_id: str, results: BacktestResults) -> list[dict[str, Any]]:
    """Map trade log DataFrame into normalized trade rows."""
    trades = results.get_trade_log_df()
    if trades.empty:
        return []
    mapped: list[dict[str, Any]] = []
    for _, row in trades.iterrows():
        mapped.append(
            {
                "run_id": run_id,
                "timestamp": _to_iso(row.get("timestamp")),
                "symbol": str(row.get("symbol", "")),
                "type": str(row.get("type", "")),
                "price": _to_float(row.get("price", 0.0)),
                "quantity": _to_float(row.get("quantity", 0.0)),
                "pnl": _to_float(row.get("pnl", 0.0)),
            },
        )
    return mapped


def map_equity_rows(run_id: str, results: BacktestResults) -> list[dict[str, Any]]:
    """Map equity curve into normalized history rows."""
    equity = results.get_equity_curve(initial_capital=results.config.initial_capital)
    history = results.portfolio_history
    drawdown_lookup = {}
    if history is not None and not history.empty and "drawdown" in history.columns:
        drawdown_lookup = {k: float(v) for k, v in history["drawdown"].items()}

    mapped: list[dict[str, Any]] = []
    for timestamp, equity_value in equity.items():
        mapped.append(
            {
                "run_id": run_id,
                "timestamp": _to_iso(timestamp),
                "equity": _to_float(equity_value),
                "drawdown": float(drawdown_lookup.get(timestamp, 0.0)),
            },
        )
    return mapped


def _normalize(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return _normalize(asdict(value))
    if isinstance(value, dict):
        return {str(k): _normalize(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_normalize(v) for v in value]
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return value


def _to_iso(value: Any) -> str:
    if hasattr(value, "isoformat"):
        return value.isoformat()
    return str(value)


def _to_float(value: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0
