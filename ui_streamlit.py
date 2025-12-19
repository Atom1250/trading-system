from datetime import datetime
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from config.settings import (
    PriceDataSource,
    ensure_data_directories,
)
from indicators.technicals import bollinger_bands
from repository.prices_repository import get_prices_for_backtest
from run_strategy import load_strategy_config, run_backtest
from strategy_lab.backtest.engine import StrategyBacktestEngine

# Strategy Lab Imports
from strategy_lab.config import RiskConfig, StrategyConfig
from strategy_lab.data.providers import YFinanceHistoricalProvider
from strategy_lab.factors.base import FactorRegistry
from strategy_lab.optimization.optuna_engine import optimize_lab_strategy
from strategy_lab.risk.engine import RiskEngine
from strategy_lab.strategies.rule_based import MultiSignalRuleStrategy
from strategy_lab.strategies.volume_move import VolumeMoveBreakoutStrategy

# Ensure factors are registered


ensure_data_directories()


def render_strategy_params(strategy_def: dict) -> dict:
    """Render parameter controls for the selected strategy and return user choices."""
    params = strategy_def.get("params", {}) or {}
    hidden_params = {
        "short_window",
        "long_window",
        "initial_capital",
        "risk_per_trade",
        "atr_window",
        "stop_atr_multiple",
        "take_profit_multiple",
        "max_drawdown_pct",
    }
    visible_params = {k: v for k, v in params.items() if k not in hidden_params}
    if not visible_params:
        return {}

    st.markdown("### Strategy parameters")
    user_params = {}
    for param_name, default_val in visible_params.items():
        label = param_name.replace("_", " ").title()
        if isinstance(default_val, int):
            user_params[param_name] = int(
                st.number_input(label, value=int(default_val), step=1),
            )
        elif isinstance(default_val, float):
            user_params[param_name] = float(
                st.number_input(label, value=float(default_val), step=0.1),
            )
        else:
            user_params[param_name] = st.text_input(label, value=str(default_val))

    return user_params


def render_risk_controls(defaults: dict) -> dict:
    """Render risk management controls and return the chosen values."""
    st.markdown("### P&L and risk management")
    col1, col2, col3 = st.columns(3)

    with col1:
        initial_capital = float(
            st.number_input(
                "Initial capital",
                value=float(defaults.get("initial_capital", 100_000.0)),
                step=1000.0,
            ),
        )
        atr_window = int(
            st.number_input(
                "ATR window",
                value=int(defaults.get("atr_window", 14)),
                step=1,
                min_value=1,
            ),
        )

    with col2:
        risk_per_trade = float(
            st.number_input(
                "Risk per trade (fraction)",
                value=float(defaults.get("risk_per_trade", 0.01)),
                step=0.001,
                min_value=0.0,
                max_value=1.0,
                format="%.3f",
            ),
        )
        stop_atr_multiple = float(
            st.number_input(
                "Stop loss ATR multiple",
                value=float(defaults.get("stop_atr_multiple", 1.5)),
                step=0.1,
                min_value=0.1,
            ),
        )

    with col3:
        take_profit_multiple = float(
            st.number_input(
                "Take profit multiple",
                value=float(defaults.get("take_profit_multiple", 2.0)),
                step=0.1,
                min_value=0.1,
            ),
        )
        max_drawdown_pct = float(
            st.number_input(
                "Max drawdown (fraction)",
                value=float(defaults.get("max_drawdown_pct", 0.2)),
                step=0.01,
                min_value=0.0,
                max_value=1.0,
                format="%.2f",
            ),
        )

    return {
        "initial_capital": initial_capital,
        "risk_per_trade": risk_per_trade,
        "atr_window": atr_window,
        "stop_atr_multiple": stop_atr_multiple,
        "take_profit_multiple": take_profit_multiple,
        "max_drawdown_pct": max_drawdown_pct,
    }


st.title("Trading Strategy Backtest")

st.markdown("Use this interface to run a backtest with your configured strategies.")

data_source_label = st.sidebar.selectbox(
    "Price Data Source",
    [
        "Local Historical Repository",
        "FMP API (live)",
        "Yahoo Finance (live)",
    ],
)

