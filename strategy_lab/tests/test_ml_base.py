import pandas as pd
import numpy as np
import pytest
import os
from strategy_lab.ml.base import BasePredictor

class MockPredictor(BasePredictor):
    def train(self, X, y):
        self.trained = True

    def predict(self, X):
        return np.zeros(len(X))

    def get_feature_importances(self):
        return {"feature_a": 1.0}

def test_base_predictor_serialization(tmp_path):
    predictor = MockPredictor()
    predictor.train(pd.DataFrame(), pd.Series())

    save_path = tmp_path / "model.joblib"
    predictor.save(str(save_path))
    
    assert save_path.exists()
    
    loaded = MockPredictor.load(str(save_path))
    assert getattr(loaded, "trained", False) is True
    assert loaded.get_feature_importances() == {"feature_a": 1.0}
