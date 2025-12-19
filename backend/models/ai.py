"""AI service models."""

from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field


class RiskMetrics(BaseModel):
    """Risk assessment metrics."""

    volatility: Decimal = Field(..., description="Portfolio volatility")
    var_95: Decimal = Field(..., description="Value at Risk (95%)")
    sharpe_ratio: Decimal = Field(..., description="Sharpe ratio")
    max_drawdown: Decimal = Field(..., description="Maximum drawdown")
    beta: Decimal = Field(..., description="Portfolio beta")


class RiskAssessment(BaseModel):
    """Risk assessment result."""

    risk_score: Decimal = Field(..., description="Overall risk score 0-100")
    risk_level: str = Field(..., description="Risk level (low/medium/high/extreme)")
    metrics: RiskMetrics
    recommendations: list[str] = Field(default_factory=list)


class FeatureImportance(BaseModel):
    """Feature importance for a model."""

    feature: str
    importance: Decimal
    description: str


class ModelExplanation(BaseModel):
    """Model explanation."""

    model_name: str
    feature_importances: list[FeatureImportance]
    sample_prediction: dict[str, Any]
