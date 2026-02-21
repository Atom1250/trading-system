"""Core Machine Learning interfaces for Strategy Lab."""

import os
from abc import ABC, abstractmethod
from typing import Dict

import joblib
import numpy as np
import pandas as pd


def _get_model_dir() -> str:
    """Return the ML model directory, respecting the ML_MODEL_DIR env variable."""
    return os.environ.get("ML_MODEL_DIR", "ml_models")


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

    def save(self, name: str) -> str:
        """Serializes the model to <ML_MODEL_DIR>/<name>.joblib.

        Creates the model directory if it does not already exist.

        Args:
            name: Base name for the model file (without .joblib extension).

        Returns:
            Absolute path to the saved file.
        """
        model_dir = _get_model_dir()
        os.makedirs(model_dir, exist_ok=True)
        path = os.path.join(model_dir, f"{name}.joblib")
        joblib.dump(self, path)
        return path

    @classmethod
    def load(cls, name: str) -> "BasePredictor":
        """Loads a serialized model from <ML_MODEL_DIR>/<name>.joblib.

        Args:
            name: Base name of the model file (without .joblib extension).

        Returns:
            The deserialised predictor instance.
        """
        model_dir = _get_model_dir()
        path = os.path.join(model_dir, f"{name}.joblib")
        return joblib.load(path)
