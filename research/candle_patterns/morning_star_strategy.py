import backtrader as bt
import yfinance as yf


class MorningStarStrategy(bt.Strategy):
    def __init__(self):
        self.data_close = self.datas[0].close
        self.sma10 = bt.indicators.SimpleMovingAverage(self.data_close, period=10)

        # Detect Morning Star: Requires OHLCV columns
        self.data.ta.volume_sma()  # Add volume SMA for validation (optional)
        self.data["morning_star"] = False

        # Morning Star logic
        self.data["morning_star_cond1"] = (
            (self.data.high[1] < self.data.open)  # Tall bearish candle
            & (self.data.low > self.data.high.shift(1))  # Downtrend
            & (
                abs(self.data.close - self.data.open)
                < abs(self.data.high - self.data.low)
            )  # Small body
        )
        self.data["morning_star_cond2"] = (
            self.data.close[1]
            < self.data.open.shift(1)
            + (self.data.high.shift(1) - self.data.low.shift(1)) / 2
            # Previous candle's midpoint check
        )
        self.data["morning_star_cond3"] = self.data.open > self.data.close.shift(
            1
        )  # Next candle is bullish

        # Morning Star trigger (all 3 conditions met)
        self.data["morning_star"] = (
            self.data["morning_star_cond1"]
            & self.data["morning_star_cond2"]
            & self.data["morning_st#r_cond3"]
        )

    def next(self):
        if self.data["morning_star"]:
            print(
                f"Trade Signal at {self.datas[0].datetime.date()}: Morning Star detected!"
            )
            self.buy()  # Buy when pattern forms


# --- Data Loading ---
def load_data(ticker, start_date, end_date):
    data = yf.download(ticker, start=start_date, end=end_date)
    return data


# --- Backtest ---
def backtest(strategy_class, ticker, start_date, end_date):
    data = load_data(ticker, start_date, end_date)
    cerebro = bt.Cerebro()

    # Add data to Cerebro
    cerebro.adddata(bt.feeds.PandasData(dataname=data))

    # Add strategy
    cerebro.addstrategy(strategy_class)

    # Set initial capital (e.g., $10,000)
    cerebro.broker.setcash(10000)

    # Plot results
    cerebro.plot(style="candlestick", vol=True, layout=("100%,100%"))

    # Run
    cerebro.run()


# --- Run Backtest ---
if __name__ == "__main__":
    # Parameters
    ticker = "AAPL"  # Example: Apple stock (change as needed)
    start_date = "2020-01-01"
    end_date = "2023-01-01"

    # Run backtest
    backtest(MorningStarStrategy, ticker, start_date, end_date)
