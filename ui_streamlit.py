import streamlit as st

from run_strategy import run_backtest


st.title("Trading Strategy Backtest")

st.markdown("Use this interface to run the moving average crossover strategy backtest.")

# Input fields
symbol = st.text_input("Symbol", value="AAPL")
short_window = st.number_input("Short moving average window", min_value=1, value=20, step=1)
long_window = st.number_input("Long moving average window", min_value=2, value=50, step=1)
outputsize = st.selectbox("Output size", options=["compact", "full"], index=0)

# Run button
if st.button("Run backtest"):
    if short_window >= long_window:
        st.error("Short window must be smaller than long window.")
    elif not symbol.strip():
        st.error("Symbol is required.")
    else:
        with st.spinner("Running backtest..."):
            results = run_backtest(
                symbol=symbol.strip().upper(),
                short_window=int(short_window),
                long_window=int(long_window),
                outputsize=outputsize,
            )

        st.success("Backtest complete!")

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
