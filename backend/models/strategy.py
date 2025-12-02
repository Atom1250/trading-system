"""Strategy models for API."""
from datetime import datetime
from typing import Optional, Dict, Any, List
from decimal import Decimal
from pydantic import BaseModel, Field


class StrategyConfig(BaseModel):
    """Strategy configuration."""
    name: str = Field(..., description="Strategy name")
    module: str = Field(..., description="Python module path")
    class_name: str = Field(..., description="Strategy class name")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Strategy parameters")


class BacktestRequest(BaseModel):
    """Backtest request."""
    symbol: str = Field(..., description="Stock symbol")
    strategy_name: str = Field(..., description="Strategy name")
    parameters: Optional[Dict[str, Any]] = Field(None, description="Strategy parameters override")
    start_date: Optional[datetime] = Field(None, description="Backtest start date")
    end_date: Optional[datetime] = Field(None, description="Backtest end date")
    initial_capital: Decimal = Field(Decimal("100000"), description="Initial capital")
    data_source: Optional[str] = Field("local", description="Data source")


class BacktestMetrics(BaseModel):
    """Backtest performance metrics."""
    total_return: Decimal = Field(..., description="Total return")
    total_return_pct: Decimal = Field(..., description="Total return %")
    sharpe_ratio: Optional[Decimal] = Field(None, description="Sharpe ratio")
    max_drawdown: Decimal = Field(..., description="Maximum drawdown")
    max_drawdown_pct: Decimal = Field(..., description="Maximum drawdown %")
    win_rate: Optional[Decimal] = Field(None, description="Win rate %")
    num_trades: int = Field(..., description="Number of trades")
    avg_trade: Optional[Decimal] = Field(None, description="Average trade P&L")


class BacktestResult(BaseModel):
    """Backtest result."""
    symbol: str
    strategy_name: str
    metrics: BacktestMetrics
    equity_curve: List[Dict[str, Any]] = Field(default_factory=list)
    trades: List[Dict[str, Any]] = Field(default_factory=list)
    parameters: Dict[str, Any] = Field(default_factory=dict)
    executed_at: datetime = Field(default_factory=datetime.now)


class StrategyInfo(BaseModel):
    """Strategy information."""
    name: str
    description: str
    parameters: Dict[str, Any]
    available: bool = True
