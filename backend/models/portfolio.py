"""Core data models for the trading system."""
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field, ConfigDict


class PositionSide(str, Enum):
    """Position side enum."""
    LONG = "long"
    SHORT = "short"


class OrderType(str, Enum):
    """Order type enum."""
    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"
    STOP_LIMIT = "stop_limit"


class TradeStatus(str, Enum):
    """Trade status enum."""
    OPEN = "open"
    CLOSED = "closed"
    CANCELLED = "cancelled"


# Portfolio Models
class PortfolioBase(BaseModel):
    """Base portfolio model."""
    name: str = Field(..., description="Portfolio name")
    description: Optional[str] = Field(None, description="Portfolio description")
    initial_capital: Decimal = Field(..., description="Initial capital")
    currency: str = Field(default="USD", description="Portfolio currency")


class PortfolioCreate(PortfolioBase):
    """Portfolio creation model."""
    pass


class Portfolio(PortfolioBase):
    """Portfolio model with ID and timestamps."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    current_value: Decimal = Field(..., description="Current portfolio value")
    cash_balance: Decimal = Field(..., description="Available cash")
    created_at: datetime
    updated_at: datetime


# Position Models
class PositionBase(BaseModel):
    """Base position model."""
    symbol: str = Field(..., description="Stock symbol")
    quantity: Decimal = Field(..., description="Number of shares")
    side: PositionSide = Field(..., description="Long or short")
    entry_price: Decimal = Field(..., description="Average entry price")


class PositionCreate(PositionBase):
    """Position creation model."""
    portfolio_id: int


class Position(PositionBase):
    """Position model with ID and metrics."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    portfolio_id: int
    current_price: Optional[Decimal] = Field(None, description="Current market price")
    unrealized_pnl: Optional[Decimal] = Field(None, description="Unrealized P&L")
    unrealized_pnl_pct: Optional[Decimal] = Field(None, description="Unrealized P&L %")
    opened_at: datetime
    updated_at: datetime


# Trade Models
class TradeBase(BaseModel):
    """Base trade model."""
    symbol: str = Field(..., description="Stock symbol")
    quantity: Decimal = Field(..., description="Number of shares")
    price: Decimal = Field(..., description="Execution price")
    side: PositionSide = Field(..., description="Buy or sell")
    order_type: OrderType = Field(default=OrderType.MARKET, description="Order type")
    commission: Decimal = Field(default=Decimal("0"), description="Commission paid")


class TradeCreate(TradeBase):
    """Trade creation model."""
    portfolio_id: int
    strategy_id: Optional[int] = Field(None, description="Strategy that generated trade")


class Trade(TradeBase):
    """Trade model with ID and status."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    portfolio_id: int
    strategy_id: Optional[int]
    status: TradeStatus = Field(default=TradeStatus.OPEN)
    realized_pnl: Optional[Decimal] = Field(None, description="Realized P&L")
    executed_at: datetime
    closed_at: Optional[datetime] = None


# Performance Metrics Models
class PortfolioMetrics(BaseModel):
    """Portfolio performance metrics."""
    total_value: Decimal
    cash_balance: Decimal
    positions_value: Decimal
    total_pnl: Decimal
    total_pnl_pct: Decimal
    daily_pnl: Decimal
    daily_pnl_pct: Decimal
    max_drawdown: Decimal
    max_drawdown_pct: Decimal
    sharpe_ratio: Optional[Decimal] = None
    win_rate: Optional[Decimal] = None
    num_trades: int
    num_winning_trades: int
    num_losing_trades: int


class PortfolioHistory(BaseModel):
    """Portfolio value history point."""
    date: datetime
    total_value: Decimal
    cash_balance: Decimal
    positions_value: Decimal
    daily_pnl: Decimal
    cumulative_pnl: Decimal
