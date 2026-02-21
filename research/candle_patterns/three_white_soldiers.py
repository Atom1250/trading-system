from datetime import datetime

import backtrader as bt
import yfinance as yf


# Define the Three White Soldiers Strategy
class ThreeWhiteSoldiersStrategy(bt.Strategy):
    def __init__(self):
        # Calculate a simple moving average for context (optional)
        self.sma = bt.indicators.SimpleMovingAverage(self.data.close, period=20)

        # Initialize counters for Three White Soldiers
        self.counter = 0

    def next(self):
        # Define criteria for a "White Soldier":
        # Long bullish candle (Close > Open) with increasing volume
        is_white_soldier = (
            self.data.close[0] > self.data.open[0]
            and self.data.volume[0] > self.data.volume[-1]  # Increasing volume
        )

        # Check if the candle is sufficiently 'long' (e.g., 2x body size)
        body_size = abs(self.data.close[0] - self.data.open[0])
        max_range = self.data.high[0] - self.data.low[0]
        is_long_body = body_size > 0.5 * max_range

        if is_white_soldier and is_long_body:
            self.counter += 1
        else:
            self.counter = 0

        # Trigger a trade if we have three white soldiers
        if self.counter == 3:
            print(
                f"Trade Signal at {self.data.datetime.date()}: Three White Soldiers detected!"
            )
            self.buy()
            # Reset counter to avoid overlapping patterns
            self.counter = 8


# Load Data (Yahoo Finance)
def fetch_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data


# Backtest Function
def backtest(
    strategy_class,
    ticker="AAPL",
    start_date="2021-01-01",
    end_date=datetime.today().strftime("%Y-%m-%d"),
):
    data = fetch_data(ticker, start_date, end_date)
    cerebro = bt.Cerebro()

    # Add data and strategy
    cerebro.adddata(bt.feeds.PandasData(dataname=data))
    cerebro.addstrategy(strategy_class)

    # Set capital and run backtest
    cerebro.broker.setcash(10000)
    cerebro.run()
    cerebro.plot(style="candlestick")


# Run Backtest
if __name__ == "__main__":
    backtest(ThreeWhiteSoldiersStrategy, ticker="AAPL")
