import os
import pytest
import numpy as np
import pandas as pd

from backend.services.ai.feature_service import FeatureImportanceService
from strategy_lab.ml.models.tree_models import RandomForestPredictor


def test_feature_service_model_not_found(tmp_path, monkeypatch):
    """Returns error payload (not placeholder data) when no model file exists."""
    monkeypatch.setenv("ML_MODEL_DIR", str(tmp_path))
    service = FeatureImportanceService()
    result = service.get_feature_importance("nonexistent")

    assert result["model_name"] == "nonexistent"
    assert result["feature_importances"] == []
    assert "not found" in (result.get("error") or "").lower()


def test_feature_service_loads_real_model(tmp_path, monkeypatch):
    """Returns real importances from a saved model when the file exists."""
    monkeypatch.setenv("ML_MODEL_DIR", str(tmp_path))

    X = pd.DataFrame({"feat_a": np.random.rand(50), "feat_b": np.random.rand(50)})
    y = pd.Series(np.random.randint(0, 2, 50))
    model = RandomForestPredictor(n_estimators=5)
    model.train(X, y)
    model.save("test_rf")  # now uses ML_MODEL_DIR from env

    service = FeatureImportanceService()
    result = service.get_feature_importance("test_rf")

    assert result["model_name"] == "test_rf"
    assert result["error"] is None
    feats = {f["feature"] for f in result["feature_importances"]}
    assert "feat_a" in feats and "feat_b" in feats


def test_feature_service_list_available_models(tmp_path, monkeypatch):
    """list_available_models() returns names from ML_MODEL_DIR."""
    monkeypatch.setenv("ML_MODEL_DIR", str(tmp_path))

    X = pd.DataFrame({"x": np.random.rand(30)})
    y = pd.Series(np.random.randint(0, 2, 30))
    model = RandomForestPredictor(n_estimators=3)
    model.train(X, y)
    model.save("alpha")
    model.save("beta")

    service = FeatureImportanceService()
    names = service.list_available_models()
    assert "alpha" in names
    assert "beta" in names


def test_base_predictor_save_respects_env(tmp_path, monkeypatch):
    """BasePredictor.save() creates the directory and file using ML_MODEL_DIR."""
    monkeypatch.setenv("ML_MODEL_DIR", str(tmp_path / "models"))

    X = pd.DataFrame({"x": np.random.rand(30)})
    y = pd.Series(np.random.randint(0, 2, 30))
    model = RandomForestPredictor(n_estimators=3)
    model.train(X, y)

    saved_path = model.save("env_test")
    assert os.path.isfile(saved_path)
    assert "env_test.joblib" in saved_path
