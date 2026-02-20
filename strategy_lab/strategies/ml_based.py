"""ML Strategy Base Class bridging the strategy engine and ML predictors."""

from typing import Optional, Any
import pandas as pd

from strategy_lab.strategies.base import Strategy, SignalType
from strategy_lab.config import StrategyConfig
from strategy_lab.data.base import MarketDataSlice
from strategy_lab.ml.base import BasePredictor
from strategy_lab.ml.features import TimeSeriesFeatureGenerator

# Type alias matching base.py conventions
MarketDataSlices = dict[str, MarketDataSlice]
FactorPanels = dict[str, pd.DataFrame]

_SIGNAL_MAP = {
    1: 1,    # Predictor says UP  -> LONG  (+1)
    0: -1,   # Predictor says DOWN -> SHORT (-1)
}


class MLStrategy(Strategy):
    """A trading strategy driven by a trained ML predictor.

    Usage:
        predictor = XGBoostPredictor()
        predictor.train(X_train, y_train)

        config = StrategyConfig(name="ml_xgb", parameters={})
        strategy = MLStrategy(config=config, predictor=predictor)

        signals = strategy.generate_signals(data, factor_panels)
    """

    def __init__(
        self,
        config: StrategyConfig,
        predictor: BasePredictor,
        feature_generator: Optional[TimeSeriesFeatureGenerator] = None,
    ):
        super().__init__(config=config)
        self.predictor = predictor
        self.feature_generator = feature_generator or TimeSeriesFeatureGenerator()

    def generate_signals(
        self,
        data: MarketDataSlices,
        factor_panels: FactorPanels,
    ) -> dict[str, pd.Series]:
        """Generate trading signals for each symbol using the ML predictor.

        Returns:
            Dict mapping symbol -> pd.Series of signal values (+1=long, -1=short, 0=flat).
        """
        signals: dict[str, pd.Series] = {}

        for symbol, market_slice in data.items():
            df = market_slice.df.copy()

            # Rename columns to title case so feature generator can find 'Close'.
            df.columns = [c.capitalize() for c in df.columns]

            if "Close" not in df.columns or len(df) < 50:
                # Insufficient data to generate meaningful features — emit flat.
                signals[symbol] = pd.Series(0, index=df.index, dtype=int, name=symbol)
                continue

            try:
                features_df = self.feature_generator.generate_features(df)
            except Exception:
                signals[symbol] = pd.Series(0, index=df.index, dtype=int, name=symbol)
                continue

            # Drop rows with NaN features (e.g. initial warm-up period).
            valid = features_df.dropna()
            if valid.empty:
                signals[symbol] = pd.Series(0, index=df.index, dtype=int, name=symbol)
                continue

            try:
                raw_preds = self.predictor.predict(valid)
            except Exception:
                signals[symbol] = pd.Series(0, index=df.index, dtype=int, name=symbol)
                continue

            # Map predictions to +1 / -1 using vectorised operation.
            mapped = pd.Series(raw_preds, index=valid.index, dtype=int).map(_SIGNAL_MAP).fillna(0).astype(int)

            # Reindex to the full date range (warm-up rows are 0 / flat).
            signal_series = mapped.reindex(df.index, fill_value=0)
            signal_series.name = symbol
            signals[symbol] = signal_series

        return signals
