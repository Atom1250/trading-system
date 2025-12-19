"""Enhanced Streamlit UI with charting and parameter controls."""

from datetime import datetime, timedelta

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
from api_client import TradingSystemAPI

# Page config
st.set_page_config(
    page_title="Trading System",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)


# Initialize API client
@st.cache_resource
def get_api_client():
    return TradingSystemAPI()


api = get_api_client()

# Custom CSS
st.markdown(
    """
<style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .signal-buy {
        color: #00c853;
        font-weight: bold;
    }
    .signal-sell {
        color: #ff1744;
        font-weight: bold;
    }
    .signal-neutral {
        color: #ffa726;
        font-weight: bold;
    }
</style>
""",
    unsafe_allow_html=True,
)

# Sidebar
st.sidebar.title("📊 Trading System")

# Portfolio Management
with st.sidebar.expander("💼 Portfolio Management", expanded=False):
    st.subheader("Create New Portfolio")
    new_pf_name = st.text_input("Name", key="new_pf_name")
    new_pf_desc = st.text_input("Description", key="new_pf_desc")
    new_pf_capital = st.number_input(
        "Initial Capital", value=100000.0, step=1000.0, key="new_pf_capital",
    )

    if st.button("Create Portfolio"):
        if new_pf_name:
            try:
                api.create_portfolio(new_pf_name, new_pf_desc, new_pf_capital)
                st.success(f"Created '{new_pf_name}'!")
                st.rerun()
            except Exception as e:
                st.error(f"Failed: {e}")
        else:
            st.warning("Name required")

st.sidebar.markdown("---")

# Symbol selection
symbol = st.sidebar.text_input("Symbol", value="AAPL", help="Enter stock symbol")

# Data source selection
try:
    sources = api.get_data_sources()
    source_names = [s["name"] for s in sources]
    data_source = st.sidebar.selectbox(
        "Data Source",
        options=source_names,
        index=source_names.index("local") if "local" in source_names else 0,
    )
except Exception as e:
    st.sidebar.error(f"Error loading data sources: {e}")
    data_source = "local"

# Date range
st.sidebar.markdown("### Date Range")
col1, col2 = st.sidebar.columns(2)
with col1:
    start_date = st.date_input(
        "Start", value=datetime.now() - timedelta(days=365), max_value=datetime.now(),
    )
with col2:
    end_date = st.date_input("End", value=datetime.now(), max_value=datetime.now())

st.sidebar.markdown("---")

# Main content
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
    [
        "📈 Chart",
        "🎯 Strategies",
        "📡 Signals",
        "🔬 Backtests",
        "⚙️ Optimization",
        "🤖 AI Insights",
        "🔌 Integration",
    ],
)


