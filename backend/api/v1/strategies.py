"""Strategy API endpoints."""
from typing import List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from decimal import Decimal

from services.strategy.registry import registry
from services.strategy.backtest_service import backtest_service
from models.strategy import (
    StrategyInfo, BacktestRequest, BacktestResult,
    BacktestMetrics
)

router = APIRouter()


@router.get("/", response_model=List[StrategyInfo])
async def list_strategies():
    """List all available strategies."""
    strategies = registry.list_strategies()
    
    return [
        StrategyInfo(
            name=name,
            description=f"{name.replace('_', ' ').title()} Strategy",
            parameters=info["params"]
        )
        for name, info in strategies.items()
    ]


@router.get("/{strategy_name}", response_model=StrategyInfo)
async def get_strategy(strategy_name: str):
    """Get strategy details."""
    strategies = registry.list_strategies()
    
    if strategy_name not in strategies:
        raise HTTPException(
            status_code=404,
            detail=f"Strategy '{strategy_name}' not found"
        )
    
    info = strategies[strategy_name]
    return StrategyInfo(
        name=strategy_name,
        description=f"{strategy_name.replace('_', ' ').title()} Strategy",
        parameters=info["params"]
    )


@router.post("/backtest", response_model=BacktestResult)
async def run_backtest(request: BacktestRequest):
    """Run a backtest for a strategy."""
    try:
        result = backtest_service.run_backtest(
            symbol=request.symbol,
            strategy_name=request.strategy_name,
            parameters=request.parameters,
            start_date=request.start_date,
            end_date=request.end_date,
            initial_capital=request.initial_capital,
            data_source=request.data_source
        )
        
        return BacktestResult(
            symbol=result["symbol"],
            strategy_name=result["strategy_name"],
            metrics=BacktestMetrics(**result["metrics"]),
            equity_curve=result["equity_curve"],
            trades=result["trades"],
            parameters=result["parameters"],
            executed_at=result["executed_at"]
        )
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Backtest failed: {str(e)}")
