# run_strategy.py

import argparse
import importlib
import logging
import sys
from typing import Any, Optional, Tuple, Union

import pandas as pd
import yaml

from config.settings import (
    DEFAULT_PRICE_DATA_SOURCE,
    PriceDataSource,
    ensure_data_directories,
    setup_logging,
)
from indicators.technicals import sma  # assumes sma(df, window) -> pandas.Series
from repository.fundamentals_repository import get_fundamentals
from repository.prices_repository import get_prices_for_backtest
from research.experiments.optuna_ma_optimization import optimize_ma_strategy_for_symbol
from strategy_lab.backtest.engine import StrategyBacktestEngine

# Strategy Lab Imports
from strategy_lab.config import RiskConfig, StrategyConfig
from strategy_lab.data.providers import YFinanceHistoricalProvider
from strategy_lab.factors.base import FactorRegistry
from strategy_lab.risk.engine import RiskEngine
from strategy_lab.strategies.rule_based import MultiSignalRuleStrategy
from trading_backtester.backtester import Backtester
from trading_backtester.portfolio_backtester import PortfolioBacktester

# Ensure factors are registered


logger = logging.getLogger(__name__)


STRATEGY_CONFIG_PATH = "config/strategies.yaml"


def load_strategy_config(config_path: str = STRATEGY_CONFIG_PATH) -> dict[str, Any]:
    """Load strategy configuration from YAML."""
    try:
        with open(config_path, encoding="utf-8") as f:
            config = yaml.safe_load(f) or {}
    except FileNotFoundError:
        logger.error("Strategy config not found at %s", config_path)
        raise
    except yaml.YAMLError as exc:
        logger.error("Failed to parse strategy config: %s", exc)
        raise

    return config


def _default_windows(
    config: dict[str, Any],
    strategy_name: Optional[str],
) -> Tuple[Optional[int], Optional[int]]:
    """Return default short/long windows from the strategy config if present."""
    strategies = config.get("strategies", {})
    strategy_def = strategies.get(strategy_name or "")
    if not strategy_def:
        strategy_def = strategies.get(config.get("default_strategy", ""))

    params = (strategy_def or {}).get("params", {})
    return params.get("short_window"), params.get("long_window")


def _coerce_data_source(
    value: Optional[Union[str, PriceDataSource]]
) -> PriceDataSource:
    if value is None:
        return DEFAULT_PRICE_DATA_SOURCE
    if isinstance(value, PriceDataSource):
        return value
    try:
        return PriceDataSource(value.lower())
    except ValueError as exc:
        valid = ", ".join(ds.value for ds in PriceDataSource)
        raise ValueError(
            f"Unsupported data source '{value}'. Valid options: {valid}",
        ) from exc


