"""Signals API endpoints."""

from fastapi import APIRouter, HTTPException, Query
from models.signals import (
    AggregatedSignals,
    FundamentalMetric,
    FundamentalSignals,
    SentimentScore,
    SentimentSignals,
    TechnicalIndicator,
    TechnicalSignals,
)
from services.analytics.aggregator import signal_aggregator
from services.analytics.fundamental_service import fundamental_service
from services.analytics.sentiment_service import sentiment_service
from services.analytics.technical_service import technical_service

router = APIRouter()


@router.get("/technical/{symbol}", response_model=TechnicalSignals)
async def get_technical_signals(
    symbol: str, data_source: str = Query("local", description="Data source"),
):
    """Get technical indicators and signals for a symbol."""
    try:
        result = technical_service.calculate_indicators(symbol, data_source)

        return TechnicalSignals(
            symbol=result["symbol"],
            indicators=[TechnicalIndicator(**ind) for ind in result["indicators"]],
            overall_signal=result["overall_signal"],
            strength=result["strength"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error calculating technical signals: {e!s}",
        )


@router.get("/fundamental/{symbol}", response_model=FundamentalSignals)
async def get_fundamental_signals(symbol: str):
    """Get fundamental metrics and signals for a symbol."""
    try:
        result = fundamental_service.get_fundamentals(symbol)

        return FundamentalSignals(
            symbol=result["symbol"],
            metrics=[FundamentalMetric(**metric) for metric in result["metrics"]],
            score=result["score"],
            rating=result["rating"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting fundamental signals: {e!s}",
        )


@router.get("/sentiment/{symbol}", response_model=SentimentSignals)
async def get_sentiment_signals(symbol: str):
    """Get sentiment scores and signals for a symbol."""
    try:
        result = sentiment_service.get_sentiment(symbol)

        return SentimentSignals(
            symbol=result["symbol"],
            scores=[SentimentScore(**score) for score in result["scores"]],
            overall_sentiment=result["overall_sentiment"],
            signal=result["signal"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error getting sentiment signals: {e!s}",
        )


@router.get("/aggregated/{symbol}", response_model=AggregatedSignals)
async def get_aggregated_signals(
    symbol: str,
    data_source: str = Query("local", description="Data source"),
    include_technical: bool = Query(True, description="Include technical signals"),
    include_fundamental: bool = Query(True, description="Include fundamental signals"),
    include_sentiment: bool = Query(True, description="Include sentiment signals"),
):
    """Get aggregated signals from all sources."""
    try:
        result = signal_aggregator.aggregate_signals(
            symbol=symbol,
            data_source=data_source,
            include_technical=include_technical,
            include_fundamental=include_fundamental,
            include_sentiment=include_sentiment,
        )

        # Convert to response models
        technical = None
        if result.get("technical"):
            tech = result["technical"]
            technical = TechnicalSignals(
                symbol=tech["symbol"],
                indicators=[TechnicalIndicator(**ind) for ind in tech["indicators"]],
                overall_signal=tech["overall_signal"],
                strength=tech["strength"],
            )

        fundamental = None
        if result.get("fundamental"):
            fund = result["fundamental"]
            fundamental = FundamentalSignals(
                symbol=fund["symbol"],
                metrics=[FundamentalMetric(**m) for m in fund["metrics"]],
                score=fund["score"],
                rating=fund["rating"],
            )

        sentiment = None
        if result.get("sentiment"):
            sent = result["sentiment"]
            sentiment = SentimentSignals(
                symbol=sent["symbol"],
                scores=[SentimentScore(**s) for s in sent["scores"]],
                overall_sentiment=sent["overall_sentiment"],
                signal=sent["signal"],
            )

        return AggregatedSignals(
            symbol=result["symbol"],
            technical=technical,
            fundamental=fundamental,
            sentiment=sentiment,
            combined_score=result["combined_score"],
            recommendation=result["recommendation"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error aggregating signals: {e!s}",
        )