if data_source_label == "Local Historical Repository":
    use_local_repository = True
    data_source = PriceDataSource.LOCAL_REPOSITORY
elif data_source_label == "FMP API (live)":
    use_local_repository = False
    data_source = PriceDataSource.FMP
else:
    use_local_repository = False
    data_source = PriceDataSource.YAHOO_FINANCE

mode = st.radio(
    "Mode",
    options=["Single Backtest", "Optimize Strategy", "Strategy Lab"],
    index=0,
)

if mode == "Single Backtest":
    try:
        strategy_config = load_strategy_config()
        strategies = strategy_config.get("strategies", {})
        default_strategy = strategy_config.get("default_strategy")
        strategy_names = list(strategies.keys())
        if not strategy_names:
            st.error("No strategies defined in configuration.")
            st.stop()
    except Exception as exc:
        st.error(f"Unable to load strategy configuration: {exc}")
        st.stop()

    strategy_name = st.selectbox(
        "Strategy",
        options=strategy_names,
        index=strategy_names.index(default_strategy)
        if default_strategy in strategy_names
        else 0,
    )
    strategy_def = strategies.get(strategy_name, {})
    strategy_params = strategy_def.get("params", {}) or {}
    risk_defaults = {
        "initial_capital": float(strategy_params.get("initial_capital", 100_000.0)),
        "risk_per_trade": float(strategy_params.get("risk_per_trade", 0.01)),
        "atr_window": int(strategy_params.get("atr_window", 14)),
        "stop_atr_multiple": float(strategy_params.get("stop_atr_multiple", 1.5)),
        "take_profit_multiple": float(strategy_params.get("take_profit_multiple", 2.0)),
        "max_drawdown_pct": float(strategy_params.get("max_drawdown_pct", 0.2)),
    }

    # Input fields
    col_sym, col_start, col_end = st.columns(3)
    symbol = col_sym.text_input("Symbol", value="AAPL")
    start_date = col_start.date_input("Start Date", value=datetime(2023, 1, 1))
    end_date = col_end.date_input("End Date", value=datetime(2023, 12, 31))

    ma_default_short = int(strategy_params.get("short_window", 20))
    ma_default_long = int(strategy_params.get("long_window", 50))

    short_window = st.number_input(
        "Short moving average window",
        min_value=1,
        value=ma_default_short,
        step=1,
    )
    long_window = st.number_input(
        "Long moving average window",
        min_value=max(2, short_window + 1),
        value=max(ma_default_long, short_window + 1),
        step=1,
    )

    base_strategy_params = render_strategy_params(strategy_def)
    risk_settings = render_risk_controls(risk_defaults)
    user_strategy_params = {**base_strategy_params, **risk_settings}

    # Run button
    if st.button("Run backtest"):
        if short_window >= long_window:
            st.error("Short window must be smaller than long window.")
        elif not symbol.strip():
            st.error("Symbol is required.")
        else:
            try:
                with st.spinner("Running backtest..."):
                    df = get_prices_for_backtest(
                        symbol=symbol.strip().upper(),
                        use_local_repository=use_local_repository,
                        data_source=data_source,
                    )

                    # Slice Data by Date
                    if df is not None and not df.empty:
                        mask = (df.index >= pd.Timestamp(start_date)) & (
                            df.index <= pd.Timestamp(end_date)
                        )
                        df = df.loc[mask]

                        if df.empty:
                            st.error(
                                f"No data found between {start_date} and {end_date}.",
                            )
                            st.stop()

                        # We need to monkey-patch or adjust run_backtest to accept DF or respect global slicing.
                        # Since run_backtest fetches data internally using get_prices_for_backtest again,
                        # we might need to modify run_backtest signature or filter inside.
                        # For legacy run_backtest, it re-fetches. Let's fix that or filter after?
                        # ACTUALLY, run_backtest in run_strategy.py fetches data itself.
                        # Ideally we update run_backtest to accept dates.
                        # Checking run_strategy.py... it loads full history.
                        # Let's pass the date range to run_backtest if possible?
                        # LIMITATION: run_backtest currently doesn't take start/end args.
                        # QUICK FIX: We will rely on post-filtering results or modifying run_backtest.
                        # BUT the user wants the TEST PERIOD to be defined.
                        # So meaningful backtest needs to respect it.
                        # Current legacy system is rigid.
                        # Let's override the cache or modifying run_strategy is better.
                        # For now, let's keep it simple: We passed `use_local_repository`.
                        # Validated existence above.

                    results = run_backtest(
                        symbol=symbol.strip().upper(),
                        short_window=int(short_window),
                        long_window=int(long_window),
                        data_source=data_source,
                        use_local_repository=use_local_repository,
                        strategy_name=strategy_name,
                        strategy_params=user_strategy_params,
                        # TODO: We need to pass start/end to run_backtest.
                        # Assuming we will modify run_strategy run_backtest signature in next step.
                        start_date=pd.Timestamp(start_date),
                        end_date=pd.Timestamp(end_date),
                    )

            except Exception as exc:
                st.error(f"Backtest failed: {exc}")
                st.stop()

            st.success("Backtest complete!")

            st.subheader("Summary")
            st.write(f"**Symbol:** {symbol.strip().upper()}")
            st.write(f"**Short window:** {int(short_window)}")
            st.write(f"**Long window:** {int(long_window)}")
            if base_strategy_params:
                st.write("**Strategy parameters:**")
                st.json(base_strategy_params)
            if risk_settings:
                st.write("**P&L and risk settings:**")
                st.json(risk_settings)

            if "cumulative_return" in results:
                st.write(f"**Cumulative return:** {results['cumulative_return']:.2%}")
            if "max_drawdown" in results:
                st.write(f"**Max drawdown:** {results['max_drawdown']:.2%}")

            if "results_path" in results:
                st.write(f"Detailed results saved to: `{results['results_path']}`")
            if (
                results.get("data_source") == PriceDataSource.FMP.value
                and not use_local_repository
            ):
                st.warning("Data fetched directly from FMP (cache bypassed).")

            results_df = None
            results_path = results.get("results_path")
            if results_path:
                path = Path(results_path)
                if path.exists():
                    results_df = pd.read_csv(path, index_col=0)
                    results_df.index = pd.to_datetime(results_df.index)
                    results_df.sort_index(inplace=True)
                else:
                    st.warning(
                        "Results file was not found on disk; displaying in-memory results if available.",
                    )

            if results_df is None:
                in_memory = results.get("results")
                if in_memory is not None:
                    results_df = in_memory.copy()
                    if not isinstance(results_df.index, pd.DatetimeIndex):
                        results_df.index = pd.to_datetime(
                            results_df.index, errors="coerce",
                        )
                    results_df.sort_index(inplace=True)

            if results_df is not None:
                st.subheader("Backtest Results Table")
                table_df = results_df.reset_index().rename(columns={"index": "date"})
                st.dataframe(table_df)

                pnl_cols = {"equity", "pnl", "cumulative_pnl", "drawdown_pct"}
                if pnl_cols.intersection(results_df.columns):
                    latest_row = results_df.dropna(
                        subset=[col for col in pnl_cols if col in results_df],
                    ).tail(1)
                    if not latest_row.empty:
                        latest = latest_row.iloc[0]
                        metrics = st.columns(3)
                        metrics[0].metric(
                            "Ending equity",
                            f"{latest.get('equity', float('nan')):,.2f}",
                            help="Final equity after applying signals, stops, and position sizing.",
                        )
                        metrics[1].metric(
                            "Total P&L",
                            f"{latest.get('cumulative_pnl', float('nan')):,.2f}",
                            delta=f"{latest.get('pnl', float('nan')):,.2f} last bar",
                            help="Cumulative and most recent profit/loss from managed positions.",
                        )
                        metrics[2].metric(
                            "Max drawdown",
                            f"{float(results.get('max_drawdown', 0)):.2%}",
                            help="Worst peak-to-trough decline observed during the run.",
                        )

                risk_table_cols = [
                    col
                    for col in [
                        "date",
                        "equity",
                        "pnl",
                        "cumulative_pnl",
                        "position_size_units_signed",
                        "notional_exposure",
                        "stop_loss_price",
                        "take_profit_price",
                        "drawdown_pct",
                        "halt_trading",
                    ]
                    if (col == "date" and "date" in table_df.columns)
                    or (col != "date" and col in results_df.columns)
                ]
                if risk_table_cols:
                    st.subheader("Position management and risk overlays")
                    risk_view = table_df[risk_table_cols].tail(100)
                    st.dataframe(risk_view)
                if "close" not in results_df.columns:
                    st.warning("Price data unavailable for chart rendering.")
                    st.stop()

                chart_df = results_df.copy()
                bollinger_window = int(long_window) if long_window else 20
                chart_df = bollinger_bands(
                    chart_df, window=bollinger_window, column="close",
                )

                has_macd = {"MACD_line", "MACD_signal", "MACD_hist"}.issubset(
                    chart_df.columns,
                )
                rsi_columns = [
                    col for col in chart_df.columns if col.startswith("RSI_")
                ]

                subplot_count = 1 + int(has_macd) + int(bool(rsi_columns))
                fig, axes = plt.subplots(
                    nrows=subplot_count,
                    sharex=True,
                    figsize=(12, 6 + 2 * (subplot_count - 1)),
                )

                try:
                    axes = list(axes)
                except TypeError:
                    axes = [axes]

                price_ax = axes[0]
                date_index = chart_df.index

                price_ax.plot(
                    date_index,
                    chart_df["close"],
                    label="Close",
                    color="black",
                    linewidth=1.2,
                )
                if "sma_short" in chart_df.columns:
                    price_ax.plot(
                        date_index,
                        chart_df["sma_short"],
                        label="SMA Short",
                        color="blue",
                        linestyle="--",
                    )
                if "sma_long" in chart_df.columns:
                    price_ax.plot(
                        date_index,
                        chart_df["sma_long"],
                        label="SMA Long",
                        color="orange",
                        linestyle="--",
                    )

                price_ax.plot(
                    date_index,
                    chart_df["bb_middle"],
                    label="Bollinger Mid",
                    color="purple",
                    linestyle=":",
                )
                price_ax.fill_between(
                    date_index,
                    chart_df["bb_lower"],
                    chart_df["bb_upper"],
                    color="purple",
                    alpha=0.1,
                    label="Bollinger Band",
                )

                buy_signals = chart_df[
                    chart_df.get("signal", pd.Series(dtype=float)) > 0
                ]
                sell_signals = chart_df[
                    chart_df.get("signal", pd.Series(dtype=float)) < 0
                ]

                if not buy_signals.empty:
                    price_ax.scatter(
                        buy_signals.index,
                        buy_signals["close"],
                        marker="^",
                        color="green",
                        label="Buy",
                        zorder=5,
                    )
                if not sell_signals.empty:
                    price_ax.scatter(
                        sell_signals.index,
                        sell_signals["close"],
                        marker="v",
                        color="red",
                        label="Sell",
                        zorder=5,
                    )

                price_ax.set_title(f"Backtest Chart for {symbol.strip().upper()}")
                price_ax.set_xlabel("Date")
                price_ax.set_ylabel("Price")
                price_ax.grid(True, linestyle="--", alpha=0.3)
                price_ax.legend()

                axis_idx = 1
                if has_macd:
                    macd_ax = axes[axis_idx]
                    macd_ax.bar(
                        date_index,
                        chart_df["MACD_hist"],
                        label="MACD Histogram",
                        color="gray",
                        alpha=0.4,
                    )
                    macd_ax.plot(
                        date_index,
                        chart_df["MACD_line"],
                        label="MACD Line",
                        color="teal",
                    )
                    macd_ax.plot(
                        date_index,
                        chart_df["MACD_signal"],
                        label="MACD Signal",
                        color="magenta",
                        linestyle="--",
                    )
                    macd_ax.axhline(0, color="black", linewidth=0.8, linestyle=":")
                    macd_ax.set_ylabel("MACD")
                    macd_ax.grid(True, linestyle="--", alpha=0.3)
                    macd_ax.legend()
                    axis_idx += 1

                if rsi_columns:
                    rsi_ax = axes[axis_idx]
                    rsi_col = rsi_columns[0]
                    rsi_ax.plot(
                        date_index, chart_df[rsi_col], label=rsi_col, color="brown",
                    )
                    lower = user_strategy_params.get("lower_threshold", 30)
                    upper = user_strategy_params.get("upper_threshold", 70)
                    rsi_ax.axhline(
                        lower, color="green", linestyle=":", label="Lower threshold",
                    )
                    rsi_ax.axhline(
                        upper, color="red", linestyle=":", label="Upper threshold",
                    )
                    rsi_ax.set_ylabel("RSI")
                    rsi_ax.set_ylim(0, 100)
                    rsi_ax.grid(True, linestyle="--", alpha=0.3)
                    rsi_ax.legend()

                fig.tight_layout()
                st.subheader("Price, Indicators, and Signals")
                st.pyplot(fig)
            else:
                st.info("No tabular results available to display.")

