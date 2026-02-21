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


def test_market_order_fills_on_next_bar_open():
    symbol = "AAPL"
    idx = pd.date_range("2025-01-01", periods=3, freq="D")
    df = pd.DataFrame(
        {
            "open": [100.0, 110.0, 120.0],
            "high": [101.0, 111.0, 121.0],
            "low": [99.0, 109.0, 119.0],
            "close": [100.0, 110.0, 120.0],
            "volume": [1_000_000, 1_000_000, 1_000_000],
        },
        index=idx,
    )

    runner = StrategyLabBacktestRunner(data_provider=_InMemoryProvider(df, symbol))
    strategy = _FirstBarLongStrategy(StrategyConfig(name="first_bar_long"))
    results = runner.run(
        strategy=strategy,
        start_date=idx.min().to_pydatetime(),
        end_date=idx.max().to_pydatetime(),
        universe=[symbol],
        initial_capital=100_000.0,
    )

    trade_log = results.get_trade_log_df()
    assert len(trade_log) >= 1
    first_trade = trade_log.iloc[0]
    assert pd.Timestamp(first_trade["timestamp"]) == idx[1]
    assert first_trade["price"] == 110.0
