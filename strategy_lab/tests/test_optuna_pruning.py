"""Tests for the Optuna pruning engine."""

import optuna
import pytest
from unittest.mock import MagicMock, patch

# Verify the function builds a study with a MedianPruner, without running a real backtest.
def test_optimize_lab_strategy_uses_pruner():
    from strategy_lab.optimization import optuna_engine

    created_studies = []

    original_create_study = optuna.create_study

    def mock_create_study(*args, **kwargs):
        study = original_create_study(*args, **kwargs)
        created_studies.append({"pruner": kwargs.get("pruner")})
        # Immediately stop optimisation after checking params
        study.optimize = MagicMock()
        return study

    with patch.object(optuna, "create_study", side_effect=mock_create_study):
        # We just need the study creation to go through — mock out everything else.
        with patch("strategy_lab.optimization.optuna_engine.StrategyBacktestEngine"):
            with patch("strategy_lab.optimization.optuna_engine.YFinanceHistoricalProvider"):
                with patch("strategy_lab.optimization.optuna_engine.RiskEngine"):
                    from datetime import datetime
                    from strategy_lab.strategies.base import Strategy, SignalType
                    from strategy_lab.config import StrategyConfig

                    class DummyStrategy(Strategy):
                        def generate_signals(self, data, factor_panels):
                            return {}

                    try:
                        optuna_engine.optimize_lab_strategy(
                            strategy_cls=DummyStrategy,
                            symbol="AAPL",
                            start_date=datetime(2023, 1, 1),
                            end_date=datetime(2023, 12, 31),
                            initial_capital=100_000,
                            n_trials=1,
                            param_ranges={"fast_period": (5, 20, "int")},
                        )
                    except Exception:
                        pass  # We only care that create_study was called

    assert len(created_studies) == 1, "Expected create_study to be called once"
    pruner = created_studies[0]["pruner"]
    assert isinstance(pruner, optuna.pruners.MedianPruner), (
        f"Expected MedianPruner, got {type(pruner)}"
    )
