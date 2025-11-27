import logging
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Required API key for Alpha Vantage requests. Read from environment or .env.
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# Allow overriding the base URL via environment for testing, defaulting to production.
BASE_URL = os.getenv("ALPHA_VANTAGE_BASE_URL", "https://www.alphavantage.co/query")


class PriceDataSource(str, Enum):
    ALPHA_VANTAGE = "alpha_vantage"
    LOCAL_REPOSITORY = "local_repository"
    YAHOO_FINANCE = "yahoo_finance"


# Root data directory
DATA_ROOT = Path(os.environ.get("TS_DATA_ROOT", "data")).resolve()
PRICE_DATA_DIR = DATA_ROOT / "prices"
FUNDAMENTAL_DATA_DIR = DATA_ROOT / "fundamentals"
UNIVERSE_DIR = DATA_ROOT / "universe"

# Default data source; can be overridden by env var TS_PRICE_DATA_SOURCE
DEFAULT_PRICE_DATA_SOURCE = PriceDataSource(
    os.environ.get("TS_PRICE_DATA_SOURCE", PriceDataSource.ALPHA_VANTAGE.value)
)

# Optional API key for FinancialModelingPrep (for fundamentals and/or prices)
FMP_API_KEY = os.environ.get("FMP_API_KEY", "")
FMP_BASE_URL = "https://financialmodelingprep.com/api/v3"


def ensure_data_directories() -> None:
    for d in (DATA_ROOT, PRICE_DATA_DIR, FUNDAMENTAL_DATA_DIR, UNIVERSE_DIR):
        d.mkdir(parents=True, exist_ok=True)


def setup_logging(log_path: Optional[str] = None) -> None:
    """
    Configure root logging with console and file handlers.

    Logs INFO and above to stdout and to a log file under logs/trading_system.log
    (or the provided path). Creates the logs directory if needed.
    """

    log_dir = os.path.dirname(log_path) if log_path else "logs"
    os.makedirs(log_dir, exist_ok=True)

    resolved_log_path = log_path or os.path.join(log_dir, "trading_system.log")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(resolved_log_path)
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Replace existing handlers to avoid duplicate log lines if reconfigured.
    logger.handlers = [console_handler, file_handler]
