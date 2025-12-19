"""Monte Carlo Optimization Engine.

This module provides the Monte Carlo optimization engine for finding
optimal strategy parameters and assessing robustness.
"""

import copy
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

from strategy_lab.backtest.engine import StrategyBacktestEngine
from strategy_lab.backtest.results import BacktestResults
from strategy_lab.config import OptimizationConfig, RiskConstraintConfig, StrategyConfig
from strategy_lab.optimization.parameters import ParameterSpace
from strategy_lab.strategies.base import Strategy


@dataclass
class OptimizationResult:
    """Result of a single optimization trial.

    Attributes:
        parameters: Parameters used in this trial
        metrics: Performance metrics resulting from the trial
        is_valid: Whether the trial passed all risk constraints

    """

    parameters: dict[str, Any]
    metrics: dict[str, Any]
    is_valid: bool
    backtest_result: Optional[BacktestResults] = None


class MonteCarloOptimizer:
    """Monte Carlo Optimizer.

    Runs random sampling of strategy parameters to find optimal configurations
    and estimate strategy robustness.
    """

    def __init__(
        self, engine: StrategyBacktestEngine, optimization_config: OptimizationConfig,
    ):
        """Initialize optimizer.

        Args:
            engine: Backtest engine instance
            optimization_config: Optimization configuration

        """
        self.engine = engine
        self.config = optimization_config
        self.parameter_space = ParameterSpace()

        # Populate parameter space
        for bound in self.config.parameter_bounds:
            self.parameter_space.add_bound(bound)

    def optimize(
        self,
        strategy_cls: type[Strategy],
        base_strategy_config: StrategyConfig,
        start_date: datetime,
        end_date: datetime,
        universe: list[str],
    ) -> list[OptimizationResult]:
        """Run optimization loop.

        Args:
            strategy_cls: Class of the strategy to optimize
            base_strategy_config: Template configuration
            start_date: Backtest start
            end_date: Backtest end
            universe: Symbols to trade

        Returns:
            List of optimization results

        """
        results = []

        print(
            f"Starting Monte Carlo optimization with {self.config.n_trials} trials...",
        )

        for i in range(self.config.n_trials):
            # 1. Sample parameters
            params = self.parameter_space.sample()

            # 2. Create Trial Config
            # Clone base config and update parameters
            trial_config = copy.deepcopy(base_strategy_config)
            trial_config.parameters.update(params)
            # Ensure name is unique for tracking
            trial_config.name = f"{base_strategy_config.name}_trial_{i}"

            # 3. Instantiate Strategy
            strategy = strategy_cls(trial_config)

            # 4. Run Backtest
            try:
                # Create a fresh RiskEngine per run if needed, but Engine might reuse shared one?
                # The engine passed in init has a 'risk_engine'.
                # Ideally, we should update the engine's risk config if parameters affect risk,
                # but usually we optimize strategy params, not risk params.
                # If we need fresh state, we rely on the engine implementation resetting state
                # (which our engine does in `run()` by creating new PortfolioState).

                result = self.engine.run(
                    strategy=strategy,
                    start_date=start_date,
                    end_date=end_date,
                    universe=universe,
                    initial_capital=base_strategy_config.initial_capital,
                )

                metrics = result.get_metrics()

                # 5. Check Constraints (Validation)
                is_valid = self._check_constraints(
                    metrics, base_strategy_config.risk_constraints,
                )
                # Also check risk limits directly if they are in metrics
                if (
                    metrics.get("max_drawdown", 0)
                    > base_strategy_config.risk_config.max_drawdown_pct
                ):
                    is_valid = False

                # 6. Store Result
                # We might not want to store the full BacktestResult for every trial to save memory,
                # unless requested. For now, we store it.
                opt_res = OptimizationResult(
                    parameters=params,
                    metrics=metrics,
                    is_valid=is_valid,
                    backtest_result=result,
                )
                results.append(opt_res)

                print(
                    f"Trial {i + 1}/{self.config.n_trials}: Valid={is_valid}, Return={metrics['total_return']:.2%}",
                )

            except Exception as e:
                print(f"Trial {i + 1} failed: {e}")

        return results

    def _check_constraints(
        self, metrics: dict[str, Any], constraints: RiskConstraintConfig,
    ) -> bool:
        """Check if metrics satisfy risk constraints.

        Args:
           metrics: Performance metrics
           constraints: Risk constraints

        Returns:
           True if valid, False otherwise

        """
        # Example checks
        if metrics.get("volatility", 0) > constraints.max_volatility:
            return False

        # Additional checks can be added here

        return True
