"""Strategy registry for dynamic strategy loading."""

import importlib
import logging
import sys
from pathlib import Path
from typing import Any, Optional

import yaml

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from config.settings import STRATEGY_CONFIG_PATH

logger = logging.getLogger(__name__)


class StrategyRegistry:
    """Registry for managing trading strategies."""

    def __init__(self, config_path: Optional[str] = None):
        self.config_path: str = config_path or STRATEGY_CONFIG_PATH
        self._strategies: dict[str, dict[str, Any]] = {}
        self._default_strategy: Optional[str] = None
        self._load_strategies()

    def _load_strategies(self):
        """Load strategies from YAML config."""
        try:
            with open(self.config_path) as f:
                config = yaml.safe_load(f)

            self._default_strategy = config.get("default_strategy")
            strategies_config = config.get("strategies", {})

            for name, strategy_def in strategies_config.items():
                self._strategies[name] = {
                    "module": strategy_def.get("module"),
                    "class": strategy_def.get("class"),
                    "params": strategy_def.get("params", {}),
                }
        except (OSError, yaml.YAMLError) as exc:
            logger.exception("Error loading strategies from %s: %s", self.config_path, exc)
            self._strategies = {}
            self._default_strategy = None

    def get_strategy_class(self, name: str):
        """Get strategy class by name."""
        if name not in self._strategies:
            raise ValueError(f"Strategy '{name}' not found")

        strategy_def = self._strategies[name]
        module_name = strategy_def["module"]
        class_name = strategy_def["class"]

        try:
            module = importlib.import_module(module_name)
            strategy_class = getattr(module, class_name)
            return strategy_class
        except (ImportError, AttributeError) as e:
            raise ValueError(f"Failed to load strategy '{name}': {e}")

    def create_strategy(
        self, name: str, override_params: Optional[dict[str, Any]] = None,
    ):
        """Create strategy instance with parameters."""
        if name not in self._strategies:
            raise ValueError(f"Strategy '{name}' not found")

        strategy_class = self.get_strategy_class(name)
        strategy_def = self._strategies[name]

        # Merge default params with overrides
        params = dict(strategy_def["params"])
        if override_params:
            # Filter params based on class signature
            import inspect

            sig = inspect.signature(strategy_class.__init__)
            valid_params = {
                k: v
                for k, v in override_params.items()
                if k in sig.parameters
                or any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())
            }
            params.update(valid_params)

        # Filter params to only those accepted by the class
        import inspect

        sig = inspect.signature(strategy_class.__init__)
        final_params = {
            k: v
            for k, v in params.items()
            if k in sig.parameters
            or any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())
        }

        return strategy_class(**final_params)

    def list_strategies(self) -> dict[str, dict[str, Any]]:
        """List all available strategies."""
        return {
            name: {
                "module": info["module"],
                "class": info["class"],
                "params": info["params"],
            }
            for name, info in self._strategies.items()
        }

    def get_default_strategy(self) -> Optional[str]:
        """Get default strategy name."""
        return self._default_strategy


# Global registry instance
registry = StrategyRegistry()
