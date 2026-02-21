from datetime import date
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class BacktestRequest(BaseModel):
    """Request schema for running a backtest."""

    strategy_name: str
    symbol: str  # For now single symbol, can extend to universe list
    start_date: date
    end_date: date
    initial_capital: float = 10000.0
    parameters: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_name": "MovingAverageCrossover",
                "symbol": "AAPL",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_capital": 100000.0,
                "parameters": {"short_window": 50, "long_window": 200},
            }
        }


class EquityPoint(BaseModel):
    timestamp: str  # ISO format date
    equity: float
    drawdown: float


class TradeRecord(BaseModel):
    timestamp: str
    symbol: str
    type: str
    price: float
    quantity: float
    pnl: float


class BacktestMetrics(BaseModel):
    total_return: float
    cagr: float
    sharpe_ratio: float
    max_drawdown: float
    win_rate: float
    total_trades: int


class BacktestResponse(BaseModel):
    """Response schema for backtest results."""

    strategy_name: str
    symbol: str
    metrics: BacktestMetrics
    equity_curve: List[EquityPoint]
    trades: List[TradeRecord]
    execution_chart: Optional[str] = None  # Base64 encoded chart image
