"""Tearsheet generator.

This module provides the TearsheetGenerator class for creating comprehensive
performance reports from backtest results, including metrics and plots.
"""

import os
from datetime import datetime
from typing import Any, Optional

from strategy_lab.backtest.results import BacktestResults
from strategy_lab.reporting.plots import PerformancePlotter


class TearsheetGenerator:
    """Generator for strategy performance tearsheets.

    Attributes:
        results: BacktestResults object
        plotter: PerformancePlotter instance

    """

    def __init__(self, results: BacktestResults, style: str = "seaborn-v0_8-darkgrid"):
        """Initialize tearsheet generator.

        Args:
            results: Backtest results to report on
            style: Plotting style

        """
        self.results = results
        self.plotter = PerformancePlotter(style=style)

    def create_full_report(self, output_dir: Optional[str] = None) -> dict[str, Any]:
        """Create full performance report.

        Args:
            output_dir: Directory to save report assets (optional)

        Returns:
            Dictionary containing report components

        """
        # Get metrics and standard summary
        metrics = self.results.get_metrics()
        summary = self.results.summary()

        # specific plots
        returns = self.results.returns

        figs = {}
        figs["equity"] = self.plotter.plot_equity_curve(
            returns=returns, title=f"Equity Curve: {self.results.strategy_name}",
        )

        figs["drawdown"] = self.plotter.plot_drawdowns(
            returns=returns, title=f"Drawdown: {self.results.strategy_name}",
        )

        figs["monthly_heatmap"] = self.plotter.plot_monthly_heatmap(returns=returns)

        report = {
            "strategy_name": self.results.strategy_name,
            "timestamp": datetime.now().isoformat(),
            "metrics": metrics,
            "summary_text": summary,
            "figures": figs,
        }

        if output_dir:
            self.save_report(report, output_dir)

        return report

    def save_report(self, report: dict[str, Any], output_dir: str) -> None:
        """Save report to directory.

        Args:
            report: Report dictionary
            output_dir: Output directory

        """
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)

        # Save summary text
        with open(os.path.join(output_dir, "summary.txt"), "w") as f:
            f.write(report["summary_text"])

        # Save plots
        for name, fig in report["figures"].items():
            if fig:
                fig.savefig(os.path.join(output_dir, f"{name}.png"))

        print(f"Report saved to {output_dir}")
