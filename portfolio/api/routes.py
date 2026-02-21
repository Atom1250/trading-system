"""FastAPI endpoints for the Portfolio subsystem."""

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from backend.db.database import get_db
from portfolio.accounting.engine import rebuild_portfolio
from portfolio.accounting.schemas import PortfolioSnapshot
from portfolio.journal.repo import add_note, get_notes_for_trade
from portfolio.journal.schemas import TradeNoteCreate, TradeNoteEvent
from portfolio.ledger.repo import list_trades
from portfolio.ledger.schemas import TradeEvent
from portfolio.metrics.aggregation import aggregate_strategy_metrics
from portfolio.metrics.performance import calculate_performance_metrics
from portfolio.metrics.schemas import PerformanceMetrics, StrategyMetrics

router = APIRouter()


def get_timeline(run_id: str, db: Session):
    trades = list_trades(db, run_id=run_id)
    if not trades:
        raise HTTPException(status_code=404, detail="Run ID not found or has no trades")
    return rebuild_portfolio(trades, price_marks={}, initial_cash=100000.0)


@router.get("/state", response_model=PortfolioSnapshot)
def get_portfolio_state(run_id: str = Query(...), db: Session = Depends(get_db)):
    timeline = get_timeline(run_id, db)
    return timeline.final_state


@router.get("/trades", response_model=List[TradeEvent])
def get_portfolio_trades(run_id: str = Query(...), db: Session = Depends(get_db)):
    trades = list_trades(db, run_id=run_id)
    if not trades:
        raise HTTPException(status_code=404, detail="Run ID not found or has no trades")
    return trades


@router.get("/equity", response_model=List[dict])
def get_portfolio_equity(run_id: str = Query(...), db: Session = Depends(get_db)):
    timeline = get_timeline(run_id, db)
    return [
        {"timestamp": s.timestamp, "equity": s.equity, "cash": s.cash}
        for s in timeline.snapshots
    ]


@router.get("/metrics", response_model=PerformanceMetrics)
def get_portfolio_metrics(run_id: str = Query(...), db: Session = Depends(get_db)):
    timeline = get_timeline(run_id, db)
    return calculate_performance_metrics(timeline)


@router.get("/positions", response_model=dict)
def get_portfolio_positions(run_id: str = Query(...), db: Session = Depends(get_db)):
    timeline = get_timeline(run_id, db)
    return timeline.final_state.positions


@router.get("/allocations", response_model=List[StrategyMetrics])
def get_portfolio_allocations(run_id: str = Query(...), db: Session = Depends(get_db)):
    trades = list_trades(db, run_id=run_id)
    if not trades:
        raise HTTPException(status_code=404, detail="Run ID not found or has no trades")
    return aggregate_strategy_metrics(trades)


@router.post("/journal", response_model=TradeNoteEvent)
def create_trade_note(note: TradeNoteCreate, db: Session = Depends(get_db)):
    """Add a new journal entry to a trade."""
    return add_note(db, note)


@router.get("/journal/{trade_id}", response_model=List[TradeNoteEvent])
def get_trade_notes(trade_id: str, db: Session = Depends(get_db)):
    """Fetch all journal entries for a given trade."""
    return get_notes_for_trade(db, trade_id)
