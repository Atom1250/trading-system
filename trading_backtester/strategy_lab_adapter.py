"""Legacy adapter that routes backtests through Strategy Lab runner."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd

from strategy_lab.backtest.runner import StrategyLabBacktestRunner
from strategy_lab.config import StrategyConfig
from strategy_lab.data.base import MarketDataSlice
from strategy_lab.strategies.base import FactorPanels, MarketDataSlices, Strategy


class _DataFrameHistoryProvider:
    """Historical provider wrapper over an in-memory DataFrame."""

    def __init__(self, symbol: str, df: pd.DataFrame):
        self.symbol = symbol
        self.df = df

    def get_history(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> MarketDataSlice:
        if symbol != self.symbol:
            raise ValueError(f"Unknown symbol '{symbol}' for adapter provider")
        sliced = self.df.loc[(self.df.index >= start) & (self.df.index <= end)]
        return MarketDataSlice(symbol=symbol, df=sliced.copy())


class _PrecomputedSignalStrategy(Strategy):
    """Strategy that replays precomputed signals from input DataFrame."""

    def __init__(self, config: StrategyConfig, signal_column: str):
        super().__init__(config)
        self.signal_column = signal_column

    def generate_signals(
        self,
        data: MarketDataSlices,
        factor_panels: FactorPanels,
    ) -> dict[str, pd.Series]:
        del factor_panels
        out: dict[str, pd.Series] = {}
        for symbol, market_slice in data.items():
            if self.signal_column not in market_slice.df.columns:
                raise KeyError(
                    f"Column '{self.signal_column}' not found in DataFrame.",
                )
            out[symbol] = market_slice.df[self.signal_column].fillna(0).astype(float)
        return out


def run_backtest_via_strategy_lab(
    *,
    df: pd.DataFrame,
    price_column: str,
    signal_column: str,
    results_path: str | Path,
    initial_cash: float,
    commission: float,
) -> dict[str, Any]:
    """Run legacy backtest inputs through Strategy Lab runner."""
    del commission
    symbol = "LEGACY"
    provider = _DataFrameHistoryProvider(symbol=symbol, df=df)
    runner = StrategyLabBacktestRunner(data_provider=provider)
    strategy = _PrecomputedSignalStrategy(
        StrategyConfig(name="legacy_precomputed_signal"),
        signal_column=signal_column,
    )
    start = df.index.min().to_pydatetime()
    end = df.index.max().to_pydatetime()
    backtest_results = runner.run(
        strategy=strategy,
        start_date=start,
        end_date=end,
        universe=[symbol],
        initial_capital=initial_cash,
    )

    equity_series = backtest_results.get_equity_curve(initial_capital=initial_cash)
    strategy_returns = equity_series.pct_change().fillna(0)
    cumulative_returns = equity_series.div(equity_series.iloc[0]).sub(1)

    results = df.copy()
    results["equity"] = equity_series.reindex(df.index).to_numpy()
    results["strategy_returns"] = strategy_returns.reindex(df.index).to_numpy()
    results["cumulative_returns"] = cumulative_returns.reindex(df.index).to_numpy()
    if (
        backtest_results.portfolio_history is not None
        and "drawdown" in backtest_results.portfolio_history
    ):
        drawdown = (
            backtest_results.portfolio_history["drawdown"].reindex(df.index).fillna(0)
            / 100.0
        )
        results["drawdown"] = drawdown.to_numpy()
    else:
        running_max = equity_series.cummax()
        drawdown = (equity_series - running_max) / running_max.replace(0, pd.NA)
        results["drawdown"] = drawdown.reindex(df.index).to_numpy()

    out_path = Path(results_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    results.to_csv(out_path)

    metrics = backtest_results.get_metrics()
    trade_log = backtest_results.get_trade_log_df()
    num_trades = (
        int((trade_log["type"] == "STOP_EXIT").sum()) if not trade_log.empty else 0
    )
    wins = (
        int((trade_log["pnl"] > 0).sum())
        if not trade_log.empty and "pnl" in trade_log
        else 0
    )
    win_rate = (wins / num_trades * 100.0) if num_trades > 0 else 0.0

    stats = {
        "Return [%]": float(metrics.get("total_return", 0.0) * 100.0),
        "Max. Drawdown [%]": float(metrics.get("max_drawdown", 0.0) * 100.0),
        "# Trades": num_trades,
        "Win Rate [%]": win_rate,
        "Sharpe Ratio": float(metrics.get("sharpe_ratio", 0.0)),
    }

    return {
        "results": results,
        "stats": stats,
        "equity_curve": equity_series,
        "trades": pd.DataFrame(),
        "cumulative_return": float(metrics.get("total_return", 0.0)),
        "max_drawdown": float(metrics.get("max_drawdown", 0.0)),
        "results_path": str(out_path),
    }
