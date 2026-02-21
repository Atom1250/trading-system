"""Strategy Lab backtest service for API endpoints."""

from __future__ import annotations

from datetime import datetime
from uuid import uuid4

import pandas as pd

from backend.schemas.backtests_v2 import BacktestRunRequest
from strategy_lab.backtest.reports import build_backtest_report
from strategy_lab.backtest.runner import StrategyLabBacktestRunner
from strategy_lab.config import RiskConfig, StrategyConfig
from strategy_lab.data.providers import YFinanceHistoricalProvider
from strategy_lab.persistence.repo import BacktestRepository
from strategy_lab.risk.engine import RiskEngine
from strategy_lab.risk.metrics import RiskMetrics
from strategy_lab.strategies.simple.moving_average import MovingAverageCrossoverStrategy
from strategy_lab.strategies.simple.rsi import RSIMeanReversionStrategy
from strategy_lab.strategies.simple.trend_pullback import TrendPullbackStrategy


class BacktestService:
    """Run and retrieve Strategy Lab backtests."""

    STRATEGIES = {
        "MovingAverageCrossover": MovingAverageCrossoverStrategy,
        "RSIMeanReversion": RSIMeanReversionStrategy,
        "TrendPullback": TrendPullbackStrategy,
    }

    def __init__(
        self,
        *,
        data_provider=None,
        repository: BacktestRepository | None = None,
    ):
        self.data_provider = data_provider or YFinanceHistoricalProvider()
        self.repository = repository or BacktestRepository()
        self._run_summaries: dict[str, dict] = {}

    def run_backtest(self, request: BacktestRunRequest) -> dict:
        """Run a backtest, persist artifacts, and return run summary."""
        strategy_cls = self.STRATEGIES.get(request.strategy_name)
        if strategy_cls is None:
            raise ValueError(f"Strategy '{request.strategy_name}' not found")

        risk_config = RiskConfig()
        risk_engine = RiskEngine(risk_config=risk_config)
        strategy_config = StrategyConfig(
            name=request.strategy_name,
            initial_capital=request.initial_capital,
            parameters=request.parameters,
            risk_config=risk_config,
            universe=[request.symbol],
        )
        strategy = strategy_cls(config=strategy_config)
        runner = StrategyLabBacktestRunner(
            data_provider=self.data_provider,
            risk_engine=risk_engine,
        )
        start_dt = datetime.combine(request.start_date, datetime.min.time())
        end_dt = datetime.combine(request.end_date, datetime.max.time())
        results = runner.run(
            strategy=strategy,
            start_date=start_dt,
            end_date=end_dt,
            universe=[request.symbol],
            initial_capital=request.initial_capital,
        )

        run_id = str(uuid4())
        persistence = self.repository.save_backtest_results(
            run_id=run_id, results=results
        )
        report = build_backtest_report(results)
        summary = report["summary"]
        self._run_summaries[run_id] = summary

        return {
            "run_id": run_id,
            "strategy_name": request.strategy_name,
            "symbol": request.symbol,
            "config_hash": persistence["config_hash"],
            "summary": summary,
        }

    def get_run_summary(self, run_id: str) -> dict:
        run = self.repository.get_run_summary(run_id)
        if run is None:
            raise KeyError(run_id)
        summary = self._run_summaries.get(run_id)
        if summary is None:
            summary = self._derive_summary_from_persisted_rows(run_id)
        return {
            "run_id": run["run_id"],
            "strategy_name": run["strategy_name"],
            "config_hash": run["config_hash"],
            "created_at": run["created_at"],
            "summary": summary,
        }

    def get_run_trades(self, run_id: str) -> dict:
        trades_df = self.repository.get_run_trades(run_id)
        return {
            "run_id": run_id,
            "trades": trades_df.to_dict("records"),
        }

    def get_run_equity(self, run_id: str) -> dict:
        equity_df = self.repository.get_run_equity_history(run_id)
        return {
            "run_id": run_id,
            "equity": equity_df.to_dict("records"),
        }

    def _derive_summary_from_persisted_rows(self, run_id: str) -> dict:
        equity_df = self.repository.get_run_equity_history(run_id)
        trades_df = self.repository.get_run_trades(run_id)
        if equity_df.empty:
            return {
                "total_return": 0.0,
                "cumulative_return": 0.0,
                "max_drawdown": 0.0,
                "sharpe_ratio": 0.0,
                "num_trades": 0.0,
                "win_rate": 0.0,
            }

        equity_series = pd.Series(equity_df["equity"].values)
        returns = equity_series.pct_change().fillna(0.0)
        metrics = RiskMetrics.calculate_all(returns)
        cumulative_return = (
            float(equity_series.iloc[-1] / equity_series.iloc[0] - 1.0)
            if float(equity_series.iloc[0]) != 0.0
            else 0.0
        )
        num_trades = float(len(trades_df))
        wins = float((trades_df["pnl"] > 0).sum()) if not trades_df.empty else 0.0
        win_rate = wins / num_trades if num_trades > 0 else 0.0
        return {
            "total_return": float(metrics.get("total_return", 0.0)),
            "cumulative_return": cumulative_return,
            "max_drawdown": float(metrics.get("max_drawdown", 0.0)),
            "sharpe_ratio": float(metrics.get("sharpe_ratio", 0.0)),
            "num_trades": num_trades,
            "win_rate": win_rate,
        }
