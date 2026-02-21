import pandas as pd
import numpy as np
import pytest
from strategy_lab.config import StrategyConfig
from strategy_lab.data.base import MarketDataSlice
from strategy_lab.ml.base import BasePredictor
from strategy_lab.strategies.ml_based import MLStrategy


class AlwaysBuyPredictor(BasePredictor):
    def train(self, X, y): pass
    def predict(self, X): return np.ones(len(X), dtype=int)
    def get_feature_importances(self): return {}


class AlwaysSellPredictor(BasePredictor):
    def train(self, X, y): pass
    def predict(self, X): return np.zeros(len(X), dtype=int)
    def get_feature_importances(self): return {}


def _make_slice(symbol: str, n=100) -> MarketDataSlice:
    dates = pd.date_range("2023-01-01", periods=n)
    df = pd.DataFrame({
        "close": np.linspace(10, 110, n),
        "open": np.linspace(10, 110, n),
        "high": np.linspace(11, 111, n),
        "low": np.linspace(9, 109, n),
        "volume": np.ones(n) * 1000,
    }, index=dates)
    return MarketDataSlice(symbol=symbol, df=df)


def _config(name="test_ml") -> StrategyConfig:
    return StrategyConfig(name=name, parameters={})


def test_ml_strategy_long_signals():
    data = {"AAPL": _make_slice("AAPL")}
    strategy = MLStrategy(config=_config(), predictor=AlwaysBuyPredictor())
    signals = strategy.generate_signals(data, {})
    
    assert "AAPL" in signals
    sig = signals["AAPL"]
    # At least some non-zero signals after the warm-up window
    assert (sig == 1).sum() > 0


def test_ml_strategy_short_signals():
    data = {"MSFT": _make_slice("MSFT")}
    strategy = MLStrategy(config=_config(), predictor=AlwaysSellPredictor())
    signals = strategy.generate_signals(data, {})
    
    assert "MSFT" in signals
    sig = signals["MSFT"]
    # Sell predictor should produce -1 signals after warm-up
    assert (sig == -1).sum() > 0


def test_ml_strategy_insufficient_data():
    """With fewer than 50 bars the strategy should emit all-zero signals."""
    dates = pd.date_range("2023-01-01", periods=20)
    df = pd.DataFrame({"close": np.linspace(10, 30, 20)}, index=dates)
    data = {"SHORT": MarketDataSlice(symbol="SHORT", df=df)}
    strategy = MLStrategy(config=_config(), predictor=AlwaysBuyPredictor())
    signals = strategy.generate_signals(data, {})
    
    assert "SHORT" in signals
    assert (signals["SHORT"] == 0).all()
