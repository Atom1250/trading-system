from __future__ import annotations

from datetime import datetime

import pandas as pd

from strategy_lab.backtest.runner import StrategyLabBacktestRunner
from strategy_lab.config import StrategyConfig
from strategy_lab.data.base import MarketDataSlice
from strategy_lab.ml.feature_registry import FeatureRegistry
from strategy_lab.ml.model_interface import ScoreModel
from strategy_lab.strategies.model_strategy import ModelScoreStrategy


class _InMemoryProvider:
    def __init__(self, payload: dict[str, pd.DataFrame]):
        self.payload = payload

    def get_history(
        self,
        symbol: str,
        start: datetime,
        end: datetime,
    ) -> MarketDataSlice:
        df = self.payload[symbol]
        df = df.loc[(df.index >= start) & (df.index <= end)]
        return MarketDataSlice(symbol=symbol, df=df.copy())


class _DummyLinearModel(ScoreModel):
    def predict_scores(self, features: pd.DataFrame) -> pd.Series:
        # Deterministic score: weighted sum of normalized features.
        score = pd.Series(0.0, index=features.index)
        for col in features.columns:
            score = score + features[col].fillna(0.0)
        return score


def _fixture_df() -> pd.DataFrame:
    idx = pd.date_range("2025-06-01", periods=6, freq="D")
    close = [100.0, 101.0, 102.5, 101.0, 103.0, 104.0]
    return pd.DataFrame(
        {
            "open": close,
            "high": [p + 1.0 for p in close],
            "low": [p - 1.0 for p in close],
            "close": close,
            "volume": [1_000_000] * len(close),
        },
        index=idx,
    )


def test_dummy_model_strategy_backtest_runs_and_is_stable():
    symbol = "AAPL"
    df = _fixture_df()
    registry = FeatureRegistry()
    registry.register("mom1", lambda frame: frame["close"].pct_change().fillna(0.0))
    registry.register(
        "dist_from_mean",
        lambda frame: (frame["close"] / frame["close"].rolling(3).mean() - 1.0).fillna(
            0.0
        ),
    )

    strategy = ModelScoreStrategy(
        StrategyConfig(
            name="dummy_model_strategy",
            parameters={
                "feature_names": ["mom1", "dist_from_mean"],
                "long_threshold": 0.001,
                "short_threshold": -0.001,
            },
            universe=[symbol],
            initial_capital=100_000.0,
        ),
        model=_DummyLinearModel(),
        feature_registry=registry,
    )

    runner = StrategyLabBacktestRunner(data_provider=_InMemoryProvider({symbol: df}))
    first = runner.run(
        strategy=strategy,
        start_date=df.index.min().to_pydatetime(),
        end_date=df.index.max().to_pydatetime(),
        universe=[symbol],
        initial_capital=100_000.0,
    )
    second = runner.run(
        strategy=strategy,
        start_date=df.index.min().to_pydatetime(),
        end_date=df.index.max().to_pydatetime(),
        universe=[symbol],
        initial_capital=100_000.0,
    )

    assert first.portfolio_history is not None and not first.portfolio_history.empty
    assert first.trade_log is not None and not first.trade_log.empty
    assert len(first.portfolio_history) == len(df)
    pd.testing.assert_frame_equal(first.portfolio_history, second.portfolio_history)
    pd.testing.assert_frame_equal(first.trade_log, second.trade_log)
