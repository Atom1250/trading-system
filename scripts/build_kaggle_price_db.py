"""Build the local SQLite database for Kaggle historical prices.

This script downloads the Kaggle dataset, normalises it into the canonical
schema, and writes it to a SQLite database for consumption by the trading
system. Re-running the script rebuilds the database from the latest dataset
snapshot.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path
from typing import Dict

import pandas as pd
import kagglehub

DATASET_HANDLE = "nelgiriyewithana/world-stock-prices-daily-updating"
# Path to a specific file inside the Kaggle dataset, if required (e.g., "data.csv").
# Leave as an empty string to load the default DataFrame from the adapter.
DATASET_FILE_PATH = ""
DB_PATH = Path("data/historical_prices_kaggle.db")
TABLE_NAME = "prices"


def load_raw_kaggle_df() -> pd.DataFrame:
    """Load the raw Kaggle dataset into a pandas DataFrame."""
    # Download the dataset files
    path = kagglehub.dataset_download(DATASET_HANDLE)
    
    # Look for the CSV file
    csv_files = list(Path(path).glob("*.csv"))
    if not csv_files:
        raise ValueError(f"No CSV files found in downloaded dataset at {path}")
    
    # Use the largest CSV file if multiple exist, or specific one if configured
    if DATASET_FILE_PATH:
        target_file = Path(path) / DATASET_FILE_PATH
        if not target_file.exists():
            raise ValueError(f"Configured file {DATASET_FILE_PATH} not found in {path}")
        file_to_load = target_file
    else:
        # Default to the largest CSV file
        file_to_load = max(csv_files, key=lambda p: p.stat().st_size)
    
    print(f"Loading data from {file_to_load}...")
    return pd.read_csv(file_to_load)


def _find_column(df: pd.DataFrame, candidates: list[str]) -> str | None:
    columns = {col.lower(): col for col in df.columns}
    for candidate in candidates:
        match = columns.get(candidate.lower())
        if match is not None:
            return match
    return None


def normalise_schema(df: pd.DataFrame) -> pd.DataFrame:
    """Normalise dataset columns to the canonical schema.

    Required columns: symbol, date, close.
    Optional columns: open, high, low, volume.
    """

    column_map: Dict[str, list[str]] = {
        "symbol": ["symbol", "ticker"],
        "date": ["date"],
        "open": ["open", "open_price"],
        "high": ["high", "high_price"],
        "low": ["low", "low_price"],
        "close": ["close", "close_price", "adj_close", "adjusted_close"],
        "volume": ["volume", "vol"],
    }

    resolved: Dict[str, str] = {}
    
    # Create a case-insensitive map of existing columns
    existing_cols_lower = {col.lower(): col for col in df.columns}
    
    for canonical, candidates in column_map.items():
        for candidate in candidates:
            match = existing_cols_lower.get(candidate.lower())
            if match:
                resolved[canonical] = match
                break

    missing_required = [col for col in ("symbol", "date", "close") if col not in resolved]
    if missing_required:
        raise ValueError(f"Missing required columns in dataset: {', '.join(missing_required)}")

    # Invert the map for renaming: {original_name: canonical_name}
    rename_map = {original: canonical for canonical, original in resolved.items()}
    renamed = df.rename(columns=rename_map)

    # Convert date column to datetime objects (handling timezones)
    renamed["date"] = pd.to_datetime(renamed["date"], utc=True, errors="coerce")
    
    # Drop rows with invalid dates
    renamed = renamed.dropna(subset=["date"])
    
    # Convert to date objects (remove time component and timezone)
    renamed["date"] = renamed["date"].dt.date

    canonical_columns = [col for col in ("symbol", "date", "open", "high", "low", "close", "volume") if col in renamed.columns]
    normalised = renamed.loc[:, canonical_columns]
    normalised = normalised.drop_duplicates(subset=["symbol", "date"]).sort_values(["symbol", "date"]).reset_index(drop=True)

    return normalised


def write_to_sqlite(df: pd.DataFrame, db_path: Path, table_name: str = TABLE_NAME) -> None:
    """Write the normalised DataFrame to a SQLite database."""
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        df.to_sql(table_name, conn, if_exists="replace", index=False)
        conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_symbol_date ON {table_name} (symbol, date)")
        conn.commit()


def main() -> None:
    """Build the Kaggle-backed historical prices SQLite database."""
    print("Loading Kaggle dataset...")
    raw_df = load_raw_kaggle_df()
    print(f"Raw columns: {list(raw_df.columns)}")

    print("Normalising schema...")
    normalised_df = normalise_schema(raw_df)
    print(f"Normalised columns: {list(normalised_df.columns)}")

    print(f"Writing to SQLite at {DB_PATH}...")
    write_to_sqlite(normalised_df, DB_PATH)

    print(f"Done. Wrote {len(normalised_df)} rows to {DB_PATH} in table '{TABLE_NAME}'.")


if __name__ == "__main__":
    main()
