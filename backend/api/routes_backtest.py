"""Backtest run/fetch API routes (Phase 7)."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from backend.schemas.backtests_v2 import (
    BacktestEquityResponse,
    BacktestRunRequest,
    BacktestRunResponse,
    BacktestSummaryResponse,
    BacktestTradesResponse,
)
from backend.services.backtest_service import BacktestService

router = APIRouter()
backtest_service = BacktestService()


@router.post("/backtests/run", response_model=BacktestRunResponse)
def run_backtest(request: BacktestRunRequest):
    try:
        return backtest_service.run_backtest(request)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Backtest execution failed: {exc}")


@router.get("/backtests/{run_id}/summary", response_model=BacktestSummaryResponse)
def get_backtest_summary(run_id: str):
    try:
        return backtest_service.get_run_summary(run_id)
    except KeyError:
        raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")


@router.get("/backtests/{run_id}/trades", response_model=BacktestTradesResponse)
def get_backtest_trades(run_id: str):
    return backtest_service.get_run_trades(run_id)


@router.get("/backtests/{run_id}/equity", response_model=BacktestEquityResponse)
def get_backtest_equity(run_id: str):
    return backtest_service.get_run_equity(run_id)
