import logging
from pathlib import Path

from config.settings import (
    DEFAULT_PRICE_DATA_SOURCE,
    UNIVERSE_DIR,
    PriceDataSource,
    ensure_data_directories,
)
from repository.prices_repository import (
    append_new_rows,
    fetch_and_cache_prices,
    load_local_prices,
    price_file_path,
)

logger = logging.getLogger(__name__)


def load_universe(path: Path) -> list[str]:
    """Read a simple text file with one symbol per line and return a list of symbols.
    Ignore blank lines and comments starting with '#'.
    """
    symbols: list[str] = []
    if not path.exists():
        logger.warning("Universe file not found at %s", path)
        return symbols

    with path.open("r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("#"):
                continue
            symbols.append(stripped.upper())
    return symbols


def update_symbol_daily(symbol: str, data_source: PriceDataSource) -> None:
    """Load existing local prices, fetch updates from the external source, and append new rows.
    If no local file exists, fetch full history.
    """
    existing = load_local_prices(symbol)

    if existing.empty:
        logger.info(
            "No local data for %s. Fetching full history from %s.",
            symbol,
            data_source.value,
        )
        fresh = fetch_and_cache_prices(symbol, data_source=data_source)
        logger.info("Fetched %s rows for %s.", len(fresh), symbol)
        return

    last_date = existing.index.max()
    logger.info("Last cached date for %s: %s", symbol, last_date.date())

    fetched = fetch_and_cache_prices(symbol, data_source=data_source)
    if fetched.empty:
        logger.warning("No data returned for %s from %s.", symbol, data_source.value)
        return

    new_rows = fetched[fetched.index > last_date]
    if new_rows.empty:
        logger.info("No new rows for %s; already up to date.", symbol)
        return

    append_new_rows(symbol, new_rows)
    logger.info(
        "Appended %s new rows for %s. File: %s",
        len(new_rows),
        symbol,
        price_file_path(symbol),
    )


def main() -> None:
    """Load universe and update historical prices using the configured data source (defaults to FMP)."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(message)s",
    )
    ensure_data_directories()

    universe_path = UNIVERSE_DIR / "universe_equities.txt"
    symbols = load_universe(universe_path)
    if not symbols:
        logger.warning("No symbols to update. Universe file may be empty.")
        return

    data_source = DEFAULT_PRICE_DATA_SOURCE or PriceDataSource.FMP
    logger.info(
        "Starting historical data update for %s symbols using %s.",
        len(symbols),
        data_source.value,
    )

    for sym in symbols:
        try:
            update_symbol_daily(sym, data_source)
        except Exception as exc:  # noqa: BLE001 - log and continue
            logger.warning("Failed to update %s: %s", sym, exc)


if __name__ == "__main__":
    main()
