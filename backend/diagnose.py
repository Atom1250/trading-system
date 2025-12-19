import os
import sys
import logging

logger = logging.getLogger(__name__)

# Add /app to sys.path to mimic Docker environment if needed
sys.path.insert(0, "/app")

logger.info("=== DIAGNOSTICS START ===")
logger.info("CWD: %s", os.getcwd())
logger.info("PYTHONPATH: %s", os.environ.get("PYTHONPATH"))
logger.info("TS_DATA_ROOT: %s", os.environ.get("TS_DATA_ROOT"))

# Check Data Directory
data_root = os.environ.get("TS_DATA_ROOT", "/app/data")
logger.info("Checking data root: %s", data_root)
if os.path.exists(data_root):
    logger.info("  Data root exists. Contents: %s", os.listdir(data_root))
    prices_dir = os.path.join(data_root, "prices")
    if os.path.exists(prices_dir):
        logger.info("  Prices dir exists. Contents: %s", os.listdir(prices_dir))
    else:
        logger.warning("  Prices dir MISSING")
else:
    logger.warning("  Data root MISSING")

# Test Price Service
logger.info("\n--- Testing PriceDataService ---")
try:
    from services.data.price_service import PriceDataService

    service = PriceDataService()
    logger.info("  PriceDataService initialized")

    # Try to list sources
    logger.info("  Sources: %s", service.get_available_sources())

    # Try to fetch data for a known symbol (e.g. AAPL)
    symbol = "AAPL"
    logger.info("  Fetching prices for %s (source=local)...", symbol)
    df = service.get_prices(symbol, source="local")
    if df.empty:
        logger.info("  Result: EMPTY DataFrame")
    else:
        logger.info("  Result: %s rows", len(df))
        logger.debug("  Columns: %s", df.columns.tolist())
        logger.debug("  Head:\n%s", df.head())

except Exception as exc:
    logger.exception("  FAILED to fetch prices: %s", exc)

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
        data_source="local",
    )
    print("  Backtest SUCCESS")
    print(f"  Metrics: {result.get('metrics')}")
    print(f"  Trades: {len(result.get('trades', []))}")

    # Minimal backtesting library test
    print("\n--- Minimal Backtesting Library Test ---")
    try:
        from backtesting.lib import crossover
        from backtesting.test import GOOG, SMA

        from backtesting import Backtest, Strategy

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

        bt = Backtest(GOOG, SmaCross, commission=0.002, exclusive_orders=True)
        stats = bt.run()
        logger.info("  Minimal test stats:")
        logger.info("%s", stats)
        logger.info("  Minimal test SUCCESS")
    except Exception as exc:
        logger.exception("  Minimal test FAILED: %s", exc)

except Exception as exc:
    logger.exception("  Backtest FAILED: %s", exc)

# Test Google Sheets Service
logger.info("\n--- Testing GoogleSheetsService ---")
try:
    from services.integration.google_sheets_service import GoogleSheetsService

    gs = GoogleSheetsService()
    logger.info("  GoogleSheetsService initialized. Credentials path: %s", gs.credentials_path)
    logger.info("  Connected: %s", gs.is_connected())

    if not gs.is_connected():
        logger.info("  Not connected. Checking credentials file...")
        if os.path.exists(gs.credentials_path):
            logger.info("  File exists at %s", gs.credentials_path)
        else:
            logger.warning("  File MISSING at %s", gs.credentials_path)
except Exception as exc:
    logger.exception("  GoogleSheetsService FAILED: %s", exc)

logger.info("=== DIAGNOSTICS END ===")
