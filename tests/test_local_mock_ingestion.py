"""In-memory tests for the local mock ingestion pipeline."""

import socket
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from ai_stock.repositories import close_connection, create_connection
from ai_stock.services import (
    LocalDataPersistenceService,
    LocalMockIngestionService,
)


class LocalMockIngestionServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.connection = create_connection(":memory:")
        self.addCleanup(close_connection, self.connection)
        self.persistence = LocalDataPersistenceService(self.connection)
        self.ingestion = LocalMockIngestionService(self.persistence)

    def test_ingest_market_dataset_parses_and_persists_fake_payloads(self) -> None:
        dataset = {
            "stocks": [
                {
                    "symbol": "005930",
                    "name": "Mock Stock",
                    "market": "KOSPI",
                    "currency": "KRW",
                }
            ],
            "prices": [
                {
                    "symbol": "005930",
                    "lastPrice": "70123.4500",
                    "timestamp": "2026-06-23T09:00:00Z",
                    "currency": "KRW",
                }
            ],
            "candles": {
                "stockCode": "005930",
                "interval": "1d",
                "candles": [
                    {
                        "timestamp": "2026-06-23T09:00:00Z",
                        "openPrice": "70000.00",
                        "highPrice": "71000.10",
                        "lowPrice": "69900.20",
                        "closePrice": "70500.30",
                        "volume": "123456",
                        "currency": "KRW",
                    }
                ],
            },
            "exchangeRates": {
                "baseCurrency": "USD",
                "quoteCurrency": "KRW",
                "exchangeRates": [
                    {
                        "exchangeRate": "1375.2500",
                        "dateTime": "2026-06-23T09:00:00Z",
                    }
                ],
            },
        }

        counts = self.ingestion.ingest_market_dataset(dataset)

        self.assertEqual(
            counts,
            {
                "stocks": 1,
                "price_snapshots": 1,
                "candles": 1,
                "exchange_rates": 1,
            },
        )
        self.assertEqual(self.persistence.list_stocks()[0].stock_code, "005930")
        snapshot = self.persistence.list_price_snapshots("005930")[0]
        candle = self.persistence.list_candles("005930", "1d")[0]
        rate = self.persistence.list_exchange_rates("USD", "KRW")[0]

        self.assertIsInstance(snapshot.price, Decimal)
        self.assertEqual(snapshot.price, Decimal("70123.4500"))
        self.assertEqual(snapshot.timestamp, "2026-06-23T09:00:00Z")
        self.assertEqual(candle.close, Decimal("70500.30"))
        self.assertEqual(candle.timestamp, "2026-06-23T09:00:00Z")
        self.assertEqual(rate.exchange_rate, Decimal("1375.2500"))
        self.assertEqual(rate.date_time, "2026-06-23T09:00:00Z")

    def test_stock_ingestion_uses_upsert_storage_flow(self) -> None:
        self.ingestion.ingest_stocks_payload(
            [{"symbol": "005930", "name": "Before", "market": "KOSPI"}]
        )
        processed = self.ingestion.ingest_stocks_payload(
            [{"symbol": "005930", "name": "After", "market": "KOSPI"}]
        )

        stocks = self.persistence.list_stocks()

        self.assertEqual(processed, 1)
        self.assertEqual(len(stocks), 1)
        self.assertEqual(stocks[0].stock_name, "After")

    def test_append_ingestion_keeps_multiple_market_rows(self) -> None:
        self.ingestion.ingest_stocks_payload(
            [{"symbol": "005930", "name": "Mock Stock", "market": "KOSPI"}]
        )
        price_payload = {
            "prices": [
                {
                    "symbol": "005930",
                    "lastPrice": "1.10",
                    "timestamp": "2026-06-23T09:00:00Z",
                },
                {
                    "symbol": "005930",
                    "lastPrice": "2.20",
                    "timestamp": "2026-06-23T09:01:00Z",
                },
            ]
        }

        row_ids = self.ingestion.ingest_price_snapshots_payload(price_payload)
        stored = self.persistence.list_price_snapshots("005930")

        self.assertEqual(len(row_ids), 2)
        self.assertEqual([item.price for item in stored], [Decimal("1.10"), Decimal("2.20")])

    def test_ingestion_does_not_open_network_sockets(self) -> None:
        with patch.object(
            socket,
            "socket",
            side_effect=AssertionError("network access is forbidden"),
        ):
            self.ingestion.ingest_stocks_payload(
                [{"symbol": "005930", "name": "Mock Stock", "market": "KOSPI"}]
            )
            self.assertEqual(len(self.persistence.list_stocks()), 1)

    def test_source_does_not_create_clients_auth_contexts_or_send_requests(self) -> None:
        import ai_stock.services.local_mock_ingestion as local_mock_ingestion

        service_source = Path(local_mock_ingestion.__file__).read_text(
            encoding="utf-8"
        )

        forbidden_terms = (
            "ai_stock.clients",
            "token_provider",
            "request_context",
            "httpx.Client",
            "httpx.AsyncClient",
            ".send(",
            "accountSeq",
            "Order",
            "Portfolio",
            "Balance",
            "Execution",
        )
        for term in forbidden_terms:
            self.assertNotIn(term, service_source)


if __name__ == "__main__":
    unittest.main()
