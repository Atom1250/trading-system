from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

from config.settings import (
    DEFAULT_PRICE_DATA_SOURCE,
    PriceDataSource,
    ensure_data_directories,
)
from indicators.technicals import bollinger_bands
from research.experiments.optuna_ma_optimization import optimize_ma_strategy_for_symbol
from repository.prices_repository import get_prices_for_backtest
from run_strategy import load_strategy_config, run_backtest


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
                st.number_input(label, value=int(default_val), step=1)
            )
        elif isinstance(default_val, float):
            user_params[param_name] = float(
                st.number_input(label, value=float(default_val), step=0.1)
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
                "Initial capital", value=float(defaults.get("initial_capital", 100_000.0)), step=1000.0
            )
        )
        atr_window = int(st.number_input("ATR window", value=int(defaults.get("atr_window", 14)), step=1, min_value=1))

    with col2:
        risk_per_trade = float(
            st.number_input(
                "Risk per trade (fraction)",
                value=float(defaults.get("risk_per_trade", 0.01)),
                step=0.001,
                min_value=0.0,
                max_value=1.0,
                format="%.3f",
            )
        )
        stop_atr_multiple = float(
            st.number_input(
                "Stop loss ATR multiple",
                value=float(defaults.get("stop_atr_multiple", 1.5)),
                step=0.1,
                min_value=0.1,
            )
        )

    with col3:
        take_profit_multiple = float(
            st.number_input(
                "Take profit multiple",
                value=float(defaults.get("take_profit_multiple", 2.0)),
                step=0.1,
                min_value=0.1,
            )
        )
        max_drawdown_pct = float(
            st.number_input(
                "Max drawdown (fraction)",
                value=float(defaults.get("max_drawdown_pct", 0.2)),
                step=0.01,
                min_value=0.0,
                max_value=1.0,
                format="%.2f",
            )
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
    options=["Single Backtest", "Optimize MA Strategy"],
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
        index=strategy_names.index(default_strategy) if default_strategy in strategy_names else 0,
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
    symbol = st.text_input("Symbol", value="AAPL")

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
                    if df is None or df.empty:
                        st.error("No price data found for the selected source.")
                        st.stop()

                    results = run_backtest(
                        symbol=symbol.strip().upper(),
                        short_window=int(short_window),
                        long_window=int(long_window),
                        data_source=data_source,
                        use_local_repository=use_local_repository,
                        strategy_name=strategy_name,
                        strategy_params=user_strategy_params,
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
            if results.get("data_source") == "fmp" and not use_cache:
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
                        "Results file was not found on disk; displaying in-memory results if available."
                    )

            if results_df is None:
                in_memory = results.get("results")
                if in_memory is not None:
                    results_df = in_memory.copy()
                    if not isinstance(results_df.index, pd.DatetimeIndex):
                        results_df.index = pd.to_datetime(results_df.index, errors="coerce")
                    results_df.sort_index(inplace=True)

            if results_df is not None:
                st.subheader("Backtest Results Table")
                table_df = results_df.reset_index().rename(columns={"index": "date"})
                st.dataframe(table_df)

                pnl_cols = {"equity", "pnl", "cumulative_pnl", "drawdown_pct"}
                if pnl_cols.intersection(results_df.columns):
                    latest_row = results_df.dropna(subset=[col for col in pnl_cols if col in results_df]).tail(1)
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
                    if (col == "date" and "date" in table_df.columns) or (col != "date" and col in results_df.columns)
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
                chart_df = bollinger_bands(chart_df, window=bollinger_window, column="close")

                has_macd = {"MACD_line", "MACD_signal", "MACD_hist"}.issubset(chart_df.columns)
                rsi_columns = [col for col in chart_df.columns if col.startswith("RSI_")]

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

                price_ax.plot(date_index, chart_df["close"], label="Close", color="black", linewidth=1.2)
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
                    date_index, chart_df["bb_middle"], label="Bollinger Mid", color="purple", linestyle=":"
                )
                price_ax.fill_between(
                    date_index,
                    chart_df["bb_lower"],
                    chart_df["bb_upper"],
                    color="purple",
                    alpha=0.1,
                    label="Bollinger Band",
                )

                buy_signals = chart_df[chart_df.get("signal", pd.Series(dtype=float)) > 0]
                sell_signals = chart_df[chart_df.get("signal", pd.Series(dtype=float)) < 0]

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
                    macd_ax.plot(date_index, chart_df["MACD_line"], label="MACD Line", color="teal")
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
                    rsi_ax.plot(date_index, chart_df[rsi_col], label=rsi_col, color="brown")
                    lower = user_strategy_params.get("lower_threshold", 30)
                    upper = user_strategy_params.get("upper_threshold", 70)
                    rsi_ax.axhline(lower, color="green", linestyle=":", label="Lower threshold")
                    rsi_ax.axhline(upper, color="red", linestyle=":", label="Upper threshold")
                    rsi_ax.set_ylabel("RSI")
                    rsi_ax.set_ylim(0, 100)
                    rsi_ax.grid(True, linestyle="--", alpha=0.3)
                    rsi_ax.legend()

                fig.tight_layout()
                st.subheader("Price, Indicators, and Signals")
                st.pyplot(fig)
            else:
                st.info("No tabular results available to display.")

elif mode == "Optimize MA Strategy":
    st.markdown("Run Optuna-based optimization for the MA crossover strategy.")
    opt_symbol = st.text_input("Symbol for optimization", value="AAPL")
    n_trials = int(
        st.number_input("Number of trials", min_value=1, value=50, step=10)
    )

    st.markdown("#### Optional parameter ranges")
    col1, col2 = st.columns(2)
    with col1:
        short_min = int(st.number_input("Short window min", min_value=1, value=5))
        short_max = int(st.number_input("Short window max", min_value=short_min + 1, value=50))
    with col2:
        long_min = int(st.number_input("Long window min", min_value=2, value=20))
        long_max = int(st.number_input("Long window max", min_value=long_min + 1, value=200))

    if st.button("Run optimization"):
        if not opt_symbol.strip():
            st.error("Symbol is required for optimization.")
            st.stop()

        if short_min >= short_max:
            st.error("Short window min must be less than max.")
            st.stop()
        if long_min >= long_max:
            st.error("Long window min must be less than max.")
            st.stop()
        if short_max >= long_max:
            st.error("Short window max must be less than long window max to allow feasible pairs.")
            st.stop()

        try:
            with st.spinner("Running Optuna optimization..."):
                best_params, best_value = optimize_ma_strategy_for_symbol(
                    symbol=opt_symbol.strip().upper(),
                    n_trials=n_trials,
                    short_window_range=(short_min, short_max),
                    long_window_range=(long_min, long_max),
                )
        except Exception as exc:
            st.error(f"Optimization failed: {exc}")
        else:
            st.success("Optimization complete!")
            st.write(f"**Best objective value:** {best_value:.4f}")
            st.write("**Best parameters:**")
            st.json(best_params)

            report_path = (
                Path(__file__).resolve().parents[1]
                / "reports"
                / f"optuna_ma_{opt_symbol.strip().upper()}.csv"
            )
            st.info(f"Trial results saved to: `{report_path}`")
