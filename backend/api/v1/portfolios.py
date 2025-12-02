"""Portfolio API endpoints."""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from db.database import get_db
from models.portfolio import (
    Portfolio, PortfolioCreate, PortfolioMetrics, PortfolioHistory,
    Position, Trade
)
from services import portfolio_service

router = APIRouter()


@router.post("/", response_model=Portfolio, status_code=status.HTTP_201_CREATED)
async def create_portfolio(
    portfolio: PortfolioCreate,
    db: Session = Depends(get_db)
):
    """Create a new portfolio."""
    return portfolio_service.create_portfolio(db, portfolio)


@router.get("/", response_model=List[Portfolio])
async def list_portfolios(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """List all portfolios."""
    return portfolio_service.get_portfolios(db, skip=skip, limit=limit)


@router.get("/{portfolio_id}", response_model=Portfolio)
async def get_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """Get portfolio by ID."""
    portfolio = portfolio_service.get_portfolio(db, portfolio_id)
    if not portfolio:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    return portfolio


@router.get("/{portfolio_id}/positions", response_model=List[Position])
async def get_portfolio_positions(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """Get all positions for a portfolio."""
    return portfolio_service.get_positions(db, portfolio_id)


@router.get("/{portfolio_id}/trades", response_model=List[Trade])
async def get_portfolio_trades(
    portfolio_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """Get trade history for a portfolio."""
    return portfolio_service.get_trades(db, portfolio_id, skip=skip, limit=limit)


@router.get("/{portfolio_id}/metrics", response_model=PortfolioMetrics)
async def get_portfolio_metrics(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """Get performance metrics for a portfolio."""
    return portfolio_service.calculate_metrics(db, portfolio_id)


@router.get("/{portfolio_id}/history", response_model=List[PortfolioHistory])
async def get_portfolio_history(
    portfolio_id: int,
    days: int = 30,
    db: Session = Depends(get_db)
):
    """Get historical values for a portfolio."""
    return portfolio_service.get_history(db, portfolio_id, days=days)


@router.delete("/{portfolio_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_portfolio(
    portfolio_id: int,
    db: Session = Depends(get_db)
):
    """Delete a portfolio."""
    success = portfolio_service.delete_portfolio(db, portfolio_id)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Portfolio {portfolio_id} not found"
        )
    return None
