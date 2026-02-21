"""Portfolio service layer."""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional

from sqlalchemy import desc
from sqlalchemy.orm import Session

from backend.db.models import PortfolioDB, PortfolioHistoryDB, PositionDB, TradeDB
from backend.models.portfolio import (
    Portfolio,
    PortfolioCreate,
    PortfolioHistory,
    PortfolioMetrics,
    Position,
    Trade,
)


def create_portfolio(db: Session, portfolio: PortfolioCreate) -> Portfolio:
    """Create a new portfolio."""
    db_portfolio = PortfolioDB(
        name=portfolio.name,
        description=portfolio.description,
        initial_capital=portfolio.initial_capital,
        current_value=portfolio.initial_capital,
        cash_balance=portfolio.initial_capital,
        currency=portfolio.currency,
    )
    db.add(db_portfolio)
    db.commit()
    db.refresh(db_portfolio)
    return Portfolio.model_validate(db_portfolio)


def get_portfolios(db: Session, skip: int = 0, limit: int = 100) -> list[Portfolio]:
    """Get all portfolios."""
    portfolios = db.query(PortfolioDB).offset(skip).limit(limit).all()
    return [Portfolio.model_validate(p) for p in portfolios]


def get_portfolio(db: Session, portfolio_id: int) -> Optional[Portfolio]:
    """Get portfolio by ID."""
    portfolio = db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
    return Portfolio.model_validate(portfolio) if portfolio else None


def get_positions(db: Session, portfolio_id: int) -> list[Position]:
    """Get all positions for a portfolio."""
    positions = (
        db.query(PositionDB).filter(PositionDB.portfolio_id == portfolio_id).all()
    )
    return [Position.model_validate(p) for p in positions]


def get_trades(
    db: Session,
    portfolio_id: int,
    skip: int = 0,
    limit: int = 100,
) -> list[Trade]:
    """Get trade history for a portfolio."""
    trades = (
        db.query(TradeDB)
        .filter(TradeDB.portfolio_id == portfolio_id)
        .order_by(desc(TradeDB.executed_at))
        .offset(skip)
        .limit(limit)
        .all()
    )
    return [Trade.model_validate(t) for t in trades]


def calculate_metrics(db: Session, portfolio_id: int) -> PortfolioMetrics:
    """Calculate performance metrics for a portfolio."""
    portfolio = db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
    if not portfolio:
        raise ValueError(f"Portfolio {portfolio_id} not found")

    positions = (
        db.query(PositionDB).filter(PositionDB.portfolio_id == portfolio_id).all()
    )
    trades = db.query(TradeDB).filter(TradeDB.portfolio_id == portfolio_id).all()

    # Calculate basic metrics
    positions_value = sum(
        (p.current_price or p.entry_price) * p.quantity for p in positions
    )
    total_value = portfolio.cash_balance + positions_value
    total_pnl = total_value - portfolio.initial_capital
    total_pnl_pct = (
        (total_pnl / portfolio.initial_capital) * 100
        if portfolio.initial_capital > 0
        else Decimal(0)
    )

    # Get yesterday's value for daily P&L
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_history = (
        db.query(PortfolioHistoryDB)
        .filter(
            PortfolioHistoryDB.portfolio_id == portfolio_id,
            PortfolioHistoryDB.date >= yesterday,
        )
        .order_by(desc(PortfolioHistoryDB.date))
        .first()
    )

    if yesterday_history:
        daily_pnl = total_value - yesterday_history.total_value
        daily_pnl_pct = (
            (daily_pnl / yesterday_history.total_value) * 100
            if yesterday_history.total_value > 0
            else Decimal(0)
        )
    else:
        daily_pnl = Decimal(0)
        daily_pnl_pct = Decimal(0)

    # Calculate max drawdown from history
    history = (
        db.query(PortfolioHistoryDB)
        .filter(PortfolioHistoryDB.portfolio_id == portfolio_id)
        .all()
    )
    if history:
        peak = max(h.total_value for h in history)
        current_dd = peak - total_value
        max_drawdown = current_dd
        max_drawdown_pct = (max_drawdown / peak) * 100 if peak > 0 else Decimal(0)
    else:
        max_drawdown = Decimal(0)
        max_drawdown_pct = Decimal(0)

    # Trade statistics
    num_trades = len(trades)
    winning_trades = [t for t in trades if t.realized_pnl and t.realized_pnl > 0]
    losing_trades = [t for t in trades if t.realized_pnl and t.realized_pnl < 0]
    win_rate = (
        (len(winning_trades) / num_trades * 100) if num_trades > 0 else Decimal(0)
    )

    return PortfolioMetrics(
        total_value=total_value,
        cash_balance=portfolio.cash_balance,
        positions_value=positions_value,
        total_pnl=total_pnl,
        total_pnl_pct=total_pnl_pct,
        daily_pnl=daily_pnl,
        daily_pnl_pct=daily_pnl_pct,
        max_drawdown=max_drawdown,
        max_drawdown_pct=max_drawdown_pct,
        sharpe_ratio=None,  # TODO: Implement Sharpe calculation
        win_rate=win_rate,
        num_trades=num_trades,
        num_winning_trades=len(winning_trades),
        num_losing_trades=len(losing_trades),
    )


