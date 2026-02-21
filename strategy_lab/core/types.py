"""Canonical domain contracts for Strategy Lab."""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Optional


class SignalType(str, Enum):
    """Canonical signal direction/type."""

    LONG = "long"
    SHORT = "short"
    FLAT = "flat"
    CLOSE = "close"


class OrderSide(str, Enum):
    """Order side."""

    BUY = "buy"
    SELL = "sell"


class OrderType(str, Enum):
    """Order type."""

    MARKET = "market"
    LIMIT = "limit"
    STOP = "stop"


class ExecutionStatus(str, Enum):
    """Execution status for an order attempt."""

    FILLED = "filled"
    REJECTED = "rejected"
    PARTIAL = "partial"
    PENDING = "pending"
    CANCELLED = "cancelled"


@dataclass
class Signal:
    """Strategy signal emitted before risk evaluation."""

    symbol: str
    signal_type: SignalType
    timestamp: datetime
    strength: float = 1.0
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate signal strength bounds."""
        if not 0 <= self.strength <= 1:
            raise ValueError(
                f"Signal strength must be between 0 and 1, got {self.strength}",
            )


@dataclass
class RiskViolation:
    """Structured risk rejection payload."""

    code: str
    message: str
    details: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderIntent:
    """Risk-approved order intent forwarded to execution engine."""

    symbol: str
    side: OrderSide
    order_type: OrderType
    quantity: float
    timestamp: datetime
    limit_price: Optional[float] = None
    stop_price: Optional[float] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate order quantity."""
        if self.quantity <= 0:
            raise ValueError(f"Order quantity must be positive, got {self.quantity}")


@dataclass
class RiskDecision:
    """Output contract from risk engine."""

    approved: bool
    order_intent: Optional[OrderIntent] = None
    violation: Optional[RiskViolation] = None

    def __post_init__(self) -> None:
        """Ensure valid mutually exclusive decision shape."""
        if self.approved and self.order_intent is None:
            raise ValueError("approved=True requires order_intent")
        if not self.approved and self.violation is None:
            raise ValueError("approved=False requires violation")
        if self.order_intent is not None and self.violation is not None:
            raise ValueError("order_intent and violation cannot both be set")


@dataclass
class ExecutionReport:
    """Execution engine result contract."""

    status: ExecutionStatus
    symbol: str
    side: OrderSide
    order_type: OrderType
    requested_quantity: float
    filled_quantity: float
    submitted_at: datetime
    filled_at: Optional[datetime] = None
    avg_fill_price: Optional[float] = None
    rejection_reason: Optional[str] = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self) -> None:
        """Validate fill quantities."""
        if self.requested_quantity <= 0:
            raise ValueError("requested_quantity must be positive")
        if self.filled_quantity < 0:
            raise ValueError("filled_quantity cannot be negative")
        if self.filled_quantity > self.requested_quantity:
            raise ValueError("filled_quantity cannot exceed requested_quantity")