elif mode == "Optimize Strategy":
    st.markdown("## Optimization Lab")
    st.info("Optimize parameters for Strategy Lab strategies using Optuna.")

    col_strat, col_sym = st.columns(2)
    strat_name = col_strat.selectbox(
        "Strategy Class", ["MultiSignalRuleStrategy", "VolumeMoveBreakoutStrategy"],
    )
    opt_symbol = col_sym.text_input("Symbol", value="AAPL")

    col_d1, col_d2 = st.columns(2)
    start_date = col_d1.date_input(
        "Start Date", value=datetime(2023, 1, 1), key="opt_start",
    )
    end_date = col_d2.date_input(
        "End Date", value=datetime(2023, 12, 31), key="opt_end",
    )

    n_trials = int(st.number_input("Number of Trials", min_value=10, value=20, step=10))

    st.markdown("### Parameter Bounds")
    param_ranges = {}
    fixed_params = {}

    if strat_name == "MultiSignalRuleStrategy":
        # Simplified optimization for demo
        st.write("Optimizing Threshold")
        min_t = st.number_input("Min Threshold", 0.0, 5.0, 0.1)
        max_t = st.number_input("Max Threshold", 0.0, 5.0, 1.0)
        param_ranges["threshold"] = (min_t, max_t, "float")

        # Factors fixed for now
        avail = FactorRegistry.list_factors()
        factors = st.multiselect(
            "Fixed Factors", avail, default=["sma_cross", "rsi_oversold"],
        )
        fixed_params["factors"] = factors
        fixed_params["weights"] = dict.fromkeys(factors, 1.0)

    elif strat_name == "VolumeMoveBreakoutStrategy":
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("**Move Threshold %**")
            mt_min = st.number_input("Min", 0.01, 0.10, 0.02, key="mt_min")
            mt_max = st.number_input("Max", 0.01, 0.20, 0.05, key="mt_max")
            param_ranges["move_threshold_pct"] = (mt_min, mt_max, "float")

        with c2:
            st.markdown("**Take Profit %**")
            tp_min = st.number_input("Min", 0.05, 0.50, 0.10, key="tp_min")
            tp_max = st.number_input("Max", 0.05, 1.00, 0.30, key="tp_max")
            param_ranges["take_profit_pct"] = (tp_min, tp_max, "float")

        # Fixed defaults for others to reduce search space
        fixed_params["min_volume_multiple"] = 1.0
        fixed_params["stop_loss_pct"] = -0.05  # Tighter stop
        fixed_params["avg_volume_window"] = 20

    if st.button("Run Optimization"):
        status = st.empty()
        status.info("Running Optuna Study...")

        try:
            strat_cls = (
                MultiSignalRuleStrategy
                if strat_name == "MultiSignalRuleStrategy"
                else VolumeMoveBreakoutStrategy
            )

            best_params = optimize_lab_strategy(
                strategy_cls=strat_cls,
                symbol=opt_symbol,
                start_date=pd.Timestamp(start_date),
                end_date=pd.Timestamp(end_date),
                initial_capital=100_000.0,
                n_trials=n_trials,
                param_ranges=param_ranges,
                fixed_params=fixed_params,
            )

            status.success("Optimization Complete!")
            st.write("### Best Parameters")
            st.json(best_params)

            # TODO: Auto-run best backtest?
            st.info(
                "You can now plug these parameters into the Strategy Lab tab to visualize the result.",
            )

        except Exception as e:
            st.error(f"Optimization Failed: {e}")
            st.exception(e)

