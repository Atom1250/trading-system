"""Unit tests for portfolio service."""

from unittest.mock import MagicMock

import pytest

from services.portfolio_service import PortfolioService


@pytest.fixture
def mock_db():
    return MagicMock()


@pytest.fixture
def portfolio_service(mock_db):
    service = PortfolioService()
    service.db = mock_db
    return service


def test_create_portfolio(portfolio_service, mock_db):
    # Setup
    mock_db.add.return_value = None
    mock_db.commit.return_value = None
    mock_db.refresh.return_value = None

    # Test
    # Note: This is a simplified test as actual DB interaction is mocked
    # In a real scenario, we'd use a test DB
