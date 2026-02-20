import os
import pytest
import joblib
import numpy as np
import pandas as pd
import tempfile

from backend.services.ai.feature_service import FeatureImportanceService
from strategy_lab.ml.models.tree_models import RandomForestPredictor


def test_feature_service_fallback():
    """When no model file exists, the service should return placeholder data."""
    service = FeatureImportanceService()
    result = service.get_feature_importance("nonexistent_model")

    assert result["model_name"] == "nonexistent_model"
    assert len(result["feature_importances"]) > 0
    # Placeholder entries have a description
    assert result["feature_importances"][0]["description"] != ""


def test_feature_service_loads_real_model(tmp_path):
    """When a valid model file exists, service should return its feature importances."""
    # Train a tiny RF model
    X = pd.DataFrame({"feat_a": np.random.rand(50), "feat_b": np.random.rand(50)})
    y = pd.Series(np.random.randint(0, 2, 50))
    model = RandomForestPredictor(n_estimators=5)
    model.train(X, y)

    # Save the model to a temp directory
    model.save(str(tmp_path / "test_rf.joblib"))

    # Point service at the temp directory
    service = FeatureImportanceService()
    import backend.services.ai.feature_service as fs
    original_dir = fs.MODEL_DIR
    fs.MODEL_DIR = str(tmp_path)

    try:
        result = service.get_feature_importance("test_rf")
        assert result["model_name"] == "test_rf"
        feats = {f["feature"] for f in result["feature_importances"]}
        assert "feat_a" in feats
        assert "feat_b" in feats
    finally:
        fs.MODEL_DIR = original_dir
