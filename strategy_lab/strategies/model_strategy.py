"""ML-backed strategy that converts model scores to trading signals."""

from __future__ import annotations

import pandas as pd

from strategy_lab.ml.feature_registry import FeatureRegistry
from strategy_lab.ml.model_interface import ScoreModel
from strategy_lab.ml.score_policy import score_to_signal_series
from strategy_lab.strategies.base import FactorPanels, MarketDataSlices, Strategy


class ModelScoreStrategy(Strategy):
    """Strategy that builds features, predicts scores, and emits signals."""

    def __init__(
        self,
        config,
        *,
        model: ScoreModel,
        feature_registry: FeatureRegistry,
    ):
        super().__init__(config)
        self.model = model
        self.feature_registry = feature_registry

    def generate_signals(
        self,
        data: MarketDataSlices,
        factor_panels: FactorPanels,
    ) -> dict[str, pd.Series]:
        del factor_panels
        features = self.config.parameters.get("feature_names", [])
        long_threshold = float(self.config.parameters.get("long_threshold", 0.1))
        short_threshold = float(self.config.parameters.get("short_threshold", -0.1))

        out: dict[str, pd.Series] = {}
        for symbol, market_slice in data.items():
            feature_frame = self.feature_registry.build(market_slice.df, features)
            scores = self.model.predict_scores(feature_frame).reindex(
                market_slice.df.index
            )
            out[symbol] = score_to_signal_series(
                scores.fillna(0.0),
                long_threshold=long_threshold,
                short_threshold=short_threshold,
            )
        return out
