"""Portfolio-level backtesting aggregation."""
from __future__ import annotations

from pathlib import Path
from typing import Dict

import pandas as pd


class PortfolioBacktester:
    """Aggregate single-asset backtests into an equal-weight portfolio."""

    def __init__(
        self,
        results_path: str | Path = "reports/portfolio_results.csv",
        strategy_return_column: str = "strategy_returns",
    ) -> None:
        self.results_path = Path(results_path)
        self.strategy_return_column = strategy_return_column

    def run(self, results_by_symbol: Dict[str, pd.DataFrame]) -> dict[str, pd.DataFrame | float | str]:
        """Run a simple equal-weight portfolio backtest from individual results.

        Args:
            results_by_symbol: Mapping of symbol to the single-asset backtest
                results DataFrame containing a strategy returns column.

        Returns:
            Dict containing portfolio-level results, cumulative return, max drawdown,
            and the export path for the aggregated CSV.
        """
        if not results_by_symbol:
            raise ValueError("No results provided for portfolio backtest.")

        return_series = []
        for symbol, df in results_by_symbol.items():
            if self.strategy_return_column not in df.columns:
                raise KeyError(
                    f"Column '{self.strategy_return_column}' not found in results for {symbol}."
                )
            series = df[self.strategy_return_column].rename(symbol)
            return_series.append(series)

        strategy_returns = pd.concat(return_series, axis=1).fillna(0.0)
        portfolio_strategy_returns = strategy_returns.mean(axis=1)

        equity_curve = (1 + portfolio_strategy_returns).cumprod()
        cumulative_returns = equity_curve - 1
        running_max = equity_curve.cummax()
        drawdown = (equity_curve - running_max) / running_max.replace(0, pd.NA)

        results = pd.DataFrame(
            {
                "portfolio_strategy_returns": portfolio_strategy_returns,
                "equity_curve": equity_curve,
                "cumulative_returns": cumulative_returns,
                "drawdown": drawdown,
            }
        )

        self._export_results(results)

        cumulative_return = float(cumulative_returns.iloc[-1]) if not results.empty else 0.0
        max_drawdown = float(drawdown.min()) if not results.empty else 0.0

        return {
            "portfolio_results": results,
            "cumulative_return": cumulative_return,
            "max_drawdown": max_drawdown,
            "results_path": str(self.results_path),
        }

    def _export_results(self, results: pd.DataFrame) -> None:
        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        results.to_csv(self.results_path)