def get_history(
    db: Session,
    portfolio_id: int,
    days: int = 30,
) -> list[PortfolioHistory]:
    """Get historical values for a portfolio."""
    cutoff_date = datetime.now() - timedelta(days=days)
    history = (
        db.query(PortfolioHistoryDB)
        .filter(
            PortfolioHistoryDB.portfolio_id == portfolio_id,
            PortfolioHistoryDB.date >= cutoff_date,
        )
        .order_by(PortfolioHistoryDB.date)
        .all()
    )
    return [PortfolioHistory.model_validate(h) for h in history]


def delete_portfolio(db: Session, portfolio_id: int) -> bool:
    """Delete a portfolio."""
    portfolio = db.query(PortfolioDB).filter(PortfolioDB.id == portfolio_id).first()
    if not portfolio:
        return False

    db.delete(portfolio)
    db.commit()
    return True


class PortfolioService:
    """Convenience object wrapper around portfolio functions for DI/testing."""

    def __init__(self, db: Optional[Session] = None):
        self.db = db

    def create_portfolio(self, portfolio: PortfolioCreate) -> Portfolio:
        if self.db is None:
            raise RuntimeError("Database session not set on PortfolioService")
        return create_portfolio(self.db, portfolio)

    def get_portfolios(self, skip: int = 0, limit: int = 100) -> list[Portfolio]:
        if self.db is None:
            raise RuntimeError("Database session not set on PortfolioService")
        return get_portfolios(self.db, skip, limit)

    def get_portfolio(self, portfolio_id: int) -> Optional[Portfolio]:
        if self.db is None:
            raise RuntimeError("Database session not set on PortfolioService")
        return get_portfolio(self.db, portfolio_id)

    def get_positions(self, portfolio_id: int) -> list[Position]:
        if self.db is None:
            raise RuntimeError("Database session not set on PortfolioService")
        return get_positions(self.db, portfolio_id)

    def get_trades(
        self,
        portfolio_id: int,
        skip: int = 0,
        limit: int = 100,
    ) -> list[Trade]:
        if self.db is None:
            raise RuntimeError("Database session not set on PortfolioService")
        return get_trades(self.db, portfolio_id, skip, limit)

    def calculate_metrics(self, portfolio_id: int) -> PortfolioMetrics:
        if self.db is None:
            raise RuntimeError("Database session not set on PortfolioService")
        return calculate_metrics(self.db, portfolio_id)

    def get_history(self, portfolio_id: int, days: int = 30) -> list[PortfolioHistory]:
        if self.db is None:
            raise RuntimeError("Database session not set on PortfolioService")
        return get_history(self.db, portfolio_id, days)

    def delete_portfolio(self, portfolio_id: int) -> bool:
        if self.db is None:
            raise RuntimeError("Database session not set on PortfolioService")
        return delete_portfolio(self.db, portfolio_id)