with tab1:
    st.header(f"Price Chart - {symbol}")

    try:
        # Get price data
        price_data = api.get_prices(
            symbol=symbol,
            source=data_source,
            start_date=datetime.combine(start_date, datetime.min.time()),
            end_date=datetime.combine(end_date, datetime.min.time()),
        )

        if price_data and price_data.get("data"):
            df_prices = pd.DataFrame(price_data["data"])
            df_prices["date"] = pd.to_datetime(df_prices["date"])

            # Create candlestick chart
            fig = go.Figure()

            fig.add_trace(
                go.Candlestick(
                    x=df_prices["date"],
                    open=df_prices["open"],
                    high=df_prices["high"],
                    low=df_prices["low"],
                    close=df_prices["close"],
                    name="Price",
                ),
            )

            # Add volume bar chart
            fig.add_trace(
                go.Bar(
                    x=df_prices["date"],
                    y=df_prices["volume"],
                    name="Volume",
                    yaxis="y2",
                    marker=dict(color="rgba(100, 100, 100, 0.3)"),
                ),
            )

            # Technical Indicators Overlay
            with st.expander("Technical Indicators", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    show_sma = st.checkbox("SMA (20, 50)", value=False)
                with col2:
                    show_bb = st.checkbox("Bollinger Bands (20, 2)", value=False)
                with col3:
                    show_ema = st.checkbox("EMA (20)", value=False)

            if show_sma:
                df_prices["SMA_20"] = df_prices["close"].rolling(window=20).mean()
                df_prices["SMA_50"] = df_prices["close"].rolling(window=50).mean()
                fig.add_trace(
                    go.Scatter(
                        x=df_prices["date"],
                        y=df_prices["SMA_20"],
                        name="SMA 20",
                        line=dict(color="orange", width=1),
                    ),
                )
                fig.add_trace(
                    go.Scatter(
                        x=df_prices["date"],
                        y=df_prices["SMA_50"],
                        name="SMA 50",
                        line=dict(color="blue", width=1),
                    ),
                )

            if show_ema:
                df_prices["EMA_20"] = (
                    df_prices["close"].ewm(span=20, adjust=False).mean()
                )
                fig.add_trace(
                    go.Scatter(
                        x=df_prices["date"],
                        y=df_prices["EMA_20"],
                        name="EMA 20",
                        line=dict(color="purple", width=1),
                    ),
                )

            if show_bb:
                window = 20
                std_dev = 2
                df_prices["BB_Middle"] = (
                    df_prices["close"].rolling(window=window).mean()
                )
                df_prices["BB_Std"] = df_prices["close"].rolling(window=window).std()
                df_prices["BB_Upper"] = df_prices["BB_Middle"] + (
                    df_prices["BB_Std"] * std_dev
                )
                df_prices["BB_Lower"] = df_prices["BB_Middle"] - (
                    df_prices["BB_Std"] * std_dev
                )

                fig.add_trace(
                    go.Scatter(
                        x=df_prices["date"],
                        y=df_prices["BB_Upper"],
                        name="BB Upper",
                        line=dict(color="gray", width=1, dash="dash"),
                    ),
                )
                fig.add_trace(
                    go.Scatter(
                        x=df_prices["date"],
                        y=df_prices["BB_Lower"],
                        name="BB Lower",
                        line=dict(color="gray", width=1, dash="dash"),
                        fill="tonexty",
                        fillcolor="rgba(128, 128, 128, 0.1)",
                    ),
                )
                fig.add_trace(
                    go.Scatter(
                        x=df_prices["date"],
                        y=df_prices["BB_Middle"],
                        name="BB Middle",
                        line=dict(color="gray", width=1, dash="dot"),
                    ),
                )

            # Try to get technical signals and overlay them
            try:
                signals = api.get_technical_signals(symbol, data_source=data_source)

                # Add SMA lines if available
                for indicator in signals.get("indicators", []):
                    if "SMA" in indicator["name"]:
                        # This is simplified - in production you'd get the full series
                        pass

            except Exception as e:
                st.warning(f"Failed to get technical signals: {e}")

            fig.update_layout(
                title=f"{symbol} Price Chart",
                yaxis_title="Price ($)",
                yaxis2=dict(title="Volume", overlaying="y", side="right"),
                xaxis_rangeslider_visible=False,
                hovermode="x unified",
                height=600,
            )

            st.plotly_chart(fig, use_container_width=True)

            # Display current price info
            latest = df_prices.iloc[-1]
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Close", f"${latest['close']:.2f}")
            with col2:
                st.metric("High", f"${latest['high']:.2f}")
            with col3:
                st.metric("Low", f"${latest['low']:.2f}")
            with col4:
                st.metric("Volume", f"{latest['volume']:,.0f}")
        else:
            st.info("No price data available for the selected symbol and date range")

    except Exception as e:
        st.error(f"Error loading chart: {e}")

with tab2:
    st.header("Strategies")

    try:
        strategies = api.get_strategies()

        if strategies:
            st.subheader("Available Strategies")

            for strategy in strategies:
                with st.expander(f"📈 {strategy['name']}", expanded=False):
                    st.write(f"**Description:** {strategy.get('description', 'N/A')}")
                    st.write("**Default Parameters:**")

                    params = strategy.get("parameters", {})
                    if params:
                        for key, value in params.items():
                            st.write(f"- `{key}`: {value}")
                    else:
                        st.write("No parameters")
        else:
            st.info("No strategies available")

    except Exception as e:
        st.error(f"Error loading strategies: {e}")

with tab3:
    st.header(f"Signals - {symbol}")

    signal_type = st.radio(
        "Signal Type",
        options=["Aggregated", "Technical", "Fundamental", "Sentiment"],
        horizontal=True,
    )

    try:
        if signal_type == "Aggregated":
            signals = api.get_aggregated_signals(symbol, data_source=data_source)

            # Overall recommendation
            rec = signals.get("recommendation", "hold")
            score = signals.get("combined_score", 50)

            st.metric(
                "Combined Score", f"{score}/100", f"Recommendation: {rec.upper()}",
            )

            # Individual signals
            col1, col2, col3 = st.columns(3)

            with col1:
                if signals.get("technical"):
                    tech = signals["technical"]
                    st.subheader("Technical")
                    st.metric("Signal", tech.get("overall_signal", "N/A").upper())
                    st.metric("Strength", f"{tech.get('strength', 0)}%")

                    # Show indicators
                    if tech.get("indicators"):
                        st.write("**Indicators:**")
                        for ind in tech["indicators"]:
                            st.write(
                                f"- {ind['name']}: {ind['value']:.2f} ({ind.get('signal', 'N/A')})",
                            )

            with col2:
                if signals.get("fundamental"):
                    fund = signals["fundamental"]
                    st.subheader("Fundamental")
                    st.metric("Rating", fund.get("rating", "N/A").upper())
                    st.metric("Score", f"{fund.get('score', 0)}/100")

            with col3:
                if signals.get("sentiment"):
                    sent = signals["sentiment"]
                    st.subheader("Sentiment")
                    st.metric("Signal", sent.get("signal", "N/A").upper())
                    st.metric("Score", f"{float(sent.get('overall_sentiment', 0)):.2f}")

        elif signal_type == "Technical":
            signals = api.get_technical_signals(symbol, data_source=data_source)

            st.metric("Overall Signal", signals.get("overall_signal", "N/A").upper())
            st.metric("Strength", f"{signals.get('strength', 0)}%")

            st.subheader("Indicators")
            indicators = signals.get("indicators", [])
            if indicators:
                df = pd.DataFrame(indicators)
                st.dataframe(df, use_container_width=True)

        elif signal_type == "Fundamental":
            signals = api.get_fundamental_signals(symbol)

            st.metric("Rating", signals.get("rating", "N/A").upper())
            st.metric("Score", f"{signals.get('score', 0)}/100")

            st.subheader("Metrics")
            metrics = signals.get("metrics", [])
            if metrics:
                df = pd.DataFrame(metrics)
                st.dataframe(df, use_container_width=True)

        elif signal_type == "Sentiment":
            signals = api.get_sentiment_signals(symbol)

            st.metric("Signal", signals.get("signal", "N/A").upper())
            st.metric(
                "Overall Sentiment", f"{float(signals.get('overall_sentiment', 0)):.2f}",
            )

            st.subheader("Sources")
            scores = signals.get("scores", [])
            if scores:
                df = pd.DataFrame(scores)
                st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error(f"Error loading signals: {e}")

with tab4:
    st.header("Run Backtest")

    col1, col2 = st.columns([1, 1])

    with col1:
        try:
            strategies = api.get_strategies()
            strategy_names = [s["name"] for s in strategies]
            selected_strategy = st.selectbox("Strategy", options=strategy_names)

            # Get strategy details to show parameters
            if selected_strategy:
                strategy_info = next(
                    (s for s in strategies if s["name"] == selected_strategy), None,
                )
                if strategy_info:
                    st.write("**Configure Parameters:**")
                    default_params = strategy_info.get("parameters", {})

                    # Create dynamic parameter inputs
                    custom_params = {}
                    for param_name, param_value in default_params.items():
                        if isinstance(param_value, int):
                            custom_params[param_name] = st.number_input(
                                param_name.replace("_", " ").title(),
                                value=int(param_value),
                                step=1,
                                key=f"param_{param_name}",
                            )
                        elif isinstance(param_value, float):
                            custom_params[param_name] = st.number_input(
                                param_name.replace("_", " ").title(),
                                value=float(param_value),
                                key=f"param_{param_name}",
                            )
                        elif isinstance(param_value, bool):
                            custom_params[param_name] = st.checkbox(
                                param_name.replace("_", " ").title(),
                                value=param_value,
                                key=f"param_{param_name}",
                            )
                        else:
                            custom_params[param_name] = st.text_input(
                                param_name.replace("_", " ").title(),
                                value=str(param_value),
                                key=f"param_{param_name}",
                            )
        except Exception as e:
            st.warning(f"Failed to load strategies: {e}")
            selected_strategy = st.text_input(
                "Strategy Name", value="moving_average_crossover",
            )
            custom_params = {}

        initial_capital = st.number_input(
            "Initial Capital", min_value=1000, value=100000, step=1000,
        )

    with col2:
        st.write("**Backtest Configuration:**")
        commission = (
            st.number_input("Commission (%)", min_value=0.0, value=0.1, step=0.01) / 100
        )

        st.write(f"**Date Range:** {start_date} to {end_date}")
        st.write(f"**Data Source:** {data_source}")

    if st.button("Run Backtest", type="primary"):
        try:
            with st.spinner("Running backtest..."):
                result = api.run_backtest(
                    symbol=symbol,
                    strategy_name=selected_strategy,
                    parameters=custom_params if custom_params else None,
                    start_date=datetime.combine(start_date, datetime.min.time()),
                    end_date=datetime.combine(end_date, datetime.min.time()),
                    initial_capital=initial_capital,
                    data_source=data_source,
                )

            st.success("Backtest completed!")

            # Metrics
            metrics = result.get("metrics", {})
            col1, col2, col3, col4 = st.columns(4)

            with col1:
                st.metric(
                    "Total Return", f"{float(metrics.get('total_return_pct', 0)):.2f}%",
                )
            with col2:
                sharpe = metrics.get("sharpe_ratio")
                st.metric("Sharpe Ratio", f"{float(sharpe):.2f}" if sharpe else "N/A")
            with col3:
                st.metric(
                    "Max Drawdown", f"{float(metrics.get('max_drawdown_pct', 0)):.2f}%",
                )
            with col4:
                win_rate = metrics.get("win_rate")
                st.metric("Win Rate", f"{float(win_rate):.2f}%" if win_rate else "N/A")

            # Equity curve with signals
            equity_curve = result.get("equity_curve", [])
            trades = result.get("trades", [])

            if equity_curve:
                st.subheader("Equity Curve with Trade Signals")
                df_equity = pd.DataFrame(equity_curve)
                df_equity["date"] = pd.to_datetime(df_equity["date"])

                fig = go.Figure()

                # Equity curve
                fig.add_trace(
                    go.Scatter(
                        x=df_equity["date"],
                        y=df_equity["value"],
                        mode="lines",
                        name="Portfolio Value",
                        line=dict(color="#1f77b4", width=2),
                    ),
                )

                # Add trade markers
                if trades:
                    df_trades = pd.DataFrame(trades)
                    if "entry_date" in df_trades.columns:
                        df_trades["entry_date"] = pd.to_datetime(
                            df_trades["entry_date"],
                        )

                        # Merge with equity to get values at trade times
                        # Simplified - just show entry points
                        fig.add_trace(
                            go.Scatter(
                                x=df_trades["entry_date"],
                                y=[initial_capital] * len(df_trades),  # Simplified
                                mode="markers",
                                name="Trades",
                                marker=dict(
                                    size=10,
                                    color=[
                                        "green" if pnl > 0 else "red"
                                        for pnl in df_trades.get(
                                            "pnl", [0] * len(df_trades),
                                        )
                                    ],
                                    symbol="triangle-up",
                                ),
                            ),
                        )

                fig.update_layout(
                    title="Portfolio Value Over Time",
                    xaxis_title="Date",
                    yaxis_title="Value ($)",
                    hovermode="x unified",
                    height=500,
                )
                st.plotly_chart(fig, use_container_width=True)

            # Trades table
            if trades:
                st.subheader(f"Trades ({len(trades)})")
                df_trades = pd.DataFrame(trades)
                st.dataframe(df_trades, use_container_width=True)

        except Exception as e:
            st.error(f"Backtest failed: {e}")

with tab5:
    st.header("Strategy Optimization")
    st.info("Optimize strategy parameters using Optuna to find the best configuration.")

    col1, col2 = st.columns([1, 1])

    with col1:
        try:
            strategies = api.get_strategies()
            strategy_names = [s["name"] for s in strategies]
            opt_strategy = st.selectbox(
                "Strategy to Optimize", options=strategy_names, key="opt_strategy",
            )

            # Dynamic parameter ranges based on strategy
            param_ranges = {}
            if opt_strategy:
                strategy_info = next(
                    (s for s in strategies if s["name"] == opt_strategy), None,
                )
                if strategy_info:
                    st.write("**Parameter Ranges:**")
                    default_params = strategy_info.get("parameters", {})

                    for param_name, param_value in default_params.items():
                        if isinstance(param_value, (int, float)):
                            with st.expander(f"{param_name}", expanded=True):
                                p_type = (
                                    "int" if isinstance(param_value, int) else "float"
                                )

                                c1, c2, c3 = st.columns(3)
                                with c1:
                                    min_val = st.number_input(
                                        "Min",
                                        value=float(param_value) * 0.5,
                                        key=f"min_{param_name}",
                                    )
                                with c2:
                                    max_val = st.number_input(
                                        "Max",
                                        value=float(param_value) * 1.5,
                                        key=f"max_{param_name}",
                                    )
                                with c3:
                                    step_val = st.number_input(
                                        "Step",
                                        value=1.0 if p_type == "int" else 0.1,
                                        key=f"step_{param_name}",
                                    )

                                param_ranges[param_name] = {
                                    "type": p_type,
                                    "min": min_val,
                                    "max": max_val,
                                    "step": step_val,
                                }
        except Exception as e:
            st.error(f"Failed to load strategies: {e}")
            param_ranges = {}

    with col2:
        st.write("**Optimization Config:**")
        n_trials = st.number_input(
            "Number of Trials", min_value=5, max_value=100, value=20, step=5,
        )
        opt_metric = st.selectbox(
            "Metric to Optimize",
            options=["sharpe_ratio", "total_return_pct", "max_drawdown_pct"],
        )
        opt_direction = st.selectbox("Direction", options=["maximize", "minimize"])

        if st.button("Run Optimization", type="primary"):
            if not param_ranges:
                st.warning("No parameters to optimize.")
            else:
                try:
                    with st.spinner(f"Running {n_trials} trials..."):
                        result = api.run_optimization(
                            strategy_name=opt_strategy,
                            symbol=symbol,
                            parameter_ranges=param_ranges,
                            initial_capital=100000,
                            data_source=data_source,
                            n_trials=n_trials,
                            metric=opt_metric,
                            direction=opt_direction,
                        )

                    st.success(
                        f"Optimization complete! Best Value: {result['best_value']:.4f}",
                    )
                    st.json(result["best_params"])

                    # Show trials
                    if result.get("trials"):
                        st.subheader("Trial History")
                        df_trials = pd.DataFrame(result["trials"])

                        # Convert string values (inf, -inf, nan) back to float for sorting/plotting
                        if "value" in df_trials.columns:
                            df_trials["value"] = df_trials["value"].replace(
                                {
                                    "inf": float("inf"),
                                    "-inf": float("-inf"),
                                    "nan": float("nan"),
                                },
                            )
                            df_trials["value"] = pd.to_numeric(df_trials["value"])

                        # Flatten params
                        df_params = pd.json_normalize(df_trials["params"])
                        df_trials = pd.concat(
                            [df_trials.drop("params", axis=1), df_params], axis=1,
                        )

                        st.dataframe(
                            df_trials.sort_values(
                                "value", ascending=(opt_direction == "minimize"),
                            ),
                            use_container_width=True,
                        )

                        # Plot optimization history
                        fig = px.scatter(
                            df_trials,
                            x="number",
                            y="value",
                            title="Optimization History",
                        )
                        st.plotly_chart(fig, use_container_width=True)

                except Exception as e:
                    st.error(f"Optimization failed: {e}")

with tab6:
    st.header("AI Insights")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Risk Assessment")
        if st.button("Assess Risk"):
            try:
                risk = api.session.post(
                    f"{api.base_url}/api/v1/ai/risk_assessment",
                    params={"symbol": symbol, "data_source": data_source},
                ).json()

                st.metric("Risk Score", f"{float(risk['risk_score']):.1f}/100")
                st.metric("Risk Level", risk["risk_level"].upper())

                st.write("**Metrics:**")
                metrics = risk["metrics"]
                st.write(f"- Volatility: {float(metrics['volatility']):.2%}")
                st.write(f"- VaR (95%): {float(metrics['var_95']):.2%}")
                st.write(f"- Sharpe Ratio: {float(metrics['sharpe_ratio']):.2f}")
                st.write(f"- Max Drawdown: {float(metrics['max_drawdown']):.2%}")

                if risk.get("recommendations"):
                    st.write("**Recommendations:**")
                    for rec in risk["recommendations"]:
                        st.write(f"- {rec}")
            except Exception as e:
                st.error(f"Risk assessment failed: {e}")

    with col2:
        st.subheader("Feature Importance")
        if st.button("Show Feature Importance"):
            try:
                features = api.session.get(
                    f"{api.base_url}/api/v1/ai/feature_importance",
                ).json()

                st.write(f"**Model:** {features['model_name']}")

                # Create bar chart
                importances = features["feature_importances"]
                df_features = pd.DataFrame(importances)

                fig = px.bar(
                    df_features,
                    x="importance",
                    y="feature",
                    orientation="h",
                    title="Feature Importance",
                    labels={"importance": "Importance", "feature": "Feature"},
                )
                st.plotly_chart(fig, use_container_width=True)

            except Exception as e:
                st.error(f"Feature importance failed: {e}")

with tab7:
    st.header("Integration & Export")

    st.info("Export your portfolio data to Google Sheets or download as CSV/Excel.")

    try:
        portfolios = api.get_portfolios()
        if portfolios:
            portfolio_options = {p["name"]: p["id"] for p in portfolios}
            selected_portfolio_name = st.selectbox(
                "Select Portfolio", options=list(portfolio_options.keys()),
            )
            selected_portfolio_id = portfolio_options[selected_portfolio_name]

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("Google Sheets")
                sheet_name = st.text_input(
                    "Spreadsheet Name",
                    value=f"Portfolio Export - {selected_portfolio_name}",
                )

                if st.button("Export to Google Sheets"):
                    try:
                        with st.spinner("Exporting..."):
                            result = api.export_to_google_sheets(
                                selected_portfolio_id, sheet_name,
                            )
                        st.success(
                            f"Export successful! [Open Sheet]({result['spreadsheet_url']})",
                        )
                    except Exception as e:
                        st.error(f"Export failed: {e}")

            with col2:
                st.subheader("File Download")
                format_type = st.radio("Format", options=["CSV", "Excel"])

                if st.button("Prepare Download"):
                    try:
                        with st.spinner("Generating file..."):
                            file_content = api.download_portfolio_export(
                                selected_portfolio_id, format_type.lower(),
                            )

                            file_name = f"portfolio_{selected_portfolio_id}.{format_type.lower()}"
                            mime_type = (
                                "text/csv"
                                if format_type == "CSV"
                                else "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )

                            st.download_button(
                                label=f"Download {format_type} File",
                                data=file_content,
                                file_name=file_name,
                                mime=mime_type,
                            )
                    except Exception as e:
                        st.error(f"Download failed: {e}")

        else:
            st.warning("No portfolios found. Please create a portfolio first.")

    except Exception as e:
        st.error(f"Error loading portfolios: {e}")


# Footer
st.sidebar.markdown("---")
st.sidebar.markdown("**Trading System v2.0**")
st.sidebar.markdown("Powered by FastAPI + Streamlit")
