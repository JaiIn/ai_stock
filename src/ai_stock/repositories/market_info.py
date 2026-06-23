"""SQLite repository for reference exchange rates."""

import sqlite3
from decimal import Decimal

from ai_stock.models.market_info import ExchangeRate


def _decimal_text(value: Decimal) -> str:
    if not value.is_finite():
        raise ValueError("Exchange rates must be finite Decimal instances.")
    return str(value)


class MarketInfoRepository:
    def __init__(self, connection: sqlite3.Connection) -> None:
        self._connection = connection

    def insert_exchange_rate(self, rate: ExchangeRate) -> int:
        with self._connection:
            cursor = self._connection.execute(
                """
                INSERT INTO exchange_rates(
                    base_currency, quote_currency, exchange_rate, date_time
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    rate.base_currency,
                    rate.quote_currency,
                    _decimal_text(rate.exchange_rate),
                    rate.date_time,
                ),
            )
        return int(cursor.lastrowid)

    def list_exchange_rates(
        self,
        base_currency: str | None = None,
        quote_currency: str | None = None,
    ) -> list[ExchangeRate]:
        clauses: list[str] = []
        parameters: list[str] = []
        if base_currency is not None:
            clauses.append("base_currency = ?")
            parameters.append(base_currency)
        if quote_currency is not None:
            clauses.append("quote_currency = ?")
            parameters.append(quote_currency)

        sql = """
            SELECT base_currency, quote_currency, exchange_rate, date_time
            FROM exchange_rates
        """
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY date_time, id"
        rows = self._connection.execute(sql, parameters).fetchall()
        return [
            ExchangeRate(
                base_currency=row["base_currency"],
                quote_currency=row["quote_currency"],
                exchange_rate=Decimal(row["exchange_rate"]),
                date_time=row["date_time"],
            )
            for row in rows
        ]
