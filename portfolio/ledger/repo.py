"""Repository for the ledger subsystem."""

import uuid
from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from .models import Trade
from .schemas import TradeEvent


def append_trade(db: Session, event: TradeEvent) -> Trade:
    """Appends a new trade event into the ledger. Updates are not allowed."""
    trade_data = event.model_dump(exclude_unset=True)
    if not trade_data.get("trade_id"):
        trade_data["trade_id"] = str(uuid.uuid4())

    db_trade = Trade(**trade_data)
    db.add(db_trade)
    db.commit()
    db.refresh(db_trade)
    return db_trade


def list_trades(
    db: Session,
    run_id: Optional[str] = None,
    strategy_id: Optional[str] = None,
    symbol: Optional[str] = None,
    start_time: Optional[datetime] = None,
    end_time: Optional[datetime] = None,
) -> List[Trade]:
    """Retrieves trade events from the ledger."""
    query = db.query(Trade)
    if run_id:
        query = query.filter(Trade.run_id == run_id)
    if strategy_id:
        query = query.filter(Trade.strategy_id == strategy_id)
    if symbol:
        query = query.filter(Trade.symbol == symbol)
    if start_time:
        query = query.filter(Trade.timestamp >= start_time)
    if end_time:
        query = query.filter(Trade.timestamp <= end_time)

    return query.order_by(Trade.timestamp.asc(), Trade.trade_id.asc()).all()
