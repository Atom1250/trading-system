"""Repository for Trade Journal access."""

from typing import List

from sqlalchemy.orm import Session

from .models import TradeNote
from .schemas import TradeNoteCreate


def add_note(db: Session, note: TradeNoteCreate) -> TradeNote:
    """Adds a new text note to a trade."""
    db_note = TradeNote(
        trade_id=note.trade_id, note_text=note.note_text, tags=note.tags or []
    )
    db.add(db_note)
    db.commit()
    db.refresh(db_note)
    return db_note


def get_notes_for_trade(db: Session, trade_id: str) -> List[TradeNote]:
    """Retrieves all notes associated with a specific trade_id."""
    return (
        db.query(TradeNote)
        .filter(TradeNote.trade_id == trade_id)
        .order_by(TradeNote.timestamp.desc())
        .all()
    )
