# run_strategy.py

import importlib
import logging
from typing import Any, Dict

import pandas as pd
import yaml

from ingestion.alpha_vantage_client import AlphaVantageClient
from ingestion.cache import load_cached_daily, save_cached_daily
from indicators.technicals import sma  # assumes sma(df, window) -> pandas.Series
from backtesting.backtester import Backtester
from backtesting.portfolio_backtester import PortfolioBacktester
from config.settings import ALPHA_VANTAGE_API_KEY, setup_logging


logger = logging.getLogger(__name__)


STRATEGY_CONFIG_PATH = "config/strategies.yaml"


def load_strategy_config(config_path: str = STRATEGY_CONFIG_PATH) -> Dict[str, Any]:
    """Load strategy configuration from YAML."""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.error("Strategy config not found at %s", config_path)
        raise
    except yaml.YAMLError as exc:
        logger.error("Failed to parse strategy config: %s", exc)
        raise

    return config


def build_strategy(
    strategy_name: str | None,
    *,
    override_params: Dict[str, Any] | None = None,
    config_path: str = STRATEGY_CONFIG_PATH,
):
    """Instantiate a strategy dynamically based on YAML configuration."""
    config = load_strategy_config(config_path)
    default_strategy = config.get("default_strategy")
    strategies = config.get("strategies", {})

    chosen_strategy = strategy_name or default_strategy
    if not chosen_strategy:
        raise ValueError("No strategy specified and no default_strategy defined in config.")

    if chosen_strategy not in strategies:
        raise ValueError(
            f"Strategy '{chosen_strategy}' not found in configuration. Available: {list(strategies)}"
        )

    strategy_def = strategies[chosen_strategy]
    module_name = strategy_def.get("module")
    class_name = strategy_def.get("class")
    if not module_name or not class_name:
        raise ValueError(f"Strategy definition for '{chosen_strategy}' is incomplete.")

    params: Dict[str, Any] = dict(strategy_def.get("params", {}))
    if override_params:
        params.update(override_params)

    try:
        module = importlib.import_module(module_name)
    except ImportError as exc:
        logger.error("Unable to import strategy module %s: %s", module_name, exc)
        raise

    try:
        strategy_class = getattr(module, class_name)
    except AttributeError:
        logger.error("Strategy class %s not found in module %s", class_name, module_name)
        raise

    return strategy_class(**params), chosen_strategy


def run_backtest(
    symbol: str,
    short_window: int,
    long_window: int,
    outputsize: str = "compact",
    *,
    free_tier_only: bool = True,
    use_cache: bool = True,
    force_refresh: bool = False,
    strategy_name: str | None = None,
):
    """
    Core function that runs the full backtest and returns a results dict.
    This is called by both the console UI and the Streamlit UI.
    """
    # 1. Download data (cache-aware)
    cache_loaded = False
    cache_seeded = False
    df = None
    active_strategy_name = strategy_name

    if use_cache and not force_refresh:
        df = load_cached_daily(symbol, outputsize=outputsize)
        if df is not None:
            cache_loaded = True

    if df is None:
        effective_outputsize = outputsize
        if free_tier_only and outputsize == "full":
            logger.info("Free tier mode: forcing outputsize='compact' to limit data usage.")
            effective_outputsize = "compact"

        if use_cache and not force_refresh:
            logger.info(
                "No cache found for %s. Fetching from Alpha Vantage and seeding cache.",
                symbol,
            )
        elif use_cache and force_refresh:
            logger.info("Force refresh enabled for %s. Fetching from Alpha Vantage.", symbol)
        else:
            logger.info("Fetching live data for %s from Alpha Vantage.", symbol)

        if not ALPHA_VANTAGE_API_KEY:
            raise RuntimeError(
                "ALPHA_VANTAGE_API_KEY is not set and no cached data is available. "
                "Add it to your environment or .env file to fetch data."
            )

        client = AlphaVantageClient(ALPHA_VANTAGE_API_KEY)
        df = client.get_daily(
            symbol=symbol,
            outputsize=effective_outputsize,
            fallback_to_free_tier=free_tier_only,
        )

        if use_cache:
            save_cached_daily(symbol, df, outputsize=effective_outputsize)
            cache_seeded = True

    data_source = "cache" if cache_loaded else "api"

    # 2. Compute indicators needed by the strategy
    df["sma_short"] = sma(df, window=short_window)
    df["sma_long"] = sma(df, window=long_window)

    # 3. Run strategy
    override_params: Dict[str, Any] = {
        "short_window": short_window,
        "long_window": long_window,
    }
    try:
        strategy, active_strategy_name = build_strategy(
            strategy_name, override_params=override_params
        )
    except Exception as exc:
        logger.error("Failed to load strategy: %s", exc)
        raise

    df = strategy.run(df)

    # 4. Run backtest
    backtester = Backtester()
    results = backtester.run(df)

    plot_path = None
    try:
        plot_path = backtester.plot_results(df, symbol=symbol)
        results["plot_path"] = plot_path
    except Exception as exc:
        logger.warning("Failed to generate plot for %s: %s", symbol, exc)

    results.update(
        {
            "data_source": data_source,
            "cache_used": cache_loaded,
            "cache_seeded": cache_seeded,
            "force_refresh": force_refresh,
            "strategy": active_strategy_name,
        }
    )

    return results


