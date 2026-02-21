"""Database models for the Trade Journal."""

from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.sql import func

from backend.db.models import Base


class TradeNote(Base):
    __tablename__ = "portfolio_trade_notes"

    id = Column(Integer, primary_key=True, index=True)
    trade_id = Column(String(36), index=True, nullable=False)
    timestamp = Column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    note_text = Column(String, nullable=False)
    tags = Column(JSON, nullable=True)  # List of tags
