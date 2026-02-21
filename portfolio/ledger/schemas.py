"""Pydantic schemas for the ledger subsystem."""

from datetime import datetime
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict


class TradeEvent(BaseModel):
    """Pydantic schema representing a single trade event/fill."""

    trade_id: Optional[str] = None
    timestamp: datetime
    symbol: str
    side: str
    quantity: float
    price: float
    commission: float = 0.0
    slippage: float = 0.0
    order_id: Optional[str] = None
    strategy_id: Optional[str] = None
    run_id: Optional[str] = None
    execution_venue: str
    meta_data: Optional[Dict[str, Any]] = None

    model_config = ConfigDict(from_attributes=True)
