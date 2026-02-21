import logging
import os
import sys
from enum import Enum
from pathlib import Path
from typing import Optional

from dotenv import find_dotenv, load_dotenv

# Load environment variables from the nearest .env file (repo root or current dir),
# and fall back to a .env next to this file's parent directory.
DOTENV_PATH = find_dotenv(usecwd=True)
if not DOTENV_PATH:
    DOTENV_PATH = (Path(__file__).resolve().parent.parent / ".env").as_posix()

load_dotenv(DOTENV_PATH, override=True)


class PriceDataSource(str, Enum):
    LOCAL_REPOSITORY = "local_repository"
    YAHOO_FINANCE = "yahoo_finance"
    FMP = "fmp"
    KAGGLE = "kaggle"


# Root data directory
DATA_ROOT = Path(os.environ.get("TS_DATA_ROOT", "data")).resolve()
PRICE_DATA_DIR = DATA_ROOT / "prices"
KAGGLE_DB_PATH = DATA_ROOT / "historical_prices_kaggle.db"
FUNDAMENTAL_DATA_DIR = DATA_ROOT / "fundamentals"
UNIVERSE_DIR = DATA_ROOT / "universe"

# Default data source; can be overridden by env var TS_PRICE_DATA_SOURCE
DEFAULT_PRICE_DATA_SOURCE = PriceDataSource(
    os.environ.get("TS_PRICE_DATA_SOURCE", PriceDataSource.FMP.value),
)

# API key and base URL for FinancialModelingPrep (for fundamentals and prices)
FMP_API_KEY = os.environ.get("FMP_API_KEY", "")
FMP_BASE_URL = os.environ.get(
    "FMP_BASE_URL",
    "https://financialmodelingprep.com/stable",
)
FMP_FALLBACK_BASE_URL = os.environ.get(
    "FMP_FALLBACK_BASE_URL",
    "https://financialmodelingprep.com/stable",
)

if not FMP_API_KEY:
    logging.getLogger(__name__).warning(
        "FMP_API_KEY is not set. Loaded .env from %s",
        DOTENV_PATH or "environment",
    )

# Strategy configuration path
STRATEGY_CONFIG_PATH = str(Path(__file__).resolve().parent / "strategies.yaml")


def ensure_data_directories() -> None:
    for d in (DATA_ROOT, PRICE_DATA_DIR, FUNDAMENTAL_DATA_DIR, UNIVERSE_DIR):
        d.mkdir(parents=True, exist_ok=True)


def setup_logging(log_path: Optional[str] = None) -> None:
    """Configure root logging with console and file handlers.

    Logs INFO and above to stdout and to a log file under logs/trading_system.log
    (or the provided path). Creates the logs directory if needed.
    """
    log_dir = os.path.dirname(log_path) if log_path else "logs"
    os.makedirs(log_dir, exist_ok=True)

    resolved_log_path = log_path or os.path.join(log_dir, "trading_system.log")
    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # Use RotatingFileHandler for log rotation (10MB max, 5 backups)
    from logging.handlers import RotatingFileHandler

    file_handler = RotatingFileHandler(
        resolved_log_path, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)

    # Replace existing handlers to avoid duplicate log lines if reconfigured.
    logger.handlers = [console_handler, file_handler]
