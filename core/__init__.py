"""Core framework-agnostic interfaces."""

from .interfaces import (
    BacktestRunner,
    DataProvider,
    Reporter,
    Strategy,
)

__all__ = [
    'DataProvider',
    'Strategy',
    'BacktestRunner',
    'Reporter',
]
