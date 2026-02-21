"""Performance plotting utilities.

This module provides visualization tools for strategy performance analysis,
including equity curves, drawdowns, and monthly returns heatmaps.
"""

from typing import Any, Optional

import numpy as np
import pandas as pd

try:
    import matplotlib.dates as mdates
    import matplotlib.pyplot as plt
    from matplotlib.figure import Figure
except ImportError:
    plt = None
    Figure = Any


class PerformancePlotter:
    """Class for generating performance plots."""

    def __init__(self, style: str = "seaborn-v0_8-darkgrid"):
        """Initialize plotter.

        Args:
            style: Matplotlib style to use

        """
        self.style = style
        if plt:
            try:
                plt.style.use(style)
            except OSError:
                # Fallback if style not found
                plt.style.use("default")

    def plot_equity_curve(
        self,
        returns: pd.Series,
        benchmark_returns: Optional[pd.Series] = None,
        title: str = "Equity Curve",
    ) -> Optional[Figure]:
        """Plot cumulative equity curve.

        Args:
            returns: Series of period returns
            benchmark_returns: Optional benchmark returns
            title: Plot title

        Returns:
            Matplotlib Figure object

        """
        if plt is None:
            return None

        cum_returns = (1 + returns).cumprod()

        fig, ax = plt.subplots(figsize=(12, 6))
        ax.plot(cum_returns.index, cum_returns.values, label="Strategy", linewidth=2)

        if benchmark_returns is not None:
            cum_bench = (1 + benchmark_returns).cumprod()
            # Align dates
            cum_bench = cum_bench.reindex(cum_returns.index).fillna(method="ffill")
            ax.plot(
                cum_bench.index,
                cum_bench.values,
                label="Benchmark",
                alpha=0.6,
                linestyle="--",
            )

        ax.set_title(title, fontsize=14)
        ax.set_xlabel("Date")
        ax.set_ylabel("Cumulative Return")
        ax.legend(loc="best")
        ax.grid(True, alpha=0.3)

        # Format dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()

        return fig

    def plot_drawdowns(
        self,
        returns: pd.Series,
        title: str = "Drawdown",
    ) -> Optional[Figure]:
        """Plot underwater drawdown chart.

        Args:
            returns: Series of period returns
            title: Plot title

        Returns:
            Matplotlib Figure object

        """
        if plt is None:
            return None

        cum_returns = (1 + returns).cumprod()
        running_max = cum_returns.cummax()
        drawdown = (cum_returns - running_max) / running_max

        fig, ax = plt.subplots(figsize=(12, 4))
        ax.fill_between(drawdown.index, drawdown.values, 0, color="red", alpha=0.3)
        ax.plot(drawdown.index, drawdown.values, color="red", linewidth=1)

        ax.set_title(title, fontsize=14)
        ax.set_xlabel("Date")
        ax.set_ylabel("Drawdown")
        ax.grid(True, alpha=0.3)

        # Format dates
        ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()

        return fig

    def plot_monthly_heatmap(self, returns: pd.Series) -> Optional[Figure]:
        """Plot monthly returns heatmap.

        Args:
            returns: Series of daily returns

        Returns:
            Matplotlib Figure object

        """
        if plt is None:
            return None

        # Resample to monthly returns
        monthly_ret = returns.resample("ME").apply(lambda x: (1 + x).prod() - 1)

        # Create pivot table (Year x Month)
        monthly_ret.index = pd.to_datetime(monthly_ret.index)
        df = pd.DataFrame({"return": monthly_ret.values})
        df["year"] = monthly_ret.index.year
        df["month"] = monthly_ret.index.month

        pivot = df.pivot(index="year", columns="month", values="return")

        fig, ax = plt.subplots(figsize=(10, len(pivot) * 0.5 + 2))
        im = ax.imshow(pivot.values, cmap="RdYlGn", aspect="auto", vmin=-0.1, vmax=0.1)

        # Add labels
        ax.set_xticks(np.arange(len(pivot.columns)))
        ax.set_yticks(np.arange(len(pivot.index)))
        ax.set_xticklabels(pivot.columns)
        ax.set_yticklabels(pivot.index)

        # Add text annotations
        for i in range(len(pivot.index)):
            for j in range(len(pivot.columns)):
                val = pivot.values[i, j]
                if not np.isnan(val):
                    ax.text(
                        j,
                        i,
                        f"{val:.1%}",
                        ha="center",
                        va="center",
                        color="black",
                        fontsize=8,
                    )

        ax.set_title("Monthly Returns", fontsize=14)
        fig.colorbar(im, ax=ax, label="Return")
        fig.tight_layout()

        return fig

    def plot_trade_execution(
        self,
        data: pd.DataFrame,
        trade_log: pd.DataFrame,
        symbol: str = "Asset",
    ) -> Optional[Figure]:
        """Plot OHLCV with signals and trade entry/exit markers.

        Args:
            data: Market data with OHLCV columns
            trade_log: DataFrame of executed trades
            symbol: Asset symbol for the title

        Returns:
            Matplotlib Figure object
        """
        if plt is None:
            return None

        # Create subplots: 2 rows (Price/Trades, Volume)
        fig, (ax1, ax2) = plt.subplots(
            2, 1, figsize=(14, 10), gridspec_kw={"height_ratios": [3, 1]}, sharex=True
        )

        # 1. Plot Price (Close)
        ax1.plot(
            data.index, data["close"], label="Close Price", color="gray", alpha=0.5
        )

        # 2. Plot Trades
        if not trade_log.empty:
            # Entry Markers
            opens = trade_log[trade_log["type"].str.contains("OPEN")]
            closes = trade_log[trade_log["type"].str.contains("CLOSE")]

            for _, trade in opens.iterrows():
                marker = "^" if "BUY" in trade["type"] else "v"
                color = "green" if "BUY" in trade["type"] else "red"
                ax1.scatter(
                    trade["timestamp"],
                    trade["price"],
                    marker=marker,
                    color=color,
                    s=100,
                    label=(
                        "Open"
                        if "Open" not in ax1.get_legend_handles_labels()[1]
                        else ""
                    ),
                )

            for _, trade in closes.iterrows():
                marker = "x"
                color = "black"
                reason = trade.get("reason", "SIGNAL")
                if reason == "SL":
                    color = "darkred"
                elif reason == "TP":
                    color = "darkgreen"

                ax1.scatter(
                    trade["timestamp"],
                    trade["price"],
                    marker=marker,
                    color=color,
                    s=100,
                    label=(
                        "Close"
                        if "Close" not in ax1.get_legend_handles_labels()[1]
                        else ""
                    ),
                )

        ax1.set_title(f"Trade Execution: {symbol}", fontsize=14)
        ax1.set_ylabel("Price")
        ax1.legend(loc="best")
        ax1.grid(True, alpha=0.3)

        # 3. Plot Volume
        colors = [
            "green" if data.loc[dt, "close"] >= data.loc[dt, "open"] else "red"
            for dt in data.index
        ]
        ax2.bar(data.index, data["volume"], color=colors, alpha=0.7)
        ax2.set_ylabel("Volume")
        ax2.grid(True, alpha=0.3)

        # Format dates
        ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d"))
        fig.autofmt_xdate()
        fig.tight_layout()

        return fig
