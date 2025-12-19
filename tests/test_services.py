import sys
import types
from decimal import Decimal

import pytest
import yaml
from services.analytics.aggregator import signal_aggregator
from services.strategy.registry import StrategyRegistry


class DummyFundamentalService:
    def get_fundamentals(self, symbol: str):
        return {"symbol": symbol, "score": Decimal(60), "rating": "buy"}


class DummySentimentService:
    def get_sentiment(self, symbol: str):
        return {"overall_sentiment": 0.0}


def test_aggregator_handles_missing_technical(monkeypatch):
    """If technical service errors, aggregator should continue and compute based on others."""
    # Make technical service raise
    from services.analytics import (
        fundamental_service,
        sentiment_service,
        technical_service,
    )

    def _raise():
        raise RuntimeError("boom")

    monkeypatch.setattr(
        technical_service,
        "calculate_indicators",
        lambda *a, **k: (_ for _ in ()).throw(RuntimeError("boom")),
    )
    monkeypatch.setattr(
        fundamental_service,
        "get_fundamentals",
        DummyFundamentalService().get_fundamentals,
    )
    monkeypatch.setattr(
        sentiment_service,
        "get_sentiment",
        DummySentimentService().get_sentiment,
    )

    res = signal_aggregator.aggregate_signals(
        "TEST",
        include_technical=True,
    )

    assert res["technical"] is None
    assert res["fundamental"]["score"] == Decimal(60)
    assert isinstance(res["combined_score"], Decimal)
    assert isinstance(res["recommendation"], str)


def test_aggregator_all_none_returns_neutral(monkeypatch):
    """If all sources fail or return None, aggregator should return neutral 50 and 'hold'."""
    from services.analytics import (
        fundamental_service,
        sentiment_service,
        technical_service,
    )

    monkeypatch.setattr(technical_service, "calculate_indicators", lambda *a, **k: None)
    monkeypatch.setattr(fundamental_service, "get_fundamentals", lambda *a, **k: None)
    monkeypatch.setattr(sentiment_service, "get_sentiment", lambda *a, **k: None)

    res = signal_aggregator.aggregate_signals(
        "TEST", include_technical=True, include_fundamental=True, include_sentiment=True,
    )

    assert res["combined_score"] == Decimal(50)
    assert res["recommendation"] == "hold"


def test_strategy_registry_create_and_load(tmp_path):
    """StrategyRegistry should load config and create strategy instances using dynamic modules."""
    # Create a fake module with a dummy strategy class
    mod_name = "fake_mod_for_tests"
    mod = types.ModuleType(mod_name)

    class DummyStrategy:
        def __init__(self, short=10, long=50, **kwargs):
            self.short = short
            self.long = long
            self.kwargs = kwargs

    mod.DummyStrategy = DummyStrategy
    sys.modules[mod_name] = mod

    # Write a tiny YAML config
    config = {
        "default_strategy": "basic",
        "strategies": {
            "basic": {
                "module": mod_name,
                "class": "DummyStrategy",
                "params": {"short": 5, "long": 20},
            },
        },
    }

    cfg_path = tmp_path / "strategies.yaml"
    cfg_path.write_text(yaml.safe_dump(config))

    registry = StrategyRegistry(config_path=str(cfg_path))

    # Ensure list_strategies returns the config
    strategies = registry.list_strategies()
    assert "basic" in strategies

    # Create an instance with override params
    inst = registry.create_strategy("basic", override_params={"short": 42, "extra": 1})

    assert isinstance(inst, DummyStrategy)
    assert inst.short == 42
    assert inst.long == 20
    assert inst.kwargs.get("extra") == 1


def test_strategy_registry_invalid_module(tmp_path):
    """If the module doesn't import, get_strategy_class should raise ValueError."""
    config = {
        "strategies": {"broken": {"module": "non_existent_mod", "class": "NoClass"}},
    }
    cfg_path = tmp_path / "broken.yaml"
    cfg_path.write_text(yaml.safe_dump(config))

    registry = StrategyRegistry(config_path=str(cfg_path))

    with pytest.raises(ValueError):
        registry.get_strategy_class("broken")


def test_strategy_registry_missing_strategy(tmp_path):
    """Requesting a non-existent strategy should raise ValueError."""
    config = {"strategies": {"existent": {"module": "some_mod", "class": "SomeClass"}}}
    cfg_path = tmp_path / "existent.yaml"
    cfg_path.write_text(yaml.safe_dump(config))

    registry = StrategyRegistry(config_path=str(cfg_path))

    with pytest.raises(ValueError):
        registry.get_strategy_class("non_existent")