elif mode == "Strategy Lab":
    st.markdown("## Strategy Lab Experiment")

    # 1. Configuration Panel
    with st.expander("Configuration", expanded=True):
        col_sym, col_date = st.columns(2)
        with col_sym:
            lab_symbol = st.text_input("Symbol", value="AAPL", key="lab_sym")
        with col_date:
            start_date = st.date_input("Start Date", value=datetime(2023, 1, 1))
            end_date = st.date_input("End Date", value=datetime(2023, 12, 31))

    # 2. Risk Settings
    with st.expander("Risk Settings", expanded=False):
        c1, c2 = st.columns(2)
        initial_cap = c1.number_input("Initial Equity", value=100000.0, step=1000.0)
        risk_per_trade = c2.number_input(
            "Risk % per Trade", value=0.01, step=0.005, format="%.3f",
        )
        max_dd = c1.number_input("Max Drawdown limit", value=0.20, step=0.05)
        stop_atr = c2.number_input("Stop Loss ATR", value=1.5, step=0.1)

    # 3. Strategy Settings
    with st.expander("Strategy Logic", expanded=True):
        strategy_class_name = st.selectbox(
            "Strategy Class", ["MultiSignalRuleStrategy", "VolumeMoveBreakoutStrategy"],
        )

        lab_params = {}

        if strategy_class_name == "MultiSignalRuleStrategy":
            # Factor Selection
            available_factors = FactorRegistry.list_factors()
            selected_factors = st.multiselect(
                "Active Factors", available_factors, default=available_factors,
            )

            # Weights (simple equal weight logic for now, or dynamic inputs)
            weights = {}
            if selected_factors:
                st.write("Factor Weights:")
                cols = st.columns(len(selected_factors))
                for i, f in enumerate(selected_factors):
                    weights[f] = cols[i].number_input(
                        f"{f} weight", value=1.0, key=f"w_{f}",
                    )

            threshold = st.slider("Signal Threshold", 0.0, 5.0, 0.5, step=0.1)

            lab_params = {
                "factors": selected_factors,
                "weights": weights,
                "threshold": threshold,
            }

        else:
            # VolumeMoveBreakoutStrategy
            c1, c2 = st.columns(2)
            move_thresh = c1.number_input("Move Threshold %", value=0.03, step=0.01)
            min_vol = c2.number_input("Min Volume Multiple", value=1.0, step=0.1)

            c3, c4 = st.columns(2)
            tp = c3.number_input("Take Profit %", value=0.20, step=0.05)
            sl = c4.number_input("Stop Loss %", value=-0.10, step=0.05)

            vol_window = st.number_input("Avg Volume Window", value=20, step=5)

            lab_params = {
                "move_threshold_pct": move_thresh,
                "min_volume_multiple": min_vol,
                "take_profit_pct": tp,
                "stop_loss_pct": sl,
                "avg_volume_window": vol_window,
            }

    # Execution
    if st.button("Run Lab Backtest"):
        status = st.empty()
        status.info("Initializing Engine...")

        try:
            # Build Configs
            risk_cfg = RiskConfig(
                max_drawdown_pct=max_dd,
                risk_per_trade=risk_per_trade,
                stop_loss_atr_multiple=stop_atr,
            )

            strat_cfg = StrategyConfig(
                name="LabStrategy",
                initial_capital=initial_cap,
                risk_config=risk_cfg,
                parameters=lab_params,
            )

            # Instantiate Components
            # Use YFinance Provider (which wraps Repository)
            provider = YFinanceHistoricalProvider(force_refresh=False)
            risk_engine = RiskEngine(risk_config=risk_cfg)

            engine = StrategyBacktestEngine(
                data_provider=provider,
                risk_engine=risk_engine,
                factor_registry=FactorRegistry,
            )

            # Create Strategy
            if strategy_class_name == "MultiSignalRuleStrategy":
                strategy = MultiSignalRuleStrategy(strat_cfg)
            else:
                strategy = VolumeMoveBreakoutStrategy(strat_cfg)

            # Run
            status.info("Running Backtest Loop...")
            result = engine.run(
                strategy=strategy,
                start_date=pd.Timestamp(start_date),
                end_date=pd.Timestamp(end_date),
                universe=[lab_symbol],
                initial_capital=initial_cap,
            )

            status.success("Backtest Complete")

            # Display Results
            metrics = result.get_metrics()

            # 1. Metrics Row
            m1, m2, m3, m4 = st.columns(4)
            m1.metric("Total Return", f"{metrics['total_return']:.2%}")
            m2.metric("Sharpe Ratio", f"{metrics['sharpe_ratio']:.2f}")
            m3.metric("Max Drawdown", f"{metrics['max_drawdown']:.2%}")
            m4.metric("Win Rate", f"{metrics.get('win_rate', 0):.2%}")

            # Risk Feedback
            if (
                result.portfolio_history is not None
                and "halt_trading" in result.portfolio_history.columns
            ):
                is_halted = result.portfolio_history["halt_trading"].iloc[-1]
                if is_halted:
                    st.error(
                        f"⚠️ RISK EVENT: Max Drawdown Limit ({max_dd:.1%}) was reached! Trading was halted.",
                    )
                else:
                    st.success("✅ Risk Constraints Satisfied.")

            # 2. Charts
            st.subheader("Performance Analysis")

            if result.portfolio_history is not None:
                # Prepare Data for Main Chart
                # We need data from result.data joined with result.portfolio_history or just result.data
                chart_data = result.data.copy()

                # Plotting
                tab_price, tab_equity = st.tabs(
                    ["Price & Signals", "Equity & Drawdown"],
                )

                with tab_price:
                    # Interactive Plot? Or Matplotlib?
                    # Using Matplotlib to match other tabs for consistency and control
                    fig, ax = plt.subplots(figsize=(12, 6))
                    ax.plot(
                        chart_data.index,
                        chart_data["close"],
                        label="Close",
                        color="black",
                        alpha=0.6,
                    )

                    # Add Trades
                    if result.trade_log is not None and not result.trade_log.empty:
                        buys = result.trade_log[
                            result.trade_log["type"].str.contains("BUY")
                        ]
                        sells = result.trade_log[
                            result.trade_log["type"].str.contains("SELL")
                        ]

                        ax.scatter(
                            buys["timestamp"],
                            buys["price"],
                            marker="^",
                            color="green",
                            label="Buy",
                            zorder=5,
                            s=100,
                        )
                        ax.scatter(
                            sells["timestamp"],
                            sells["price"],
                            marker="v",
                            color="red",
                            label="Sell",
                            zorder=5,
                            s=100,
                        )

                    ax.set_title(f"Price Chart - {lab_symbol}")
                    ax.legend()
                    ax.grid(True, alpha=0.3)
                    st.pyplot(fig)

                with tab_equity:
                    equity = result.portfolio_history["equity"]
                    drawdown = (equity / equity.cummax()) - 1

                    c1, c2 = st.columns(2)
                    c1.line_chart(equity)
                    c2.area_chart(drawdown)

            # 3. Trade Log
            st.subheader("Trade Log")
            if result.trade_log is not None and not result.trade_log.empty:
                st.dataframe(
                    result.trade_log.style.format(
                        {"price": "{:.2f}", "quantity": "{:.4f}", "pnl": "{:.2f}"},
                    ),
                )
            else:
                st.info("No trades executed.")

        except Exception as e:
            status.error(f"Error: {e!s}")
            st.exception(e)
