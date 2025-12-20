"""Backtesting engine.

This module provides the backtesting engine that orchestrates the
interaction between Data, Factors, Strategy, and Risk Management
modules.
"""

import os
import sys
from datetime import datetime
from decimal import Decimal
from typing import Optional

import pandas as pd

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from strategy_lab.backtest.results import BacktestResults
from strategy_lab.data.base import HistoricalDataProvider, MarketDataSlice
from strategy_lab.factors.base import FactorRegistry
from strategy_lab.risk.engine import RiskEngine, RiskViolation
from strategy_lab.risk.portfolio_state import (
    PortfolioState,
    PositionSide,
    PositionState,
)
from strategy_lab.sentiment.pipeline import SentimentPipeline
from strategy_lab.strategies.base import Strategy


class StrategyBacktestEngine:
    """Event-driven backtesting engine.

    Orchestrates the backtest by determining timeline, fetching data,
    computing factors, running the strategy, and simulating execution
    through the Risk Engine.

    Attributes:
        data_provider: Source of historical market data
        factor_registry: Registry of available factors
        risk_engine: Risk management engine
        sentiment_pipeline: Optional sentiment analysis pipeline

    """

    def __init__(
        self,
        data_provider: HistoricalDataProvider,
        risk_engine: RiskEngine,
        factor_registry: Optional[FactorRegistry] = None,
        sentiment_pipeline: Optional[SentimentPipeline] = None,
    ):
        """Initialize backtest engine.

        Args:
            data_provider: Data provider instance
            risk_engine: Risk engine instance
            factor_registry: Factor registry (optional, uses global if None)
            sentiment_pipeline: Sentiment pipeline (optional)

        """
        self.data_provider = data_provider
        self.risk_engine = risk_engine
        self.factor_registry = (
            factor_registry  # Using global registry mostly, but kept for DI
        )
        self.sentiment_pipeline = sentiment_pipeline

    def run(
        self,
        strategy: Strategy,
        start_date: datetime,
        end_date: datetime,
        universe: list[str],
        initial_capital: float = 100000.0,
        **kwargs,
    ) -> BacktestResults:
        """Run backtest simulation.

        Args:
            strategy: Strategy instance to test
            start_date: Backtest start
            end_date: Backtest end
            universe: List of symbols to trade
            initial_capital: Starting equity
            **kwargs: Additional parameters

        Returns:
            BacktestResults object

        """
        print(f"Starting backtest for {strategy.name} from {start_date} to {end_date}")

        # 1. Fetch Data
        print("Fetching historical data...")
        market_data: dict[str, MarketDataSlice] = {}
        for symbol in universe:
            market_data[symbol] = self.data_provider.get_history(
                symbol,
                start_date,
                end_date,
            )

        if not market_data:
            raise ValueError("No data found for universe")

        # Combine timeline (union of all timestamps)
        all_timestamps = sorted(
            list(set().union(*[d.df.index for d in market_data.values()])),
        )

        # 2. Compute Factors (Pre-computation)
        print("Pre-computing factors...")
        factor_panels: dict[str, pd.DataFrame] = self._compute_factors(
            strategy,
            market_data,
        )

        # 3. Generate Strategy Signals (Vectorised)
        print("Generating strategy signals...")
        raw_signals = strategy.generate_signals(market_data, factor_panels)

        # 4. Event-Driven Execution Loop
        print("Running execution loop...")

        # Initialize State
        portfolio = PortfolioState(
            initial_equity=Decimal(str(initial_capital)),
            current_equity=Decimal(str(initial_capital)),
        )

        trade_log = []
        equity_curve = []
        returns_series = []

        # To calculate returns, we need previous equity
        prev_equity = portfolio.current_equity

        for timestamp in all_timestamps:
            # A. Mark to Market
            self._update_portfolio_valuation(portfolio, market_data, timestamp)

            # Record Equity
            equity_curve.append(
                {
                    "timestamp": timestamp,
                    "equity": float(portfolio.current_equity),
                    "drawdown": float(portfolio.current_drawdown_pct),
                },
            )

            # Calculate daily return (simplified, assuming daily steps)
            current_ret = (
                (portfolio.current_equity - prev_equity) / prev_equity
                if prev_equity > 0
                else 0
            )
            returns_series.append(float(current_ret))
            prev_equity = portfolio.current_equity

            # B. Process Signals
            signals_at_time = self._get_signals_at_timestamp(raw_signals, timestamp)

            for symbol, signal_val in signals_at_time.items():
                if signal_val == 0:
                    continue

                # Get current price
                if (
                    symbol not in market_data
                    or timestamp not in market_data[symbol].df.index
                ):
                    continue

                bar = market_data[symbol].df.loc[timestamp]
                price = float(bar["close"])

                # Approximate ATR if not available (requires full calc in reality)
                # Here we assume ATR is passed or calculated.
                # For this implementation, we'll estimate or use a factor if present.
                # FALLBACK: 1% of price if no ATR factor
                atr = price * 0.01

                # Determine Side and Intent
                side = PositionSide.LONG if signal_val > 0 else PositionSide.SHORT

                # Check for Close logic:
                # If we have a LONG position and signal is SHORT (flip) or 0 (flat - explicitly handled if signal_val was 0)
                # Here simplified: If signal direction opposite to position, close first.

                if portfolio.has_position(symbol):
                    pos = portfolio.get_position(symbol)
                    if (pos.side == PositionSide.LONG and signal_val < 0) or (
                        pos.side == PositionSide.SHORT and signal_val > 0
                    ):
                        # Close existing
                        self._execute_close(
                            portfolio,
                            symbol,
                            price,
                            timestamp,
                            trade_log,
                        )
                # If not just a close, try to open/flip
                # Note: If we just closed, we might want to open the new side immediately

                try:
                    # C. Risk Engine Proposal
                    # Only propose if we don't have a position (or if pyramiding, which risk engine handles)
                    # If we just closed, we can open new.
                    if not portfolio.has_position(symbol):
                        # Calc Position Size
                        proposed_pos = self.risk_engine.propose_trade(
                            symbol=symbol,
                            side=side,
                            price=price,
                            atr=atr,
                            portfolio=portfolio,
                        )

                        # D. Execute Trade
                        self._execute_open(
                            portfolio,
                            proposed_pos,
                            price,
                            timestamp,
                            trade_log,
                        )

                except RiskViolation:
                    # Log rejection?
                    # print(f"Trade rejected for {symbol} at {timestamp}: {e}")
                    pass

        # 5. Compile Results
        results_df = pd.DataFrame(equity_curve).set_index("timestamp")
        returns_s = pd.Series(index=all_timestamps, data=returns_series)

        # Flatten raw signals for compatibility with Results object (just taking one symbol or aggregating?)
        # Results expects `signals` as a Series. If multi-asset, this is complex.
        # We will create a representative signal series (e.g. combined) or just store the primary one if single asset.

        # For multi-asset support in Results, we might need to adjust.
        # For now, let's create a dummy combined signal series or leave empty if not strictly required by metrics.
        # We supply the explicit `trade_log` which we added support for.

        return BacktestResults(
            strategy_name=strategy.name,
            signals=pd.Series(),  # Placeholder, relying on trade_log
            returns=returns_s,
            data=market_data[universe[0]].df if universe else pd.DataFrame(),
            config=strategy.config,
            trade_log=pd.DataFrame(trade_log),
            portfolio_history=results_df,
        )

    def _compute_factors(
        self,
        strategy: Strategy,
        market_data: dict[str, MarketDataSlice],
    ) -> dict[str, pd.DataFrame]:
        """Compute factors for the universe.

        Note: ideally this would be done by the strategy asking for specific factors,
        but here we assume standard factors or configured ones.
        """
        panels = {}
        for symbol, data in market_data.items():
            # Placeholder: Create a DataFrame for factors
            # In a real impl, we'd iterate FactorRegistry or strategy requirements
            panels[symbol] = pd.DataFrame(index=data.df.index)
        return panels

    def _get_signals_at_timestamp(
        self,
        raw_signals: dict[str, pd.Series],
        timestamp,
    ) -> dict[str, float]:
        """Extract signals for a specific timestamp."""
        current_signals = {}
        for symbol, signal_series in raw_signals.items():
            if timestamp in signal_series.index:
                val = signal_series.loc[timestamp]
                if val != 0 and not pd.isna(val):
                    current_signals[symbol] = val
        return current_signals

    def _update_portfolio_valuation(
        self,
        portfolio: PortfolioState,
        market_data: dict[str, MarketDataSlice],
        timestamp,
    ):
        """Mark to market all open positions."""
        for symbol, pos in portfolio.open_positions.items():
            if symbol in market_data and timestamp in market_data[symbol].df.index:
                current_price = Decimal(
                    str(market_data[symbol].df.loc[timestamp, "close"]),
                )
                pos.update_unrealized_pnl(current_price)

        portfolio.update_equity()

    def _execute_open(
        self,
        portfolio: PortfolioState,
        position: PositionState,
        price: float,
        timestamp,
        trade_log: list,
    ):
        """Execute trade to open position."""
        cost = position.quantity * position.avg_price

        # Deduct cash (assuming fully funded)
        portfolio.cash -= cost
        # Add position
        position.entry_timestamp = timestamp.timestamp()  # Store as float/int
        portfolio.add_position(position)

        trade_log.append(
            {
                "timestamp": timestamp,
                "symbol": position.symbol,
                "type": (
                    "BUY_OPEN" if position.side == PositionSide.LONG else "SELL_OPEN"
                ),
                "price": price,
                "quantity": float(position.quantity),
                "pnl": 0.0,
            },
        )

    def _execute_close(
        self,
        portfolio: PortfolioState,
        symbol: str,
        price: float,
        timestamp,
        trade_log: list,
    ):
        """Execute trade to close position."""
        pos = portfolio.remove_position(symbol)
        if not pos:
            return

        exit_price = Decimal(str(price))

        # Calculate PnL
        if pos.side == PositionSide.LONG:
            pnl = (exit_price - pos.avg_price) * pos.quantity
            returned_capital = pos.quantity * exit_price
        else:
            pnl = (pos.avg_price - exit_price) * pos.quantity
            returned_capital = pos.quantity * (
                2 * pos.avg_price - exit_price
            )  # Crude approx for short margin return
            # Correct cash flow for short:
            # Initial: Cash - (Price * Q) [Collateral set aside]
            # Exit: Cash + (Price * Q) + PnL
            # Here simplified: Cash was reduced by value. Now add back value + pnl.
            returned_capital = (pos.quantity * pos.avg_price) + pnl

        portfolio.cash += returned_capital
        portfolio.total_realized_pnl += pnl

        trade_log.append(
            {
                "timestamp": timestamp,
                "symbol": symbol,
                "type": "SELL_CLOSE" if pos.side == PositionSide.LONG else "BUY_CLOSE",
                "price": float(price),
                "quantity": float(pos.quantity),
                "pnl": float(pnl),
            },
        )
