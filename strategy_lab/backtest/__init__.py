"""Backtest module - Backtesting engine for strategy lab."""

from strategy_lab.backtest.engine import StrategyBacktestEngine
from strategy_lab.backtest.reports import (
    build_backtest_report,
    to_equity_df,
    to_summary_metrics,
    to_trades_df,
)
from strategy_lab.backtest.results import BacktestResults
from strategy_lab.backtest.runner import StrategyLabBacktestRunner, run_backtest

__all__ = [
    "BacktestResults",
    "StrategyBacktestEngine",
    "build_backtest_report",
    "StrategyLabBacktestRunner",
    "to_equity_df",
    "to_summary_metrics",
    "to_trades_df",
    "run_backtest",
]
