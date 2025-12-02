"""Feature importance service."""
from typing import Dict, Any, List
from decimal import Decimal


class FeatureImportanceService:
    """Service for model explainability."""
    
    def get_feature_importance(
        self,
        model_name: str = "default"
    ) -> Dict[str, Any]:
        """
        Get feature importance for a model.
        
        Note: This is a placeholder implementation.
        In production, you would integrate with actual ML models.
        """
        # Placeholder feature importances
        feature_importances = [
            {
                "feature": "RSI_14",
                "importance": Decimal("0.25"),
                "description": "Relative Strength Index (14-period)"
            },
            {
                "feature": "MACD_signal",
                "importance": Decimal("0.20"),
                "description": "MACD signal line"
            },
            {
                "feature": "SMA_50",
                "importance": Decimal("0.18"),
                "description": "50-day Simple Moving Average"
            },
            {
                "feature": "Volume",
                "importance": Decimal("0.15"),
                "description": "Trading volume"
            },
            {
                "feature": "Price_momentum",
                "importance": Decimal("0.12"),
                "description": "Price momentum (20-day)"
            },
            {
                "feature": "Volatility",
                "importance": Decimal("0.10"),
                "description": "Historical volatility"
            }
        ]
        
        sample_prediction = {
            "predicted_signal": "buy",
            "confidence": 0.75,
            "explanation": "Strong RSI and MACD signals with positive momentum"
        }
        
        return {
            "model_name": model_name,
            "feature_importances": feature_importances,
            "sample_prediction": sample_prediction
        }


# Global service instance
feature_service = FeatureImportanceService()
