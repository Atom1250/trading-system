from __future__ import annotations

from unittest.mock import patch

import pandas as pd

from trading_backtester.backtester import Backtester


def test_legacy_backtester_run_delegates_to_strategy_lab_adapter():
    idx = pd.date_range("2025-01-01", periods=3, freq="D")
    df = pd.DataFrame(
        {
            "open": [100.0, 101.0, 102.0],
            "high": [101.0, 102.0, 103.0],
            "low": [99.0, 100.0, 101.0],
            "close": [100.0, 101.0, 102.0],
            "volume": [1_000_000, 1_000_000, 1_000_000],
            "signal": [0.0, 1.0, 0.0],
        },
        index=idx,
    )

    expected = {
        "results": df.copy(),
        "stats": {},
        "equity_curve": pd.Series([100_000.0, 100_000.0, 100_000.0], index=idx),
        "trades": pd.DataFrame(),
        "cumulative_return": 0.0,
        "max_drawdown": 0.0,
        "results_path": "reports/results.csv",
    }

    with patch(
        "trading_backtester.backtester.run_backtest_via_strategy_lab",
        return_value=expected,
    ) as mocked:
        backtester = Backtester()
        result = backtester.run(df)

    mocked.assert_called_once()
    assert result is expected
