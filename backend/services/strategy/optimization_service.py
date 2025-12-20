"""Optimization service using Optuna."""

import logging
from typing import Any

import optuna

from services.strategy.backtest_service import BacktestService

logger = logging.getLogger(__name__)


class OptimizationService:
    """Service for optimizing strategy parameters using Optuna."""

    def __init__(self):
        self.backtest_service = BacktestService()

    def optimize(
        self,
        strategy_name: str,
        symbol: str,
        parameter_ranges: dict[str, dict[str, Any]],
        initial_capital: float = 100000.0,
        data_source: str = "local",
        n_trials: int = 20,
        metric: str = "sharpe_ratio",
        direction: str = "maximize",
    ) -> dict[str, Any]:
        """Run an Optuna study to optimize strategy parameters.

        Args:
            strategy_name: Name of the strategy to optimize.
            symbol: Symbol to backtest on.
            parameter_ranges: Dictionary defining parameter ranges.
                Format: {
                    "param_name": {"type": "int", "min": 10, "max": 50, "step": 1},
                    "param_name_2": {"type": "float", "min": 0.1, "max": 0.5, "step": 0.1},
                    "param_name_3": {"type": "categorical", "choices": ["a", "b"]}
                }
            initial_capital: Initial capital for backtests.
            data_source: Data source for prices.
            n_trials: Number of trials to run.
            metric: Metric to optimize (e.g., "sharpe_ratio", "total_return_pct").
            direction: "maximize" or "minimize".

        Returns:
            Dictionary containing best parameters, best value, and trial history.

        """
        # Get price data once to avoid fetching it in every trial
        # We can pass this to the backtest service if we modify it,
        # or rely on caching in the price service (which is already implemented).
        # For now, we'll rely on the cache.

        def objective(trial: optuna.trial.Trial) -> float:
            # Construct parameters for this trial
            params = {}
            for name, config in parameter_ranges.items():
                param_type = config.get("type")

                if param_type == "int":
                    params[name] = trial.suggest_int(
                        name,
                        int(config["min"]),
                        int(config["max"]),
                        step=int(config.get("step", 1)),
                    )
                elif param_type == "float":
                    params[name] = trial.suggest_float(
                        name,
                        float(config["min"]),
                        float(config["max"]),
                        step=(
                            float(config.get("step", 0.1)) if "step" in config else None
                        ),
                    )
                elif param_type == "categorical":
                    params[name] = trial.suggest_categorical(name, config["choices"])

            try:
                # Run backtest
                result = self.backtest_service.run_backtest(
                    symbol=symbol,
                    strategy_name=strategy_name,
                    parameters=params,
                    initial_capital=initial_capital,
                    data_source=data_source,
                )

                metrics = result.get("metrics", {})
                value = metrics.get(metric)

                # Handle None or invalid values
                if value is None:
                    return float("-inf") if direction == "maximize" else float("inf")

                return float(value)

            except Exception as e:
                # Log error and return bad value
                logger.exception(
                    "Trial failed for strategy=%s symbol=%s params=%s: %s",
                    strategy_name,
                    symbol,
                    params,
                    e,
                )
                return float("-inf") if direction == "maximize" else float("inf")

        study = optuna.create_study(direction=direction)
        study.optimize(objective, n_trials=n_trials)

        def safe_value(val):
            if val is None:
                return None
            if isinstance(val, float):
                if val == float("inf"):
                    return "inf"
                if val == float("-inf"):
                    return "-inf"
                if val != val:  # NaN check
                    return "nan"
            return val

        return {
            "best_params": study.best_params,
            "best_value": safe_value(study.best_value),
            "trials": [
                {
                    "number": t.number,
                    "params": t.params,
                    "value": safe_value(t.value),
                    "state": t.state.name,
                }
                for t in study.trials
            ],
        }


optimization_service = OptimizationService()
