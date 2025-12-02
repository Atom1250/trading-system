"""Optimization API endpoints."""
from fastapi import APIRouter, HTTPException, Query, Body
from typing import Dict, Any, Optional
from pydantic import BaseModel
import traceback

from services.strategy.optimization_service import optimization_service

router = APIRouter()

class ParameterRange(BaseModel):
    type: str  # "int", "float", "categorical"
    min: Optional[float] = None
    max: Optional[float] = None
    step: Optional[float] = None
    choices: Optional[list] = None

class OptimizationRequest(BaseModel):
    strategy_name: str
    symbol: str
    parameter_ranges: Dict[str, ParameterRange]
    initial_capital: float = 100000.0
    data_source: str = "local"
    n_trials: int = 20
    metric: str = "sharpe_ratio"
    direction: str = "maximize"

@router.post("/run")
async def run_optimization(request: OptimizationRequest):
    """Run a strategy optimization."""
    try:
        # Convert Pydantic models to dict for service
        param_ranges = {
            k: v.model_dump(exclude_none=True) 
            for k, v in request.parameter_ranges.items()
        }
        
        result = optimization_service.optimize(
            strategy_name=request.strategy_name,
            symbol=request.symbol,
            parameter_ranges=param_ranges,
            initial_capital=request.initial_capital,
            data_source=request.data_source,
            n_trials=request.n_trials,
            metric=request.metric,
            direction=request.direction
        )
        return result
    except Exception as e:
        error_msg = f"Optimization failed: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)
