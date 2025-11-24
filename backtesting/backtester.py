"""Vectorized backtesting engine for trading strategies."""
from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd


class Backtester:
    """Run a vectorized backtest on price data and strategy signals."""

    def __init__(
        self,
        price_column: str = "close",
        signal_column: str = "signal",
        results_path: str | Path = "reports/results.csv",
    ) -> None:
        self.price_column = price_column
        self.signal_column = signal_column
        self.results_path = Path(results_path)

    def run(self, df: pd.DataFrame) -> dict[str, pd.DataFrame | float | str]:
        """Execute the backtest, export results, and compute summary metrics.

        Args:
            df: Price DataFrame with columns for price and strategy signals.

        Returns:
            Dict containing the full results DataFrame, cumulative return,
            maximum drawdown, and the export path.
        """
        self._validate_inputs(df)

        prices = df[self.price_column]
        raw_returns = prices.pct_change().fillna(0)

        positions = df[self.signal_column].shift(1).fillna(0)
        strategy_returns = positions * raw_returns

        equity_curve = (1 + strategy_returns).cumprod()
        cumulative_returns = equity_curve - 1

        running_max = equity_curve.cummax()
        drawdown = (equity_curve - running_max) / running_max.replace(0, pd.NA)

        results = df.copy()
        results["returns"] = raw_returns
        results["strategy_returns"] = strategy_returns
        results["cumulative_returns"] = cumulative_returns
        results["drawdown"] = drawdown

        self._export_results(results)

        cumulative_return = float(cumulative_returns.iloc[-1]) if not results.empty else 0.0
        max_drawdown = float(drawdown.min()) if not results.empty else 0.0

        return {
            "results": results,
            "cumulative_return": cumulative_return,
            "max_drawdown": max_drawdown,
            "results_path": str(self.results_path),
        }

    def plot_results(
        self,
        df: pd.DataFrame,
        symbol: str,
        output_path: str | Path | None = None,
    ) -> str:
        """Plot price, moving averages, and buy/sell signals over time.

        Saves the plot under ``reports/`` by default and returns the saved path.
        """

        self._validate_inputs(df)

        output = Path(output_path) if output_path is not None else Path("reports") / f"{symbol}_backtest.png"
        output.parent.mkdir(parents=True, exist_ok=True)

        fig, ax = plt.subplots(figsize=(12, 6))

        df[self.price_column].plot(ax=ax, label="Close", color="black", linewidth=1.2)

        if "sma_short" in df.columns:
            df["sma_short"].plot(ax=ax, label="SMA Short", color="blue", linestyle="--")
        if "sma_long" in df.columns:
            df["sma_long"].plot(ax=ax, label="SMA Long", color="orange", linestyle="--")

        if self.signal_column in df.columns:
            buy_signals = df[df[self.signal_column] > 0]
            sell_signals = df[df[self.signal_column] < 0]

            if not buy_signals.empty:
                ax.scatter(
                    buy_signals.index,
                    buy_signals[self.price_column],
                    marker="^",
                    color="green",
                    label="Buy",
                    zorder=5,
                )
            if not sell_signals.empty:
                ax.scatter(
                    sell_signals.index,
                    sell_signals[self.price_column],
                    marker="v",
                    color="red",
                    label="Sell",
                    zorder=5,
                )

        ax.set_title(f"Backtest Results for {symbol}")
        ax.set_xlabel("Date")
        ax.set_ylabel("Price")
        ax.legend()
        ax.grid(True, linestyle="--", alpha=0.3)

        fig.tight_layout()
        fig.savefig(output, bbox_inches="tight")
        plt.close(fig)

        return str(output)

    def _validate_inputs(self, df: pd.DataFrame) -> None:
        if self.price_column not in df.columns:
            raise KeyError(f"Column '{self.price_column}' not found in DataFrame.")
        if self.signal_column not in df.columns:
            raise KeyError(f"Column '{self.signal_column}' not found in DataFrame.")

    def _export_results(self, results: pd.DataFrame) -> None:
        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        results.to_csv(self.results_path)
