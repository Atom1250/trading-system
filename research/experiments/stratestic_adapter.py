"""Adapters for converting local market data into Stratestic-friendly formats."""

from __future__ import annotations


import pandas as pd
from stratestic.data import PriceSeries


_REQUIRED_COLUMNS: set[str] = {"open", "high", "low", "close", "volume"}


def _validate_ohlcv_dataframe(df: pd.DataFrame) -> None:
    missing: set[str] = _REQUIRED_COLUMNS.difference(df.columns)
    if missing:
        raise ValueError(f"DataFrame is missing required OHLCV columns: {sorted(missing)}")

    if not isinstance(df.index, pd.DatetimeIndex):
        raise TypeError("DataFrame index must be a pandas.DatetimeIndex")


def dataframe_to_stratestic_timeseries(df: pd.DataFrame) -> PriceSeries:
    """
    Convert an OHLCV ``DataFrame`` into Stratestic's canonical :class:`~stratestic.data.PriceSeries`.

    The incoming frame is expected to have a :class:`~pandas.DatetimeIndex` and at least the
    ``open``, ``high``, ``low``, ``close``, and ``volume`` columns. Data is sorted by index and
    forwarded to Stratestic's factory for building a price/volume time series.

    Parameters
    ----------
    df: pd.DataFrame
        Source OHLCV data with a datetime index and the required price/volume columns.

    Returns
    -------
    PriceSeries
        A Stratestic ``PriceSeries`` instance representing the same OHLCV history.
    """

    _validate_ohlcv_dataframe(df)

    normalized = df.loc[:, _REQUIRED_COLUMNS].sort_index()
    return PriceSeries.from_ohlcv(
        open=normalized["open"],
        high=normalized["high"],
        low=normalized["low"],
        close=normalized["close"],
        volume=normalized["volume"],
        index=normalized.index,
    )
