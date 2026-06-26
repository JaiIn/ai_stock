"""Offline tests for OAuth plus single-symbol Stock Warnings smoke."""

import unittest

import httpx

from ai_stock.clients import OAUTH_TOKEN_PATH
from ai_stock.clients.stock_warnings_smoke import (
    DEFAULT_WARNING_SYMBOL,
    StockWarningsSmokePhase,
    execute_stock_warnings_single_symbol_smoke,
)
from ai_stock.models import OAuthTokenRequest
from ai_stock.risk import LiveApiSafetyGate, TossEndpointMetadata

WARNINGS_PATH = "/api/v1/stocks/005930/warnings"


class RecordingSafetyGate(LiveApiSafetyGate):
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.metadata: TossEndpointMetadata | None = None

    def evaluate(self, metadata, *args, **kwargs):
        self.events.append("safety_gate")
        self.metadata = metadata
        return super().evaluate(metadata, *args, **kwargs)


class StockWarningsLiveSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw_token = "synthetic-stock-warnings-live-token-value"
        self.events: list[str] = []

    def make_client(self, handler) -> httpx.Client:
        client = httpx.Client(
            base_url="https://mock.invalid",
            transport=httpx.MockTransport(handler),
        )
        self.addCleanup(client.close)
        return client

    def test_oauth_then_gate_then_single_warnings_flow(self) -> None:
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path == OAUTH_TOKEN_PATH:
                self.events.append("oauth")
                return self._token_response(request)
            if request.url.path == WARNINGS_PATH:
                self.events.append("warnings")
                self.assertEqual(request.method, "GET")
                self.assertNotIn(self.raw_token, repr(request))
                return self._warnings_response(request)
            raise AssertionError(f"unexpected endpoint: {request.url.path}")

        gate = RecordingSafetyGate(self.events)
        result = self._execute(self.make_client(handler), gate=gate)

        self.assertEqual(calls, [OAUTH_TOKEN_PATH, WARNINGS_PATH])
        self.assertEqual(self.events, ["oauth", "safety_gate", "warnings"])
        self.assertIsNotNone(gate.metadata)
        assert gate.metadata is not None
        self.assertEqual(gate.metadata.method, "GET")
        self.assertEqual(gate.metadata.path, WARNINGS_PATH)
        self.assertEqual(gate.metadata.endpoint_category, "stock_info")
        self.assertTrue(gate.metadata.requires_auth)
        self.assertFalse(gate.metadata.requires_account_seq)
        self.assertTrue(result.success)
        self.assertEqual(
            result.phase,
            StockWarningsSmokePhase.READONLY_STOCK_WARNINGS,
        )
        self.assertEqual(result.http_status_code, 200)
        safe = result.safe_dict()
        self.assertEqual(safe["requested_symbol"], "005930")
        self.assertEqual(safe["warning_count"], 1)
        self.assertTrue(safe["parsed_symbol_present"])
        self.assertTrue(safe["warning_type_present"])
        self.assertTrue(safe["exchange_field_supported"])
        self.assertTrue(safe["start_date_field_supported"])
        self.assertTrue(safe["end_date_field_supported"])
        self.assertNotIn(self.raw_token, repr(result))
        self.assertNotIn(self.raw_token, repr(safe))

    def test_empty_warning_array_is_a_successful_parse(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == OAUTH_TOKEN_PATH:
                return self._token_response(request)
            return httpx.Response(200, json={"result": []}, request=request)

        result = self._execute(self.make_client(handler))

        self.assertTrue(result.success)
        safe = result.safe_dict()
        self.assertEqual(safe["warning_count"], 0)
        self.assertFalse(safe["parsed_symbol_present"])
        self.assertTrue(safe["empty_warning_array_supported"])

    def test_oauth_failure_stops_before_warnings_endpoint(self) -> None:
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            return httpx.Response(
                401,
                json={"error": {"message": self.raw_token}},
                request=request,
            )

        result = self._execute(self.make_client(handler))

        self.assertFalse(result.success)
        self.assertEqual(result.phase, StockWarningsSmokePhase.OAUTH_TOKEN)
        self.assertEqual(result.http_status_code, 401)
        self.assertEqual(calls, [OAUTH_TOKEN_PATH])
        self._assert_safe(result)

    def test_warnings_error_preserves_safe_status(self) -> None:
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path == OAUTH_TOKEN_PATH:
                return self._token_response(request)
            return httpx.Response(
                404,
                json={
                    "error": {
                        "requestId": "safe-id",
                        "code": "stock-not-found",
                        "message": self.raw_token,
                    }
                },
                request=request,
            )

        result = self._execute(self.make_client(handler))

        self.assertFalse(result.success)
        self.assertEqual(
            result.phase,
            StockWarningsSmokePhase.READONLY_STOCK_WARNINGS,
        )
        self.assertEqual(result.http_status_code, 404)
        self.assertEqual(result.safe_error_code, "stock-not-found")
        self.assertEqual(calls, [OAUTH_TOKEN_PATH, WARNINGS_PATH])
        self._assert_safe(result)

    def test_response_parse_failure_is_safe(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == OAUTH_TOKEN_PATH:
                return self._token_response(request)
            return httpx.Response(
                200,
                json={"result": [{"exchange": "KRX"}]},
                request=request,
            )

        result = self._execute(self.make_client(handler))

        self.assertFalse(result.success)
        self.assertEqual(result.phase, StockWarningsSmokePhase.RESPONSE_PARSE)
        self.assertEqual(result.http_status_code, 200)
        self.assertEqual(result.safe_error_type, "response_parse_failed")
        self._assert_safe(result)

    def test_no_stocks_query_or_other_business_endpoint_is_called(self) -> None:
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path == OAUTH_TOKEN_PATH:
                return self._token_response(request)
            if request.url.path == WARNINGS_PATH:
                return self._warnings_response(request)
            raise AssertionError(f"unexpected endpoint: {request.url.path}")

        result = self._execute(self.make_client(handler))

        self.assertTrue(result.success)
        self.assertEqual(calls, [OAUTH_TOKEN_PATH, WARNINGS_PATH])
        self.assertNotIn("/api/v1/stocks", calls)

    def _execute(
        self,
        client: httpx.Client,
        *,
        gate: LiveApiSafetyGate | None = None,
    ):
        return execute_stock_warnings_single_symbol_smoke(
            client,
            OAuthTokenRequest(
                client_id="synthetic-client-id",
                client_secret="synthetic-client-secret",
            ),
            gate or LiveApiSafetyGate(),
            allow_live_api=True,
            allow_real_order=False,
            dry_run_only=True,
            stock_warnings_live_smoke_allowed=True,
            symbol=DEFAULT_WARNING_SYMBOL,
        )

    def _token_response(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "access_token": self.raw_token,
                "token_type": "Bearer",
                "expires_in": 3600,
            },
            request=request,
        )

    def _warnings_response(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "result": [
                    {
                        "warningType": "VI_STATIC",
                        "exchange": "KRX",
                        "startDate": "2026-06-26",
                        "endDate": None,
                    }
                ]
            },
            request=request,
        )

    def _assert_safe(self, result) -> None:
        text = repr(result.safe_dict())
        self.assertNotIn(self.raw_token, text)
        self.assertNotIn("synthetic-client-secret", text)
        self.assertNotIn("Authorization", text)


if __name__ == "__main__":
    unittest.main()
