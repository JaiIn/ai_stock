"""Tests for read-only snapshot ingestion with fake providers only."""

import socket
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from ai_stock.models import Candle, CandlePage, ExchangeRate, PriceSnapshot, StockInfo
from ai_stock.repositories import close_connection, create_connection
from ai_stock.services import (
    LocalDataPersistenceService,
    ReadOnlySnapshotIngestionRequest,
    ReadOnlySnapshotIngestionService,
)


class FakeStockProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_stock_info(self, symbol: str):
        self.calls.append(symbol)
        return [
            StockInfo(
                stock_code=symbol,
                stock_name="Samsung Electronics",
                market="KOSPI",
                currency="KRW",
            )
        ]


class FakePriceProvider:
    def __init__(self) -> None:
        self.calls: list[str] = []

    def get_price_snapshots(self, symbol: str):
        self.calls.append(symbol)
        return [
            PriceSnapshot(
                stock_code=symbol,
                price=Decimal("70123.4500"),
                timestamp="2026-06-26T09:00:00+09:00",
                currency="KRW",
            )
        ]


class FakeCandleProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, int, bool]] = []

    def get_candles(
        self,
        symbol: str,
        *,
        interval: str,
        count: int,
        adjusted: bool,
    ):
        self.calls.append((symbol, interval, count, adjusted))
        return CandlePage(
            candles=(
                Candle(
                    timestamp="2026-06-26T00:00:00+09:00",
                    open=Decimal("70000.00"),
                    high=Decimal("71000.10"),
                    low=Decimal("69900.20"),
                    close=Decimal("70500.30"),
                    volume=Decimal("1234567"),
                    currency="KRW",
                ),
            ),
            next_before=None,
        )


class FakeExchangeRateProvider:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str]] = []

    def get_exchange_rates(self, base_currency: str, quote_currency: str):
        self.calls.append((base_currency, quote_currency))
        return [
            ExchangeRate(
                base_currency=base_currency,
                quote_currency=quote_currency,
                exchange_rate=Decimal("1375.2500"),
                valid_from="2026-06-26T00:00:00+09:00",
                valid_until="2026-06-27T00:00:00+09:00",
                date_time="2026-06-26T00:00:00+09:00",
            )
        ]


class ReadOnlySnapshotIngestionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = create_connection(":memory:")
        self.addCleanup(close_connection, self.connection)
        self.persistence = LocalDataPersistenceService(self.connection)
        self.stock_provider = FakeStockProvider()
        self.price_provider = FakePriceProvider()
        self.candle_provider = FakeCandleProvider()
        self.exchange_rate_provider = FakeExchangeRateProvider()
        self.service = ReadOnlySnapshotIngestionService(
            self.persistence,
            stock_provider=self.stock_provider,
            price_provider=self.price_provider,
            candle_provider=self.candle_provider,
            exchange_rate_provider=self.exchange_rate_provider,
        )

    def test_ingests_readonly_snapshot_into_in_memory_sqlite(self) -> None:
        result = self.service.ingest_snapshot(
            ReadOnlySnapshotIngestionRequest(
                symbol="005930",
                exchange_base_currency="USD",
                exchange_quote_currency="KRW",
                candle_interval="1d",
                candle_count=1,
                adjusted=True,
            )
        )

        self.assertTrue(result.success)
        self.assertEqual(result.requested_symbol, "005930")
        self.assertEqual(result.saved_stock_count, 1)
        self.assertEqual(result.saved_price_snapshot_count, 1)
        self.assertEqual(result.saved_candle_count, 1)
        self.assertEqual(result.saved_exchange_rate_count, 1)
        self.assertTrue(result.stock_warnings_deferred)
        self.assertEqual(result.skipped_stock_warnings_count, 0)
        self.assertFalse(result.actual_network_call_performed)
        self.assertIn("stock warnings persistence is deferred", result.safe_message)
        self.assertEqual(self.stock_provider.calls, ["005930"])
        self.assertEqual(self.price_provider.calls, ["005930"])
        self.assertEqual(self.candle_provider.calls, [("005930", "1d", 1, True)])
        self.assertEqual(self.exchange_rate_provider.calls, [("USD", "KRW")])

        stocks = self.persistence.list_stocks()
        prices = self.persistence.list_price_snapshots("005930")
        candles = self.persistence.list_candles("005930", "1d")
        rates = self.persistence.list_exchange_rates("USD", "KRW")

        self.assertEqual(stocks[0].stock_code, "005930")
        self.assertEqual(prices[0].price, Decimal("70123.4500"))
        self.assertEqual(prices[0].timestamp, "2026-06-26T09:00:00+09:00")
        self.assertEqual(candles[0].close, Decimal("70500.30"))
        self.assertEqual(candles[0].timestamp, "2026-06-26T00:00:00+09:00")
        self.assertEqual(rates[0].exchange_rate, Decimal("1375.2500"))
        self.assertEqual(rates[0].date_time, "2026-06-26T00:00:00+09:00")

    def test_service_uses_no_network_or_oauth_provider(self) -> None:
        with patch.object(
            socket,
            "socket",
            side_effect=AssertionError("network access is forbidden"),
        ):
            result = self.service.ingest_snapshot(
                ReadOnlySnapshotIngestionRequest(symbol="005930")
            )

        self.assertTrue(result.success)
        self.assertFalse(result.actual_network_call_performed)

    def test_rejects_invalid_symbol_before_provider_calls(self) -> None:
        with self.assertRaises(ValueError):
            self.service.ingest_snapshot(
                ReadOnlySnapshotIngestionRequest(symbol="005930/invalid")
            )

        self.assertEqual(self.stock_provider.calls, [])
        self.assertEqual(self.price_provider.calls, [])
        self.assertEqual(self.candle_provider.calls, [])
        self.assertEqual(self.exchange_rate_provider.calls, [])

    def test_rejects_invalid_interval(self) -> None:
        with self.assertRaises(ValueError):
            self.service.ingest_snapshot(
                ReadOnlySnapshotIngestionRequest(
                    symbol="005930",
                    candle_interval="1w",
                )
            )

    def test_rejects_invalid_count(self) -> None:
        for count in (0, 201):
            with self.subTest(count=count):
                with self.assertRaises(ValueError):
                    self.service.ingest_snapshot(
                        ReadOnlySnapshotIngestionRequest(
                            symbol="005930",
                            candle_count=count,
                        )
                    )

    def test_rejects_non_boolean_adjusted(self) -> None:
        with self.assertRaises(ValueError):
            self.service.ingest_snapshot(
                ReadOnlySnapshotIngestionRequest(
                    symbol="005930",
                    adjusted="true",  # type: ignore[arg-type]
                )
            )

    def test_rejects_live_real_order_and_account_flags(self) -> None:
        unsafe_requests = (
            ReadOnlySnapshotIngestionRequest(
                symbol="005930",
                live_mode_enabled=True,
            ),
            ReadOnlySnapshotIngestionRequest(
                symbol="005930",
                real_order_allowed=True,
            ),
            ReadOnlySnapshotIngestionRequest(
                symbol="005930",
                order_send_requested=True,
            ),
            ReadOnlySnapshotIngestionRequest(
                symbol="005930",
                account_scope_requested=True,
            ),
            ReadOnlySnapshotIngestionRequest(
                symbol="005930",
                account_seq="1",
            ),
        )
        for request in unsafe_requests:
            with self.subTest(request=request):
                with self.assertRaises(ValueError):
                    self.service.ingest_snapshot(request)

        self.assertEqual(self.stock_provider.calls, [])

    def test_service_source_does_not_import_live_client_or_http_transport(self) -> None:
        import ai_stock.services.readonly_snapshot_ingestion as ingestion

        source = Path(ingestion.__file__).read_text(encoding="utf-8")
        forbidden_terms = (
            "ai_stock.clients",
            "httpx",
            "TokenProvider",
            "authorization_header",
            "accountSeq",
        )
        for term in forbidden_terms:
            self.assertNotIn(term, source)

    def test_no_real_db_file_is_created_by_in_memory_tests(self) -> None:
        self.service.ingest_snapshot(
            ReadOnlySnapshotIngestionRequest(symbol="005930")
        )

        self.assertFalse(Path("data/ai_stock.sqlite3").exists())


if __name__ == "__main__":
    unittest.main()
