"""Ledger data models using SQLAlchemy."""

import uuid

from sqlalchemy import JSON, Column, DateTime, Float, String
from sqlalchemy.sql import func

from backend.db.models import Base


class Trade(Base):
    """Immutable record of a trade fill."""

    __tablename__ = "portfolio_trades"

    trade_id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    timestamp = Column(DateTime(timezone=True), nullable=False)
    symbol = Column(String, nullable=False, index=True)
    side = Column(String, nullable=False)  # "BUY" or "SELL"
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    commission = Column(Float, default=0.0)
    slippage = Column(Float, default=0.0)
    order_id = Column(String, nullable=True)
    strategy_id = Column(String, nullable=True, index=True)
    run_id = Column(String, nullable=True, index=True)
    execution_venue = Column(String, nullable=False)  # "BACKTEST", "PAPER", "LIVE"
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    meta_data = Column(JSON, nullable=True)
