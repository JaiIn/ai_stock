"""Offline request and parsing tests for the Toss market-data client."""

import unittest
from decimal import Decimal

import httpx

from ai_stock.clients import (
    AuthenticatedRequestContextFactory,
    MockTokenProvider,
    TossApiError,
    TossClientConfig,
    TossClientConfigError,
    TossClientFoundation,
    TossMarketDataClient,
)


def _fake_response(result: object) -> httpx.Response:
    return httpx.Response(
        200,
        json={"result": result},
        request=httpx.Request("GET", "https://mock.invalid/market-data"),
    )


class TossMarketDataClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.network_called = False
        self.token = "mock-market-data-token"

        def fail_if_called(request: httpx.Request) -> httpx.Response:
            self.network_called = True
            raise AssertionError(f"unexpected network send: {request.url}")

        self.http_client = httpx.Client(
            transport=httpx.MockTransport(fail_if_called)
        )
        self.addCleanup(self.http_client.close)
        self.foundation = TossClientFoundation(
            TossClientConfig(base_url="https://mock.invalid"),
            http_client=self.http_client,
        )
        context = AuthenticatedRequestContextFactory(
            MockTokenProvider(access_token=self.token)
        ).create()
        self.client = TossMarketDataClient(self.foundation, context)

    def test_single_symbol_interfaces_build_documented_requests(self) -> None:
        cases = [
            (self.client.get_orderbook("005930"), "/api/v1/orderbook"),
            (self.client.get_trades("005930", count=10), "/api/v1/trades"),
            (self.client.get_price_limit("005930"), "/api/v1/price-limits"),
        ]

        for request, expected_path in cases:
            with self.subTest(path=expected_path):
                self.assertEqual(request.method, "GET")
                self.assertEqual(request.url.path, expected_path)
                self.assertEqual(request.url.params["symbol"], "005930")
                self.assertNotIn("X-Tossinvest-Account", request.headers)
        self.assertFalse(self.network_called)

    def test_get_prices_builds_multi_symbol_request_without_sending(self) -> None:
        request = self.client.get_prices(["005930", "AAPL"])

        self.assertEqual(request.url.path, "/api/v1/prices")
        self.assertEqual(request.url.params["symbols"], "005930,AAPL")
        self.assertNotIn(
            self.token,
            repr(self.foundation.safe_request_context(request)),
        )
        self.assertFalse(self.network_called)

    def test_get_candles_builds_documented_query(self) -> None:
        request = self.client.get_candles(
            "005930",
            interval="1d",
            count=20,
            before="2026-01-01T00:00:00Z",
            adjusted=True,
        )

        self.assertEqual(request.url.path, "/api/v1/candles")
        self.assertEqual(request.url.params["symbol"], "005930")
        self.assertEqual(request.url.params["interval"], "1d")
        self.assertEqual(request.url.params["count"], "20")
        self.assertEqual(request.url.params["before"], "2026-01-01T00:00:00Z")
        self.assertEqual(request.url.params["adjusted"], "true")
        self.assertFalse(self.network_called)

    def test_documented_count_limits_are_enforced(self) -> None:
        with self.assertRaises(TossClientConfigError):
            self.client.get_trades("005930", count=51)
        with self.assertRaises(TossClientConfigError):
            self.client.get_candles("005930", interval="1d", count=201)
        with self.assertRaises(TossClientConfigError):
            self.client.get_prices([f"FAKE{index}" for index in range(201)])

    def test_parse_prices_uses_decimal_and_minimal_documented_fields(self) -> None:
        prices = self.client.parse_prices_response(
            _fake_response(
                [
                    {
                        "symbol": "005930",
                        "timestamp": "2026-01-01T00:00:00Z",
                        "lastPrice": "70123.45",
                        "currency": "KRW",
                    }
                ]
            )
        )

        self.assertEqual(prices[0].stock_code, "005930")
        self.assertEqual(prices[0].price, Decimal("70123.45"))
        self.assertEqual(prices[0].currency, "KRW")

    def test_parse_candles_uses_official_result_object(self) -> None:
        page = self.client.parse_candles_response(
            _fake_response(
                {
                    "candles": [
                        {
                            "timestamp": "2026-01-01T00:00:00Z",
                            "openPrice": "100.1",
                            "highPrice": "110.2",
                            "lowPrice": "90.3",
                            "closePrice": "105.4",
                            "volume": "12345",
                            "currency": "USD",
                        }
                    ],
                    "nextBefore": "2025-12-31T23:59:00Z",
                }
            )
        )

        self.assertEqual(page.candles[0].open, Decimal("100.1"))
        self.assertEqual(page.candles[0].close, Decimal("105.4"))
        self.assertEqual(page.candles[0].volume, Decimal("12345"))
        self.assertEqual(page.next_before, "2025-12-31T23:59:00Z")

    def test_parse_candles_supports_missing_next_before(self) -> None:
        page = self.client.parse_candles_response(_fake_response({"candles": []}))

        self.assertEqual(page.candles, ())
        self.assertIsNone(page.next_before)

    def test_invalid_result_shape_raises_safe_error(self) -> None:
        sensitive_text = self.token

        with self.assertRaises(TossApiError) as raised:
            self.client.parse_prices_response(
                _fake_response({"unexpected": sensitive_text})
            )

        self.assertNotIn(sensitive_text, str(raised.exception))


if __name__ == "__main__":
    unittest.main()
