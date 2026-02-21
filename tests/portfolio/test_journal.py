import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.models import Base
from portfolio.journal.repo import add_note, get_notes_for_trade
from portfolio.journal.schemas import TradeNoteCreate


@pytest.fixture
def journal_db():
    engine = create_engine(
        "sqlite:///:memory:", connect_args={"check_same_thread": False}
    )
    Base.metadata.create_all(bind=engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    yield db
    db.close()


def test_add_and_get_trade_notes(journal_db):
    note1 = TradeNoteCreate(trade_id="t1", note_text="Bad entry", tags=["mistake"])
    note2 = TradeNoteCreate(
        trade_id="t1", note_text="Closed early", tags=["psychology"]
    )
    note3 = TradeNoteCreate(trade_id="t2", note_text="Perfect setup", tags=["A+"])

    add_note(journal_db, note1)
    add_note(journal_db, note2)
    add_note(journal_db, note3)

    notes_t1 = get_notes_for_trade(journal_db, "t1")
    assert len(notes_t1) == 2
    # newest first? repo orders by timestamp.desc()
    # they were generated sequentially in sqlite but times could be identical
    # so assert sets
    texts = {n.note_text for n in notes_t1}
    assert texts == {"Bad entry", "Closed early"}

    notes_t2 = get_notes_for_trade(journal_db, "t2")
    assert len(notes_t2) == 1
    assert notes_t2[0].tags == ["A+"]


def test_empty_notes_for_unknown_trade(journal_db):
    assert get_notes_for_trade(journal_db, "nonexistent") == []
