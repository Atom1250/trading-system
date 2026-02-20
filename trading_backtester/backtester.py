"""Backtester that routes execution through ``backtesting.py``."""

from __future__ import annotations

import importlib.machinery
import importlib.util
import logging
import sys
from pathlib import Path

import matplotlib as mpl

mpl.use("Agg")
from typing import TYPE_CHECKING, Any, Optional, Union

if TYPE_CHECKING:
    from collections.abc import Sequence

import matplotlib.pyplot as plt
import pandas as pd

logger = logging.getLogger(__name__)

project_root = Path(__file__).resolve().parent.parent
shadow_dir = project_root / "backtesting"

# Prefer the installed ``backtesting.py`` package by searching site-packages
# explicitly. If a local ``backtesting/`` directory exists, warn but do not
# block imports—restrict the search path to site-packages to avoid shadowing.
site_paths = [p for p in sys.path if "site-packages" in p]
search_paths = site_paths or None

if shadow_dir.exists():
    _warn_msg = (
        "Detected local 'backtesting' directory at %s; will attempt to load the "
        "external package from site-packages to avoid shadowing."
    )
    logger.warning(_warn_msg, shadow_dir)

# Ensure any earlier import of the local ``backtesting`` package does not leak
# into the dependency import below.
sys.modules.pop("backtesting", None)

if not search_paths:
    _msg = (
        "Unable to locate site-packages on sys.path; cannot import "
        "external 'backtesting' dependency."
    )
    raise ImportError(_msg)

module_root = Path(search_paths[0]) / "backtesting"
init_path = module_root / "__init__.py"

if not init_path.exists():
    _msg = (
        "The external 'backtesting' package is required. "
        "Install it with 'pip install backtesting'."
    )
    raise ImportError(_msg)

# Temporarily restrict sys.path to stdlib + site-packages so the external
# dependency is imported instead of the local ``backtesting/`` helper directory.
original_sys_path = sys.path.copy()
stdlib_paths = [
    p for p in original_sys_path if "lib/python" in p and "site-packages" not in p
]
try:
    sys.path = stdlib_paths + search_paths
    _backtesting_spec = importlib.util.spec_from_file_location(
        "backtesting",
        init_path,
        submodule_search_locations=[str(module_root)],
    )
    if _backtesting_spec is None or _backtesting_spec.loader is None:
        _msg = (
            "The external 'backtesting' package is required. "
            "Install it with 'pip install backtesting'."
        )
        raise ImportError(_msg)

    _backtesting_module = importlib.util.module_from_spec(_backtesting_spec)
    if _backtesting_spec.loader is None:
        _msg = "Inconsistency loading backtesting package: loader is missing"
        raise ImportError(_msg)
    _backtesting_spec.loader.exec_module(_backtesting_module)
finally:
    sys.path = original_sys_path
Backtest = _backtesting_module.Backtest

Strategy: Any = _backtesting_module.Strategy


class PrecomputedSignalStrategy(Strategy):  # type: ignore[misc]
    """Strategy that replays precomputed signals for backtesting."""

    signal_values: Sequence[float] = []

    def init(self) -> None:
        """Initialize internal indicator with precomputed signals."""
        self.signal = self.I(lambda: self.signal_values, name="signal")

    def next(self) -> None:
        """Apply the latest signal to manage positions."""
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


