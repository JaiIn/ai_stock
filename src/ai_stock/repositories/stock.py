"""SQLite repository for basic stock metadata."""

import sqlite3

from ai_stock.models.stock_info import StockInfo


class StockRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def upsert_stock(self, stock: StockInfo) -> None:
        with self._connection:
            self._connection.execute(
                """
                INSERT INTO stocks(
                    symbol, name, market, currency, english_name,
                    isin_code, security_type, status, updated_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, strftime('%Y-%m-%dT%H:%M:%fZ', 'now'))
                ON CONFLICT(symbol) DO UPDATE SET
                    name = excluded.name,
                    market = excluded.market,
                    currency = excluded.currency,
                    english_name = excluded.english_name,
                    isin_code = excluded.isin_code,
                    security_type = excluded.security_type,
                    status = excluded.status,
                    updated_at = excluded.updated_at
                """,
                (
                    stock.stock_code,
                    stock.stock_name,
                    stock.market,
                    stock.currency,
                    stock.english_name,
                    stock.isin_code,
                    stock.security_type,
                    stock.status,
                ),
            )

    def list_stocks(self) -> list[StockInfo]:
        rows = self._connection.execute(
            """
            SELECT symbol, name, market, currency, english_name,
                   isin_code, security_type, status
            FROM stocks
            ORDER BY symbol
            """
        ).fetchall()
        return [
            StockInfo(
                stock_code=row["symbol"],
                stock_name=row["name"],
                market=row["market"],
                currency=row["currency"],
                english_name=row["english_name"],
                isin_code=row["isin_code"],
                security_type=row["security_type"],
                status=row["status"],
            )
            for row in rows
        ]
