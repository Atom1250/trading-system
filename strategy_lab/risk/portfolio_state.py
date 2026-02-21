"""Portfolio and Position State Management.

This module defines the core state objects that represent the current state
of positions and the overall portfolio during backtesting and live trading.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import Enum
from typing import Optional


class PositionSide(Enum):
    """Position direction."""

    LONG = "long"
    SHORT = "short"


@dataclass
class PositionState:
    """Represents the current state of a single position.

    Attributes:
        symbol: Trading symbol/ticker
        side: Position direction (LONG or SHORT)
        quantity: Number of shares/contracts held
        avg_price: Average entry price
        realized_pnl: Realized profit/loss from closed portions
        unrealized_pnl: Current unrealized profit/loss
        entry_timestamp: When the position was first opened
        last_update_timestamp: Last time the position was modified

    """

    symbol: str
    side: PositionSide
    quantity: Decimal
    avg_price: Decimal
    realized_pnl: Decimal = Decimal(0)
    unrealized_pnl: Decimal = Decimal(0)
    stop_loss_price: Optional[Decimal] = None
    take_profit_price: Optional[Decimal] = None
    entry_timestamp: Optional[int] = None
    last_update_timestamp: Optional[int] = None

    @property
    def market_value(self) -> Decimal:
        """Calculate current market value of the position."""
        return self.quantity * self.avg_price

    @property
    def total_pnl(self) -> Decimal:
        """Calculate total P&L (realized + unrealized)."""
        return self.realized_pnl + self.unrealized_pnl

    def update_unrealized_pnl(self, current_price: Decimal) -> None:
        """Update unrealized P&L based on current market price.

        Args:
            current_price: Current market price of the symbol

        """
        price_diff = current_price - self.avg_price
        if self.side == PositionSide.SHORT:
            price_diff = -price_diff
        self.unrealized_pnl = price_diff * self.quantity


@dataclass
class PortfolioState:
    """Represents the current state of the entire portfolio.

    Attributes:
        initial_equity: Starting capital
        current_equity: Current total equity (cash + positions)
        peak_equity: Highest equity value reached
        max_drawdown_pct: Maximum drawdown percentage from peak
        open_positions: Dictionary of currently open positions by symbol
        cash: Available cash balance
        total_realized_pnl: Cumulative realized P&L across all trades
        total_fees: Cumulative fees paid

    """

    initial_equity: Decimal
    current_equity: Decimal
    peak_equity: Decimal = field(init=False)
    max_drawdown_pct: Decimal = Decimal(0)
    open_positions: dict[str, PositionState] = field(default_factory=dict)
    cash: Decimal = field(init=False)
    total_realized_pnl: Decimal = Decimal(0)
    total_fees: Decimal = Decimal(0)

    def __post_init__(self):
        """Initialize derived fields."""
        if not hasattr(self, "peak_equity") or self.peak_equity is None:
            self.peak_equity = self.initial_equity
        if not hasattr(self, "cash") or self.cash is None:
            self.cash = self.initial_equity

    @property
    def current_drawdown_pct(self) -> Decimal:
        """Calculate current drawdown percentage from peak equity.

        Returns:
            Current drawdown as a percentage (0-100)

        """
        if self.peak_equity == 0:
            return Decimal(0)

        drawdown = (self.peak_equity - self.current_equity) / self.peak_equity * 100
        return max(Decimal(0), drawdown)

    @property
    def total_position_value(self) -> Decimal:
        """Calculate total market value of all open positions."""
        return sum(pos.market_value for pos in self.open_positions.values())

    @property
    def total_unrealized_pnl(self) -> Decimal:
        """Calculate total unrealized P&L across all positions."""
        return sum(pos.unrealized_pnl for pos in self.open_positions.values())

    @property
    def equity_utilization_pct(self) -> Decimal:
        """Calculate percentage of equity currently deployed in positions.

        Returns:
            Utilization percentage (0-100)

        """
        if self.current_equity == 0:
            return Decimal(0)
        return (self.total_position_value / self.current_equity) * 100

    def update_equity(self) -> None:
        """Recalculate current equity based on cash and positions."""
        self.current_equity = (
            self.cash + self.total_position_value + self.total_unrealized_pnl
        )

        # Update peak equity and max drawdown
        self.peak_equity = max(self.peak_equity, self.current_equity)

        current_dd = self.current_drawdown_pct
        self.max_drawdown_pct = max(self.max_drawdown_pct, current_dd)

    def add_position(self, position: PositionState) -> None:
        """Add or update a position in the portfolio.

        Args:
            position: Position to add or update

        """
        self.open_positions[position.symbol] = position

    def remove_position(self, symbol: str) -> Optional[PositionState]:
        """Remove a position from the portfolio.

        Args:
            symbol: Symbol of the position to remove

        Returns:
            The removed position, or None if not found

        """
        return self.open_positions.pop(symbol, None)

    def get_position(self, symbol: str) -> Optional[PositionState]:
        """Get a position by symbol.

        Args:
            symbol: Symbol to look up

        Returns:
            The position if found, None otherwise

        """
        return self.open_positions.get(symbol)

    def has_position(self, symbol: str) -> bool:
        """Check if a position exists for the given symbol.

        Args:
            symbol: Symbol to check

        Returns:
            True if position exists, False otherwise

        """
        return symbol in self.open_positions
