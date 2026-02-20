import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, HTTPException

from backend.schemas.optimize import OptimizationRequest, OptimizationResponse
from strategy_lab.optimization.optuna_engine import optimize_lab_strategy
from strategy_lab.strategies.simple.moving_average import MovingAverageCrossoverStrategy
from strategy_lab.strategies.simple.rsi import RSIMeanReversionStrategy
from strategy_lab.strategies.simple.trend_pullback import TrendPullbackStrategy

router = APIRouter()

# Strategy Registry (Same as backtest, should be centralized ideally)
STRATEGIES = {
    "MovingAverageCrossover": MovingAverageCrossoverStrategy,
    "RSIMeanReversion": RSIMeanReversionStrategy,
    "TrendPullback": TrendPullbackStrategy,
}

@router.post("/run", response_model=OptimizationResponse)
def run_optimization(request: OptimizationRequest):
    """
    Run an optimization task using Optuna.
    """
    try:
        # 1. Resolve Strategy Class
        if request.strategy_name not in STRATEGIES:
            raise HTTPException(status_code=400, detail=f"Strategy '{request.strategy_name}' not found.")
        
        StrategyClass = STRATEGIES[request.strategy_name]
        
        # 2. Convert Dates (UTC aware)
        start_dt = datetime.combine(request.start_date, datetime.min.time()).replace(tzinfo=timezone.utc)
        end_dt = datetime.combine(request.end_date, datetime.max.time()).replace(tzinfo=timezone.utc)
        
        # 3. Format Parameter Ranges for Engine
        # Engine expects: dict[str, tuple[Any, Any, str]]  # name -> (min, max, type)
        # Note: The engine signature in optuna_engine.py might need slight adjustment or we match it here.
        # Looking at optuna_engine.py: param_ranges: dict[str, tuple[Any, Any, str]]
        
        formatted_ranges = {}
        for p in request.parameter_ranges:
            formatted_ranges[p.name] = (p.min_value, p.max_value, p.type)
            
        # 4. Run Optimization
        # Note: This is synchronous and could take a LONG time. 
        # In a production app, this should be a background task (Celery/RQ).
        # For this prototype, we'll run it synchronously but limit n_trials in UI recommendation.
        
        try:
            best_params = optimize_lab_strategy(
                strategy_cls=StrategyClass,
                symbol=request.symbol,
                start_date=start_dt,
                end_date=end_dt,
                initial_capital=request.initial_capital,
                n_trials=request.n_trials,
                param_ranges=formatted_ranges,
                fixed_params=request.fixed_parameters
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Optimization execution failed: {str(e)}")
            
        # 5. Return Results
        # The engine currently returns just best_params. 
        # Ideally it would return the study or best value too.
        # We might need to adjust the engine or just return params for now.
        # For now, we will return best_params and a placeholder value if not returned by engine.
        
        return OptimizationResponse(
            strategy_name=request.strategy_name,
            symbol=request.symbol,
            best_params=best_params,
            best_value=0.0, # Engine needs update to return this, or we infer from a re-run
            optimization_id=str(uuid.uuid4())
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")
