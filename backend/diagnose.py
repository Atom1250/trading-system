import os
import sys
import traceback
from pathlib import Path
from datetime import datetime

# Add /app to sys.path to mimic Docker environment if needed
sys.path.insert(0, "/app")

print("=== DIAGNOSTICS START ===")
print(f"CWD: {os.getcwd()}")
print(f"PYTHONPATH: {os.environ.get('PYTHONPATH')}")
print(f"TS_DATA_ROOT: {os.environ.get('TS_DATA_ROOT')}")

# Check Data Directory
data_root = os.environ.get('TS_DATA_ROOT', '/app/data')
print(f"Checking data root: {data_root}")
if os.path.exists(data_root):
    print(f"  Data root exists. Contents: {os.listdir(data_root)}")
    prices_dir = os.path.join(data_root, "prices")
    if os.path.exists(prices_dir):
        print(f"  Prices dir exists. Contents: {os.listdir(prices_dir)}")
    else:
        print("  Prices dir MISSING")
else:
    print("  Data root MISSING")

# Test Price Service
print("\n--- Testing PriceDataService ---")
try:
    from services.data.price_service import PriceDataService
    service = PriceDataService()
    print("  PriceDataService initialized")
    
    # Try to list sources
    print(f"  Sources: {service.get_available_sources()}")
    
    # Try to fetch data for a known symbol (e.g. AAPL)
    symbol = "AAPL"
    print(f"  Fetching prices for {symbol} (source=local)...")
    df = service.get_prices(symbol, source="local")
    if df.empty:
        print("  Result: EMPTY DataFrame")
    else:
        print(f"  Result: {len(df)} rows")
        print(f"  Columns: {df.columns.tolist()}")
        print(f"  Head:\n{df.head()}")

except Exception:
    print("  FAILED to fetch prices:")
    traceback.print_exc()

# Test Backtest Service
print("\n--- Testing BacktestService ---")
try:
    from services.strategy.backtest_service import BacktestService
    from services.strategy.registry import registry
    
    bs = BacktestService()
    print("  BacktestService initialized")
    
    # Get data first to inspect
    print(f"  Fetching data for {symbol}...")
    df = bs.price_service.get_prices(symbol, source="local")
    print(f"  Data shape: {df.shape}")
    print(f"  Data types:\n{df.dtypes}")
    
    # Run strategy manually
    print("  Running strategy manually...")
    strategy_name = "moving_average_crossover"
    strategy = registry.create_strategy(strategy_name)
    df_sig = strategy.run(df.copy())
    
    print("  Strategy run complete.")
    print(f"  Columns: {df_sig.columns.tolist()}")
    
    if "signal" in df_sig.columns:
        signals = df_sig["signal"]
        print(f"  Signal stats: {signals.describe()}")
        print(f"  Non-zero signals: {signals[signals != 0].count()}")
        print(f"  First 10 signals:\n{signals.head(10)}")
        print(f"  Last 10 signals:\n{signals.tail(10)}")
        
        # Check SMAs
        if "SMA_50" in df_sig.columns:
            print(f"  SMA_50 non-null: {df_sig['SMA_50'].count()}")
        if "SMA_200" in df_sig.columns:
            print(f"  SMA_200 non-null: {df_sig['SMA_200'].count()}")
            
    else:
        print("  ERROR: 'signal' column missing!")

    # Run full backtest
    print(f"  Running full backtest for {symbol}...")
    result = bs.run_backtest(
        symbol=symbol,
        strategy_name=strategy_name,
        initial_capital=100000,
        data_source="local"
    )
    print("  Backtest SUCCESS")
    print(f"  Metrics: {result.get('metrics')}")
    print(f"  Trades: {len(result.get('trades', []))}")

    # Minimal backtesting library test
    print("\n--- Minimal Backtesting Library Test ---")
    try:
        from backtesting import Backtest, Strategy
        from backtesting.lib import crossover
        from backtesting.test import SMA, GOOG

        class SmaCross(Strategy):
            def init(self):
                price = self.data.Close
                self.ma1 = self.I(SMA, price, 10)
                self.ma2 = self.I(SMA, price, 20)

            def next(self):
                if crossover(self.ma1, self.ma2):
                    self.buy()
                elif crossover(self.ma2, self.ma1):
                    self.sell()

        bt = Backtest(GOOG, SmaCross, commission=.002, exclusive_orders=True)
        stats = bt.run()
        print("  Minimal test stats:")
        print(stats)
        print("  Minimal test SUCCESS")
    except Exception:
        print("  Minimal test FAILED:")
        traceback.print_exc()

except Exception:
    print("  Backtest FAILED:")
    traceback.print_exc()

# Test Google Sheets Service
print("\n--- Testing GoogleSheetsService ---")
try:
    from services.integration.google_sheets_service import GoogleSheetsService
    gs = GoogleSheetsService()
    print(f"  GoogleSheetsService initialized. Credentials path: {gs.credentials_path}")
    print(f"  Connected: {gs.is_connected()}")
    
    if not gs.is_connected():
        print("  Not connected. Checking credentials file...")
        if os.path.exists(gs.credentials_path):
            print(f"  File exists at {gs.credentials_path}")
        else:
            print(f"  File MISSING at {gs.credentials_path}")
except Exception:
    print("  GoogleSheetsService FAILED:")
    traceback.print_exc()

print("=== DIAGNOSTICS END ===")
