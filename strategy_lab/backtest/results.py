"""Backtest results processing.

This module provides classes for processing and analyzing backtest results.
"""

from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd

from strategy_lab.config import StrategyConfig
from strategy_lab.risk.metrics import RiskMetrics


@dataclass
class BacktestResults:
    """Backtest results container.

    Attributes:
        strategy_name: Name of the strategy
        signals: Trading signals (raw strategy output)
        returns: Strategy returns (realized)
        data: Market data used
        config: Strategy configuration
        trade_log: Optional explicit trade log from engine
        portfolio_history: Optional history of portfolio state

    """

    strategy_name: str
    signals: pd.Series
    returns: pd.Series
    data: pd.DataFrame
    config: StrategyConfig
    trade_log: Optional[pd.DataFrame] = None
    portfolio_history: Optional[pd.DataFrame] = None

    def get_equity_curve(self, initial_capital: Optional[float] = None) -> pd.Series:
        """Calculate equity curve.

        Args:
            initial_capital: Initial capital (defaults to config)

        Returns:
            Equity curve series

        """
        if self.portfolio_history is not None:
            # Use actual equity from simulation
            return self.portfolio_history["equity"]

        capital = initial_capital or self.config.initial_capital
        return (1 + self.returns).cumprod() * capital

    def get_metrics(self) -> dict[str, Any]:
        """Calculate performance metrics.

        Returns:
            Dictionary of performance metrics

        """
        metrics = RiskMetrics.calculate_all(self.returns)

        if self.trade_log is not None and not self.trade_log.empty:
            num_trades = len(self.trade_log)
            winning_trades = len(self.trade_log[self.trade_log["pnl"] > 0])
            win_rate = winning_trades / num_trades if num_trades > 0 else 0

            avg_win = self.trade_log[self.trade_log["pnl"] > 0]["pnl"].mean()
            avg_loss = abs(self.trade_log[self.trade_log["pnl"] < 0]["pnl"].mean())
            avg_win = 0 if pd.isna(avg_win) else avg_win
            avg_loss = 0 if pd.isna(avg_loss) else avg_loss

        else:
            # Fallback to signal-based approximation
            trades = self.signals.diff().abs()
            num_trades = (trades > 0).sum()
            winning_trades = (self.returns > 0).sum()
            win_rate = winning_trades / num_trades if num_trades > 0 else 0

            wins = self.returns[self.returns > 0]
            losses = self.returns[self.returns < 0]
            avg_win = wins.mean() if len(wins) > 0 else 0
            avg_loss = abs(losses.mean()) if len(losses) > 0 else 0

        # Profit factor
        if (
            self.trade_log is not None
            and not self.trade_log.empty
            and "pnl" in self.trade_log.columns
        ):
            gross_profit = self.trade_log[self.trade_log["pnl"] > 0]["pnl"].sum()
            gross_loss = abs(self.trade_log[self.trade_log["pnl"] < 0]["pnl"].sum())
            profit_factor = gross_profit / gross_loss if gross_loss > 0 else 0
        else:
            wins = self.returns[self.returns > 0]
            losses = self.returns[self.returns < 0]
            profit_factor = wins.sum() / abs(losses.sum()) if len(losses) > 0 else 0

        metrics.update(
            {
                "num_trades": num_trades,
                "win_rate": win_rate,
                "avg_win": avg_win,
                "avg_loss": avg_loss,
                "profit_factor": profit_factor,
                "expectancy": avg_win * win_rate - avg_loss * (1 - win_rate),
            },
        )

        return metrics

    def get_trade_log_df(self) -> pd.DataFrame:
        """Get trade log as DataFrame.

        Returns:
            DataFrame with trade details

        """
        if self.trade_log is not None:
            return self.trade_log

        # Fallback to signal-based generation
        signal_changes = self.signals.diff()
        trades = signal_changes[signal_changes != 0]

        log = []
        for timestamp, signal in trades.items():
            if timestamp in self.data.index:
                price = self.data.loc[timestamp, "close"]
                log.append(
                    {
                        "timestamp": timestamp,
                        "signal": signal,
                        "price": price,
                        "type": "LONG"
                        if signal > 0
                        else "SHORT"
                        if signal < 0
                        else "CLOSE",
                    },
                )

        return pd.DataFrame(log)

    def summary(self) -> str:
        """Generate summary report.

        Returns:
            Summary string

        """
        metrics = self.get_metrics()

        summary = f"""
Backtest Results: {self.strategy_name}
{"=" * 50}

Performance Metrics:
  Total Return:       {metrics["total_return"]:.2%}
  Annual Return:      {metrics["mean_return"]:.2%}
  Sharpe Ratio:       {metrics["sharpe_ratio"]:.2f}
  Sortino Ratio:      {metrics["sortino_ratio"]:.2f}
  Calmar Ratio:       {metrics["calmar_ratio"]:.2f}
  Max Drawdown:       {metrics["max_drawdown"]:.2%}
  Volatility:         {metrics["volatility"]:.2%}

Risk Metrics:
  VaR (95%):          {metrics["var_95"]:.2%}
  CVaR (95%):         {metrics["cvar_95"]:.2%}
  Downside Dev:       {metrics["downside_deviation"]:.2%}

Trade Statistics:
  Number of Trades:   {metrics["num_trades"]:.0f}
  Win Rate:           {metrics["win_rate"]:.2%}
  Profit Factor:      {metrics["profit_factor"]:.2f}
  Avg Win:            {metrics["avg_win"]:.2f}
  Avg Loss:           {metrics["avg_loss"]:.2f}
  Expectancy:         {metrics["expectancy"]:.4f}
        """

        return summary.strip()

    def to_dict(self) -> dict[str, Any]:
        """Convert results to dictionary.

        Returns:
            Dictionary representation

        """
        return {
            "strategy_name": self.strategy_name,
            "metrics": self.get_metrics(),
            "equity_curve": self.get_equity_curve().to_dict(),
            "trade_log": self.get_trade_log_df().to_dict("records")
            if not self.get_trade_log_df().empty
            else [],
            "config": {
                "initial_capital": self.config.initial_capital,
                "commission": self.config.commission,
                "slippage": self.config.slippage,
            },
        }
