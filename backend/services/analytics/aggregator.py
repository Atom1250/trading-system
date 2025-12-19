"""Signal aggregation service."""

import logging
from decimal import Decimal
from typing import Any

from services.analytics.fundamental_service import fundamental_service
from services.analytics.sentiment_service import sentiment_service
from services.analytics.technical_service import technical_service

logger = logging.getLogger(__name__)


class SignalAggregator:
    """Aggregates signals from multiple sources."""

    def aggregate_signals(
        self,
        symbol: str,
        data_source: str = "local",
        include_technical: bool = True,
        include_fundamental: bool = True,
        include_sentiment: bool = True,
    ) -> dict[str, Any]:
        """Aggregate signals from all sources.

        Returns combined signals with overall recommendation.
        """
        technical = None
        fundamental = None
        sentiment = None

        # Get technical signals
        if include_technical:
            try:
                technical = technical_service.calculate_indicators(symbol, data_source)
            except Exception as exc:
                logger.exception("Error getting technical signals for %s: %s", symbol, exc)

        # Get fundamental signals
        if include_fundamental:
            try:
                fundamental = fundamental_service.get_fundamentals(symbol)
            except Exception as exc:
                logger.exception("Error getting fundamental signals for %s: %s", symbol, exc)

        # Get sentiment signals
        if include_sentiment:
            try:
                sentiment = sentiment_service.get_sentiment(symbol)
            except Exception as exc:
                logger.exception("Error getting sentiment signals for %s: %s", symbol, exc)

        # Calculate combined score (0-100)
        scores = []
        weights = []

        if technical:
            scores.append(float(technical["strength"]))
            weights.append(0.4)  # 40% weight

        if fundamental:
            scores.append(float(fundamental["score"]))
            weights.append(0.4)  # 40% weight

        if sentiment:
            # Convert sentiment (-1 to 1) to score (0-100)
            sentiment_score = (float(sentiment["overall_sentiment"]) + 1) * 50
            scores.append(sentiment_score)
            weights.append(0.2)  # 20% weight

        if scores:
            combined_score = sum(s * w for s, w in zip(scores, weights)) / sum(weights)
        else:
            combined_score = 50  # Neutral

        # Determine recommendation
        if combined_score >= 70:
            recommendation = "strong_buy"
        elif combined_score >= 55:
            recommendation = "buy"
        elif combined_score >= 45:
            recommendation = "hold"
        elif combined_score >= 30:
            recommendation = "sell"
        else:
            recommendation = "strong_sell"

        return {
            "symbol": symbol,
            "technical": technical,
            "fundamental": fundamental,
            "sentiment": sentiment,
            "combined_score": Decimal(str(combined_score)),
            "recommendation": recommendation,
        }


# Global aggregator instance
signal_aggregator = SignalAggregator()