def main():
    """
    Simple console-based UI that asks the user for inputs.
    This replaces the strict command-line-argument approach that caused the error.
    """
    setup_logging()
    logger.info("=== Trading System Runner ===")

    try:
        strategy_config = load_strategy_config()
    except Exception:
        logger.error("Unable to load strategy configuration. Aborting.")
        return

    strategies = strategy_config.get("strategies", {})
    default_strategy = strategy_config.get("default_strategy")
    strategy_names = list(strategies.keys())

    raw_symbols = input("Enter symbol or comma-separated symbols (e.g. AAPL or AAPL,MSFT): ")
    symbols = [s.strip().upper() for s in raw_symbols.split(",") if s.strip()]
    if not symbols:
        logger.error("At least one symbol is required.")
        return

    try:
        short_window = int(input("Enter SHORT moving average window (e.g. 20): ").strip())
        long_window = int(input("Enter LONG moving average window (e.g. 50): ").strip())
    except ValueError:
        logger.error("Short and long windows must be integers.")
        return

    if short_window >= long_window:
        logger.error("Short window must be smaller than long window.")
        return

    outputsize = input("Output size 'compact' or 'full' [compact]: ").strip().lower()
    if outputsize == "":
        outputsize = "compact"
    if outputsize not in ("compact", "full"):
        logger.warning("Invalid output size, defaulting to 'compact'.")
        outputsize = "compact"

    strategy_prompt = (
        f"Enter strategy name {strategy_names} [{default_strategy}]: " if strategy_names else "Enter strategy name: "
    )
    selected_strategy = input(strategy_prompt).strip()
    if not selected_strategy:
        selected_strategy = default_strategy
    if selected_strategy and selected_strategy not in strategy_names:
        logger.warning(
            "Strategy '%s' not found in config. Falling back to default '%s'.",
            selected_strategy,
            default_strategy,
        )
        selected_strategy = default_strategy

    logger.info("Running backtest...")

    if len(symbols) == 1:
        symbol = symbols[0]
        results = run_backtest(
            symbol,
            short_window,
            long_window,
            outputsize,
            strategy_name=selected_strategy,
        )

        # Expected keys in results: 'cumulative_return', 'max_drawdown'
        logger.info("\n=== Backtest Summary ===")
        logger.info("Symbol: %s", symbol)
        logger.info("Short window: %s, Long window: %s", short_window, long_window)
        if "cumulative_return" in results:
            logger.info("Cumulative return: %.2f%%", results["cumulative_return"] * 100)
        if "max_drawdown" in results:
            logger.info("Max drawdown: %.2f%%", results["max_drawdown"] * 100)
        if "results_path" in results:
            logger.info("Detailed results saved to: %s", results["results_path"])
        else:
            logger.info(
                "Detailed results may be in reports/results.csv (depending on your Backtester implementation)."
            )
        plot_path = results.get("plot_path")
        if plot_path:
            logger.info("Backtest chart saved to: %s", plot_path)
        else:
            logger.info("No backtest chart generated.")
    else:
        logger.info("Running backtests for %s symbols...", len(symbols))
        portfolio_inputs: dict[str, pd.DataFrame] = {}
        for symbol in symbols:
            logger.info("--- %s ---", symbol)
            try:
                results = run_backtest(
                    symbol,
                    short_window,
                    long_window,
                    outputsize,
                    strategy_name=selected_strategy,
                )
            except Exception as exc:  # surface per-symbol errors without stopping all
                logger.error("Error running backtest for %s: %s", symbol, exc)
                continue

            logger.info("Short window: %s, Long window: %s", short_window, long_window)
            if "cumulative_return" in results:
                logger.info("Cumulative return: %.2f%%", results["cumulative_return"] * 100)
            if "max_drawdown" in results:
                logger.info("Max drawdown: %.2f%%", results["max_drawdown"] * 100)
            if "results_path" in results:
                logger.info("Detailed results saved to: %s", results["results_path"])
            else:
                logger.info(
                    "Detailed results may be in reports/results.csv (depending on your Backtester implementation)."
                )

            if "results" in results:
                portfolio_inputs[symbol] = results["results"]

        if portfolio_inputs:
            logger.info("=== Portfolio Summary ===")
            try:
                portfolio_backtester = PortfolioBacktester()
                portfolio_results = portfolio_backtester.run(portfolio_inputs)
            except Exception as exc:
                logger.error("Error running portfolio backtest: %s", exc)
            else:
                logger.info(
                    "Portfolio cumulative return: %.2f%%",
                    portfolio_results["cumulative_return"] * 100,
                )
                logger.info(
                    "Portfolio max drawdown: %.2f%%",
                    portfolio_results["max_drawdown"] * 100,
                )
                if "results_path" in portfolio_results:
                    logger.info(
                        "Portfolio results saved to: %s", portfolio_results["results_path"]
                    )


if __name__ == "__main__":
    main()
