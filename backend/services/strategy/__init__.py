"""Strategy services package.

Avoid importing heavy modules at package import time to make test collection and
lightweight operations (like loading the registry) possible without pulling in
heavy dependencies such as plotting or backtesting libraries.
"""

__all__ = (
    []
)  # Access submodules directly (e.g., `from services.strategy.registry import ...`)
