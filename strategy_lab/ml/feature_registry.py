"""Feature registry/pipeline for ML-driven strategies."""

from __future__ import annotations

from collections.abc import Callable

import pandas as pd

FeatureFn = Callable[[pd.DataFrame], pd.Series]


class FeatureRegistry:
    """Registry for feature-building callables."""

    def __init__(self):
        self._builders: dict[str, FeatureFn] = {}

    def register(self, name: str, fn: FeatureFn) -> None:
        self._builders[name] = fn

    def build(self, df: pd.DataFrame, feature_names: list[str]) -> pd.DataFrame:
        out = pd.DataFrame(index=df.index)
        for name in feature_names:
            if name not in self._builders:
                raise KeyError(f"Feature '{name}' is not registered")
            series = self._builders[name](df)
            out[name] = series.reindex(df.index)
        return out
