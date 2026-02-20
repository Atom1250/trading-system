"""Feature importance service with integrated ML model loading."""

import logging
import os
from decimal import Decimal
from typing import Any

import joblib

logger = logging.getLogger(__name__)

# Default directory where trained ML models are stored.
MODEL_DIR = os.getenv("ML_MODEL_DIR", os.path.join(os.path.dirname(__file__), "../../../ml_models"))

# Placeholder feature importances used as fallback when no model file is found.
_PLACEHOLDER_IMPORTANCES = [
    {
        "feature": "RSI_14",
        "importance": Decimal("0.25"),
        "description": "Relative Strength Index (14-period)",
    },
    {
        "feature": "MACD_signal",
        "importance": Decimal("0.20"),
        "description": "MACD signal line",
    },
    {
        "feature": "SMA_50",
        "importance": Decimal("0.18"),
        "description": "50-day Simple Moving Average",
    },
    {
        "feature": "Volume",
        "importance": Decimal("0.15"),
        "description": "Trading volume",
    },
    {
        "feature": "Price_momentum",
        "importance": Decimal("0.12"),
        "description": "Price momentum (20-day)",
    },
    {
        "feature": "Volatility",
        "importance": Decimal("0.10"),
        "description": "Historical volatility",
    },
]

_PLACEHOLDER_PREDICTION = {
    "predicted_signal": "buy",
    "confidence": 0.75,
    "explanation": "Strong RSI and MACD signals with positive momentum",
}


class FeatureImportanceService:
    """Service for model explainability.

    Attempts to load a serialised BasePredictor from disk using the provided
    model_name. Falls back to static placeholder data if no model file is found,
    allowing the service to remain functional during development.
    """

    def get_feature_importance(self, model_name: str = "default") -> dict[str, Any]:
        """Return feature importance for a model.

        Args:
            model_name: Name of the model (resolves to ``<MODEL_DIR>/<model_name>.joblib``).

        Returns:
            Dictionary with keys ``model_name``, ``feature_importances``, and
            ``sample_prediction``.
        """
        model_path = os.path.join(MODEL_DIR, f"{model_name}.joblib")

        if os.path.isfile(model_path):
            try:
                model = joblib.load(model_path)
                raw_importances = model.get_feature_importances()

                # Normalise to the standard list-of-dicts schema.
                feature_importances = [
                    {"feature": feat, "importance": Decimal(str(round(imp, 6))), "description": ""}
                    for feat, imp in sorted(raw_importances.items(), key=lambda x: -x[1])
                ]

                return {
                    "model_name": model_name,
                    "feature_importances": feature_importances,
                    "sample_prediction": _PLACEHOLDER_PREDICTION,
                }
            except Exception as exc:
                logger.warning(
                    "Failed to load model '%s' from %s: %s. Falling back to placeholder data.",
                    model_name,
                    model_path,
                    exc,
                )

        # Fallback — no model file found or loading failed.
        return {
            "model_name": model_name,
            "feature_importances": _PLACEHOLDER_IMPORTANCES,
            "sample_prediction": _PLACEHOLDER_PREDICTION,
        }


# Global service instance
feature_service = FeatureImportanceService()
