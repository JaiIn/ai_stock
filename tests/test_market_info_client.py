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
            base_currency="usd",
            quote_currency="krw",
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
        request = self.client.get_exchange_rate(
            base_currency="USD",
            quote_currency="KRW",
        )

        self.assertNotIn("dateTime", request.url.params)
        self.assertEqual(request.url.params["baseCurrency"], "USD")
        self.assertEqual(request.url.params["quoteCurrency"], "KRW")
        self.assertFalse(self.network_called)

    def test_blank_date_time_is_rejected(self) -> None:
        with self.assertRaises(TossClientConfigError):
            self.client.get_exchange_rate(
                base_currency="USD",
                quote_currency="KRW",
                date_time=" ",
            )

    def test_unsupported_or_same_currency_is_rejected_before_send(self) -> None:
        with self.assertRaises(TossClientConfigError):
            self.client.get_exchange_rate(
                base_currency="EUR",
                quote_currency="KRW",
            )
        with self.assertRaises(TossClientConfigError):
            self.client.get_exchange_rate(
                base_currency="USD",
                quote_currency="USD",
            )
        self.assertFalse(self.network_called)

    def test_fake_exchange_rate_response_is_parsed_as_decimal(self) -> None:
        rate = self.client.parse_exchange_rate_response(
            _fake_response(
                {
                    "baseCurrency": "USD",
                    "quoteCurrency": "KRW",
                    "rate": "1375.25",
                    "midRate": "1370.00",
                    "basisPoint": "38.3211678832",
                    "rateChangeType": "UP",
                    "validFrom": "2026-01-01T00:00:00Z",
                    "validUntil": "2026-01-01T00:05:00Z",
                }
            ),
        )

        self.assertEqual(rate.base_currency, "USD")
        self.assertEqual(rate.quote_currency, "KRW")
        self.assertEqual(rate.exchange_rate, Decimal("1375.25"))
        self.assertEqual(rate.rate, Decimal("1375.25"))
        self.assertEqual(rate.mid_rate, Decimal("1370.00"))
        self.assertEqual(rate.basis_point, Decimal("38.3211678832"))
        self.assertEqual(rate.rate_change_type, "UP")
        self.assertEqual(rate.valid_from, "2026-01-01T00:00:00Z")
        self.assertEqual(rate.valid_until, "2026-01-01T00:05:00Z")

    def test_missing_required_official_response_field_is_rejected(self) -> None:
        with self.assertRaises(TossApiError):
            self.client.parse_exchange_rate_response(
                _fake_response(
                    {
                        "baseCurrency": "USD",
                        "quoteCurrency": "KRW",
                        "rate": "1375.25",
                        "midRate": "1375.00",
                        "basisPoint": "1.8181818182",
                        "rateChangeType": "UP",
                    }
                ),
            )

    def test_documented_exchange_rate_errors_are_safely_parsed(self) -> None:
        unsupported = self.client.parse_exchange_rate_error_response(
            httpx.Response(
                400,
                json={
                    "error": {
                        "requestId": "safe-request-id",
                        "code": "invalid-request",
                        "message": "Unsupported currency.",
                        "data": {
                            "field": "baseCurrency",
                            "allowedValues": ["KRW", "USD"],
                        },
                    }
                },
            )
        )
        same_currency = self.client.parse_exchange_rate_error_response(
            httpx.Response(
                400,
                json={
                    "error": {
                        "requestId": "safe-request-id-2",
                        "code": "invalid-request",
                        "message": "Currencies must be different.",
                        "data": {"field": "baseCurrency,quoteCurrency"},
                    }
                },
            )
        )

        self.assertEqual(unsupported.code, "invalid-request")
        self.assertEqual(unsupported.field, "baseCurrency")
        self.assertEqual(unsupported.allowed_values, ("KRW", "USD"))
        self.assertEqual(same_currency.field, "baseCurrency,quoteCurrency")
        self.assertEqual(same_currency.allowed_values, ())

    def test_documented_404_429_and_500_error_envelopes_are_parsed(self) -> None:
        cases = (
            (404, "exchange-rate-not-found"),
            (429, "rate-limit-exceeded"),
            (500, "internal-error"),
        )
        for status_code, code in cases:
            with self.subTest(status_code=status_code):
                parsed = self.client.parse_exchange_rate_error_response(
                    httpx.Response(
                        status_code,
                        json={
                            "error": {
                                "requestId": f"request-{status_code}",
                                "code": code,
                                "message": "Safe documented summary.",
                            }
                        },
                    )
                )
                self.assertEqual(parsed.request_id, f"request-{status_code}")
                self.assertEqual(parsed.code, code)
                self.assertEqual(parsed.message, "Safe documented summary.")

    def test_invalid_result_shape_raises_safe_error(self) -> None:
        sensitive_text = self.token

        with self.assertRaises(TossApiError) as raised:
            self.client.parse_exchange_rate_response(
                _fake_response([{"unexpected": sensitive_text}]),
            )

        self.assertNotIn(sensitive_text, str(raised.exception))


if __name__ == "__main__":
    unittest.main()
