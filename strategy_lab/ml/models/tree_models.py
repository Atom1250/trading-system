"""Tree-based Machine Learning Models."""

import pandas as pd
import numpy as np
from typing import Dict, Any

from xgboost import XGBClassifier, XGBRegressor
from sklearn.ensemble import RandomForestClassifier

from strategy_lab.ml.base import BasePredictor

class XGBoostPredictor(BasePredictor):
    """Predictor wrapper for XGBoost models."""

    def __init__(self, objective: str = "binary:logistic", **kwargs: Any):
        """Initializes the XGBoost model."""
        if objective in ["binary:logistic", "multi:softmax", "multi:softprob"]:
            self.model = XGBClassifier(objective=objective, **kwargs)
        else:
            self.model = XGBRegressor(objective=objective, **kwargs)
        self.feature_names = []

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Trains the XGBoost model."""
        self.feature_names = list(X.columns)
        self.model.fit(X, y)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generates predictions."""
        return self.model.predict(X)

    def get_feature_importances(self) -> Dict[str, float]:
        """Returns feature importances mapped to names."""
        if not hasattr(self.model, "feature_importances_"):
            return {}
            
        importances = self.model.feature_importances_
        return {name: float(imp) for name, imp in zip(self.feature_names, importances)}

class RandomForestPredictor(BasePredictor):
    """Predictor wrapper for Sklearn Random Forest Classifier."""

    def __init__(self, n_estimators: int = 100, **kwargs: Any):
        """Initializes the Random Forest model."""
        self.model = RandomForestClassifier(n_estimators=n_estimators, **kwargs)
        self.feature_names = []

    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Trains the Random Forest model."""
        self.feature_names = list(X.columns)
        self.model.fit(X, y)

    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generates predictions."""
        return self.model.predict(X)

    def get_feature_importances(self) -> Dict[str, float]:
        """Returns feature importances mapped to names."""
        if not hasattr(self.model, "feature_importances_"):
            return {}
            
        importances = self.model.feature_importances_
        return {name: float(imp) for name, imp in zip(self.feature_names, importances)}
