"""Integration API endpoints."""


from db.database import get_db
from fastapi import APIRouter, Depends, HTTPException, Query, Response
from services.integration.export_service import export_service
from services.integration.google_sheets_service import google_sheets_service
from sqlalchemy.orm import Session
from typing import Optional

from services import portfolio_service

router = APIRouter()


@router.post("/google_sheets/export/{portfolio_id}")
async def export_to_google_sheets(
    portfolio_id: int,
    spreadsheet_name: Optional[str] = Query(
        None, description="Name of the spreadsheet",
    ),
    db: Session = Depends(get_db),
):
    """Export portfolio to Google Sheets."""
    try:
        # Get portfolio data
        portfolio = portfolio_service.get_portfolio(db, portfolio_id)

        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Convert to dict for export (simplified)
        # In a real app, we'd have a proper serializer
        # Get positions and trades explicitly
        positions = portfolio_service.get_positions(db, portfolio_id)
        trades = portfolio_service.get_trades(db, portfolio_id)

        portfolio_data = {
            "name": portfolio.name,
            "cash": float(portfolio.cash_balance),
            "total_value": float(portfolio.current_value),
            "positions": [
                {
                    "symbol": p.symbol,
                    "quantity": float(p.quantity),
                    "cost_basis": float(p.entry_price * p.quantity),
                    "current_price": float(p.current_price) if p.current_price else 0,
                    "market_value": float(p.current_price * p.quantity)
                    if p.current_price
                    else 0,
                    "unrealized_pnl": float(p.unrealized_pnl)
                    if p.unrealized_pnl
                    else 0,
                }
                for p in positions
            ],
            "trades": [
                {
                    "symbol": t.symbol,
                    "type": t.side,
                    "quantity": float(t.quantity),
                    "price": float(t.price),
                    "timestamp": t.executed_at.isoformat(),
                }
                for t in trades
            ],
        }

        if not spreadsheet_name:
            spreadsheet_name = f"Portfolio Export - {portfolio.name}"

        result = google_sheets_service.export_portfolio(
            portfolio_data, spreadsheet_name,
        )
        return result

    except RuntimeError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e!s}")


@router.get("/export/{portfolio_id}")
async def export_file(
    portfolio_id: int,
    format: str = Query("csv", regex="^(csv|excel|xlsx)$"),
    db: Session = Depends(get_db),
):
    """Export portfolio to CSV or Excel file."""
    try:
        portfolio = portfolio_service.get_portfolio(db, portfolio_id)

        if not portfolio:
            raise HTTPException(status_code=404, detail="Portfolio not found")

        # Get positions and trades explicitly
        positions = portfolio_service.get_positions(db, portfolio_id)
        trades = portfolio_service.get_trades(db, portfolio_id)

        portfolio_data = {
            "name": portfolio.name,
            "cash": float(portfolio.cash_balance),
            "total_value": float(portfolio.current_value),
            "positions": [
                {
                    "symbol": p.symbol,
                    "quantity": float(p.quantity),
                    "cost_basis": float(p.entry_price * p.quantity),
                    "current_price": float(p.current_price) if p.current_price else 0,
                    "market_value": float(p.current_price * p.quantity)
                    if p.current_price
                    else 0,
                    "unrealized_pnl": float(p.unrealized_pnl)
                    if p.unrealized_pnl
                    else 0,
                }
                for p in positions
            ],
            "trades": [
                {
                    "symbol": t.symbol,
                    "type": t.side,
                    "quantity": float(t.quantity),
                    "price": float(t.price),
                    "timestamp": t.executed_at.isoformat(),
                }
                for t in trades
            ],
        }

        content = export_service.export_portfolio(portfolio_data, format)

        media_type = (
            "text/csv"
            if format == "csv"
            else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        filename = f"portfolio_{portfolio_id}.{format}"
        if format == "excel":
            filename = f"portfolio_{portfolio_id}.xlsx"

        return Response(
            content=content,
            media_type=media_type,
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Export failed: {e!s}")
