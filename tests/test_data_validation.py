"""Unit tests for data validation utilities."""

import pandas as pd
import pytest

from utils.data_validation import clean_price_data, validate_price_data


class TestDataValidation:
    """Tests for data validation functions."""

    def test_validate_empty_dataframe(self):
        """Test validation of empty DataFrame."""
        df = pd.DataFrame()
        is_valid, warnings = validate_price_data(df, "TEST")

        assert not is_valid
        assert len(warnings) == 1
        assert "empty" in warnings[0].lower()

    def test_validate_missing_columns(self):
        """Test validation with missing required columns."""
        df = pd.DataFrame(
            {
                "open": [100, 101],
                "high": [102, 103],
                # Missing 'low', 'close', 'volume'
            },
        )

        is_valid, warnings = validate_price_data(df, "TEST")

        assert not is_valid
        assert any("missing" in w.lower() for w in warnings)

    def test_validate_valid_data(self):
        """Test validation of valid price data."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame(
            {
                "open": [100, 101, 102, 103, 104],
                "high": [105, 106, 107, 108, 109],
                "low": [99, 100, 101, 102, 103],
                "close": [102, 103, 104, 105, 106],
                "volume": [1000, 1100, 1200, 1300, 1400],
            },
            index=dates,
        )

        is_valid, warnings = validate_price_data(df, "TEST")

        assert is_valid
        # May have warnings but should be valid

    def test_validate_invalid_high_low(self):
        """Test validation detects high < low."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        df = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [105, 100, 107],  # Second row: high < low
                "low": [99, 101, 101],
                "close": [102, 103, 104],
                "volume": [1000, 1100, 1200],
            },
            index=dates,
        )

        is_valid, warnings = validate_price_data(df, "TEST")

        assert not is_valid
        assert any("high < low" in w.lower() for w in warnings)

    def test_validate_negative_prices(self):
        """Test validation detects negative prices."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        df = pd.DataFrame(
            {
                "open": [100, -101, 102],  # Negative price
                "high": [105, 106, 107],
                "low": [99, 100, 101],
                "close": [102, 103, 104],
                "volume": [1000, 1100, 1200],
            },
            index=dates,
        )

        is_valid, warnings = validate_price_data(df, "TEST")

        assert not is_valid
        assert any("negative" in w.lower() for w in warnings)

    def test_validate_null_values(self):
        """Test validation detects null values."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        df = pd.DataFrame(
            {
                "open": [100, None, 102],  # Null value
                "high": [105, 106, 107],
                "low": [99, 100, 101],
                "close": [102, 103, 104],
                "volume": [1000, 1100, 1200],
            },
            index=dates,
        )

        is_valid, warnings = validate_price_data(df, "TEST")

        # Should have warnings about null values
        assert any("null" in w.lower() for w in warnings)

    def test_clean_removes_invalid_rows(self):
        """Test cleaning removes invalid rows."""
        dates = pd.date_range("2024-01-01", periods=5, freq="D")
        df = pd.DataFrame(
            {
                "open": [100, -101, 102, 103, 104],  # Row 1 has negative
                "high": [105, 106, 100, 108, 109],  # Row 2 has high < low
                "low": [99, 100, 101, 102, 103],
                "close": [102, 103, 104, 105, 106],
                "volume": [1000, 1100, 1200, 1300, 1400],
            },
            index=dates,
        )

        cleaned = clean_price_data(df, "TEST")

        # Should have removed rows with issues
        assert len(cleaned) < len(df)
        # All remaining rows should have positive prices
        assert (cleaned["open"] > 0).all()
        # All remaining rows should have high >= low
        assert (cleaned["high"] >= cleaned["low"]).all()

    def test_clean_removes_duplicates(self):
        """Test cleaning removes duplicate dates."""
        dates = pd.to_datetime(["2024-01-01", "2024-01-02", "2024-01-02", "2024-01-03"])
        df = pd.DataFrame(
            {
                "open": [100, 101, 101.5, 102],
                "high": [105, 106, 106.5, 107],
                "low": [99, 100, 100.5, 101],
                "close": [102, 103, 103.5, 104],
                "volume": [1000, 1100, 1150, 1200],
            },
            index=dates,
        )

        cleaned = clean_price_data(df, "TEST")

        # Should have removed duplicate
        assert len(cleaned) == 3
        # Should keep the last occurrence
        assert not cleaned.index.duplicated().any()

    def test_clean_fixes_negative_volume(self):
        """Test cleaning fixes negative volume."""
        dates = pd.date_range("2024-01-01", periods=3, freq="D")
        df = pd.DataFrame(
            {
                "open": [100, 101, 102],
                "high": [105, 106, 107],
                "low": [99, 100, 101],
                "close": [102, 103, 104],
                "volume": [1000, -1100, 1200],  # Negative volume
            },
            index=dates,
        )

        cleaned = clean_price_data(df, "TEST")

        # Should have set negative volume to 0
        assert (cleaned["volume"] >= 0).all()

    def test_clean_sorts_by_date(self):
        """Test cleaning sorts data by date."""
        dates = pd.to_datetime(["2024-01-03", "2024-01-01", "2024-01-02"])
        df = pd.DataFrame(
            {
                "open": [102, 100, 101],
                "high": [107, 105, 106],
                "low": [101, 99, 100],
                "close": [104, 102, 103],
                "volume": [1200, 1000, 1100],
            },
            index=dates,
        )

        cleaned = clean_price_data(df, "TEST")

        # Should be sorted
        assert cleaned.index.is_monotonic_increasing


class TestDataValidationIntegration:
    """Integration tests for data validation."""

    def test_validation_with_real_data_structure(self):
        """Test validation with realistic data structure."""
        # Simulate data from Yahoo Finance or FMP
        dates = pd.date_range("2024-01-01", periods=100, freq="D")
        df = pd.DataFrame(
            {
                "open": [100 + i * 0.5 for i in range(100)],
                "high": [105 + i * 0.5 for i in range(100)],
                "low": [99 + i * 0.5 for i in range(100)],
                "close": [102 + i * 0.5 for i in range(100)],
                "volume": [1000000 + i * 1000 for i in range(100)],
            },
            index=dates,
        )

        is_valid, warnings = validate_price_data(df, "AAPL")

        assert is_valid
        # Should have minimal or no warnings for clean data


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