class Backtester:
    """Run backtests using the ``backtesting.py`` engine."""

    def __init__(
        self,
        price_column: str = "close",
        signal_column: str = "signal",
        results_path: str | Path = "reports/results.csv",
        initial_cash: float = 100_000.0,
        commission: float = 0.001,  # 0.1% per trade (changed from 0.0)
    ) -> None:
        """Create a Backtester with default configuration values.

        Args:
            price_column: Column name for price data (default: "close")
            signal_column: Column name for strategy signals (default: "signal")
            results_path: Path to save backtest results CSV
            initial_cash: Starting capital for backtest (default: $100,000)
            commission: Commission per trade as a fraction (default: 0.001 = 0.1%)
                       Set to 0.0 for zero-commission backtests (not realistic)
        """
        self.price_column = price_column
        self.signal_column = signal_column
        self.results_path = Path(results_path)
        self.initial_cash = initial_cash
        self.commission = commission

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

        # Set signal values on the strategy class
        # Ensure we copy values to avoid reference issues if run multiple times
        PrecomputedSignalStrategy.signal_values = (
            df[self.signal_column].fillna(0).to_numpy()
        )

        logger.debug("Strategy MRO: %s", PrecomputedSignalStrategy.mro())

        bt_kwargs = {
            "cash": self.initial_cash,
            "commission": self.commission,
            "exclusive_orders": True,
        }

        _version = (
            _backtesting_module.__version__
            if hasattr(_backtesting_module, "__version__")
            else "unknown"
        )
        logger.info("Backtesting version: %s", _version)

        bt = Backtest(bt_df, PrecomputedSignalStrategy, **bt_kwargs)

        stats = bt.run()
        equity_curve = stats["_equity_curve"].copy()

        # Align equity metrics to the input DataFrame length to avoid pandas
        # length-mismatch errors when assigning columns. ``backtesting.py``
        # sometimes returns ``len(df)`` rows (one per bar) and sometimes
        # ``len(df) + 1`` (including a baseline row). Always take the most recent
        # ``len(df)`` values and align them to ``df.index``.
        equity_values = equity_curve["Equity"].to_numpy()
        equity_series = pd.Series(equity_values[-len(df) :], index=df.index)

        strategy_returns = equity_series.pct_change().fillna(0)
        cumulative_returns = equity_series.div(equity_series.iloc[0]).sub(1)

        results = df.copy()
        results["equity"] = equity_series.to_numpy()
        results["strategy_returns"] = strategy_returns.to_numpy()
        results["cumulative_returns"] = cumulative_returns.to_numpy()

        if "DrawdownPct" in equity_curve.columns:
            drawdown_values = equity_curve["DrawdownPct"].to_numpy()[-len(df) :]
            drawdown = pd.Series(drawdown_values, index=df.index).div(100)
        else:
            running_max = equity_series.cummax()
            drawdown = (equity_series - running_max) / running_max.replace(0, pd.NA)
        results["drawdown"] = drawdown.to_numpy()

        self._export_results(results)

        logger.info("Backtest completed; results exported to %s", self.results_path)

        cumulative_return = float(stats.get("Return [%]", 0.0)) / 100.0
        max_drawdown = float(stats.get("Max. Drawdown [%]", 0.0)) / 100.0

        return {
            "results": results,
            "stats": stats,
            "equity_curve": equity_curve["Equity"],  # Return just the Equity series
            "trades": stats["_trades"],
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
        ax.grid(visible=True, linestyle="--", alpha=0.3)

        fig.tight_layout()
        fig.savefig(output, bbox_inches="tight")
        plt.close(fig)

        return str(output)

    def _validate_inputs(self, df: pd.DataFrame) -> None:
        if self.price_column not in df.columns:
            _msg = f"Column '{self.price_column}' not found in DataFrame."
            raise KeyError(_msg)
        if self.signal_column not in df.columns:
            _msg = f"Column '{self.signal_column}' not found in DataFrame."
            raise KeyError(_msg)

        for col in ("open", "high", "low", "volume"):
            if col not in df.columns:
                _msg = f"Column '{col}' not found in DataFrame."
                raise KeyError(_msg)

    def _prepare_backtesting_frame(self, df: pd.DataFrame) -> pd.DataFrame:
        """Prepare OHLCV data for consumption by ``backtesting.py``."""
        return pd.DataFrame(
            {
                "Open": df["open"],
                "High": df["high"],
                "Low": df["low"],
                "Close": df[self.price_column],
                "Volume": df["volume"],
            },
            index=df.index,
        )

    def _export_results(self, results: pd.DataFrame) -> None:
        self.results_path.parent.mkdir(parents=True, exist_ok=True)
        results.to_csv(self.results_path)
