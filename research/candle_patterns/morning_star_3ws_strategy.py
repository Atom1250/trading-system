from datetime import datetime

import backtrader as bt
import yfinance as yf


class MorningStar3WS(bt.Strategy):
    params = (bt.Param.Float("initial_entry", 1), bt.Param.Int("exit_reversals", 2))

    def __init__(self):
        self.data_close = self.datas[0].close
        self.initial_entry = self.p.initial_entry  # Track initial position size
        self.reversal_checker = bt.indicators.SMA(self.data_close, period=10)

        # Morning Star detection
        self.morning_star_detected = False

    def next(self):
        # Morning Star Conditions
        cond1 = self.data.high[1] < self.data.open and abs(  # Tall bearish candle
            self.data.close - self.data.open
        ) < (self.data.high - self.data.low)

        # Second candle's close > midpoint of first candle
        cond2 = self.data.close[1] < (self.data.high[0] + self.data.low[0]) / 2

        # Third candle (bullish)
        cond3 = self.data.open < self.data.close[2]

        # Update Morning Star flag
        if cond1 and cond2 and cond3:
            self.morning_star_detected = True
            print(f"{self.data.datetime.date()}: Morning Star detected!")
        else:
            self.morning_star_detected = False

        # Exit on bearish candle after entry
        if self.position:
            last_candle_bearish = (
                self.data.open > self.data.close
                and self.reversal_checker
                < self.data_close[1]  # Check SMA crossover (optional)
            )
            if last_candle_bearish:
                print(
                    f"{self.data.datetime.date()}: Reversal signal! Closing position."
                )
                self.close()

        # Three White Soldiers: Double position if Morning Star was already bought
        if self.initial_entry and not self.position:
            # Track 3 consecutive bullish candles with increasing volume
            soldier1 = (
                self.data.open < self.data.close
                and self.data.volume > self.data.volume[1]
            )
            soldier2 = (
                self.data.open < self.data.close
                and self.data.volume > self.data.volume[2]
            )
            soldier3 = (
                self.data.open < self.data.close
                and self.data.volume > self.data.volume[3]
            )

            if soldier1 and soldier2 and soldier3:
                print(
                    f"{self.data.datetime.date()}: Three White Soldiers detected! Doubling position."
                )
                self.buy(size=self.initial_entry)
                self.initial_entry *= 2

        # Trade entry: Morning Star + no existing position
        if self.morning_star_detected and not self.position:
            print(f"{self.data.datetime.date()}: Buying at Morning Star.")
            self.buy(size=self.initial_entry)


# Data Fetching and Backtest
def fetch_data(ticker, start_date):
    data = yf.download(
        ticker, start=start_date, end=datetime.today().strftime("%Y-%m-%d")
    )
    return data


def backtest(strategy_class, ticker="AAPL", start_date="2021-01-01"):
    data = fetch_data(ticker, start_date)
    cerebro = bt.Cerebro()

    # Add data and strategy
    cerebro.adddata(bt.feeds.PandasData(dataname=data))
    cerebro.addstrategy(strategy_class)

    # Set initial capital and run
    cerebro.broker.setcash(10000)
    cerebro.run()
    cerebro.plot(style="candlestick")


# Run
if __name__ == "__main__":
    backtest(MorningStar3WS)
