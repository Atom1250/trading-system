"""Portfolio metric calculation schemas."""

from datetime import datetime
from typing import Dict

from pydantic import BaseModel


class PerformanceMetrics(BaseModel):
    total_return: float
    max_drawdown: float
    sharpe_ratio: float
    win_rate: float
    total_trades_count: int
    winning_trades_count: int
    losing_trades_count: int


class ExposureMetrics(BaseModel):
    timestamp: datetime
    gross_exposure: float
    net_exposure: float
    long_exposure: float
    short_exposure: float
    concentration: Dict[str, float]  # Symbol to weight of gross exposure


class StrategyMetrics(BaseModel):
    strategy_id: str
    realized_pnl: float
    unrealized_pnl: float
    total_pnl: float
