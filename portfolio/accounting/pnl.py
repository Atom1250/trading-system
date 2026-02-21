"""PnL calculation helper functions."""


def calculate_realized_pnl(
    current_qty: float, avg_cost: float, fill_qty: float, fill_price: float, side: str
) -> float:
    """Calculates realized PnL when closing or reducing a position."""
    if current_qty > 0 and side == "SELL":
        close_qty = min(current_qty, fill_qty)
        return (fill_price - avg_cost) * close_qty
    elif current_qty < 0 and side == "BUY":
        close_qty = min(abs(current_qty), fill_qty)
        return (avg_cost - fill_price) * close_qty
    return 0.0


def calculate_new_avg_cost(
    current_qty: float,
    current_avg_cost: float,
    fill_qty: float,
    fill_price: float,
    side: str,
) -> float:
    """Calculates new average cost basis when adding to a position."""
    fill_signed_qty = fill_qty if side == "BUY" else -fill_qty

    if current_qty == 0:
        return fill_price

    # Same direction (adding to position)
    if (current_qty > 0 and side == "BUY") or (current_qty < 0 and side == "SELL"):
        total_value = (abs(current_qty) * current_avg_cost) + (fill_qty * fill_price)
        total_qty = abs(current_qty) + fill_qty
        return total_value / total_qty

    # Opposite direction (reducing and/or flipping position)
    new_qty = current_qty + fill_signed_qty
    if (current_qty > 0 and new_qty < 0) or (current_qty < 0 and new_qty > 0):
        # Position flipped directions, new average cost is the fill price
        return fill_price

    # Reducing only, average cost unchanged
    return current_avg_cost