def parse_args(strategy_config: dict[str, Any]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run trading strategy backtests")
    parser.add_argument(
        "--symbol",
        help="Symbol or comma-separated symbols to backtest",
    )
    parser.add_argument(
        "--short-window",
        type=int,
        dest="short_window",
        help="Short moving average window",
    )
    parser.add_argument(
        "--long-window",
        type=int,
        dest="long_window",
        help="Long moving average window",
    )
    parser.add_argument(
        "--strategy",
        help="Strategy name defined in config/strategies.yaml",
    )
    parser.add_argument(
        "--force-refresh",
        action="store_true",
        help="Force re-download data even if cached",
    )
    parser.add_argument(
        "--no-cache",
        action="store_true",
        help="Skip reading/writing cached prices (fetch fresh data)",
    )
    parser.add_argument(
        "--allow-interactive",
        action="store_true",
        help="Allow interactive prompts even when stdin is not a TTY",
    )
    parser.add_argument(
        "--mode",
        choices=["legacy", "lab"],
        default="legacy",
        help="Run mode: 'legacy' for old strategies, 'lab' for new Strategy Lab",
    )

    defaults = _default_windows(
        strategy_config,
        strategy_config.get("default_strategy"),
    )
    parser.set_defaults(
        default_short_window=defaults[0],
        default_long_window=defaults[1],
    )

    return parser.parse_args()


def build_strategy(
    strategy_name: Optional[str],
    *,
    override_params: Optional[dict[str, Any]] = None,
    fundamentals: Optional[dict[str, Any]] = None,
    config_path: str = STRATEGY_CONFIG_PATH,
):
    """Instantiate a strategy dynamically based on YAML configuration."""
    config = load_strategy_config(config_path)
    default_strategy = config.get("default_strategy")
    strategies = config.get("strategies", {})

    chosen_strategy = strategy_name or default_strategy
    if not chosen_strategy:
        raise ValueError(
            "No strategy specified and no default_strategy defined in config.",
        )

    if chosen_strategy not in strategies:
        raise ValueError(
            f"Strategy '{chosen_strategy}' not found in configuration. Available: {list(strategies)}",
        )

    strategy_def = strategies[chosen_strategy]
    module_name = strategy_def.get("module")
    class_name = strategy_def.get("class")
    if not module_name or not class_name:
        raise ValueError(f"Strategy definition for '{chosen_strategy}' is incomplete.")

    params: dict[str, Any] = dict(strategy_def.get("params", {}))
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
        logger.error(
            "Strategy class %s not found in module %s",
            class_name,
            module_name,
        )
        raise

    import inspect

    sig = inspect.signature(strategy_class.__init__)
    valid_params = {
        k: v
        for k, v in params.items()
        if k in sig.parameters
        or any(p.kind == p.VAR_KEYWORD for p in sig.parameters.values())
    }

    # If fundamentals is accepted, pass it
    if "fundamentals" in sig.parameters or any(
        p.kind == p.VAR_KEYWORD for p in sig.parameters.values()
    ):
        return (
            strategy_class(
                **valid_params,
                fundamentals=fundamentals,
            ),
            chosen_strategy,
        )

    return strategy_class(**valid_params), chosen_strategy


def run_backtest(
    symbol: str,
    short_window: Optional[int] = None,
    long_window: Optional[int] = None,
    data_source: Optional[Union[str, PriceDataSource]] = PriceDataSource.FMP,
    *,
    use_local_repository: bool = True,
    fundamentals: Optional[dict[str, Any]] = None,
    strategy_name: Optional[str] = None,
    strategy_params: Optional[dict[str, Any]] = None,
    start_date: Optional[pd.Timestamp] = None,
    end_date: Optional[pd.Timestamp] = None,
):
    """Core function that runs the full backtest and returns a results dict.
    This is called by both the console UI and the Streamlit UI.
    """
    # 1. Download data (cache-aware)
    active_strategy_name = strategy_name

    source = _coerce_data_source(data_source)

    df = get_prices_for_backtest(
        symbol=symbol,
        use_local_repository=use_local_repository,
        data_source=source,
    )

    if df is None or df.empty:
        print(
            "Error: No data available for the selected source. Check your repository, symbol, or API key.",
        )
        sys.exit(1)

    # 1b. Slice by date if requested
    if start_date and end_date:
        mask = (df.index >= start_date) & (df.index <= end_date)
        df = df.loc[mask]

    if df.empty:
        print(f"Error: No data available between {start_date} and {end_date}.")
        # We should probably raise or return empty instead of sys.exit(1) for Streamlit safety,
        # but sticking to existing pattern for now (CLI exit).
        # Ideally return error dict.
        # Let's return a special dict to let caller handle it if possible, but existing code exits.
        # For Streamlit, we catch exceptions.
        # Let's raise ValueError.
        raise ValueError(f"No data available between {start_date} and {end_date}.")

    source_name = (
        PriceDataSource.LOCAL_REPOSITORY.value if use_local_repository else source.value
    )

    # 2. Compute indicators needed by the strategy and for chart overlays
    if "close" not in df.columns and "adj_close" in df.columns:
        df["close"] = df["adj_close"]

    if "close" not in df.columns:
        print("Error: No 'close' column available in price data.")
        sys.exit(1)

    if short_window:
        df["sma_short"] = sma(df, window=short_window)
    if long_window:
        df["sma_long"] = sma(df, window=long_window)

    # 3. Run strategy
    override_params: dict[str, Any] = dict(strategy_params or {})
    if short_window is not None:
        override_params["short_window"] = short_window
    if long_window is not None:
        override_params["long_window"] = long_window
    if fundamentals is None and use_local_repository:
        fundamentals = get_fundamentals(symbol, use_local_repository=True)

    try:
        strategy, active_strategy_name = build_strategy(
            strategy_name,
            override_params=override_params,
            fundamentals=fundamentals,
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
            "data_source": source_name,
            "strategy": active_strategy_name,
        },
    )

    return results


def _choose_mode(interactive: bool) -> str:
    """Prompt the user for console mode selection."""
    if interactive:
        choice = input(
            "Choose mode: [1] Single backtest, [2] Optimize MA strategy via Optuna: ",
        ).strip()
        return choice or "1"

    logger.info(
        "Non-interactive mode detected; defaulting to single backtest (mode 1).",
    )
    return "1"


