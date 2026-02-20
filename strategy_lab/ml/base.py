"""Core Machine Learning interfaces for Strategy Lab."""

from abc import ABC, abstractmethod
from typing import Dict, Any
import pandas as pd
import numpy as np
import joblib

class BasePredictor(ABC):
    """Abstract base class for all ML predictors in the Strategy Lab."""

    @abstractmethod
    def train(self, X: pd.DataFrame, y: pd.Series) -> None:
        """Trains the model on the provided features and targets."""
        pass

    @abstractmethod
    def predict(self, X: pd.DataFrame) -> np.ndarray:
        """Generates predictions for the given features."""
        pass

    @abstractmethod
    def get_feature_importances(self) -> Dict[str, float]:
        """Returns a dictionary mapping feature names to their importance scores."""
        pass

    def save(self, path: str) -> None:
        """Serializes the model to disk using joblib."""
        joblib.dump(self, path)

    @classmethod
    def load(cls, path: str) -> 'BasePredictor':
        """Loads a serialized model from disk using joblib."""
        return joblib.load(path)
