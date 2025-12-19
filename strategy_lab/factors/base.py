"""Base classes for strategy factors."""

from abc import ABC, abstractmethod
from typing import Optional

from strategy_lab.data.base import MarketDataSlice


class Factor(ABC):
    """Abstract base class for all alpha factors."""

    @abstractmethod
    def compute(self, data: MarketDataSlice) -> float:
        """Compute the factor value given a slice of market data.

        Args:
            data: Market data slice containing price/volume history

        Returns:
            float: Factor value (signal strength, binary signal, etc.)

        """


class FactorRegistry:
    """Registry for managing available factors."""

    _factors: dict[str, type[Factor]] = {}

    @classmethod
    def register(cls, name: str):
        """Decorator to register a factor class.

        Args:
            name: Unique name for the factor

        """

        def decorator(factor_cls: type[Factor]):
            cls._factors[name] = factor_cls
            return factor_cls

        return decorator

    @classmethod
    def get(cls, name: str) -> Optional[type[Factor]]:
        """Retrieve a factor class by name.

        Args:
            name: Name of the factor to retrieve

        Returns:
            Type[Factor] or None if not found

        """
        return cls._factors.get(name)

    @classmethod
    def list_factors(cls) -> list[str]:
        """List all registered factors."""
        return list(cls._factors.keys())
