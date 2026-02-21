from fastapi import APIRouter
from typing import Any
from backend.services.ai.feature_service import feature_service

router = APIRouter()

@router.get("/models")
def list_models():
    """List all available ML models."""
    return {"models": feature_service.list_available_models()}

@router.get("/feature-importance/{model_name}")
def get_feature_importance(model_name: str):
    """Get feature importance for a specific model."""
    return feature_service.get_feature_importance(model_name)
