"""Risk management engine.

This module provides the risk management engine that integrates
with RiskConfig and enforces constraints.
"""

from decimal import Decimal
from typing import Optional

from strategy_lab.config import (
    CapitalAllocationMode,
    EntryMode,
    RiskConfig,
    RiskConstraintConfig,
)
from strategy_lab.risk.constraints import (
    PortfolioConstraint,
    PositionConstraint,
    RiskLimitConstraint,
)
from strategy_lab.risk.portfolio_state import (
    PortfolioState,
    PositionSide,
    PositionState,
)


class RiskViolation(Exception):
    """Exception raised when a trade violates risk constraints."""


class RiskEngine:
    """Risk management engine.

    Manages risk constraints, position sizing, and risk monitoring.

    Attributes:
        risk_config: Risk configuration
        risk_constraints: Risk constraint configuration

    """

    def __init__(
        self,
        risk_config: Optional[RiskConfig] = None,
        risk_constraints: Optional[RiskConstraintConfig] = None,
    ):
        """Initialize risk engine.

        Args:
            risk_config: Risk configuration
            risk_constraints: Risk constraint configuration

        """
        self.risk_config = risk_config or RiskConfig()
        self.risk_constraints = risk_constraints or RiskConstraintConfig()

        # Initialize constraint objects
        self.position_constraint = PositionConstraint(
            max_position_size=self.risk_config.max_position_size,
            max_leverage=self.risk_constraints.max_leverage,
            min_liquidity=self.risk_constraints.min_liquidity,
        )

        self.portfolio_constraint = PortfolioConstraint(
            max_total_exposure=1.0,
            max_sector_exposure=self.risk_constraints.max_sector_exposure,
            max_correlation=self.risk_constraints.max_correlation,
            max_concentration=self.risk_constraints.max_concentration,
        )

        # Note: max_drawdown is checked dynamically against portfolio state
        self.risk_limit_constraint = RiskLimitConstraint(
            max_var=0.05,
            max_volatility=self.risk_constraints.max_volatility,
            max_drawdown=self.risk_config.max_drawdown_pct,
            stop_loss_pct=self.risk_config.stop_loss_atr_multiple,
        )

    def _check_entry_mode(
        self,
        symbol: str,
        side: PositionSide,
        portfolio: PortfolioState,
    ) -> None:
        """Check if entry is allowed based on entry mode logic.

        Args:
            symbol: Symbol to trade
            side: Proposed position side
            portfolio: Current portfolio state

        Raises:
            RiskViolation: If entry violates entry mode rules

        """
        # If we already have a position
        if portfolio.has_position(symbol):
            current_pos = portfolio.get_position(symbol)

            # If opposite side, it's a close/reversal, which is generally allowed logic-wise
            # (though strategy usually handles this).
            # If same side, check if pyramiding is allowed.
            if current_pos.side == side:
                if self.risk_config.entry_mode != EntryMode.PYRAMID:
                    raise RiskViolation(
                        f"Pyramiding not allowed (Mode: {self.risk_config.entry_mode})",
                    )

                # Check pyramiding limits if configured
                if self.risk_config.pyramiding_config:
                    # Logic to count entries would require trade history or more state,
                    # for now we assume basic check passed if mode is PYRAMID.
                    pass

    def _check_max_drawdown(self, portfolio: PortfolioState) -> None:
        """Check if portfolio drawdown allows for new trades.

        Args:
            portfolio: Current portfolio state

        Raises:
            RiskViolation: If drawdown exceeds limit

        """
        if (
            float(portfolio.current_drawdown_pct) / 100.0
            > self.risk_config.max_drawdown_pct
        ):
            raise RiskViolation(
                f"Max drawdown exceeded: {portfolio.current_drawdown_pct}% > {self.risk_config.max_drawdown_pct:.1%}",
            )

    def _calc_position_size(
        self,
        price: float,
        atr: float,
        portfolio: PortfolioState,
    ) -> Decimal:
        """Calculate position size based on capital allocation model.

        Args:
            price: Current asset price
            atr: Current ATR
            portfolio: Current portfolio state

        Returns:
            Position size in units (Decimal)

        """
        # Determine base capital for sizing
        if self.risk_config.capital_allocation_mode == CapitalAllocationMode.FIXED:
            capital = float(portfolio.initial_equity)
        else:
            capital = float(portfolio.current_equity)

        # Risk per trade
        risk_amount = capital * self.risk_config.risk_per_trade

        # Stop distance
        stop_distance = atr * self.risk_config.stop_loss_atr_multiple

        if stop_distance == 0:
            return Decimal(0)

        # Raw size = Risk Amount / Stop Distance
        raw_size = risk_amount / stop_distance

        # Cap by max position size (fraction of portfolio)
        max_position_value = capital * self.risk_config.max_position_size
        max_size_by_value = max_position_value / price

        final_size = min(raw_size, max_size_by_value)

        return Decimal(str(final_size))

    def propose_trade(
        self,
        symbol: str,
        side: PositionSide,
        price: float,
        atr: float,
        portfolio: PortfolioState,
        stop_price: Optional[float] = None,
    ) -> PositionState:
        """Propose a trade, validation risk constraints and calculating size.

        Args:
            symbol: Ticker symbol
            side: Direction (LONG/SHORT)
            price: Current price
            atr: Asset volatility (ATR)
            portfolio: Current portfolio state
            stop_price: Manual stop price (optional, overrides internal calc)

        Returns:
            PositionState with calculated size and parameters

        Raises:
            RiskViolation: If trade is rejected

        """
        # 1. Global Portfolio Checks
        self._check_max_drawdown(portfolio)

        # 2. Entry Mode Checks
        self._check_entry_mode(symbol, side, portfolio)

        # 3. Calculate Size
        quantity = self._calc_position_size(price, atr, portfolio)

        if quantity <= 0:
            raise RiskViolation("Calculated position size is zero or negative")

        # 4. Check specific constraints (Liquidity, etc - simplified here)
        # Note: We aren't passing liquidity in propose_trade yet, assume valid for now
        # or rely on pre-filtering.

        # 5. Construct Position State
        # Calculate Stop/TP levels
        _stop_loss = None
        _take_profit = None

        # Stop Loss
        if stop_price:
            _stop_loss = Decimal(str(stop_price))
        elif self.risk_config.stop_loss_pct is not None:
            if side == PositionSide.LONG:
                _stop_loss = Decimal(str(price * (1 - self.risk_config.stop_loss_pct)))
            else:
                _stop_loss = Decimal(str(price * (1 + self.risk_config.stop_loss_pct)))
        else:
            stop_dist = atr * self.risk_config.stop_loss_atr_multiple
            if side == PositionSide.LONG:
                _stop_loss = Decimal(str(price - stop_dist))
            else:
                _stop_loss = Decimal(str(price + stop_dist))

        # Take Profit
        if self.risk_config.take_profit_pct is not None:
            if side == PositionSide.LONG:
                _take_profit = Decimal(
                    str(price * (1 + self.risk_config.take_profit_pct))
                )
            else:
                _take_profit = Decimal(
                    str(price * (1 - self.risk_config.take_profit_pct))
                )
        else:
            tp_dist = atr * self.risk_config.take_profit_atr_multiple
            if side == PositionSide.LONG:
                _take_profit = Decimal(str(price + tp_dist))
            else:
                _take_profit = Decimal(str(price - tp_dist))

        return PositionState(
            symbol=symbol,
            side=side,
            quantity=quantity,
            avg_price=Decimal(str(price)),
            stop_loss_price=_stop_loss,
            take_profit_price=_take_profit,
            entry_timestamp=None,
            last_update_timestamp=None,
        )

    # Legacy methods kept/adapted for compatibility if needed, else can be removed.
    # We'll keep helpers that might be useful.

    def calculate_stop_loss(
        self,
        entry_price: float,
        atr: float,
        direction: int = 1,
    ) -> float:
        """Calculate stop loss price."""
        stop_distance = atr * self.risk_config.stop_loss_atr_multiple
        if direction > 0:  # Long
            return entry_price - stop_distance
        # Short
        return entry_price + stop_distance
