"""Schemas for Strategy Lab backtest run/fetch endpoints."""

from __future__ import annotations

from datetime import date
from typing import Any

from pydantic import BaseModel, Field


class BacktestRunRequest(BaseModel):
    strategy_name: str
    symbol: str
    start_date: date
    end_date: date
    initial_capital: float = 100000.0
    parameters: dict[str, Any] = Field(default_factory=dict)


class BacktestSummaryMetrics(BaseModel):
    total_return: float
    cumulative_return: float
    max_drawdown: float
    sharpe_ratio: float
    num_trades: float
    win_rate: float


class BacktestRunResponse(BaseModel):
    run_id: str
    strategy_name: str
    symbol: str
    config_hash: str
    summary: BacktestSummaryMetrics


class BacktestSummaryResponse(BaseModel):
    run_id: str
    strategy_name: str
    config_hash: str
    created_at: str
    summary: BacktestSummaryMetrics


class BacktestTradeRow(BaseModel):
    timestamp: str
    symbol: str
    type: str
    price: float
    quantity: float
    pnl: float


class BacktestTradesResponse(BaseModel):
    run_id: str
    trades: list[BacktestTradeRow]


class BacktestEquityRow(BaseModel):
    timestamp: str
    equity: float
    drawdown: float


class BacktestEquityResponse(BaseModel):
    run_id: str
    equity: list[BacktestEquityRow]
