"""Optuna-based optimization for moving-average crossover parameters."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
import optuna

from research.experiments.single_asset_stratestic_backtest import (
    run_stratestic_backtest_for_symbol,
)


def _risk_adjusted_score(metrics: Dict[str, Any]) -> float:
    """Compute a risk-adjusted objective score from backtest metrics."""

    sharpe_ratio = metrics.get("sharpe_ratio")
    if sharpe_ratio is not None:
        return float(sharpe_ratio)

    cumulative_return = metrics.get("cumulative_return")
    max_drawdown = metrics.get("max_drawdown")

    if cumulative_return is None:
        return float("-inf")

    drawdown_penalty = 0.5 * float(max_drawdown) if max_drawdown is not None else 0.0
    return float(cumulative_return) - drawdown_penalty


def _objective(
    symbol: str,
    *,
    output_size: str = "compact",
    short_window_range: tuple[int, int] = (5, 50),
    long_window_range: tuple[int, int] = (20, 200),
):
    def objective(trial: optuna.trial.Trial) -> float:
        short_window = trial.suggest_int(
            "short_window", short_window_range[0], short_window_range[1]
        )
        long_window = trial.suggest_int(
            "long_window", long_window_range[0], long_window_range[1]
        )

        if short_window >= long_window:
            return float("-inf")

        try:
            result = run_stratestic_backtest_for_symbol(
                symbol=symbol,
                short_window=short_window,
                long_window=long_window,
                output_size=output_size,
            )
            trial.set_user_attr("result", result)
        except Exception as exc:  # noqa: BLE001 - optuna objective should catch broadly
            trial.set_user_attr("error", str(exc))
            return float("-1e9")

        return _risk_adjusted_score(result)

    return objective


def optimize_ma_strategy_for_symbol(
    symbol: str,
    n_trials: int = 50,
    storage: Optional[str] = None,
    study_name: Optional[str] = None,
    short_window_range: tuple[int, int] | None = None,
    long_window_range: tuple[int, int] | None = None,
):
    """
    Run an Optuna study to optimize the MA crossover parameters for `symbol`.
    Optionally use `storage` and `study_name` for persistent tracking.
    Print and return the best parameters and best value.
    """

    short_range = short_window_range or (5, 50)
    long_range = long_window_range or (20, 200)

    if short_range[0] >= short_range[1]:
        raise ValueError("short_window_range must have min < max")
    if long_range[0] >= long_range[1]:
        raise ValueError("long_window_range must have min < max")

    study = optuna.create_study(
        direction="maximize",
        storage=storage,
        study_name=study_name,
        load_if_exists=bool(storage and study_name),
    )
    study.optimize(
        _objective(
            symbol,
            short_window_range=short_range,
            long_window_range=long_range,
        ),
        n_trials=n_trials,
    )

    print("Best value (risk-adjusted score):", study.best_value)
    print("Best params:", study.best_params)

    rows = []
    for trial in study.trials:
        trial_params = trial.params or {}
        result: Dict[str, Any] | None = trial.user_attrs.get("result")  # type: ignore[assignment]

        row: Dict[str, Any] = {
            "symbol": symbol,
            "short_window": trial_params.get("short_window"),
            "long_window": trial_params.get("long_window"),
            "objective_value": trial.value,
        }

        if result:
            row.update(
                {
                    "cumulative_return": result.get("cumulative_return"),
                    "max_drawdown": result.get("max_drawdown"),
                    "sharpe_ratio": result.get("sharpe_ratio"),
                }
            )
            metrics = result.get("metrics")
            if isinstance(metrics, dict):
                row.update(metrics)

        rows.append(row)

    report_dir = Path(__file__).resolve().parents[2] / "reports"
    report_dir.mkdir(parents=True, exist_ok=True)
    report_path = report_dir / f"optuna_ma_{symbol}.csv"
    pd.DataFrame(rows).to_csv(report_path, index=False)

    print(f"Saved Optuna trial results to {report_path}")

    return study.best_params, study.best_value


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Optimize moving-average crossover parameters with Optuna.",
    )
    parser.add_argument("symbol", help="Ticker symbol to optimize (e.g., AAPL)")
    parser.add_argument(
        "--trials",
        type=int,
        default=50,
        help="Number of Optuna trials to run (default: 50)",
    )
    parser.add_argument(
        "--storage",
        type=str,
        default=None,
        help="Optuna storage URL for persistent studies (optional)",
    )
    parser.add_argument(
        "--study-name",
        type=str,
        default=None,
        help="Name of the Optuna study (required when using storage)",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()
    optimize_ma_strategy_for_symbol(
        symbol=args.symbol,
        n_trials=args.trials,
        storage=args.storage,
        study_name=args.study_name,
    )
