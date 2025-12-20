"""Signal models for API."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class TechnicalIndicator(BaseModel):
    """Technical indicator value."""

    name: str = Field(..., description="Indicator name")
    value: float = Field(..., description="Current value")
    signal: Optional[str] = Field(None, description="Signal (buy/sell/neutral)")
    timestamp: datetime = Field(default_factory=datetime.now)


class TechnicalSignals(BaseModel):
    """Technical signals for a symbol."""

    symbol: str
    indicators: list[TechnicalIndicator]
    overall_signal: str = Field(..., description="Overall signal (buy/sell/neutral)")
    strength: Decimal = Field(..., description="Signal strength 0-100")


class FundamentalMetric(BaseModel):
    """Fundamental metric."""

    name: str
    value: Optional[float]
    description: str


class FundamentalSignals(BaseModel):
    """Fundamental signals for a symbol."""

    symbol: str
    metrics: list[FundamentalMetric]
    score: Decimal = Field(..., description="Fundamental score 0-100")
    rating: str = Field(
        ...,
        description="Rating (strong_buy/buy/hold/sell/strong_sell)",
    )


class SentimentScore(BaseModel):
    """Sentiment score."""

    source: str = Field(..., description="Source (news/social/analyst)")
    score: Decimal = Field(..., description="Sentiment score -1 to 1")
    confidence: Decimal = Field(..., description="Confidence 0-1")
    timestamp: datetime = Field(default_factory=datetime.now)


class SentimentSignals(BaseModel):
    """Sentiment signals for a symbol."""

    symbol: str
    scores: list[SentimentScore]
    overall_sentiment: Decimal = Field(..., description="Overall sentiment -1 to 1")
    signal: str = Field(..., description="Signal (bullish/neutral/bearish)")


class AggregatedSignals(BaseModel):
    """Aggregated signals from all sources."""

    symbol: str
    technical: Optional[TechnicalSignals] = None
    fundamental: Optional[FundamentalSignals] = None
    sentiment: Optional[SentimentSignals] = None
    combined_score: Decimal = Field(..., description="Combined score 0-100")
    recommendation: str = Field(..., description="Overall recommendation")
    timestamp: datetime = Field(default_factory=datetime.now)
