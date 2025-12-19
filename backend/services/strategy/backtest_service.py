"""Backtest service for running strategy backtests."""

from datetime import datetime
from decimal import Decimal
from typing import Any, Optional

import pandas as pd

from services.data.price_service import PriceDataService
from services.strategy.registry import registry
from trading_backtester.backtester import Backtester


class BacktestService:
    """Service for running strategy backtests."""

    def __init__(self):
        self.price_service = PriceDataService()

    def run_backtest(
        self,
        symbol: str,
        strategy_name: str,
        parameters: Optional[dict[str, Any]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        initial_capital: Decimal = Decimal(100000),
        data_source: str = "local",
    ) -> dict[str, Any]:
        """Run a backtest for a strategy.

        Args:
            symbol: Stock symbol
            strategy_name: Name of strategy to run
            parameters: Strategy parameter overrides
            start_date: Backtest start date
            end_date: Backtest end date
            initial_capital: Initial capital
            data_source: Data source to use

        Returns:
            Dictionary with backtest results

        """
        # Get price data
        df = self.price_service.get_prices(
            symbol=symbol, source=data_source, start=start_date, end=end_date,
        )

        if df.empty:
            raise ValueError(
                f"No price data available for {symbol} in the specified date range",
            )

        # Ensure close column exists
        if "close" not in df.columns and "adj_close" in df.columns:
            df["close"] = df["adj_close"]

        if "close" not in df.columns:
            raise ValueError("No 'close' column in price data")

        # Create strategy instance
        strategy = registry.create_strategy(strategy_name, override_params=parameters)

        # Run strategy to generate signals
        df = strategy.run(df)

        # Run backtest
        backtester = Backtester(
            initial_cash=float(initial_capital),
            commission=0.001,  # 0.1% commission
        )

        results = backtester.run(df)

        # Extract metrics
        raw_stats = results.get("stats", {})
        if isinstance(raw_stats, dict):
            stats: dict[str, Any] = raw_stats
        else:
            stats = {}

        metrics = {
            "total_return": Decimal(str(stats.get("Return [%]", 0) / 100))
            if stats.get("Return [%]")
            else Decimal(0),
            "total_return_pct": Decimal(str(stats.get("Return [%]", 0)))
            if stats.get("Return [%]")
            else Decimal(0),
            "sharpe_ratio": Decimal(str(stats.get("Sharpe Ratio", 0)))
            if stats.get("Sharpe Ratio")
            else None,
            "max_drawdown": Decimal(str(abs(stats.get("Max. Drawdown [%]", 0)) / 100))
            if stats.get("Max. Drawdown [%]")
            else Decimal(0),
            "max_drawdown_pct": Decimal(str(abs(stats.get("Max. Drawdown [%]", 0))))
            if stats.get("Max. Drawdown [%]")
            else Decimal(0),
            "win_rate": Decimal(str(stats.get("Win Rate [%]", 0)))
            if stats.get("Win Rate [%]")
            else None,
            "num_trades": int(stats.get("# Trades", 0)) if stats.get("# Trades") else 0,
            "avg_trade": None,  # TODO: Calculate from trades
        }

        # Extract equity curve
        equity_curve = []
        ec = results.get("equity_curve")
        if isinstance(ec, dict) or isinstance(ec, pd.Series):
            for date, value in ec.items():
                equity_curve.append(
                    {
                        "date": date.isoformat()
                        if hasattr(date, "isoformat")
                        else str(date),
                        "value": float(value),
                    },
                )

        # Extract trades
        trades = []
        if "trades" in results:
            trades_df = results["trades"]
            if isinstance(trades_df, pd.DataFrame):
                for _, trade in trades_df.iterrows():
                    trades.append(
                        {
                            "entry_date": str(trade.get("EntryTime", "")),
                            "exit_date": str(trade.get("ExitTime", "")),
                            "entry_price": float(trade.get("EntryPrice", 0)),
                            "exit_price": float(trade.get("ExitPrice", 0)),
                            "pnl": float(trade.get("PnL", 0)),
                            "return_pct": float(trade.get("ReturnPct", 0)),
                        },
                    )

        return {
            "symbol": symbol,
            "strategy_name": strategy_name,
            "metrics": metrics,
            "equity_curve": equity_curve,
            "trades": trades,
            "parameters": parameters or {},
            "executed_at": datetime.now(),
        }


# Global service instance
backtest_service = BacktestService()
