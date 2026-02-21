from __future__ import annotations

from datetime import datetime

import pandas as pd

from strategy_lab.backtest.runner import StrategyLabBacktestRunner
from strategy_lab.config import StrategyConfig
from strategy_lab.data.base import MarketDataSlice
from strategy_lab.strategies.base import FactorPanels, MarketDataSlices, Strategy


class _InMemoryProvider:
    def __init__(self, df: pd.DataFrame, symbol: str):
        self._df = df
        self._symbol = symbol

    def get_history(
        self, symbol: str, start: datetime, end: datetime
    ) -> MarketDataSlice:
        assert symbol == self._symbol
        data = self._df.loc[(self._df.index >= start) & (self._df.index <= end)]
        return MarketDataSlice(symbol=symbol, df=data.copy())


class _FirstBarLongStrategy(Strategy):
    def generate_signals(
        self,
        data: MarketDataSlices,
        factor_panels: FactorPanels,
    ) -> dict[str, pd.Series]:
        del factor_panels
        out: dict[str, pd.Series] = {}
        for symbol, market_slice in data.items():
            s = pd.Series(0.0, index=market_slice.df.index)
            s.iloc[0] = 1.0
            out[symbol] = s
        return out


def test_stop_loss_triggers_intrabar_and_fills_at_stop_price():
    symbol = "AAPL"
    idx = pd.date_range("2025-01-01", periods=4, freq="D")
    df = pd.DataFrame(
        {
            "open": [100.0, 100.0, 99.0, 101.0],
            "high": [101.0, 101.0, 100.0, 102.0],
            "low": [99.0, 98.0, 97.0, 100.0],
            "close": [100.0, 100.0, 99.0, 101.0],
            "volume": [1_000_000, 1_000_000, 1_000_000, 1_000_000],
        },
        index=idx,
    )

    runner = StrategyLabBacktestRunner(data_provider=_InMemoryProvider(df, symbol))
    strategy = _FirstBarLongStrategy(StrategyConfig(name="stop_test"))
    results = runner.run(
        strategy=strategy,
        start_date=idx.min().to_pydatetime(),
        end_date=idx.max().to_pydatetime(),
        universe=[symbol],
        initial_capital=100_000.0,
    )

    trade_log = results.get_trade_log_df()
    assert len(trade_log) >= 2
    stop_row = trade_log[trade_log["type"] == "STOP_EXIT"].iloc[0]

    # For entry price 100 and ATR fallback 1% (1.0), stop is 100 - 1.5 = 98.5
    assert pd.Timestamp(stop_row["timestamp"]) == idx[1]
    assert stop_row["price"] == 98.5
