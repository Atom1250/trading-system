"""Model interface contract for score-producing ML models."""

from __future__ import annotations

from abc import ABC, abstractmethod

import pandas as pd


class ScoreModel(ABC):
    """Interface for models that output a continuous score per row."""

    @abstractmethod
    def predict_scores(self, features: pd.DataFrame) -> pd.Series:
        """Predict score per timestamp index."""
