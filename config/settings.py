import logging
import os
import sys
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Required API key for Alpha Vantage requests. Read from environment or .env.
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# Allow overriding the base URL via environment for testing, defaulting to production.
BASE_URL = os.getenv("ALPHA_VANTAGE_BASE_URL", "https://www.alphavantage.co/query")


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
