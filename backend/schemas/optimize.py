from datetime import date
from typing import Any, Dict, List, Literal, Union

from pydantic import BaseModel, Field


class ParameterRange(BaseModel):
    """Configuration for a parameter to be optimized."""
    name: str
    min_value: Union[int, float]
    max_value: Union[int, float]
    type: Literal["int", "float"]
    step: Union[int, float, None] = None  # Optional step size


class OptimizationRequest(BaseModel):
    """Request schema for running an optimization task."""
    strategy_name: str
    symbol: str
    start_date: date
    end_date: date
    initial_capital: float = 100000.0
    n_trials: int = 20
    parameter_ranges: List[ParameterRange]
    fixed_parameters: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        json_schema_extra = {
            "example": {
                "strategy_name": "MovingAverageCrossover",
                "symbol": "AAPL",
                "start_date": "2023-01-01",
                "end_date": "2023-12-31",
                "initial_capital": 100000.0,
                "n_trials": 20,
                "parameter_ranges": [
                    {"name": "short_window", "min_value": 10, "max_value": 50, "type": "int"},
                    {"name": "long_window", "min_value": 100, "max_value": 200, "type": "int"}
                ],
                "fixed_parameters": {}
            }
        }


class OptimizationResponse(BaseModel):
    """Response schema for optimization results."""
    strategy_name: str
    symbol: str
    best_params: Dict[str, Any]
    best_value: float  # The objective value (e.g., Sharpe Ratio)
    optimization_id: str  # Unique ID for the run (optional, for future retrieval)
