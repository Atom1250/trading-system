"""Data schemas for portfolio accounting Engine outputs."""

from datetime import datetime
from typing import Dict, List

from pydantic import BaseModel, ConfigDict


class PositionSnapshot(BaseModel):
    """Snapshot of a single position at a point in time."""

    symbol: str
    quantity: float
    avg_cost: float
    market_price: float
    unrealized_pnl: float


class PortfolioSnapshot(BaseModel):
    """Snapshot of the whole portfolio at a point in time."""

    timestamp: datetime
    cash: float
    equity: float
    realized_pnl: float
    unrealized_pnl: float
    positions: Dict[str, PositionSnapshot]

    model_config = ConfigDict(from_attributes=True)


class PortfolioTimeline(BaseModel):
    """Complete history of reconstructed portfolio state."""

    snapshots: List[PortfolioSnapshot]
    final_state: PortfolioSnapshot
