import traceback

import pydantic
from services.strategy.optimization_service import optimization_service


def test_optimization():
    print(f"Pydantic Version: {pydantic.VERSION}")
    print("Testing OptimizationService...")
    try:
        # Define simple parameter ranges
        param_ranges = {
            "short_window": {"type": "int", "min": 5, "max": 15, "step": 5},
            "long_window": {"type": "int", "min": 20, "max": 40, "step": 10},
        }

        # Run optimization
        result = optimization_service.optimize(
            strategy_name="moving_average_crossover",
            symbol="AAPL",
            parameter_ranges=param_ranges,
            initial_capital=100000.0,
            data_source="local",
            n_trials=2,
            metric="total_return_pct",
            direction="maximize",
        )

        print("Optimization Success!")
        print(f"Best Value: {result['best_value']}")
        print(f"Best Params: {result['best_params']}")

        import json

        print("Testing JSON serialization...")
        _ = json.dumps(result)
        print("JSON Serialization Success!")

    except Exception as exc:
        print("Optimization Failed!", exc)
        traceback.print_exc()


if __name__ == "__main__":
    test_optimization()
