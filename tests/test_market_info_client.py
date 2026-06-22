"""Offline tests for the Toss exchange-rate client interface."""

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
    TossMarketInfoClient,
)


def _fake_response(result: object) -> httpx.Response:
    return httpx.Response(
        200,
        json={"result": result},
        request=httpx.Request("GET", "https://mock.invalid/exchange-rate"),
    )


class TossMarketInfoClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.network_called = False
        self.token = "mock-market-info-token"

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
        self.client = TossMarketInfoClient(self.foundation, context)

    def test_get_exchange_rate_builds_documented_request_without_send(self) -> None:
        request = self.client.get_exchange_rate(
            "USD",
            "KRW",
            date_time="2026-01-01T00:00:00Z",
        )

        self.assertEqual(request.method, "GET")
        self.assertEqual(request.url.path, "/api/v1/exchange-rate")
        self.assertEqual(request.url.params["baseCurrency"], "USD")
        self.assertEqual(request.url.params["quoteCurrency"], "KRW")
        self.assertEqual(request.url.params["dateTime"], "2026-01-01T00:00:00Z")
        self.assertNotIn("X-Tossinvest-Account", request.headers)
        self.assertNotIn(
            self.token,
            repr(self.foundation.safe_request_context(request)),
        )
        self.assertFalse(self.network_called)

    def test_optional_date_time_is_omitted(self) -> None:
        request = self.client.get_exchange_rate("USD", "KRW")

        self.assertNotIn("dateTime", request.url.params)
        self.assertFalse(self.network_called)

    def test_missing_currency_is_rejected(self) -> None:
        with self.assertRaises(TossClientConfigError):
            self.client.get_exchange_rate("", "KRW")

    def test_fake_exchange_rate_response_is_parsed_as_decimal(self) -> None:
        rate = self.client.parse_exchange_rate_response(
            "USD",
            "KRW",
            _fake_response(
                {
                    "exchangeRate": "1375.25",
                    "dateTime": "2026-01-01T00:00:00Z",
                }
            ),
        )

        self.assertEqual(rate.base_currency, "USD")
        self.assertEqual(rate.quote_currency, "KRW")
        self.assertEqual(rate.exchange_rate, Decimal("1375.25"))
        self.assertEqual(rate.date_time, "2026-01-01T00:00:00Z")

    def test_optional_response_date_time_is_supported(self) -> None:
        rate = self.client.parse_exchange_rate_response(
            "USD",
            "KRW",
            _fake_response({"exchangeRate": "1375.25"}),
        )

        self.assertIsNone(rate.date_time)

    def test_invalid_result_shape_raises_safe_error(self) -> None:
        sensitive_text = self.token

        with self.assertRaises(TossApiError) as raised:
            self.client.parse_exchange_rate_response(
                "USD",
                "KRW",
                _fake_response([{"unexpected": sensitive_text}]),
            )

        self.assertNotIn(sensitive_text, str(raised.exception))


if __name__ == "__main__":
    unittest.main()
