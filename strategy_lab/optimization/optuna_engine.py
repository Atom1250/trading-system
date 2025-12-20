"""Generic Optuna Optimization for Strategy Lab."""

import logging
from datetime import datetime
from typing import Any

import optuna
import pandas as pd

from strategy_lab.backtest.engine import StrategyBacktestEngine
from strategy_lab.config import RiskConfig, StrategyConfig
from strategy_lab.data.providers import YFinanceHistoricalProvider
from strategy_lab.factors.base import FactorRegistry
from strategy_lab.risk.engine import RiskEngine  # Imported for risk proposals
from strategy_lab.strategies.base import Strategy

logger = logging.getLogger(__name__)


def optimize_lab_strategy(
    strategy_cls: type[Strategy],
    symbol: str,
    start_date: datetime,
    end_date: datetime,
    initial_capital: float,
    n_trials: int,
    param_ranges: dict[
        str,
        tuple[Any, Any, str],
    ],  # name -> (min, max, type='int'/'float')
    fixed_params: dict[str, Any] = None,
) -> dict[str, Any]:
    """Run Optuna optimization for a given Strategy Lab strategy."""
    fixed_params = fixed_params or {}

    # Pre-fetch data once to avoid fetching in every trial
    # NOTE: Engine usually fetches inside .run().
    # To optimize this, we might want to share the Data Provider cache or pass data directly.
    # YFinanceProvider has lru_cache on _fetch_prices_from_source but we should ensure we don't spam.
    # For now, relying on provider internal caching.

    def objective(trial):
        # Build Params
        trial_params = {}
        for p_name, (p_min, p_max, p_type) in param_ranges.items():
            if p_type == "int":
                trial_params[p_name] = trial.suggest_int(p_name, p_min, p_max)
            else:
                trial_params[p_name] = trial.suggest_float(p_name, p_min, p_max)

        # Merge with fixed
        full_params = {**fixed_params, **trial_params}

        # Config
        # We need a basic RiskConfig
        risk_cfg = RiskConfig(
            max_drawdown_pct=0.50,  # Loose for optimization unless optimized
            risk_per_trade=0.01,
            stop_loss_atr_multiple=full_params.get(
                "stop_loss_atr_multiple",
                2.0,
            ),  # If not in params, use default
        )

        strat_cfg = StrategyConfig(
            name="OptCandidate",
            initial_capital=initial_capital,
            risk_config=risk_cfg,
            parameters=full_params,
        )

        # Setup Engine
        provider = YFinanceHistoricalProvider(force_refresh=False)
        risk_engine = RiskEngine(risk_config=risk_cfg)  # Need import

        engine = StrategyBacktestEngine(
            data_provider=provider,
            risk_engine=risk_engine,
            factor_registry=FactorRegistry,
        )

        strategy = strategy_cls(strat_cfg)

        try:
            result = engine.run(
                strategy=strategy,
                start_date=start_date,
                end_date=end_date,
                universe=[symbol],
                initial_capital=initial_capital,
            )

            metrics = result.get_metrics()
            # Objective: Sharpe Ratio (risk-adjusted) or Total Return?
            # Let's use Sharpe, penalized if negative return or low trades
            sharpe = metrics.get("sharpe_ratio", 0.0)
            if pd.isna(sharpe):
                sharpe = -999.0

            # Simple penalty for no trades
            if metrics.get("num_trades", 0) < 5:
                # Heavy penalty
                return -999.0

            return sharpe

        except Exception as exc:
            logger.exception("Trial failed for params %s: %s", full_params, exc)
            return -9999.0

    study = optuna.create_study(direction="maximize")
    study.optimize(objective, n_trials=n_trials)

    return study.best_params
