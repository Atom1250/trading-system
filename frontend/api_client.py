"""API client for Streamlit frontend."""

import logging
import os
from datetime import datetime
from typing import Any, Optional

import requests

logger = logging.getLogger(__name__)


class TradingSystemAPI:
    """Client for Trading System API."""

    def __init__(self, base_url: str = None):
        self.base_url = base_url or os.environ.get(
            "BACKEND_URL",
            "http://localhost:8000",
        )
        self.session = requests.Session()

    def _handle_response(self, response: requests.Response) -> dict:
        """Handle API response and raise detailed errors."""
        try:
            response.raise_for_status()
            return response.json()
        except requests.exceptions.HTTPError as e:
            try:
                error_detail = response.json().get("detail", response.text)
            except ValueError as exc:
                logger.debug("Failed to decode error response as JSON: %s", exc)
                error_detail = response.text
            raise Exception(
                f"API Error ({response.status_code}): {error_detail}",
            ) from e

    # Portfolio endpoints
    def create_portfolio(
        self,
        name: str,
        description: str = "",
        initial_capital: float = 100000.0,
        currency: str = "USD",
    ) -> dict:
        """Create a new portfolio."""
        payload = {
            "name": name,
            "description": description,
            "initial_capital": initial_capital,
            "currency": currency,
        }
        response = self.session.post(
            f"{self.base_url}/api/v1/portfolios/",
            json=payload,
        )
        return self._handle_response(response)

    def get_portfolios(self) -> list[dict]:
        """Get all portfolios."""
        response = self.session.get(f"{self.base_url}/api/v1/portfolios")
        return self._handle_response(response)

    def get_portfolio(self, portfolio_id: int) -> dict:
        """Get portfolio by ID."""
        response = self.session.get(f"{self.base_url}/api/v1/portfolios/{portfolio_id}")
        return self._handle_response(response)

    def get_portfolio_metrics(self, portfolio_id: int) -> dict:
        """Get portfolio metrics."""
        response = self.session.get(
            f"{self.base_url}/api/v1/portfolios/{portfolio_id}/metrics",
        )
        return self._handle_response(response)

    def get_portfolio_history(self, portfolio_id: int, days: int = 30) -> list[dict]:
        """Get portfolio history."""
        response = self.session.get(
            f"{self.base_url}/api/v1/portfolios/{portfolio_id}/history",
            params={"days": days},
        )
        return self._handle_response(response)

    # Data endpoints
    def get_data_sources(self) -> list[dict]:
        """Get available data sources."""
        response = self.session.get(f"{self.base_url}/api/v1/data/sources")
        return self._handle_response(response)

    def get_prices(
        self,
        symbol: str,
        source: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> dict:
        """Get price data."""
        params = {}
        if source:
            params["source"] = source
        if start_date:
            params["start_date"] = start_date.isoformat()
        if end_date:
            params["end_date"] = end_date.isoformat()

        response = self.session.get(
            f"{self.base_url}/api/v1/data/prices/{symbol}",
            params=params,
        )
        return self._handle_response(response)

    # Strategy endpoints
    def get_strategies(self) -> list[dict]:
        """Get available strategies."""
        response = self.session.get(f"{self.base_url}/api/v1/strategies")
        return self._handle_response(response)

    def get_strategy(self, strategy_name: str) -> dict:
        """Get strategy details."""
        response = self.session.get(
            f"{self.base_url}/api/v1/strategies/{strategy_name}",
        )
        return self._handle_response(response)

    def run_backtest(
        self,
        symbol: str,
        strategy_name: str,
        parameters: Optional[dict[str, Any]] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        initial_capital: float = 100000,
        data_source: str = "local",
    ) -> dict:
        """Run a backtest."""
        payload = {
            "symbol": symbol,
            "strategy_name": strategy_name,
            "parameters": parameters or {},
            "initial_capital": initial_capital,
            "data_source": data_source,
        }

        if start_date:
            payload["start_date"] = start_date.isoformat()
        if end_date:
            payload["end_date"] = end_date.isoformat()

        response = self.session.post(
            f"{self.base_url}/api/v1/strategies/backtest",
            json=payload,
        )
        return self._handle_response(response)

    # Signals endpoints
    def get_technical_signals(self, symbol: str, data_source: str = "local") -> dict:
        """Get technical signals."""
        response = self.session.get(
            f"{self.base_url}/api/v1/signals/technical/{symbol}",
            params={"data_source": data_source},
        )
        return self._handle_response(response)

    def get_fundamental_signals(self, symbol: str) -> dict:
        """Get fundamental signals."""
        response = self.session.get(
            f"{self.base_url}/api/v1/signals/fundamental/{symbol}",
        )
        return self._handle_response(response)

    def get_sentiment_signals(self, symbol: str) -> dict:
        """Get sentiment signals."""
        response = self.session.get(
            f"{self.base_url}/api/v1/signals/sentiment/{symbol}",
        )
        return self._handle_response(response)

    def get_aggregated_signals(
        self,
        symbol: str,
        data_source: str = "local",
        include_technical: bool = True,
        include_fundamental: bool = True,
        include_sentiment: bool = True,
    ) -> dict:
        """Get aggregated signals."""
        response = self.session.get(
            f"{self.base_url}/api/v1/signals/aggregated/{symbol}",
            params={
                "data_source": data_source,
                "include_technical": include_technical,
                "include_fundamental": include_fundamental,
                "include_sentiment": include_sentiment,
            },
        )
        return self._handle_response(response)

    # AI endpoints
    def get_risk_assessment(self, symbol: str, data_source: str = "local") -> dict:
        """Get risk assessment."""
        response = self.session.post(
            f"{self.base_url}/api/v1/ai/risk_assessment",
            params={"symbol": symbol, "data_source": data_source},
        )
        return self._handle_response(response)

    def get_feature_importance(self, model_name: str = "default") -> dict:
        """Get feature importance."""
        response = self.session.get(
            f"{self.base_url}/api/v1/ai/feature_importance",
            params={"model_name": model_name},
        )
        return self._handle_response(response)

    # Integration endpoints
    def export_to_google_sheets(
        self,
        portfolio_id: int,
        spreadsheet_name: Optional[str] = None,
    ) -> dict:
        """Export portfolio to Google Sheets."""
        params = {}
        if spreadsheet_name:
            params["spreadsheet_name"] = spreadsheet_name

        response = self.session.post(
            f"{self.base_url}/api/v1/integration/google_sheets/export/{portfolio_id}",
            params=params,
        )
        return self._handle_response(response)

    def run_optimization(
        self,
        strategy_name: str,
        symbol: str,
        parameter_ranges: dict[str, dict[str, Any]],
        initial_capital: float = 100000.0,
        data_source: str = "local",
        n_trials: int = 20,
        metric: str = "sharpe_ratio",
        direction: str = "maximize",
    ) -> dict[str, Any]:
        """Run strategy optimization."""
        try:
            payload = {
                "strategy_name": strategy_name,
                "symbol": symbol,
                "parameter_ranges": parameter_ranges,
                "initial_capital": initial_capital,
                "data_source": data_source,
                "n_trials": n_trials,
                "metric": metric,
                "direction": direction,
            }
            response = self.session.post(
                f"{self.base_url}/api/v1/optimization/run",
                json=payload,
            )
            return self._handle_response(response)
        except requests.RequestException as exc:
            logger.exception(
                "Optimization request failed for strategy %s on symbol %s",
                strategy_name,
                symbol,
            )
            raise Exception(f"Optimization failed: {exc!s}") from exc

    def download_portfolio_export(
        self,
        portfolio_id: int,
        format: str = "csv",
    ) -> bytes:
        """Download portfolio export file content."""
        response = self.session.get(
            f"{self.base_url}/api/v1/integration/export/{portfolio_id}",
            params={"format": format},
        )
        if response.status_code != 200:
            try:
                error_detail = response.json().get("detail", response.text)
            except ValueError as exc:
                logger.debug("Failed to decode error response as JSON: %s", exc)
                error_detail = response.text
            raise Exception(f"Download failed ({response.status_code}): {error_detail}")
        return response.content
