"""Feature importance service — dynamically loads trained ML models from disk."""

import logging
import os
from decimal import Decimal
from typing import Any

import joblib

logger = logging.getLogger(__name__)


def _get_model_dir() -> str:
    """Return the ML model directory from environment (or the default)."""
    return os.environ.get("ML_MODEL_DIR", "ml_models")


class FeatureImportanceService:
    """Service for model explainability.

    Loads a serialised ``BasePredictor`` from ``<ML_MODEL_DIR>/<model_name>.joblib``
    and calls ``get_feature_importances()`` on it.  Returns a structured payload
    that matches the expected API schema.

    If the model file does not exist, a ``model_not_found`` error payload is
    returned so callers can surface a clear message rather than silently using
    stale placeholder data.
    """

    def get_feature_importance(self, model_name: str = "default") -> dict[str, Any]:
        """Return feature importance for a trained model.

        Args:
            model_name: Name of the model (resolves to ``<ML_MODEL_DIR>/<model_name>.joblib``).

        Returns:
            Dictionary with keys:
                - ``model_name`` (str)
                - ``feature_importances`` (list of dicts with ``feature``, ``importance``, ``description``)
                - ``error`` (str | None) — set when a model cannot be loaded
        """
        model_dir = _get_model_dir()
        model_path = os.path.join(model_dir, f"{model_name}.joblib")

        if not os.path.isfile(model_path):
            logger.warning(
                "ML model '%s' not found at '%s'. "
                "Train and save a model first using predictor.save('%s').",
                model_name,
                model_path,
                model_name,
            )
            return {
                "model_name": model_name,
                "feature_importances": [],
                "error": (
                    f"Model '{model_name}' not found. "
                    f"Expected file: {model_path}. "
                    "Please train and save a model using predictor.save(name)."
                ),
            }

        try:
            model = joblib.load(model_path)
            raw_importances: dict[str, float] = model.get_feature_importances()

            feature_importances = [
                {
                    "feature": feat,
                    "importance": Decimal(str(round(imp, 6))),
                    "description": "",
                }
                for feat, imp in sorted(raw_importances.items(), key=lambda x: -x[1])
            ]

            return {
                "model_name": model_name,
                "feature_importances": feature_importances,
                "error": None,
            }

        except Exception as exc:
            logger.exception("Failed to load or query model '%s': %s", model_name, exc)
            return {
                "model_name": model_name,
                "feature_importances": [],
                "error": f"Failed to load model '{model_name}': {exc}",
            }

    def list_available_models(self) -> list[str]:
        """Return the names (without extension) of all .joblib files in ML_MODEL_DIR."""
        model_dir = _get_model_dir()
        if not os.path.isdir(model_dir):
            return []
        return [
            os.path.splitext(f)[0]
            for f in sorted(os.listdir(model_dir))
            if f.endswith(".joblib")
        ]


# Global service instance
feature_service = FeatureImportanceService()
