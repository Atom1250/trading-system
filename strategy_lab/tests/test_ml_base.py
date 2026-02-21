import pandas as pd
import numpy as np
import os
import pytest
from strategy_lab.ml.base import BasePredictor

class MockPredictor(BasePredictor):
    def train(self, X, y):
        self.trained = True

    def predict(self, X):
        return np.zeros(len(X))

    def get_feature_importances(self):
        return {"feature_a": 1.0}

def test_base_predictor_serialization(tmp_path, monkeypatch):
    """save(name) uses ML_MODEL_DIR env var; load(name) restores the model."""
    monkeypatch.setenv("ML_MODEL_DIR", str(tmp_path))

    predictor = MockPredictor()
    predictor.train(pd.DataFrame(), pd.Series())

    saved_path = predictor.save("test_model")
    assert os.path.isfile(saved_path)
    assert saved_path.endswith("test_model.joblib")

    loaded = MockPredictor.load("test_model")
    assert getattr(loaded, "trained", False) is True
    assert loaded.get_feature_importances() == {"feature_a": 1.0}
