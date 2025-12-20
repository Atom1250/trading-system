"""Unit tests for price service."""

from datetime import datetime
from unittest.mock import patch

import pandas as pd
import pytest

from services.data.price_service import PriceDataService


@pytest.fixture
def price_service():
    return PriceDataService()


@patch("services.data.price_service.FMPDataSource")
def test_get_prices_fmp(mock_fmp, price_service):
    # Setup mock
    mock_instance = mock_fmp.return_value
    mock_instance.fetch_prices.return_value = pd.DataFrame(
        {
            "date": [datetime(2023, 1, 1)],
            "open": [100],
            "high": [110],
            "low": [90],
            "close": [105],
            "volume": [1000],
        },
    )

    # Test
    result = price_service.get_prices("AAPL", source="fmp")

    # Verify
    assert not result.empty
    assert "close" in result.columns
    assert len(result) == 1


def test_get_prices_invalid_source(price_service):
    with pytest.raises(ValueError):
        price_service.get_prices("AAPL", source="invalid_source")
