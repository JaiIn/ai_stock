"""Offline tests for the OAuth plus single-symbol Stock Info smoke path."""

import unittest

import httpx

from ai_stock.clients import OAUTH_TOKEN_PATH
from ai_stock.clients.stock_info_smoke import (
    DEFAULT_STOCK_SYMBOL,
    STOCKS_PATH,
    StockInfoSmokePhase,
    execute_stock_info_single_symbol_smoke,
)
from ai_stock.models import OAuthTokenRequest
from ai_stock.risk import LiveApiSafetyGate, TossEndpointMetadata


class RecordingSafetyGate(LiveApiSafetyGate):
    def __init__(self, events: list[str]) -> None:
        self.events = events
        self.metadata: TossEndpointMetadata | None = None

    def evaluate(self, metadata, *args, **kwargs):
        self.events.append("safety_gate")
        self.metadata = metadata
        return super().evaluate(metadata, *args, **kwargs)


class StockInfoLiveSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw_token = "synthetic-stock-info-live-token-value"
        self.events: list[str] = []

    def make_client(self, handler) -> httpx.Client:
        client = httpx.Client(
            base_url="https://mock.invalid",
            transport=httpx.MockTransport(handler),
        )
        self.addCleanup(client.close)
        return client

    def test_oauth_then_gate_then_single_stock_flow(self) -> None:
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path == OAUTH_TOKEN_PATH:
                self.events.append("oauth")
                return self._token_response(request)
            if request.url.path == STOCKS_PATH:
                self.events.append("stocks")
                self.assertEqual(request.method, "GET")
                self.assertEqual(request.url.params["symbols"], "005930")
                self.assertEqual(len(request.url.params.get_list("symbols")), 1)
                self.assertNotIn(self.raw_token, repr(request))
                return self._stock_response(request)
            raise AssertionError(f"unexpected endpoint: {request.url.path}")

        gate = RecordingSafetyGate(self.events)
        result = self._execute(self.make_client(handler), gate=gate)

        self.assertEqual(calls, [OAUTH_TOKEN_PATH, STOCKS_PATH])
        self.assertEqual(self.events, ["oauth", "safety_gate", "stocks"])
        self.assertIsNotNone(gate.metadata)
        assert gate.metadata is not None
        self.assertEqual(gate.metadata.method, "GET")
        self.assertEqual(gate.metadata.path, STOCKS_PATH)
        self.assertEqual(gate.metadata.endpoint_category, "stock_info")
        self.assertTrue(gate.metadata.requires_auth)
        self.assertFalse(gate.metadata.requires_account_seq)
        self.assertTrue(result.success)
        self.assertEqual(result.phase, StockInfoSmokePhase.READONLY_STOCK_INFO)
        self.assertEqual(result.http_status_code, 200)
        safe = result.safe_dict()
        self.assertEqual(safe["requested_symbols"], "005930")
        self.assertEqual(safe["result_count"], 1)
        self.assertTrue(safe["requested_symbol_present"])
        self.assertTrue(safe["shares_outstanding_present"])
        self.assertNotIn(self.raw_token, repr(result))
        self.assertNotIn(self.raw_token, repr(safe))

    def test_oauth_failure_stops_before_business_endpoint(self) -> None:
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
        self.assertEqual(result.phase, StockInfoSmokePhase.OAUTH_TOKEN)
        self.assertEqual(result.http_status_code, 401)
        self.assertEqual(calls, [OAUTH_TOKEN_PATH])
        self._assert_safe(result)

    def test_stock_info_error_preserves_safe_status(self) -> None:
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
        self.assertEqual(result.phase, StockInfoSmokePhase.READONLY_STOCK_INFO)
        self.assertEqual(result.http_status_code, 404)
        self.assertEqual(result.safe_error_code, "stock-not-found")
        self.assertEqual(calls, [OAUTH_TOKEN_PATH, STOCKS_PATH])
        self._assert_safe(result)

    def test_response_parse_failure_is_safe(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == OAUTH_TOKEN_PATH:
                return self._token_response(request)
            return httpx.Response(
                200,
                json={"result": [{"symbol": "005930"}]},
                request=request,
            )

        result = self._execute(self.make_client(handler))

        self.assertFalse(result.success)
        self.assertEqual(result.phase, StockInfoSmokePhase.RESPONSE_PARSE)
        self.assertEqual(result.http_status_code, 200)
        self.assertEqual(result.safe_error_type, "response_parse_failed")
        self._assert_safe(result)

    def test_unapproved_or_unsafe_settings_do_not_call_stocks(self) -> None:
        for allow_live_api, allow_real_order, dry_run_only in (
            (False, False, True),
            (True, True, True),
            (True, False, False),
        ):
            calls: list[str] = []

            def handler(request: httpx.Request) -> httpx.Response:
                calls.append(request.url.path)
                raise AssertionError(f"unexpected request: {request.url.path}")

            with self.subTest(
                allow_live_api=allow_live_api,
                allow_real_order=allow_real_order,
                dry_run_only=dry_run_only,
            ):
                result = execute_stock_info_single_symbol_smoke(
                    self.make_client(handler),
                    self._request(),
                    LiveApiSafetyGate(),
                    allow_live_api=allow_live_api,
                    allow_real_order=allow_real_order,
                    dry_run_only=dry_run_only,
                    stock_info_live_smoke_allowed=True,
                )
                self.assertFalse(result.success)
                self.assertEqual(calls, [])

    def test_no_warnings_or_other_business_endpoint_is_called(self) -> None:
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path == OAUTH_TOKEN_PATH:
                return self._token_response(request)
            if request.url.path == STOCKS_PATH:
                return self._stock_response(request)
            raise AssertionError(f"unexpected endpoint: {request.url.path}")

        result = self._execute(self.make_client(handler))

        self.assertTrue(result.success)
        self.assertEqual(calls, [OAUTH_TOKEN_PATH, STOCKS_PATH])
        self.assertNotIn("/api/v1/stocks/005930/warnings", calls)

    def _execute(
        self,
        client: httpx.Client,
        *,
        gate: LiveApiSafetyGate | None = None,
    ):
        return execute_stock_info_single_symbol_smoke(
            client,
            self._request(),
            gate or LiveApiSafetyGate(),
            allow_live_api=True,
            allow_real_order=False,
            dry_run_only=True,
            stock_info_live_smoke_allowed=True,
            symbol=DEFAULT_STOCK_SYMBOL,
        )

    def _request(self) -> OAuthTokenRequest:
        return OAuthTokenRequest(
            client_id="synthetic-client-id",
            client_secret="synthetic-client-secret",
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

    def _stock_response(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "result": [
                    {
                        "symbol": "005930",
                        "name": "Synthetic Stock",
                        "englishName": "SYNTHETIC STOCK",
                        "isinCode": "KR7000000000",
                        "market": "KOSPI",
                        "securityType": "STOCK",
                        "isCommonShare": True,
                        "status": "ACTIVE",
                        "currency": "KRW",
                        "listDate": None,
                        "delistDate": None,
                        "sharesOutstanding": "1000000",
                        "leverageFactor": None,
                        "koreanMarketDetail": {
                            "liquidationTrading": False,
                            "nxtSupported": True,
                            "krxTradingSuspended": False,
                            "nxtTradingSuspended": False,
                        },
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
