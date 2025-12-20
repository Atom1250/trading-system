"""Stratestic-native implementation of a moving average crossover strategy.

This module lazily imports Stratestic components so the wider application can
start even if the optional dependency is not installed. The underlying
strategy class is constructed on demand when ``build_ma_crossover_strategy``
is invoked.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from typing import TYPE_CHECKING

import pandas as pd

from research.experiments.stratestic_adapter import dataframe_to_stratestic_timeseries

if TYPE_CHECKING:  # pragma: no cover - typing-only import
    from stratestic.data import PriceSeries


@lru_cache(maxsize=1)
def _moving_average_crossover_strategy_class():
    from stratestic.strategy import Strategy

    @dataclass
    class MovingAverageCrossoverStrategy(Strategy):
        """A Stratestic strategy that trades based on a moving average crossover.

        The strategy goes long when the short moving average crosses above the
        long moving average and exits (goes flat) when the short moving average
        crosses below the long moving average.
        """

        short_window: int
        long_window: int

        def __post_init__(self) -> None:
            if self.short_window <= 0:
                raise ValueError("short_window must be a positive integer")

            if self.long_window <= 0:
                raise ValueError("long_window must be a positive integer")

            if self.short_window >= self.long_window:
                raise ValueError("short_window must be less than long_window")

            super().__init__(
                name=f"MA Crossover {self.short_window}/{self.long_window}",
            )

        def generate_signals(self, prices: PriceSeries) -> pd.DataFrame:
            """Generate signals for a given ``PriceSeries``.

            Parameters
            ----------
            prices:
                A Stratestic ``PriceSeries`` instance, typically produced via
                :func:`research.experiments.stratestic_adapter.dataframe_to_stratestic_timeseries`.

            Returns
            -------
            pandas.DataFrame
                DataFrame containing the short/long moving averages alongside the
                position signal (1 for long, 0 for flat).

            """
            closes = prices.close
            short_ma = closes.rolling(
                window=self.short_window,
                min_periods=self.short_window,
            ).mean()
            long_ma = closes.rolling(
                window=self.long_window,
                min_periods=self.long_window,
            ).mean()

            cross_up = (short_ma > long_ma) & (short_ma.shift(1) <= long_ma.shift(1))
            cross_down = (short_ma < long_ma) & (short_ma.shift(1) >= long_ma.shift(1))

            signal = pd.Series(0, index=closes.index, dtype=int)
            signal.loc[cross_up] = 1
            signal.loc[cross_down] = 0
            signal = signal.ffill().fillna(0)

            return pd.DataFrame(
                {
                    "short_ma": short_ma,
                    "long_ma": long_ma,
                    "signal": signal,
                },
            )

        def run(self, prices: PriceSeries) -> pd.DataFrame:
            """Run the strategy on the provided ``PriceSeries`` and return signals."""
            return self.generate_signals(prices)

    return MovingAverageCrossoverStrategy


def build_ma_crossover_strategy(short_window: int, long_window: int):
    """Return an instance of the Stratestic MA crossover strategy configured with the given parameters."""
    strategy_cls = _moving_average_crossover_strategy_class()
    return strategy_cls(short_window=short_window, long_window=long_window)


__all__ = [
    "build_ma_crossover_strategy",
    "dataframe_to_stratestic_timeseries",
]
