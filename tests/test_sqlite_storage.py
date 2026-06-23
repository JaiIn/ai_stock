"""Temporary-file tests for the local SQLite repository foundation."""

import socket
import sqlite3
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from ai_stock.models import Candle, ExchangeRate, PriceSnapshot, StockInfo
from ai_stock.repositories import (
    DEFAULT_DB_PATH,
    SCHEMA_VERSION,
    MarketDataRepository,
    MarketInfoRepository,
    StockRepository,
    close_connection,
    create_connection,
    initialize_schema,
)


class SQLiteStorageTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = create_connection(":memory:")
        self.addCleanup(close_connection, self.connection)
        initialize_schema(self.connection)
        self.stock_repository = StockRepository(self.connection)
        self.market_data_repository = MarketDataRepository(self.connection)
        self.market_info_repository = MarketInfoRepository(self.connection)
        self.stock = StockInfo(
            stock_code="005930",
            stock_name="테스트 종목",
            market="KOSPI",
            currency="KRW",
        )
        self.stock_repository.upsert_stock(self.stock)

    def test_default_path_and_schema_metadata(self) -> None:
        self.assertEqual(DEFAULT_DB_PATH, Path("data/ai_stock.sqlite3"))
        initialize_schema(self.connection)
        row = self.connection.execute(
            "SELECT version, applied_at FROM schema_version"
        ).fetchone()

        self.assertEqual(row["version"], SCHEMA_VERSION)
        self.assertTrue(row["applied_at"])

    def test_only_approved_data_tables_are_created(self) -> None:
        table_names = {
            row["name"]
            for row in self.connection.execute(
                """
                SELECT name FROM sqlite_master
                WHERE type = 'table' AND name NOT LIKE 'sqlite_%'
                """
            )
        }

        self.assertEqual(
            table_names,
            {
                "schema_version",
                "stocks",
                "price_snapshots",
                "candles",
                "exchange_rates",
            },
        )
        schema_sql = " ".join(
            row["sql"] or ""
            for row in self.connection.execute(
                "SELECT sql FROM sqlite_master WHERE type = 'table'"
            )
        ).lower()
        for forbidden in (
            "access_token",
            "client_secret",
            "accountseq",
            "account_number",
            "orders",
            "holdings",
            "portfolio",
        ):
            self.assertNotIn(forbidden, schema_sql)

    def test_stock_upsert_and_list(self) -> None:
        updated = StockInfo(
            stock_code="005930",
            stock_name="변경된 테스트 종목",
            market="KOSPI",
            currency="KRW",
            status="ACTIVE",
        )

        self.stock_repository.upsert_stock(updated)
        stocks = self.stock_repository.list_stocks()

        self.assertEqual(len(stocks), 1)
        self.assertEqual(stocks[0], updated)

    def test_price_snapshot_round_trip_preserves_decimal(self) -> None:
        snapshot = PriceSnapshot(
            stock_code="005930",
            price=Decimal("70123.4500"),
            timestamp="2026-01-01T00:00:00Z",
            currency="KRW",
        )

        self.market_data_repository.insert_price_snapshot(snapshot)
        stored = self.market_data_repository.list_price_snapshots("005930")

        self.assertEqual(stored, [snapshot])
        raw_price = self.connection.execute(
            "SELECT price FROM price_snapshots"
        ).fetchone()["price"]
        self.assertEqual(raw_price, "70123.4500")

    def test_candle_round_trip_preserves_decimal_values(self) -> None:
        candle = Candle(
            timestamp="2026-01-01T00:00:00Z",
            open=Decimal("100.10"),
            high=Decimal("110.20"),
            low=Decimal("90.30"),
            close=Decimal("105.40"),
            volume=Decimal("12345"),
            currency="KRW",
        )

        self.market_data_repository.insert_candle("005930", "1d", candle)
        stored = self.market_data_repository.list_candles("005930", "1d")

        self.assertEqual(stored, [candle])

    def test_exchange_rate_round_trip_preserves_decimal(self) -> None:
        rate = ExchangeRate(
            base_currency="USD",
            quote_currency="KRW",
            exchange_rate=Decimal("1375.2500"),
            date_time="2026-01-01T00:00:00Z",
        )

        self.market_info_repository.insert_exchange_rate(rate)
        stored = self.market_info_repository.list_exchange_rates("USD", "KRW")

        self.assertEqual(stored, [rate])

    def test_repository_operations_do_not_open_network_sockets(self) -> None:
        with patch.object(
            socket,
            "socket",
            side_effect=AssertionError("network access is forbidden"),
        ):
            self.assertEqual(self.stock_repository.list_stocks(), [self.stock])
            self.assertEqual(
                self.market_data_repository.list_price_snapshots(),
                [],
            )
            self.assertEqual(
                self.market_info_repository.list_exchange_rates(),
                [],
            )

    def test_foreign_keys_are_enabled(self) -> None:
        with self.assertRaises(sqlite3.IntegrityError):
            self.market_data_repository.insert_price_snapshot(
                PriceSnapshot(
                    stock_code="MISSING",
                    price=Decimal("1"),
                    timestamp="2026-01-01T00:00:00Z",
                    currency="KRW",
                )
            )


if __name__ == "__main__":
    unittest.main()
