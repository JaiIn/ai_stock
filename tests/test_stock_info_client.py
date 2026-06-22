"""Offline request and parsing tests for the Toss stock-info client."""

import unittest

import httpx

from ai_stock.clients import (
    AuthenticatedRequestContextFactory,
    MockTokenProvider,
    TossApiError,
    TossClientConfig,
    TossClientConfigError,
    TossClientFoundation,
    TossStockInfoClient,
)


def _fake_response(result: object) -> httpx.Response:
    return httpx.Response(
        200,
        json={"result": result},
        request=httpx.Request("GET", "https://mock.invalid/stock-info"),
    )


class TossStockInfoClientTests(unittest.TestCase):
    def setUp(self) -> None:
        self.network_called = False
        self.token = "mock-stock-info-token"

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
        self.client = TossStockInfoClient(self.foundation, context)

    def test_get_stocks_builds_documented_request_without_sending(self) -> None:
        request = self.client.get_stocks(["005930", "AAPL"])

        self.assertEqual(request.method, "GET")
        self.assertEqual(request.url.path, "/api/v1/stocks")
        self.assertEqual(request.url.params["symbols"], "005930,AAPL")
        self.assertNotIn("X-Tossinvest-Account", request.headers)
        self.assertNotIn(
            self.token,
            repr(self.foundation.safe_request_context(request)),
        )
        self.assertFalse(self.network_called)

    def test_get_stock_warnings_builds_request_without_sending(self) -> None:
        request = self.client.get_stock_warnings("005930")

        self.assertEqual(request.method, "GET")
        self.assertEqual(request.url.path, "/api/v1/stocks/005930/warnings")
        self.assertNotIn("X-Tossinvest-Account", request.headers)
        self.assertFalse(self.network_called)

    def test_get_stocks_rejects_more_than_documented_limit(self) -> None:
        with self.assertRaises(TossClientConfigError):
            self.client.get_stocks([f"FAKE{index}" for index in range(201)])

    def test_parse_stocks_response_uses_minimal_documented_fields(self) -> None:
        stocks = self.client.parse_stocks_response(
            _fake_response(
                [
                    {
                        "symbol": "005930",
                        "name": "테스트 종목",
                        "englishName": "Test Stock",
                        "isinCode": "FAKE-ISIN",
                        "market": "KOSPI",
                        "securityType": "STOCK",
                        "status": "ACTIVE",
                        "currency": "KRW",
                    }
                ]
            )
        )

        self.assertEqual(stocks[0].stock_code, "005930")
        self.assertEqual(stocks[0].stock_name, "테스트 종목")
        self.assertEqual(stocks[0].currency, "KRW")

    def test_parse_stock_warnings_response_uses_endpoint_symbol(self) -> None:
        warnings = self.client.parse_stock_warnings_response(
            "005930",
            _fake_response(
                [
                    {
                        "warningType": "FAKE_WARNING",
                        "exchange": "KRX",
                        "startDate": "2026-01-01",
                        "endDate": None,
                    }
                ]
            ),
        )

        self.assertEqual(warnings[0].stock_code, "005930")
        self.assertEqual(warnings[0].warning_type, "FAKE_WARNING")
        self.assertIsNone(warnings[0].end_date)

    def test_empty_warning_array_is_valid(self) -> None:
        warnings = self.client.parse_stock_warnings_response(
            "005930",
            _fake_response([]),
        )

        self.assertEqual(warnings, [])

    def test_invalid_result_shape_raises_safe_error(self) -> None:
        sensitive_text = "mock-stock-info-token"

        with self.assertRaises(TossApiError) as raised:
            self.client.parse_stocks_response(
                _fake_response({"unexpected": sensitive_text})
            )

        self.assertNotIn(sensitive_text, str(raised.exception))


if __name__ == "__main__":
    unittest.main()
