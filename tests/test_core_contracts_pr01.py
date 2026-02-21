import json
import unittest
from dataclasses import asdict
from datetime import datetime

from strategy_lab import config as legacy_config
from strategy_lab.core import config as core_config
from strategy_lab.core.types import (
    ExecutionReport,
    ExecutionStatus,
    OrderIntent,
    OrderSide,
    OrderType,
    RiskDecision,
    RiskViolation,
    Signal,
    SignalType,
)


class TestCoreConfigCompatibility(unittest.TestCase):
    def test_legacy_config_re_exports_core_symbols(self):
        self.assertIs(legacy_config.RiskConfig, core_config.RiskConfig)
        self.assertIs(legacy_config.StrategyConfig, core_config.StrategyConfig)
        self.assertIs(legacy_config.ExecutionConfig, core_config.ExecutionConfig)
        self.assertIs(legacy_config.BacktestConfig, core_config.BacktestConfig)
        self.assertIs(legacy_config.EntryMode, core_config.EntryMode)
        self.assertIs(
            legacy_config.CapitalAllocationMode,
            core_config.CapitalAllocationMode,
        )

    def test_parameter_bound_validation(self):
        with self.assertRaises(ValueError):
            core_config.ParameterBound(name="bad", min_value=2, max_value=1)

        with self.assertRaises(ValueError):
            core_config.ParameterBound(name="cat", param_type="categorical")


class TestCoreTypesContracts(unittest.TestCase):
    def test_signal_serialization_and_validation(self):
        signal = Signal(
            symbol="AAPL",
            signal_type=SignalType.LONG,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
            strength=0.8,
            metadata={"source": "unit-test"},
        )
        payload = json.loads(json.dumps(asdict(signal), default=str))
        self.assertEqual(payload["symbol"], "AAPL")
        self.assertEqual(payload["signal_type"], "long")
        self.assertEqual(payload["strength"], 0.8)

        with self.assertRaises(ValueError):
            Signal(
                symbol="AAPL",
                signal_type=SignalType.LONG,
                timestamp=datetime(2025, 1, 1, 12, 0, 0),
                strength=1.5,
            )

    def test_order_risk_and_execution_validation(self):
        with self.assertRaises(ValueError):
            OrderIntent(
                symbol="AAPL",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                quantity=0,
                timestamp=datetime(2025, 1, 1, 12, 0, 0),
            )

        order = OrderIntent(
            symbol="MSFT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            quantity=10,
            timestamp=datetime(2025, 1, 1, 12, 0, 0),
        )
        decision = RiskDecision(approved=True, order_intent=order)
        self.assertTrue(decision.approved)

        reject = RiskDecision(
            approved=False,
            violation=RiskViolation(code="MAX_DD", message="drawdown limit hit"),
        )
        self.assertFalse(reject.approved)

        with self.assertRaises(ValueError):
            RiskDecision(approved=True)

        report = ExecutionReport(
            status=ExecutionStatus.FILLED,
            symbol="MSFT",
            side=OrderSide.BUY,
            order_type=OrderType.MARKET,
            requested_quantity=10,
            filled_quantity=10,
            submitted_at=datetime(2025, 1, 1, 12, 0, 0),
            filled_at=datetime(2025, 1, 1, 12, 1, 0),
            avg_fill_price=100.5,
        )
        self.assertEqual(report.status, ExecutionStatus.FILLED)

        with self.assertRaises(ValueError):
            ExecutionReport(
                status=ExecutionStatus.PARTIAL,
                symbol="MSFT",
                side=OrderSide.BUY,
                order_type=OrderType.MARKET,
                requested_quantity=10,
                filled_quantity=11,
                submitted_at=datetime(2025, 1, 1, 12, 0, 0),
            )


if __name__ == "__main__":
    unittest.main()
