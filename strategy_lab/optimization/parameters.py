"""Parameter management for optimization.

This module provides classes for defining parameter spaces and sampling
parameters for optimization runs.
"""

import random
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from strategy_lab.config import ParameterBound


@dataclass
class ParameterSpace:
    """Manages the space of possible parameter values.

    Attributes:
        bounds: Dictionary mapping parameter names to their bounds

    """

    bounds: dict[str, ParameterBound] = field(default_factory=dict)

    def __post_init__(self):
        """Initialize and validate."""
        # bounds are passed in constructor or empty dict by default

    def add_bound(self, bound: ParameterBound):
        """Add a parameter bound definition."""
        self.bounds[bound.name] = bound

    def sample(self) -> dict[str, Any]:
        """Sample a random set of parameters from the space.

        Returns:
            Dictionary of parameter names and sampled values

        """
        params = {}
        for name, bound in self.bounds.items():
            if bound.param_type == "int":
                val = random.randint(int(bound.min_value), int(bound.max_value))
                if bound.step:
                    # Round to nearest step
                    steps = round((val - bound.min_value) / bound.step)
                    val = int(bound.min_value + (steps * bound.step))
                params[name] = val

            elif bound.param_type == "float":
                val = random.uniform(bound.min_value, bound.max_value)
                if bound.step:
                    steps = round((val - bound.min_value) / bound.step)
                    val = bound.min_value + (steps * bound.step)
                params[name] = val

            elif bound.param_type == "categorical":
                params[name] = random.choice(bound.categorical_values)

            else:
                raise ValueError(f"Unknown parameter type: {bound.param_type}")

        return params

    def grid_search_space(self) -> list[dict[str, Any]]:
        """Generate full grid of parameters (if feasible).

        Note: This can be combinatorial explosive.
        """
        # Simple implementation for grid generation if requested
        # For now, leaving as placeholder or limited implementation
        import itertools

        keys = []
        values_lists = []

        for name, bound in self.bounds.items():
            keys.append(name)
            if bound.param_type == "categorical":
                values_lists.append(bound.categorical_values)
            elif bound.step:
                # Arange equivalent
                vals = np.arange(
                    bound.min_value,
                    bound.max_value + bound.step / 1000,
                    bound.step,
                )
                # Ensure type correctness
                if bound.param_type == "int":
                    vals = [int(x) for x in vals]
                else:
                    vals = [float(x) for x in vals]
                values_lists.append(vals)
            else:
                # Continuous without step - cannot grid search properly without discretized steps
                # Fallback: create 10 steps
                vals = np.linspace(bound.min_value, bound.max_value, 10)
                values_lists.append(vals)

        # Cartesian product
        all_combinations = list(itertools.product(*values_lists))

        result = []
        for combo in all_combinations:
            result.append(dict(zip(keys, combo)))

        return result
