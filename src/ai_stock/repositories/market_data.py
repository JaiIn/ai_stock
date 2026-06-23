"""SQLite repositories for price snapshots and candles."""

import sqlite3
from decimal import Decimal

from ai_stock.models.market_data import Candle, PriceSnapshot


def _decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("Financial values must be finite Decimal instances.")
    return str(value)


class MarketDataRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def insert_price_snapshot(self, snapshot: PriceSnapshot) -> int:
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO price_snapshots(symbol, timestamp, price, currency)
                VALUES (?, ?, ?, ?)
                """,
                (
                    snapshot.stock_code,
                    snapshot.timestamp,
                    _decimal_text(snapshot.price),
                    snapshot.currency,
                ),
            )
        return int(cursor.lastrowid)

    def list_price_snapshots(
        self,
        stock_code: str | None = None,
    ) -> list[PriceSnapshot]:
        sql = "SELECT symbol, timestamp, price, currency FROM price_snapshots"
        parameters: tuple[str, ...] = ()
        if stock_code is not None:
            sql += " WHERE symbol = ?"
            parameters = (stock_code,)
        sql += " ORDER BY timestamp, id"
        rows = self._connection.execute(sql, parameters).fetchall()
        return [
            PriceSnapshot(
                stock_code=row["symbol"],
                timestamp=row["timestamp"],
                price=Decimal(row["price"]),
                currency=row["currency"],
            )
            for row in rows
        ]

    def insert_candle(
        self,
        stock_code: str,
        interval: str,
        candle: Candle,
    ) -> int:
        if not stock_code or not interval:
            raise ValueError("Candle stock_code and interval are required.")
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO candles(
                    symbol, interval, timestamp, open, high, low, close,
                    volume, currency
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    stock_code,
                    interval,
                    candle.timestamp,
                    _decimal_text(candle.open),
                    _decimal_text(candle.high),
                    _decimal_text(candle.low),
                    _decimal_text(candle.close),
                    _decimal_text(candle.volume),
                    candle.currency,
                ),
            )
        return int(cursor.lastrowid)

    def list_candles(
        self,
        stock_code: str,
        interval: str | None = None,
    ) -> list[Candle]:
        sql = """
            SELECT timestamp, open, high, low, close, volume, currency
            FROM candles
            WHERE symbol = ?
        """
        parameters: tuple[str, ...]
        if interval is None:
            parameters = (stock_code,)
        else:
            sql += " AND interval = ?"
            parameters = (stock_code, interval)
        sql += " ORDER BY timestamp, id"
        rows = self._connection.execute(sql, parameters).fetchall()
        return [
            Candle(
                timestamp=row["timestamp"],
                open=Decimal(row["open"]),
                high=Decimal(row["high"]),
                low=Decimal(row["low"]),
                close=Decimal(row["close"]),
                volume=Decimal(row["volume"]),
                currency=row["currency"],
            )
            for row in rows
        ]
