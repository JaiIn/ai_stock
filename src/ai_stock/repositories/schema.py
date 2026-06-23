"""Versioned schema initialization for the local SQLite database."""

import sqlite3

SCHEMA_VERSION = 1

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER PRIMARY KEY CHECK (version > 0),
    applied_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS stocks (
    symbol TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    market TEXT,
    currency TEXT,
    english_name TEXT,
    isin_code TEXT,
    security_type TEXT,
    status TEXT,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS price_snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    price TEXT NOT NULL,
    currency TEXT,
    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
);

CREATE INDEX IF NOT EXISTS idx_price_snapshots_symbol_timestamp
ON price_snapshots(symbol, timestamp);

CREATE TABLE IF NOT EXISTS candles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    symbol TEXT NOT NULL,
    interval TEXT NOT NULL,
    timestamp TEXT NOT NULL,
    open TEXT NOT NULL,
    high TEXT NOT NULL,
    low TEXT NOT NULL,
    close TEXT NOT NULL,
    volume TEXT NOT NULL,
    currency TEXT,
    FOREIGN KEY (symbol) REFERENCES stocks(symbol)
);

CREATE INDEX IF NOT EXISTS idx_candles_symbol_interval_timestamp
ON candles(symbol, interval, timestamp);

CREATE TABLE IF NOT EXISTS exchange_rates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    base_currency TEXT NOT NULL,
    quote_currency TEXT NOT NULL,
    exchange_rate TEXT NOT NULL,
    date_time TEXT
);

CREATE INDEX IF NOT EXISTS idx_exchange_rates_pair_date_time
ON exchange_rates(base_currency, quote_currency, date_time);
"""


def initialize_schema(connection: sqlite3.Connection) -> None:
    """Create the approved local tables and record schema version 1."""

    with connection:
        connection.executescript(_SCHEMA_SQL)
        connection.execute(
            """
            INSERT OR IGNORE INTO schema_version(version, applied_at)
            VALUES (?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
            """,
            (SCHEMA_VERSION,),
        )
