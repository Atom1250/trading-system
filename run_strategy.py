# run_strategy.py

from ingestion.alpha_vantage_client import AlphaVantageClient
from indicators.technicals import sma  # assumes sma(df, window) -> pandas.Series
from strategy.moving_average_crossover import MovingAverageCrossoverStrategy
from backtesting.backtester import Backtester
from config.settings import ALPHA_VANTAGE_API_KEY


def run_backtest(
    symbol: str,
    short_window: int,
    long_window: int,
    outputsize: str = "compact",
    *,
    free_tier_only: bool = True,
):
    """
    Core function that runs the full backtest and returns a results dict.
    This is called by both the console UI and the Streamlit UI.
    """
    if not ALPHA_VANTAGE_API_KEY:
        raise RuntimeError(
            "ALPHA_VANTAGE_API_KEY is not set. Add it to your environment or .env file."
        )

    # 1. Download data
    effective_outputsize = outputsize
    if free_tier_only and outputsize == "full":
        print("Free tier mode: forcing outputsize='compact' to limit data usage.")
        effective_outputsize = "compact"

    client = AlphaVantageClient(ALPHA_VANTAGE_API_KEY)
    df = client.get_daily(
        symbol=symbol,
        outputsize=effective_outputsize,
        fallback_to_free_tier=free_tier_only,
    )

    # 2. Compute indicators needed by the strategy
    df["sma_short"] = sma(df, window=short_window)
    df["sma_long"] = sma(df, window=long_window)

    # 3. Run strategy
    strategy = MovingAverageCrossoverStrategy(
        short_window=short_window,
        long_window=long_window
    )
    df = strategy.run(df)

    # 4. Run backtest
    backtester = Backtester()
    results = backtester.run(df)

    return results


def main():
    """
    Simple console-based UI that asks the user for inputs.
    This replaces the strict command-line-argument approach that caused the error.
    """
    print("=== Trading System Runner ===")

    symbol = input("Enter symbol (e.g. AAPL): ").strip().upper()
    if not symbol:
        print("Symbol is required.")
        return

    try:
        short_window = int(input("Enter SHORT moving average window (e.g. 20): ").strip())
        long_window = int(input("Enter LONG moving average window (e.g. 50): ").strip())
    except ValueError:
        print("Short and long windows must be integers.")
        return

    if short_window >= long_window:
        print("Short window must be smaller than long window.")
        return

    outputsize = input("Output size 'compact' or 'full' [compact]: ").strip().lower()
    if outputsize == "":
        outputsize = "compact"
    if outputsize not in ("compact", "full"):
        print("Invalid output size, defaulting to 'compact'.")
        outputsize = "compact"

    print("\nRunning backtest...")
    results = run_backtest(symbol, short_window, long_window, outputsize)

    # Expected keys in results: 'cumulative_return', 'max_drawdown'
    print("\n=== Backtest Summary ===")
    print(f"Symbol: {symbol}")
    print(f"Short window: {short_window}, Long window: {long_window}")
    if "cumulative_return" in results:
        print(f"Cumulative return: {results['cumulative_return']:.2%}")
    if "max_drawdown" in results:
        print(f"Max drawdown: {results['max_drawdown']:.2%}")
    if "results_path" in results:
        print(f"Detailed results saved to: {results['results_path']}")
    else:
        print("Detailed results may be in reports/results.csv (depending on your Backtester implementation).")


if __name__ == "__main__":
    main()
