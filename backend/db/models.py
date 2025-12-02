"""Database models using SQLAlchemy."""
from datetime import datetime
from decimal import Decimal

from sqlalchemy import Column, Integer, String, Numeric, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from models.portfolio import PositionSide, OrderType, TradeStatus

Base = declarative_base()


class PortfolioDB(Base):
    """Portfolio database model."""
    __tablename__ = "portfolios"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False, index=True)
    description = Column(String, nullable=True)
    initial_capital = Column(Numeric(precision=15, scale=2), nullable=False)
    current_value = Column(Numeric(precision=15, scale=2), nullable=False)
    cash_balance = Column(Numeric(precision=15, scale=2), nullable=False)
    currency = Column(String, default="USD")
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    positions = relationship("PositionDB", back_populates="portfolio", cascade="all, delete-orphan")
    trades = relationship("TradeDB", back_populates="portfolio", cascade="all, delete-orphan")
    history = relationship("PortfolioHistoryDB", back_populates="portfolio", cascade="all, delete-orphan")


class PositionDB(Base):
    """Position database model."""
    __tablename__ = "positions"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    quantity = Column(Numeric(precision=15, scale=4), nullable=False)
    side = Column(SQLEnum(PositionSide), nullable=False)
    entry_price = Column(Numeric(precision=15, scale=4), nullable=False)
    current_price = Column(Numeric(precision=15, scale=4), nullable=True)
    unrealized_pnl = Column(Numeric(precision=15, scale=2), nullable=True)
    unrealized_pnl_pct = Column(Numeric(precision=10, scale=4), nullable=True)
    opened_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # Relationships
    portfolio = relationship("PortfolioDB", back_populates="positions")


class TradeDB(Base):
    """Trade database model."""
    __tablename__ = "trades"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    strategy_id = Column(Integer, nullable=True)
    symbol = Column(String, nullable=False, index=True)
    quantity = Column(Numeric(precision=15, scale=4), nullable=False)
    price = Column(Numeric(precision=15, scale=4), nullable=False)
    side = Column(SQLEnum(PositionSide), nullable=False)
    order_type = Column(SQLEnum(OrderType), default=OrderType.MARKET)
    commission = Column(Numeric(precision=10, scale=2), default=0)
    status = Column(SQLEnum(TradeStatus), default=TradeStatus.OPEN)
    realized_pnl = Column(Numeric(precision=15, scale=2), nullable=True)
    executed_at = Column(DateTime(timezone=True), server_default=func.now())
    closed_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    portfolio = relationship("PortfolioDB", back_populates="trades")


class PortfolioHistoryDB(Base):
    """Portfolio history database model."""
    __tablename__ = "portfolio_history"
    
    id = Column(Integer, primary_key=True, index=True)
    portfolio_id = Column(Integer, ForeignKey("portfolios.id"), nullable=False)
    date = Column(DateTime(timezone=True), nullable=False, index=True)
    total_value = Column(Numeric(precision=15, scale=2), nullable=False)
    cash_balance = Column(Numeric(precision=15, scale=2), nullable=False)
    positions_value = Column(Numeric(precision=15, scale=2), nullable=False)
    daily_pnl = Column(Numeric(precision=15, scale=2), nullable=False)
    cumulative_pnl = Column(Numeric(precision=15, scale=2), nullable=False)
    
    # Relationships
    portfolio = relationship("PortfolioDB", back_populates="history")
