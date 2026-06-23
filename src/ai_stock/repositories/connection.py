"""SQLite connection helpers for local-only storage."""

import sqlite3
from pathlib import Path

DEFAULT_DB_PATH = Path("data/ai_stock.sqlite3")


def create_connection(
    database_path: str | Path = DEFAULT_DB_PATH,
) -> sqlite3.Connection:
    """Create a configured SQLite connection without initializing schema."""

    if database_path == ":memory:":
        connection_target = ":memory:"
    else:
        path = Path(database_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        connection_target = str(path)

    connection = sqlite3.connect(connection_target)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def close_connection(connection: sqlite3.Connection) -> None:
    """Close a connection owned by the caller."""

    connection.close()