def _choose_data_source(interactive: bool) -> tuple[bool, PriceDataSource]:
    """Prompt user to select price data source."""
    if not interactive:
        source = DEFAULT_PRICE_DATA_SOURCE
        return (source == PriceDataSource.LOCAL_REPOSITORY, source)

    while True:
        choice = (
            input(
                "Choose price data source:\n"
                "  [1] Local historical repository (recommended)\n"
                "  [2] FMP API (live)\n"
                "  [3] Yahoo Finance (live)\n"
                "  [4] Kaggle (local DB)\n"
                "Selection: ",
            ).strip()
            or "1"
        )

        if choice == "1":
            return True, PriceDataSource.LOCAL_REPOSITORY
        if choice == "2":
            return False, PriceDataSource.FMP
        if choice == "3":
            return False, PriceDataSource.YAHOO_FINANCE
        if choice == "4":
            return False, PriceDataSource.KAGGLE

        print("Invalid choice. Please enter 1, 2, 3, or 4.")


def _run_optuna_mode() -> None:
    """Run Optuna-based optimization for a user-provided symbol."""
    symbol = input("Enter symbol to optimize (e.g. AAPL): ").strip().upper()
    if not symbol:
        logger.error("Symbol is required for optimization.")
        return

    trials_raw = input("Number of Optuna trials [50]: ").strip()
    if trials_raw:
        try:
            num_trials = int(trials_raw)
        except ValueError:
            logger.error("Number of trials must be an integer.")
            return
    else:
        num_trials = 50

    logger.info(
        "Starting Optuna optimization for %s with %s trials...",
        symbol,
        num_trials,
    )

    try:
        best_params, best_value = optimize_ma_strategy_for_symbol(
            symbol,
            n_trials=num_trials,
        )
    except (
        Exception
    ) as exc:  # noqa: BLE001 - surface optimization errors to the console
        logger.error("Optuna optimization failed: %s", exc)
        return

    logger.info("=== Optuna Optimization Result ===")
    logger.info("Symbol: %s", symbol)
    logger.info("Best objective value: %s", best_value)
    logger.info("Best parameters:")
    for param, value in best_params.items():
        logger.info("  %s: %s", param, value)


def _run_strategy_lab_cli(symbol: str, strategy_name: Optional[str] = None) -> None:
    """Run a Strategy Lab backtest from the CLI."""
    logger.info("=== Strategy Lab CLI ===")
    logger.info("Symbol: %s", symbol)

    # 1. Configuration
    # For CLI, we use defaults or simple hardcoded values for now,
    # mirroring the basic "MultiSignalRuleStrategy" setup from UI
    risk_cfg = RiskConfig(
        max_drawdown_pct=0.20,
        risk_per_trade=0.01,
        stop_loss_atr_multiple=1.5,
    )

    strat_cfg = StrategyConfig(
        name="LabCLIStrategy",
        initial_capital=100_000.0,
        risk_config=risk_cfg,
        parameters={
            "factors": ["sma_cross", "rsi_oversold", "macd_cross"],  # Default set
            "weights": {"sma_cross": 1.0, "rsi_oversold": 1.0, "macd_cross": 1.0},
            "threshold": 0.5,
        },
    )

    # 2. Setup Components
    provider = YFinanceHistoricalProvider(force_refresh=False)
    risk_engine = RiskEngine(risk_config=risk_cfg)
    engine = StrategyBacktestEngine(
        data_provider=provider,
        risk_engine=risk_engine,
        factor_registry=FactorRegistry,
    )

    # 3. Create Strategy
    if strategy_name:
        try:
            strategy, _ = build_strategy(strategy_name)
            logger.info("Using strategy: %s", strategy_name)
        except Exception as exc:
            logger.error("Failed to load strategy %s: %s", strategy_name, exc)
            return
    else:
        logger.info("Using default MultiSignalRuleStrategy")
        strategy = MultiSignalRuleStrategy(strat_cfg)

    # 4. Run
    # Defaulting to 1 year backtest for CLI demo
    end_date = pd.Timestamp.now()
    start_date = end_date - pd.DateOffset(years=1)

    logger.info("Running backtest from %s to %s...", start_date.date(), end_date.date())

    try:
        result = engine.run(
            strategy=strategy,
            start_date=start_date,
            end_date=end_date,
            universe=[symbol],
            initial_capital=100_000.0,
        )

        # 5. Report
        metrics = result.get_metrics()
        logger.info("\n=== Backtest Complete ===")
        logger.info("Total Return: %.2f%%", metrics["total_return"] * 100)
        logger.info("Sharpe Ratio: %.2f", metrics["sharpe_ratio"])
        logger.info("Max Drawdown: %.2f%%", metrics["max_drawdown"] * 100)

        if result.portfolio_history is not None and not result.portfolio_history.empty:
            final_equity = result.portfolio_history["equity"].iloc[-1]
            logger.info("Final Equity: $%.2f", final_equity)

    except Exception as exc:
        logger.error("Strategy Lab backtest failed: %s", exc)


