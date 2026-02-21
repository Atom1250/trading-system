"""Pydantic schemas for Trade Journaling."""

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict


class TradeNoteCreate(BaseModel):
    trade_id: str
    note_text: str
    tags: Optional[List[str]] = None


class TradeNoteEvent(TradeNoteCreate):
    id: int
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)
