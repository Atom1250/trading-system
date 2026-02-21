"""Canonical Strategy Lab backtest runner entrypoint."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

import pandas as pd

from backend.db.database import SessionLocal
from portfolio.ledger.repo import append_trade
from portfolio.ledger.schemas import TradeEvent
from strategy_lab.backtest.results import BacktestResults
from strategy_lab.core.types import ExecutionStatus, OrderIntent, OrderSide, OrderType
from strategy_lab.data.base import HistoricalDataProvider, MarketDataSlice
from strategy_lab.execution.backtest_engine import BacktestExecutionEngine
from strategy_lab.factors.base import FactorRegistry
from strategy_lab.risk.engine import RiskEngine, RiskViolation
from strategy_lab.risk.portfolio_state import PortfolioState, PositionSide
from strategy_lab.sentiment.pipeline import SentimentPipeline
from strategy_lab.strategies.base import Strategy


class StrategyLabBacktestRunner:
    """Single canonical entrypoint for Strategy Lab backtests."""

    def __init__(
        self,
        data_provider: HistoricalDataProvider,
        risk_engine: Optional[RiskEngine] = None,
        factor_registry: Optional[FactorRegistry] = None,
        sentiment_pipeline: Optional[SentimentPipeline] = None,
    ):
        self.data_provider = data_provider
        self.risk_engine = risk_engine or RiskEngine()
        self.factor_registry = factor_registry
        self.sentiment_pipeline = sentiment_pipeline
        self.execution_engine = BacktestExecutionEngine()

    def run(
        self,
        strategy: Strategy,
        start_date: datetime,
        end_date: datetime,
        universe: list[str],
        initial_capital: float = 100000.0,
    ) -> BacktestResults:
        market_data = self._load_market_data(
            universe=universe,
            start_date=start_date,
            end_date=end_date,
        )
        all_timestamps = sorted(
            list(set().union(*[d.df.index for d in market_data.values()]))
        )
        factor_panels = self._compute_factors(strategy, market_data)
        raw_signals = strategy.generate_signals(market_data, factor_panels)

        portfolio = PortfolioState(
            initial_equity=Decimal(str(initial_capital)),
            current_equity=Decimal(str(initial_capital)),
        )

        run_id = str(uuid.uuid4())
        db = SessionLocal()

        trade_log: list[dict] = []
        equity_curve: list[dict] = []
        returns: list[float] = []
        prev_equity = portfolio.current_equity

        for timestamp in all_timestamps:
            for symbol in sorted(universe):
                market_slice = market_data.get(symbol)
                if market_slice is None or timestamp not in market_slice.df.index:
                    continue
                bar = market_slice.df.loc[timestamp]
                reports = self.execution_engine.on_bar(
                    symbol=symbol,
                    timestamp=timestamp,
                    open_price=float(bar["open"]),
                    high_price=float(bar["high"]),
                    low_price=float(bar["low"]),
                    close_price=float(bar["close"]),
                    portfolio=portfolio,
                )
                self._append_execution_reports(
                    trade_log=trade_log,
                    reports=reports,
                    portfolio=portfolio,
                    timestamp=timestamp,
                    run_id=run_id,
                    strategy_id=strategy.name,
                    db=db,
                )
                self._handle_signal_for_symbol(
                    strategy=strategy,
                    symbol=symbol,
                    timestamp=timestamp,
                    bar=bar,
                    raw_signals=raw_signals,
                    portfolio=portfolio,
                )

            equity_curve.append(
                {
                    "timestamp": timestamp,
                    "equity": float(portfolio.current_equity),
                    "drawdown": float(portfolio.current_drawdown_pct),
                },
            )
            current_ret = (
                (portfolio.current_equity - prev_equity) / prev_equity
                if prev_equity > 0
                else 0
            )
            returns.append(float(current_ret))
            prev_equity = portfolio.current_equity

        db.close()

        return BacktestResults(
            strategy_name=strategy.name,
            signals=pd.Series(),
            returns=pd.Series(index=all_timestamps, data=returns),
            data=market_data[universe[0]].df if universe else pd.DataFrame(),
            config=strategy.config,
            trade_log=pd.DataFrame(trade_log),
            portfolio_history=pd.DataFrame(equity_curve).set_index("timestamp"),
        )

    def _load_market_data(
        self,
        *,
        universe: list[str],
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, MarketDataSlice]:
        market_data: dict[str, MarketDataSlice] = {}
        for symbol in universe:
            market_data[symbol] = self.data_provider.get_history(
                symbol, start_date, end_date
            )
        if not market_data:
            raise ValueError("No data found for universe")
        return market_data

    @staticmethod
    def _compute_factors(
        strategy: Strategy,
        market_data: dict[str, MarketDataSlice],
    ) -> dict[str, pd.DataFrame]:
        del strategy
        return {
            symbol: pd.DataFrame(index=data.df.index)
            for symbol, data in market_data.items()
        }

    def _handle_signal_for_symbol(
        self,
        *,
        strategy: Strategy,
        symbol: str,
        timestamp,
        bar: pd.Series,
        raw_signals: dict[str, pd.Series],
        portfolio: PortfolioState,
    ) -> None:
        signal_series = raw_signals.get(symbol)
        if signal_series is None or timestamp not in signal_series.index:
            return
        signal_val = signal_series.loc[timestamp]
        if signal_val == 0 or pd.isna(signal_val):
            return
        if portfolio.has_position(symbol):
            return

        side = PositionSide.LONG if signal_val > 0 else PositionSide.SHORT
        price = float(bar["close"])
        atr = price * 0.01
        try:
            proposed_position = self.risk_engine.propose_trade(
                symbol=symbol,
                side=side,
                price=price,
                atr=atr,
                portfolio=portfolio,
            )
        except RiskViolation:
            return

        stop_price = self.risk_engine.calculate_stop_loss(
            entry_price=price,
            atr=atr,
            direction=1 if side == PositionSide.LONG else -1,
        )
        order_intent = OrderIntent(
            symbol=symbol,
            side=OrderSide.BUY if side == PositionSide.LONG else OrderSide.SELL,
            order_type=OrderType.MARKET,
            quantity=float(proposed_position.quantity),
            timestamp=self._to_datetime(timestamp),
            stop_price=float(stop_price),
            metadata={
                "strategy": strategy.name,
                "submission_price": price,
            },
        )
        self.execution_engine.submit_order_intent(order_intent)

    @staticmethod
    def _append_execution_reports(
        *,
        trade_log: list[dict],
        reports,
        portfolio: PortfolioState,
        timestamp,
        run_id: str,
        strategy_id: str,
        db,
    ) -> None:
        for report in reports:
            if report.status != ExecutionStatus.FILLED:
                continue

            pnl = 0.0
            trade_type = "BUY_OPEN" if report.side == OrderSide.BUY else "SELL_OPEN"
            if report.order_type == OrderType.STOP:
                trade_type = "STOP_EXIT"
            if report.order_type == OrderType.STOP:
                pnl = float(portfolio.total_realized_pnl)
            trade_log.append(
                {
                    "timestamp": timestamp,
                    "symbol": report.symbol,
                    "type": trade_type,
                    "price": (
                        float(report.avg_fill_price) if report.avg_fill_price else 0.0
                    ),
                    "quantity": float(report.filled_quantity),
                    "pnl": pnl,
                },
            )

            # Post to ledger module
            side_str = "BUY" if report.side == OrderSide.BUY else "SELL"
            trade_event = TradeEvent(
                timestamp=timestamp,
                symbol=report.symbol,
                side=side_str,
                quantity=float(report.filled_quantity),
                price=float(report.avg_fill_price) if report.avg_fill_price else 0.0,
                commission=0.0,
                slippage=0.0,
                strategy_id=strategy_id,
                run_id=run_id,
                execution_venue="BACKTEST",
                meta_data=(
                    {"fill_rule": report.metadata.get("fill_rule", "unknown")}
                    if report.metadata
                    else None
                ),
            )
            append_trade(db, trade_event)

    @staticmethod
    def _to_datetime(timestamp) -> datetime:
        if isinstance(timestamp, datetime):
            return timestamp
        return timestamp.to_pydatetime()


def run_backtest(
    strategy: Strategy,
    data_provider: HistoricalDataProvider,
    start_date: datetime,
    end_date: datetime,
    universe: list[str],
    initial_capital: float = 100000.0,
    risk_engine: Optional[RiskEngine] = None,
    factor_registry: Optional[FactorRegistry] = None,
    sentiment_pipeline: Optional[SentimentPipeline] = None,
) -> BacktestResults:
    """Functional helper for one-off canonical Strategy Lab backtests."""
    runner = StrategyLabBacktestRunner(
        data_provider=data_provider,
        risk_engine=risk_engine,
        factor_registry=factor_registry,
        sentiment_pipeline=sentiment_pipeline,
    )
    return runner.run(
        strategy=strategy,
        start_date=start_date,
        end_date=end_date,
        universe=universe,
        initial_capital=initial_capital,
    )
