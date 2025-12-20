import os
import sys
import unittest
from decimal import Decimal

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from strategy_lab.config import CapitalAllocationMode, RiskConfig
from strategy_lab.risk.engine import RiskEngine, RiskViolation
from strategy_lab.risk.portfolio_state import (
    PortfolioState,
    PositionSide,
    PositionState,
)


class TestRiskEngine(unittest.TestCase):
    def setUp(self):
        # Default Config: 100k, 1% risk per trade, Stop=2ATR, Max DD=20%
        self.risk_config = RiskConfig(
            risk_per_trade=0.01,
            stop_loss_atr_multiple=2.0,
            max_drawdown_pct=0.20,
            capital_allocation_mode=CapitalAllocationMode.FIXED,  # Fixed 100k basis
            max_position_size=1.0,  # Allow large positions for testing
        )
        self.engine = RiskEngine(risk_config=self.risk_config)

        self.portfolio = PortfolioState(
            initial_equity=Decimal(100000),
            current_equity=Decimal(100000),
        )

    def test_position_sizing_fixed(self):
        """Test calculation of position size with fixed capital model."""
        # Risk = 1% of 100k = 1000
        # Stop Distance = 2.0 * ATR(10) = 20
        # Size = 1000 / 20 = 50 units

        size = self.engine._calc_position_size(
            price=100.0,
            atr=10.0,
            portfolio=self.portfolio,
        )
        self.assertEqual(size, Decimal(50))

    def test_position_sizing_compounding(self):
        """Test calculation with compounding model."""
        self.engine.risk_config.capital_allocation_mode = (
            CapitalAllocationMode.COMPOUNDING
        )

        # Portfolio up to 150k
        self.portfolio.current_equity = Decimal(150000)

        # Risk = 1% of 150k = 1500
        # Stop 20
        # Size = 1500 / 20 = 75

        size = self.engine._calc_position_size(
            price=100.0,
            atr=10.0,
            portfolio=self.portfolio,
        )
        self.assertEqual(size, Decimal(75))

    def test_drawdown_violation(self):
        """Test blocking trades when drawdown is too high."""
        # Simulate 25% drawdown (Peak 100k -> Curr 75k)
        # Max allowed is 20%
        self.portfolio.peak_equity = Decimal(100000)
        self.portfolio.cash = Decimal(75000)  # Decrease cash to reflect loss
        self.portfolio.current_equity = Decimal(75000)

        # Manually triggering update to set max_drawdown_pct in state if needed
        self.portfolio.update_equity()

        with self.assertRaises(RiskViolation) as cm:
            self.engine.propose_trade(
                symbol="AAPL",
                side=PositionSide.LONG,
                price=150.0,
                atr=5.0,
                portfolio=self.portfolio,
            )
        self.assertIn("Max drawdown exceeded", str(cm.exception))

    def test_max_position_size_cap(self):
        """Test capping position size based on max % of portfolio."""
        self.engine.risk_config.max_position_size = 0.1  # Max 10% = 10k
        # Risk logic would suggest:
        # Risk 1000, Stop dist=1 (Tiny stop) -> Size = 1000 units @ 100 = 100k position
        # Should be capped at 10k value -> 100 units

        price = 100.0
        atr = 0.5  # Stop dist = 1.0. Raw Size = 1000 / 1 = 1000 units.

        size = self.engine._calc_position_size(price, atr, self.portfolio)

        # Max value = 100,000 * 0.1 = 10,000
        # Max units = 10,000 / 100 = 100
        self.assertEqual(size, Decimal("100.0"))

    def test_propose_trade_success(self):
        """Test successful trade proposal."""
        trade = self.engine.propose_trade(
            symbol="MSFT",
            side=PositionSide.LONG,
            price=200.0,
            atr=5.0,
            portfolio=self.portfolio,
        )

        self.assertIsInstance(trade, PositionState)
        self.assertEqual(trade.symbol, "MSFT")
        self.assertEqual(trade.side, PositionSide.LONG)

        # Risk 1000, Stop 10
        # Size = 100
        self.assertEqual(trade.quantity, Decimal(100))


if __name__ == "__main__":
    unittest.main()
