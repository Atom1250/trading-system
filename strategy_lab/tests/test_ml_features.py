import pandas as pd
import numpy as np
import pytest
from strategy_lab.ml.features import TimeSeriesFeatureGenerator

@pytest.fixture
def sample_ohlcv():
    dates = pd.date_range("2023-01-01", periods=100)
    data = {"Close": np.linspace(10, 110, 100)}  # Steadily increasing closing price
    return pd.DataFrame(data, index=dates)

def test_generate_features(sample_ohlcv):
    generator = TimeSeriesFeatureGenerator()
    features = generator.generate_features(sample_ohlcv)
    
    assert "return_lag_1" in features.columns
    assert "volatility_10" in features.columns
    assert "dist_sma_10" in features.columns
    assert "rsi_14" in features.columns
    
    # Check that lag length matches input DataFrame length
    assert len(features) == len(sample_ohlcv)

def test_generate_targets(sample_ohlcv):
    generator = TimeSeriesFeatureGenerator()
    targets = generator.generate_targets(sample_ohlcv, horizon=5)
    
    assert isinstance(targets, pd.Series)
    assert len(targets) == len(sample_ohlcv)
    assert targets.name == "target"
    
    # Since prices are steadily increasing, everything to len-horizon should be 1
    assert (targets.iloc[:-5] == 1).all()
    # The last 5 rows should be NaN since future prices don't exist
    assert targets.iloc[-5:].isna().all()
