"""In-memory tests for the local data persistence service."""

import socket
import unittest
from decimal import Decimal
from unittest.mock import patch

from ai_stock.models import Candle, ExchangeRate, PriceSnapshot, StockInfo
from ai_stock.repositories import close_connection, create_connection
from ai_stock.services import LocalDataPersistenceService


class LocalDataPersistenceServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = create_connection(":memory:")
        self.addCleanup(close_connection, self.connection)
        self.service = LocalDataPersistenceService(self.connection)
        self.stock = StockInfo(
            stock_code="005930",
            stock_name="Mock Stock",
            market="KOSPI",
            currency="KRW",
        )
        self.service.save_stocks([self.stock])

    def test_save_stocks_uses_upsert_semantics(self) -> None:
        updated = StockInfo(
            stock_code="005930",
            stock_name="Updated Mock Stock",
            market="KOSPI",
            currency="KRW",
            status="ACTIVE",
        )

        processed = self.service.save_stocks([updated])

        self.assertEqual(processed, 1)
        self.assertEqual(self.service.list_stocks(), [updated])

    def test_save_price_snapshots_preserves_decimal_and_timestamp(self) -> None:
        snapshot = PriceSnapshot(
            stock_code="005930",
            price=Decimal("70123.4500"),
            timestamp="2026-06-23T09:00:00Z",
            currency="KRW",
        )

        row_ids = self.service.save_price_snapshots([snapshot])
        stored = self.service.list_price_snapshots("005930")

        self.assertEqual(len(row_ids), 1)
        self.assertGreater(row_ids[0], 0)
        self.assertEqual(stored, [snapshot])
        self.assertIsInstance(stored[0].price, Decimal)
        self.assertEqual(stored[0].price, Decimal("70123.4500"))
        self.assertEqual(stored[0].timestamp, "2026-06-23T09:00:00Z")

    def test_save_candles_preserves_decimal_values_and_timestamp(self) -> None:
        candle = Candle(
            timestamp="2026-06-23T09:00:00Z",
            open=Decimal("70000.00"),
            high=Decimal("71000.10"),
            low=Decimal("69900.20"),
            close=Decimal("70500.30"),
            volume=Decimal("123456"),
            currency="KRW",
        )

        row_ids = self.service.save_candles("005930", "1d", [candle])
        stored = self.service.list_candles("005930", "1d")

        self.assertEqual(len(row_ids), 1)
        self.assertEqual(stored, [candle])
        self.assertIsInstance(stored[0].close, Decimal)
        self.assertEqual(stored[0].timestamp, "2026-06-23T09:00:00Z")

    def test_save_exchange_rates_preserves_decimal_and_date_time(self) -> None:
        rate = ExchangeRate(
            base_currency="USD",
            quote_currency="KRW",
            exchange_rate=Decimal("1375.2500"),
            date_time="2026-06-23T09:00:00Z",
        )

        row_ids = self.service.save_exchange_rates([rate])
        stored = self.service.list_exchange_rates("USD", "KRW")

        self.assertEqual(len(row_ids), 1)
        self.assertEqual(stored, [rate])
        self.assertIsInstance(stored[0].exchange_rate, Decimal)
        self.assertEqual(stored[0].date_time, "2026-06-23T09:00:00Z")

    def test_service_does_not_open_network_sockets(self) -> None:
        with patch.object(
            socket,
            "socket",
            side_effect=AssertionError("network access is forbidden"),
        ):
            self.assertEqual(self.service.list_stocks(), [self.stock])
            self.assertEqual(self.service.list_price_snapshots(), [])
            self.assertEqual(self.service.list_candles("005930"), [])
            self.assertEqual(self.service.list_exchange_rates(), [])

    def test_service_does_not_import_api_client_modules(self) -> None:
        from pathlib import Path

        import ai_stock.services.data_persistence as data_persistence

        service_source = Path(data_persistence.__file__).read_text(encoding="utf-8")

        self.assertNotIn("ai_stock.clients", service_source)
        self.assertNotIn("token_provider", service_source)
        self.assertNotIn("request_context", service_source)
        self.assertNotIn("httpx", service_source)


if __name__ == "__main__":
    unittest.main()
