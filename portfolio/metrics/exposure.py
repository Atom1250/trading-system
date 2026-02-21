"""Exposure metric calculations."""

from portfolio.accounting.schemas import PortfolioSnapshot

from .schemas import ExposureMetrics


def calculate_snapshot_exposure(snapshot: PortfolioSnapshot) -> ExposureMetrics:
    """Calculates exposure metrics for a single snapshot in time."""
    long_exp = 0.0
    short_exp = 0.0

    for symbol, pos in snapshot.positions.items():
        val = pos.quantity * pos.market_price
        if pos.quantity > 0:
            long_exp += val
        else:
            # val is negative for shorts, we want absolute exposure
            short_exp += abs(val)

    gross_exp = long_exp + short_exp
    net_exp = long_exp - short_exp

    concentration = {}
    if gross_exp > 0:
        for symbol, pos in snapshot.positions.items():
            val = abs(pos.quantity * pos.market_price)
            concentration[symbol] = val / gross_exp

    return ExposureMetrics(
        timestamp=snapshot.timestamp,
        gross_exposure=gross_exp,
        net_exposure=net_exp,
        long_exposure=long_exp,
        short_exposure=short_exp,
        concentration=concentration,
    )
