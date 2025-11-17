"""CLI script to fetch data, run strategy, and backtest results."""
from __future__ import annotations

import argparse

import pandas as pd

from backtesting.backtester import Backtester
from config import settings
from indicators.technicals import ema, macd, rsi, sma
from ingestion.alpha_vantage_client import AlphaVantageClient
from strategy.moving_average_crossover import MovingAverageCrossoverStrategy


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run moving average crossover backtest")
    parser.add_argument("symbol", help="Ticker symbol to download (e.g., AAPL)")
    parser.add_argument(
        "--outputsize",
        choices=["compact", "full"],
        default="compact",
        help="Alpha Vantage output size (default: compact)",
    )
    parser.add_argument("--short-window", type=int, default=50, help="Short SMA window")
    parser.add_argument("--long-window", type=int, default=200, help="Long SMA window")
    return parser.parse_args()


def ensure_api_key() -> str:
    api_key = settings.ALPHA_VANTAGE_API_KEY
    if not api_key or api_key == "REPLACE_WITH_MY_KEY":
        raise RuntimeError("Please set ALPHA_VANTAGE_API_KEY in config/settings.py before running.")
    return api_key


def compute_indicators(df: pd.DataFrame) -> pd.DataFrame:
    """Calculate a set of common indicators for inspection."""
    sma(df, window=20)
    ema(df, span=50)
    rsi(df, period=14)
    macd(df)
    return df


def main() -> None:
    args = parse_args()
    api_key = ensure_api_key()

    AlphaVantageClient.BASE_URL = settings.BASE_URL

    client = AlphaVantageClient(api_key=api_key)
    price_data = client.get_daily(args.symbol, outputsize=args.outputsize)

    compute_indicators(price_data)

    strategy = MovingAverageCrossoverStrategy(
        short_window=args.short_window, long_window=args.long_window
    )
    price_with_signals = strategy.run(price_data)

    backtester = Backtester()
    results = backtester.run(price_with_signals)

    latest_cumulative_return = results["cumulative_returns"].iloc[-1]
    max_drawdown = results["drawdown"].min()

    print(f"Results for {args.symbol}")
    print("Latest cumulative return: {:.2%}".format(latest_cumulative_return))
    print("Max drawdown: {:.2%}".format(max_drawdown))
    print("\nTail of results:")
    print(results.tail())


if __name__ == "__main__":
    main()
