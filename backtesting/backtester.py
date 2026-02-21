"""Backtester that routes execution through ``backtesting.py``."""

from __future__ import annotations

import logging
import warnings
from pathlib import Path
from typing import Optional, Union

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from backtesting import Backtest, Strategy

logger = logging.getLogger(__name__)


class Backtester:
    """Run backtests using the ``backtesting.py`` engine."""

    def __init__(
        self,
        price_column: str = "close",
        signal_column: str = "signal",
        results_path: str | Path = "reports/results.csv",
        initial_cash: float = 100_000.0,
        commission: float = 0.0,
    ) -> None:
        self.price_column = price_column
        self.signal_column = signal_column
        self.results_path = Path(results_path)
        self.initial_cash = initial_cash
        self.commission = commission
        warnings.warn(
            "backtesting.Backtester is deprecated. "
            "Use strategy_lab.backtest.runner.StrategyLabBacktestRunner instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    def run(self, df: pd.DataFrame) -> dict[str, pd.DataFrame | float | str]:
        """Execute the backtest via ``backtesting.py`` and export results.

        Args:
            df: Price DataFrame with columns for price and strategy signals.

        Returns:
            Dict containing the full results DataFrame, cumulative return,
            maximum drawdown, and the export path.

        """
        self._validate_inputs(df)

        bt_df = self._prepare_backtesting_frame(df)
        signal_values = df[self.signal_column].fillna(0).values

        class PrecomputedSignalStrategy(Strategy):
            def init(self) -> None:
                self.signal = self.I(lambda: signal_values, name="signal")

            def next(
                self,
            ) -> None:  # pragma: no cover - thin wrapper for backtesting.py
                sig = self.signal[-1]

                if sig > 0:
                    if not self.position.is_long:
                        if self.position:
                            self.position.close()
                        self.buy(size=1)
                elif sig < 0:
                    if not self.position.is_short:
                        if self.position:
                            self.position.close()
                        self.sell(size=1)
                elif self.position:
                    self.position.close()

        bt = Backtest(
            bt_df,
            PrecomputedSignalStrategy,
            cash=self.initial_cash,
            commission=self.commission,
            exclusive_orders=True,
            hedging=False,
        )

        stats = bt.run()
        equity_curve = stats["_equity_curve"].copy()

        trimmed_curve = equity_curve.iloc[-len(df) :]
        trimmed_curve.index = df.index[-len(trimmed_curve) :]

        results = df.copy()
        results["equity"] = trimmed_curve["Equity"].values
        results["strategy_returns"] = (
            trimmed_curve["Equity"].pct_change().fillna(0).values
        )
        results["cumulative_returns"] = (
            trimmed_curve["Equity"].div(trimmed_curve["Equity"].iloc[0]).sub(1).values
        )
        if "DrawdownPct" in trimmed_curve.columns:
            results["drawdown"] = trimmed_curve["DrawdownPct"].div(100).values
        else:
            running_max = trimmed_curve["Equity"].cummax()
            results["drawdown"] = (
                trimmed_curve["Equity"] - running_max
            ) / running_max.replace(0, pd.NA)

        self._export_results(results)

        logger.info("Backtest completed; results exported to %s", self.results_path)

        cumulative_return = float(stats.get("Return [%]", 0.0)) / 100.0
        max_drawdown = float(stats.get("Max. Drawdown [%]", 0.0)) / 100.0

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
        output_path: Optional[Union[str, Path]] = None,
    ) -> str:
        """Plot price, moving averages, and buy/sell signals over time.

        Saves the plot under ``reports/`` by default and returns the saved path.
        """
        self._validate_inputs(df)

        output = (
            Path(output_path)
            if output_path is not None
            else Path("reports") / f"{symbol}_backtest.png"
        )
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

        for col in ("open", "high", "low", "volume"):
            if col not in df.columns:
                raise KeyError(f"Column '{col}' not found in DataFrame.")

    def _prepare_backtesting_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare OHLCV data for consumption by ``backtesting.py``."""
        bt_df = pd.DataFrame(
            {
                "Open": df["open"],
                "High": df["high"],
                "Low": df["low"],
                "Close": df[self.price_column],
                "Volume": df["volume"],
            },
            index=df.index,
        )
        return bt_df

    def _export_results(self, results: pd.DataFrame) -> None:
        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        results.to_csv(self.results_path)