def main():
    """Simple console-based UI that asks the user for inputs.
    This replaces the strict command-line-argument approach that caused the error.
    """
    ensure_data_directories()
    setup_logging()
    logger.info("=== Trading System Runner ===")

    interactive_allowed = sys.stdin.isatty()

    # Check if mode is provided via args first to bypass interactive for LAB
    # But we need basic args parsing first.
    # To avoid logic duplication, we'll parse args early.
    try:
        # We need to load config just to satisfy parse_args signature,
        # though it's not strictly needed for LAB mode.
        strategy_config = load_strategy_config()
    except Exception as exc:
        # If config is missing, we might still want to run Lab mode?
        # For now, let's assume config is required or mock it.
        logger.warning("Failed to load strategy config at startup: %s", exc)
        strategy_config = {}

    args = parse_args(strategy_config)

    if args.mode == "lab":
        # CLI execution for Lab
        raw_symbols = args.symbol
        if not raw_symbols:
            logger.error(
                "Symbol is required for Strategy Lab mode (e.g. --symbol AAPL)",
            )
            return

        symbols = [s.strip().upper() for s in raw_symbols.split(",") if s.strip()]
        for sym in symbols:
            _run_strategy_lab_cli(sym, args.strategy)
        return

    # Legacy / Interactive Selection logic
    use_local_repository, selected_data_source = _choose_data_source(
        interactive_allowed,
    )

    mode_choice = _choose_mode(interactive_allowed)

    if mode_choice == "2":
        _run_optuna_mode()
        return

    try:
        strategy_config = load_strategy_config()
    except Exception as exc:
        logger.error("Unable to load strategy configuration. Aborting. %s", exc)
        return

    strategies = strategy_config.get("strategies", {})
    default_strategy = strategy_config.get("default_strategy")
    strategy_names = list(strategies.keys())

    args = parse_args(strategy_config)
    interactive_allowed = interactive_allowed or args.allow_interactive

    raw_symbols = args.symbol
    if not raw_symbols and interactive_allowed:
        raw_symbols = input(
            "Enter symbol or comma-separated symbols (e.g. AAPL or AAPL,MSFT): ",
        )
    if not raw_symbols:
        fallback_symbol = "AAPL"
        logger.info(
            "No symbols provided; defaulting to %s for non-interactive run.",
            fallback_symbol,
        )
        raw_symbols = fallback_symbol

    symbols = [s.strip().upper() for s in raw_symbols.split(",") if s.strip()]
    if not symbols:
        logger.error("At least one symbol is required.")
        return

    default_short, default_long = args.default_short_window, args.default_long_window

    def _resolve_window(
        prompt: str,
        provided: Optional[int],
        default_val: Optional[int],
    ) -> int:
        if provided is not None:
            return provided
        if interactive_allowed:
            return int(input(prompt).strip())
        if default_val is None:
            raise ValueError(
                "No default window configured; please provide inputs explicitly.",
            )
        logger.info("Using configured default for non-interactive run: %s", default_val)
        return default_val

    try:
        short_window = _resolve_window(
            "Enter SHORT moving average window (e.g. 20): ",
            args.short_window,
            default_short,
        )
        long_window = _resolve_window(
            "Enter LONG moving average window (e.g. 50): ",
            args.long_window,
            default_long,
        )
    except ValueError as exc:
        logger.error("Short and long windows must be integers: %s", exc)
        return

    if short_window >= long_window:
        logger.error("Short window must be smaller than long window.")
        return

    selected_strategy = args.strategy or ""
    if not selected_strategy and interactive_allowed:
        strategy_prompt = (
            f"Enter strategy name {strategy_names} [{default_strategy}]: "
            if strategy_names
            else "Enter strategy name: "
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
            symbol=symbol,
            short_window=short_window,
            long_window=long_window,
            data_source=selected_data_source,
            use_local_repository=use_local_repository,
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
                "Detailed results may be in reports/results.csv (depending on your Backtester implementation).",
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
                    symbol=symbol,
                    short_window=short_window,
                    long_window=long_window,
                    data_source=selected_data_source,
                    use_local_repository=use_local_repository,
                    strategy_name=selected_strategy,
                )
            except Exception as exc:  # surface per-symbol errors without stopping all
                logger.error("Error running backtest for %s: %s", symbol, exc)
                continue

            logger.info("Short window: %s, Long window: %s", short_window, long_window)
            if "cumulative_return" in results:
                logger.info(
                    "Cumulative return: %.2f%%",
                    results["cumulative_return"] * 100,
                )
            if "max_drawdown" in results:
                logger.info("Max drawdown: %.2f%%", results["max_drawdown"] * 100)
            if "results_path" in results:
                logger.info("Detailed results saved to: %s", results["results_path"])
            else:
                logger.info(
                    "Detailed results may be in reports/results.csv (depending on your Backtester implementation).",
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
                        "Portfolio results saved to: %s",
                        portfolio_results["results_path"],
                    )


if __name__ == "__main__":
    main()
