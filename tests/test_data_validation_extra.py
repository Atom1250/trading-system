"""Additional tests for data validation utilities."""

import pandas as pd

from utils.data_validation import clean_price_data, validate_price_data


def test_extreme_returns_detected():
    dates = pd.date_range("2024-01-01", periods=3, freq="D")
    df = pd.DataFrame(
        {
            "open": [100, 1000, 101],
            "high": [105, 1005, 102],
            "low": [99, 995, 100],
            "close": [102, 1000, 101],
            "volume": [1000, 1000, 1000],
        },
        index=dates,
    )

    is_valid, warnings = validate_price_data(df, "TEST")

    assert any("price movement" in w.lower() for w in warnings)


def test_large_gap_detected():
    dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-03-10"])
    df = pd.DataFrame(
        {
            "open": [100, 101, 102],
            "high": [105, 106, 107],
            "low": [99, 100, 101],
            "close": [102, 103, 104],
            "volume": [1000, 1100, 1200],
        },
        index=dates,
    )

    is_valid, warnings = validate_price_data(df, "TEST")

    assert any("maximum gap" in w.lower() for w in warnings)


def test_timezone_aware_index():
    dates = pd.date_range("2024-01-01", periods=3, freq="D", tz="UTC")
    df = pd.DataFrame(
        {
            "open": [100, 101, 102],
            "high": [105, 106, 107],
            "low": [99, 100, 101],
            "close": [102, 103, 104],
            "volume": [1000, 1100, 1200],
        },
        index=dates,
    )

    # validate should handle tz-aware indexes without raising
    is_valid, warnings = validate_price_data(df, "TEST")
    assert is_valid

    # clean should preserve and sort properly
    cleaned = clean_price_data(df, "TEST")
    assert cleaned.index.is_monotonic_increasing
