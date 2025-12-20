"""AI API endpoints."""

from fastapi import APIRouter, HTTPException, Query

from models.ai import (FeatureImportance, ModelExplanation, RiskAssessment,
                       RiskMetrics)
from services.ai.feature_service import feature_service
from services.ai.risk_service import risk_service

router = APIRouter()


@router.post("/risk_assessment", response_model=RiskAssessment)
async def assess_risk(
    symbol: str = Query(..., description="Stock symbol"),
    data_source: str = Query("local", description="Data source"),
):
    """Assess portfolio risk for a symbol."""
    try:
        result = risk_service.assess_risk(symbol, data_source)

        return RiskAssessment(
            risk_score=result["risk_score"],
            risk_level=result["risk_level"],
            metrics=RiskMetrics(**result["metrics"]),
            recommendations=result["recommendations"],
        )
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Risk assessment failed: {e!s}")


@router.get("/feature_importance", response_model=ModelExplanation)
async def get_feature_importance(
    model_name: str = Query("default", description="Model name"),
):
    """Get feature importance for a model."""
    try:
        result = feature_service.get_feature_importance(model_name)

        return ModelExplanation(
            model_name=result["model_name"],
            feature_importances=[
                FeatureImportance(**fi) for fi in result["feature_importances"]
            ],
            sample_prediction=result["sample_prediction"],
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Feature importance failed: {e!s}",
        )


@router.post("/strategy_ranking")
async def rank_strategies():
    """Rank strategies by performance (placeholder)."""
    return {
        "rankings": [
            {"strategy": "macd_crossover", "score": 0.85},
            {"strategy": "rsi_mean_reversion", "score": 0.78},
            {"strategy": "moving_average_crossover", "score": 0.72},
        ],
    }


@router.post("/explain_trade")
async def explain_trade():
    """Explain a trade decision (placeholder)."""
    return {
        "explanation": "Trade triggered by MACD crossover with RSI confirmation",
        "confidence": 0.82,
        "factors": [
            {"name": "MACD Signal", "contribution": 0.4},
            {"name": "RSI Level", "contribution": 0.3},
            {"name": "Volume", "contribution": 0.3},
        ],
    }
