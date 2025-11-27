"""Utility for running a single-symbol Stratestic backtest using Alpha Vantage data."""

from __future__ import annotations

from typing import Any, Dict

from config import settings
from ingestion.alpha_vantage_client import AlphaVantageClient
from research.experiments.stratestic_adapter import dataframe_to_stratestic_timeseries
from research.strategies.ma_crossover_stratestic import build_ma_crossover_strategy

# Stratestic runtime imports
from stratestic.execution import BacktestEngine
from stratestic.metrics import PerformanceReport


def _require_api_key() -> str:
    api_key = settings.ALPHA_VANTAGE_API_KEY
    if not api_key:
        raise RuntimeError("Set ALPHA_VANTAGE_API_KEY in your environment or .env file.")
    return api_key


def run_stratestic_backtest_for_symbol(
    symbol: str,
    short_window: int,
    long_window: int,
    output_size: str = "compact",
) -> Dict[str, Any]:
    """
    Run a moving-average crossover backtest for a single symbol using Stratestic.

    The function downloads OHLCV data via Alpha Vantage, converts it into
    Stratestic's :class:`~stratestic.data.PriceSeries`, executes the Stratestic-native
    moving average crossover strategy, and returns a summary of key performance
    metrics for downstream optimization workflows.
    """

    api_key = _require_api_key()

    client = AlphaVantageClient(api_key=api_key)
    raw_data = client.get_daily(symbol, output_size=output_size)

    price_series = dataframe_to_stratestic_timeseries(raw_data)
    strategy = build_ma_crossover_strategy(short_window=short_window, long_window=long_window)

    engine = BacktestEngine(prices=price_series, strategy=strategy)
    run_result = engine.run()

    report = PerformanceReport.from_run(run_result)
    metrics = report.to_dict()

    return {
        "symbol": symbol,
        "short_window": short_window,
        "long_window": long_window,
        "cumulative_return": metrics.get("cumulative_return") or metrics.get("cumulative") or metrics.get("cumulative_return_pct"),
        "max_drawdown": metrics.get("max_drawdown"),
        "sharpe_ratio": metrics.get("sharpe_ratio") or metrics.get("sharpe"),
        "metrics": metrics,
    }


__all__ = ["run_stratestic_backtest_for_symbol"]
