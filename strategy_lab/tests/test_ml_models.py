import pandas as pd
import numpy as np
import pytest
from strategy_lab.ml.models.tree_models import XGBoostPredictor, RandomForestPredictor

@pytest.fixture
def sample_data():
    X = pd.DataFrame({
        "feature1": np.random.rand(100),
        "feature2": np.random.rand(100)
    })
    y = pd.Series(np.random.randint(0, 2, 100))
    return X, y

def test_xgboost_predictor(sample_data):
    X, y = sample_data
    model = XGBoostPredictor()
    
    # Test training
    model.train(X, y)
    assert model.feature_names == ["feature1", "feature2"]
    
    # Test predicting
    preds = model.predict(X)
    assert len(preds) == 100
    
    # Test feature importances
    importances = model.get_feature_importances()
    assert "feature1" in importances
    assert "feature2" in importances
    assert isinstance(importances["feature1"], float)

def test_random_forest_predictor(sample_data):
    X, y = sample_data
    model = RandomForestPredictor(n_estimators=10)
    
    # Test training
    model.train(X, y)
    assert model.feature_names == ["feature1", "feature2"]
    
    # Test predicting
    preds = model.predict(X)
    assert len(preds) == 100
    
    # Test feature importances
    importances = model.get_feature_importances()
    assert "feature1" in importances
    assert "feature2" in importances
    assert isinstance(importances["feature1"], float)
