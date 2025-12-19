"""Fundamental data service."""

import sys
from decimal import Decimal
from pathlib import Path
from typing import Any

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

import logging

from ingestion.fmp_client import FMPClient

logger = logging.getLogger(__name__)


class FundamentalService:
    """Service for fundamental analysis."""

    def __init__(self):
        try:
            self.fmp_client = FMPClient()
        except Exception as exc:  # pragma: no cover - environment dependent
            logger.warning("FMP client unavailable: %s", exc)
            self.fmp_client = None

    def get_fundamentals(self, symbol: str) -> dict[str, Any]:
        """Get fundamental metrics for a symbol.

        Returns dict with fundamental metrics and score.
        """
        try:
            # Get key metrics from FMP
            # Note: This is a simplified implementation
            # In production, you'd fetch real data from FMP API

            metrics = [
                {
                    "name": "P/E Ratio",
                    "value": None,  # Would fetch from FMP
                    "description": "Price to Earnings Ratio",
                },
                {
                    "name": "P/B Ratio",
                    "value": None,
                    "description": "Price to Book Ratio",
                },
                {
                    "name": "Debt/Equity",
                    "value": None,
                    "description": "Debt to Equity Ratio",
                },
                {"name": "ROE", "value": None, "description": "Return on Equity"},
                {
                    "name": "Revenue Growth",
                    "value": None,
                    "description": "Year-over-Year Revenue Growth",
                },
            ]

            # Calculate fundamental score (simplified)
            # In production, this would be based on actual metrics
            score = Decimal(50)  # Neutral score

            # Determine rating based on score
            if score >= 80:
                rating = "strong_buy"
            elif score >= 60:
                rating = "buy"
            elif score >= 40:
                rating = "hold"
            elif score >= 20:
                rating = "sell"
            else:
                rating = "strong_sell"

            return {
                "symbol": symbol,
                "metrics": metrics,
                "score": score,
                "rating": rating,
            }

        except Exception as exc:
            logger.exception("Failed to compute fundamentals for %s: %s", symbol, exc)
            # Return neutral fundamentals on error
            return {
                "symbol": symbol,
                "metrics": [],
                "score": Decimal(50),
                "rating": "hold",
            }


# Global service instance
fundamental_service = FundamentalService()
