"""SQLite persistence repository for Strategy Lab backtests."""

from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import pandas as pd

from strategy_lab.backtest.results import BacktestResults
from strategy_lab.persistence.mappers import (
    map_equity_rows,
    map_run_row,
    map_trade_rows,
)


class BacktestRepository:
    """Repository for persisting and fetching backtest artifacts."""

    def __init__(self, db_path: str | Path = "backend/trading_system.db"):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self):
        conn = sqlite3.connect(self.db_path)
        try:
            yield conn
        finally:
            conn.close()

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS backtest_runs (
                    run_id TEXT PRIMARY KEY,
                    strategy_name TEXT NOT NULL,
                    config_hash TEXT NOT NULL,
                    config_json TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS backtest_trades (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    symbol TEXT NOT NULL,
                    type TEXT NOT NULL,
                    price REAL NOT NULL,
                    quantity REAL NOT NULL,
                    pnl REAL NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES backtest_runs(run_id),
                    UNIQUE(run_id, timestamp, symbol, type, price, quantity, pnl)
                );

                CREATE TABLE IF NOT EXISTS backtest_equity_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    run_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    equity REAL NOT NULL,
                    drawdown REAL NOT NULL,
                    FOREIGN KEY(run_id) REFERENCES backtest_runs(run_id),
                    UNIQUE(run_id, timestamp)
                );
                """,
            )
            conn.commit()

    def save_backtest_results(
        self,
        *,
        run_id: str,
        results: BacktestResults,
    ) -> dict[str, Any]:
        """Persist run metadata, trades, and equity history with idempotency."""
        run_row = map_run_row(run_id, results)
        trade_rows = map_trade_rows(run_id, results)
        equity_rows = map_equity_rows(run_id, results)

        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                INSERT OR IGNORE INTO backtest_runs(run_id, strategy_name, config_hash, config_json)
                VALUES (?, ?, ?, ?)
                """,
                (
                    run_row["run_id"],
                    run_row["strategy_name"],
                    run_row["config_hash"],
                    run_row["config_json"],
                ),
            )
            run_inserted = cur.rowcount > 0

            trades_inserted = 0
            for row in trade_rows:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO backtest_trades
                    (run_id, timestamp, symbol, type, price, quantity, pnl)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        row["run_id"],
                        row["timestamp"],
                        row["symbol"],
                        row["type"],
                        row["price"],
                        row["quantity"],
                        row["pnl"],
                    ),
                )
                if cur.rowcount > 0:
                    trades_inserted += 1

            equity_inserted = 0
            for row in equity_rows:
                cur.execute(
                    """
                    INSERT OR IGNORE INTO backtest_equity_history
                    (run_id, timestamp, equity, drawdown)
                    VALUES (?, ?, ?, ?)
                    """,
                    (
                        row["run_id"],
                        row["timestamp"],
                        row["equity"],
                        row["drawdown"],
                    ),
                )
                if cur.rowcount > 0:
                    equity_inserted += 1

            conn.commit()

        return {
            "run_id": run_id,
            "run_inserted": run_inserted,
            "config_hash": run_row["config_hash"],
            "trades_inserted": trades_inserted,
            "equity_inserted": equity_inserted,
        }

    def get_run_summary(self, run_id: str) -> dict[str, Any] | None:
        with self._connect() as conn:
            cur = conn.cursor()
            cur.execute(
                """
                SELECT run_id, strategy_name, config_hash, config_json, created_at
                FROM backtest_runs
                WHERE run_id = ?
                """,
                (run_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            return {
                "run_id": row[0],
                "strategy_name": row[1],
                "config_hash": row[2],
                "config_json": row[3],
                "created_at": row[4],
            }

    def get_run_trades(self, run_id: str) -> pd.DataFrame:
        with self._connect() as conn:
            return pd.read_sql_query(
                """
                SELECT timestamp, symbol, type, price, quantity, pnl
                FROM backtest_trades
                WHERE run_id = ?
                ORDER BY timestamp, id
                """,
                conn,
                params=(run_id,),
            )

    def get_run_equity_history(self, run_id: str) -> pd.DataFrame:
        with self._connect() as conn:
            return pd.read_sql_query(
                """
                SELECT timestamp, equity, drawdown
                FROM backtest_equity_history
                WHERE run_id = ?
                ORDER BY timestamp, id
                """,
                conn,
                params=(run_id,),
            )
