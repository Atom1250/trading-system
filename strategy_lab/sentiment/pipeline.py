"""Sentiment processing pipeline.

This module provides a framework for sentiment analysis pipelines
that can process news, social media, and other text data sources.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

import pandas as pd


@dataclass
class SentimentScore:
    """Sentiment score result.

    Attributes:
        symbol: Trading symbol
        timestamp: Timestamp of sentiment
        score: Sentiment score (-1 to 1, negative to positive)
        confidence: Confidence in the score (0 to 1)
        source: Source of sentiment data
        metadata: Additional metadata

    """

    symbol: str
    timestamp: pd.Timestamp
    score: float
    confidence: float = 1.0
    source: str = "unknown"
    metadata: dict[str, Any] = None

    def __post_init__(self):
        """Validate sentiment score."""
        if not -1 <= self.score <= 1:
            raise ValueError(
                f"Sentiment score must be between -1 and 1, got {self.score}",
            )
        if not 0 <= self.confidence <= 1:
            raise ValueError(
                f"Confidence must be between 0 and 1, got {self.confidence}",
            )
        if self.metadata is None:
            self.metadata = {}


class SentimentPipeline(ABC):
    """Abstract base class for sentiment analysis pipelines.

    A sentiment pipeline processes raw text data and produces
    sentiment scores that can be used in trading strategies.
    """

    def __init__(self, name: Optional[str] = None):
        """Initialize sentiment pipeline.

        Args:
            name: Pipeline name

        """
        self.name = name or self.__class__.__name__

    @abstractmethod
    def process(self, text: str, symbol: str, **kwargs) -> SentimentScore:
        """Process text and generate sentiment score.

        Args:
            text: Text to analyze
            symbol: Trading symbol associated with the text
            **kwargs: Additional parameters

        Returns:
            SentimentScore object

        """

    def process_batch(
        self,
        texts: list[str],
        symbols: list[str],
        **kwargs,
    ) -> list[SentimentScore]:
        """Process multiple texts in batch.

        Args:
            texts: List of texts to analyze
            symbols: List of symbols (must match length of texts)
            **kwargs: Additional parameters

        Returns:
            List of SentimentScore objects

        """
        if len(texts) != len(symbols):
            raise ValueError("texts and symbols must have same length")

        return [
            self.process(text, symbol, **kwargs) for text, symbol in zip(texts, symbols)
        ]

    def aggregate_scores(
        self,
        scores: list[SentimentScore],
        method: str = "weighted_average",
    ) -> float:
        """Aggregate multiple sentiment scores.

        Args:
            scores: List of sentiment scores
            method: Aggregation method ('average', 'weighted_average', 'median')

        Returns:
            Aggregated sentiment score

        """
        if not scores:
            return 0.0

        if method == "average":
            return sum(s.score for s in scores) / len(scores)
        if method == "weighted_average":
            total_weight = sum(s.confidence for s in scores)
            if total_weight == 0:
                return 0.0
            return sum(s.score * s.confidence for s in scores) / total_weight
        if method == "median":
            return pd.Series([s.score for s in scores]).median()
        raise ValueError(f"Unknown aggregation method: {method}")


class SimpleSentimentPipeline(SentimentPipeline):
    """Simple keyword-based sentiment pipeline.

    This is a basic implementation that uses keyword matching
    for sentiment analysis. More sophisticated implementations
    would use NLP models.
    """

    def __init__(
        self,
        positive_keywords: Optional[list[str]] = None,
        negative_keywords: Optional[list[str]] = None,
        name: Optional[str] = None,
    ):
        """Initialize simple sentiment pipeline.

        Args:
            positive_keywords: List of positive keywords
            negative_keywords: List of negative keywords
            name: Pipeline name

        """
        super().__init__(name or "SimpleSentiment")

        self.positive_keywords = positive_keywords or [
            "bullish",
            "positive",
            "growth",
            "profit",
            "gain",
            "strong",
            "beat",
            "exceed",
            "upgrade",
            "buy",
        ]
        self.negative_keywords = negative_keywords or [
            "bearish",
            "negative",
            "loss",
            "decline",
            "fall",
            "weak",
            "miss",
            "downgrade",
            "sell",
            "risk",
        ]

    def process(self, text: str, symbol: str, **kwargs) -> SentimentScore:
        """Process text using keyword matching.

        Args:
            text: Text to analyze
            symbol: Trading symbol
            **kwargs: Additional parameters (timestamp, etc.)

        Returns:
            SentimentScore object

        """
        text_lower = text.lower()

        # Count positive and negative keywords
        positive_count = sum(1 for kw in self.positive_keywords if kw in text_lower)
        negative_count = sum(1 for kw in self.negative_keywords if kw in text_lower)

        # Calculate score
        total_count = positive_count + negative_count
        if total_count == 0:
            score = 0.0
            confidence = 0.0
        else:
            score = (positive_count - negative_count) / total_count
            confidence = min(total_count / 10.0, 1.0)  # Max confidence at 10+ keywords

        timestamp = kwargs.get("timestamp", pd.Timestamp.now())

        return SentimentScore(
            symbol=symbol,
            timestamp=timestamp,
            score=score,
            confidence=confidence,
            source=self.name,
            metadata={
                "positive_count": positive_count,
                "negative_count": negative_count,
                "text_length": len(text),
            },
        )
