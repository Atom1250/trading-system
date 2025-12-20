from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any

from config.settings import FUNDAMENTAL_DATA_DIR, ensure_data_directories

logger = logging.getLogger(__name__)

ensure_data_directories()


def fundamentals_file_path(symbol: str) -> Path:
    return FUNDAMENTAL_DATA_DIR / f"{symbol.upper()}.json"


def load_local_fundamentals(symbol: str) -> dict[str, Any]:
    """Load fundamentals for a symbol from JSON if present; return {} otherwise."""
    ensure_data_directories()
    path = fundamentals_file_path(symbol)
    if not path.exists():
        logger.debug("No local fundamentals found for %s at %s", symbol, path)
        return {}

    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as exc:  # noqa: BLE001 - log and return empty
        logger.warning("Failed to load fundamentals for %s: %s", symbol, exc)
        return {}


def get_fundamentals(symbol: str, use_local_repository: bool = True) -> dict[str, Any]:
    """Retrieve fundamentals for ``symbol``. Currently supports local repository reads."""
    if use_local_repository:
        return load_local_fundamentals(symbol)

    logger.info(
        "Non-local fundamentals lookup for %s not implemented; returning empty.",
        symbol,
    )
    return {}
