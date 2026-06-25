"""Offline request and parsing tests for the Toss stock-info client."""

from decimal import Decimal
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


def _fake_response(result: object, *, status_code: int = 200) -> httpx.Response:
    return httpx.Response(
        status_code,
        json={"result": result},
        request=httpx.Request("GET", "https://mock.invalid/stock-info"),
    )


def _fake_error_response(
    status_code: int,
    *,
    code: str,
    data: object | None = None,
) -> httpx.Response:
    error = {
        "requestId": "safe-request-id",
        "code": code,
        "message": "Safe error message.",
    }
    if data is not None:
        error["data"] = data
    return httpx.Response(
        status_code,
        json={"error": error},
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

    def test_get_stocks_supports_one_official_example_symbol(self) -> None:
        request = self.client.get_stocks(["005930"])

        self.assertEqual(request.url.params["symbols"], "005930")
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

    def test_get_stocks_accepts_exactly_documented_limit(self) -> None:
        request = self.client.get_stocks(
            [f"FAKE{index}" for index in range(200)]
        )

        self.assertEqual(len(request.url.params["symbols"].split(",")), 200)
        self.assertFalse(self.network_called)

    def test_stock_symbol_validation_rejects_unsupported_characters(self) -> None:
        invalid_symbols = ("005930/KS", "AAPL,MSFT", "AAPL US")

        for symbol in invalid_symbols:
            with self.subTest(symbol=symbol):
                with self.assertRaises(TossClientConfigError):
                    self.client.get_stocks([symbol])
                with self.assertRaises(TossClientConfigError):
                    self.client.get_stock_warnings(symbol)

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
                        "isCommonShare": True,
                        "status": "ACTIVE",
                        "currency": "KRW",
                        "listDate": "1975-06-11",
                        "delistDate": None,
                        "sharesOutstanding": "5919637922",
                        "leverageFactor": None,
                        "koreanMarketDetail": {
                            "liquidationTrading": False,
                            "nxtSupported": True,
                            "krxTradingSuspended": False,
                            "nxtTradingSuspended": False,
                        },
                    }
                ]
            )
        )

        self.assertEqual(stocks[0].stock_code, "005930")
        self.assertEqual(stocks[0].stock_name, "테스트 종목")
        self.assertEqual(stocks[0].currency, "KRW")
        self.assertEqual(stocks[0].shares_outstanding, Decimal("5919637922"))
        self.assertIsNone(stocks[0].leverage_factor)
        self.assertIsNotNone(stocks[0].korean_market_detail)
        self.assertTrue(stocks[0].korean_market_detail.nxt_supported)

    def test_parse_stocks_response_allows_optional_fields_to_be_missing(self) -> None:
        stocks = self.client.parse_stocks_response(
            _fake_response(
                [
                    {
                        "symbol": "AAPL",
                        "name": "Apple",
                        "englishName": "APPLE INC",
                        "isinCode": "US0378331005",
                        "market": "NASDAQ",
                        "securityType": "STOCK",
                        "isCommonShare": True,
                        "status": "ACTIVE",
                        "currency": "USD",
                        "sharesOutstanding": "14702703000",
                    }
                ]
            )
        )

        self.assertIsNone(stocks[0].list_date)
        self.assertIsNone(stocks[0].delist_date)
        self.assertIsNone(stocks[0].leverage_factor)
        self.assertIsNone(stocks[0].korean_market_detail)

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

    def test_parse_invalid_request_error_keeps_safe_constraint_fields(self) -> None:
        error = self.client.parse_stock_info_error_response(
            _fake_error_response(
                400,
                code="invalid-request",
                data={
                    "field": "symbols",
                    "allowedValues": ["005930", "AAPL"],
                    "constraint": {"min": 1, "max": 200},
                },
            )
        )

        self.assertEqual(error.request_id, "safe-request-id")
        self.assertEqual(error.field, "symbols")
        self.assertEqual(error.allowed_values, ("005930", "AAPL"))
        self.assertEqual(error.constraint_min, 1)
        self.assertEqual(error.constraint_max, 200)

    def test_parse_standard_errors_keeps_only_safe_metadata(self) -> None:
        cases = (
            (404, "stock-not-found"),
            (429, "rate-limit-exceeded"),
            (500, "internal-error"),
        )

        for status_code, code in cases:
            with self.subTest(status_code=status_code):
                error = self.client.parse_stock_info_error_response(
                    _fake_error_response(status_code, code=code)
                )
                self.assertEqual(error.code, code)
                self.assertEqual(error.message, "Safe error message.")
                self.assertIsNone(error.field)


if __name__ == "__main__":
    unittest.main()
