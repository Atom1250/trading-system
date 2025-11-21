import streamlit as st

from run_strategy import run_backtest


st.title("Trading Strategy Backtest")

st.markdown("Use this interface to run the moving average crossover strategy backtest.")

# Input fields
symbol = st.text_input("Symbol", value="AAPL")
short_window = st.number_input("Short moving average window", min_value=1, value=20, step=1)
long_window = st.number_input("Long moving average window", min_value=2, value=50, step=1)
outputsize = st.selectbox("Output size", options=["compact", "full"], index=0)
data_source = st.radio(
    "Data source",
    ["Cached (use local data if available)", "Live API (fetch from Alpha Vantage)"],
    index=0,
)
use_cache = data_source.startswith("Cached")

refresh_cache = st.button("Refresh cache from API")

if refresh_cache:
    if not symbol.strip():
        st.error("Symbol is required to refresh the cache.")
    else:
        st.info(f"Refreshing cache for {symbol.strip().upper()} from Alpha Vantage...")
        try:
            run_backtest(
                symbol=symbol.strip().upper(),
                short_window=int(short_window),
                long_window=int(long_window),
                outputsize=outputsize,
                use_cache=True,
                force_refresh=True,
            )
        except Exception as exc:
            st.error(f"Cache refresh failed: {exc}")
        else:
            st.success(f"Cache refreshed for {symbol.strip().upper()}.")
        st.stop()

# Run button
if st.button("Run backtest"):
    if short_window >= long_window:
        st.error("Short window must be smaller than long window.")
    elif not symbol.strip():
        st.error("Symbol is required.")
    else:
        requested_outputsize = outputsize
        if requested_outputsize == "full":
            st.info(
                "Free tier mode is enabled. Requests for 'full' output will fall back to "
                "'compact' to avoid premium endpoints."
            )

        try:
            with st.spinner("Running backtest..."):
                results = run_backtest(
                    symbol=symbol.strip().upper(),
                    short_window=int(short_window),
                    long_window=int(long_window),
                    outputsize=requested_outputsize,
                    use_cache=use_cache,
                )
        except Exception as exc:  # Surface Alpha Vantage errors clearly in the UI
            st.error(f"Backtest failed: {exc}")
            st.stop()

        st.success("Backtest complete!")

        if use_cache and results.get("cache_seeded"):
            st.info(
                f"No cache found for {symbol.strip().upper()}. "
                "Fetched data from Alpha Vantage and seeded the cache."
            )

        st.subheader("Summary")
        st.write(f"**Symbol:** {symbol.strip().upper()}")
        st.write(f"**Short window:** {int(short_window)}")
        st.write(f"**Long window:** {int(long_window)}")

        if "cumulative_return" in results:
            st.write(f"**Cumulative return:** {results['cumulative_return']:.2%}")
        if "max_drawdown" in results:
            st.write(f"**Max drawdown:** {results['max_drawdown']:.2%}")

        if "results_path" in results:
            st.write(f"Detailed results saved to: `{results['results_path']}`")
        if results.get("data_source") == "api" and not use_cache:
            st.warning("Data fetched directly from Alpha Vantage (cache bypassed).")
