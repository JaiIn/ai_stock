"""Offline tests for the OAuth plus single-symbol Candles smoke path."""

import unittest

import httpx

from ai_stock.clients import OAUTH_TOKEN_PATH
from ai_stock.clients.candles_smoke import (
    CANDLES_PATH,
    DEFAULT_CANDLE_ADJUSTED,
    DEFAULT_CANDLE_COUNT,
    DEFAULT_CANDLE_INTERVAL,
    DEFAULT_CANDLE_SYMBOL,
    CandlesSmokePhase,
    execute_candles_single_symbol_smoke,
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


class CandlesLiveSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw_token = "synthetic-candles-live-token-value"
        self.events: list[str] = []

    def make_client(self, handler) -> httpx.Client:
        client = httpx.Client(
            base_url="https://mock.invalid",
            transport=httpx.MockTransport(handler),
        )
        self.addCleanup(client.close)
        return client

    def test_oauth_then_gate_then_single_candles_flow(self) -> None:
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path == OAUTH_TOKEN_PATH:
                self.events.append("oauth")
                return self._token_response(request)
            if request.url.path == CANDLES_PATH:
                self.events.append("candles")
                self.assertEqual(request.method, "GET")
                self.assertEqual(request.url.params["symbol"], "005930")
                self.assertEqual(request.url.params["interval"], "1d")
                self.assertEqual(request.url.params["count"], "1")
                self.assertEqual(request.url.params["adjusted"], "true")
                self.assertNotIn("before", request.url.params)
                self.assertNotIn(self.raw_token, repr(request))
                return self._candles_response(request)
            raise AssertionError(f"unexpected endpoint: {request.url.path}")

        gate = RecordingSafetyGate(self.events)
        result = self._execute(self.make_client(handler), gate=gate)

        self.assertEqual(calls, [OAUTH_TOKEN_PATH, CANDLES_PATH])
        self.assertEqual(self.events, ["oauth", "safety_gate", "candles"])
        self.assertIsNotNone(gate.metadata)
        assert gate.metadata is not None
        self.assertEqual(gate.metadata.method, "GET")
        self.assertEqual(gate.metadata.path, CANDLES_PATH)
        self.assertEqual(gate.metadata.endpoint_category, "market_data")
        self.assertTrue(gate.metadata.requires_auth)
        self.assertFalse(gate.metadata.requires_account_seq)
        self.assertTrue(result.success)
        self.assertEqual(result.phase, CandlesSmokePhase.READONLY_CANDLES)
        self.assertEqual(result.http_status_code, 200)
        safe = result.safe_dict()
        self.assertEqual(safe["requested_symbol"], "005930")
        self.assertEqual(safe["requested_interval"], "1d")
        self.assertEqual(safe["requested_count"], 1)
        self.assertTrue(safe["requested_adjusted"])
        self.assertFalse(safe["before_parameter_used"])
        self.assertEqual(safe["candles_count"], 1)
        self.assertTrue(safe["timestamp_present"])
        self.assertTrue(safe["open_present"])
        self.assertTrue(safe["high_present"])
        self.assertTrue(safe["low_present"])
        self.assertTrue(safe["close_present"])
        self.assertTrue(safe["volume_present"])
        self.assertTrue(safe["currency_present"])
        self.assertTrue(safe["next_before_supported"])
        self.assertTrue(safe["decimal_conversion_success"])
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
        self.assertEqual(result.phase, CandlesSmokePhase.OAUTH_TOKEN)
        self.assertEqual(result.http_status_code, 401)
        self.assertEqual(calls, [OAUTH_TOKEN_PATH])
        self._assert_safe(result)

    def test_candles_error_preserves_safe_status(self) -> None:
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
                        "code": "candle-not-found",
                        "message": self.raw_token,
                    }
                },
                request=request,
            )

        result = self._execute(self.make_client(handler))

        self.assertFalse(result.success)
        self.assertEqual(result.phase, CandlesSmokePhase.READONLY_CANDLES)
        self.assertEqual(result.http_status_code, 404)
        self.assertEqual(result.safe_error_code, "candle-not-found")
        self.assertEqual(calls, [OAUTH_TOKEN_PATH, CANDLES_PATH])
        self._assert_safe(result)

    def test_response_parse_failure_is_safe(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == OAUTH_TOKEN_PATH:
                return self._token_response(request)
            return httpx.Response(
                200,
                json={"result": {"candles": [{"timestamp": "2026-06-26"}]}},
                request=request,
            )

        result = self._execute(self.make_client(handler))

        self.assertFalse(result.success)
        self.assertEqual(result.phase, CandlesSmokePhase.RESPONSE_PARSE)
        self.assertEqual(result.http_status_code, 200)
        self.assertEqual(result.safe_error_type, "response_parse_failed")
        self._assert_safe(result)

    def test_unsafe_settings_do_not_call_any_endpoint(self) -> None:
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
                result = execute_candles_single_symbol_smoke(
                    self.make_client(handler),
                    self._request(),
                    LiveApiSafetyGate(),
                    allow_live_api=allow_live_api,
                    allow_real_order=allow_real_order,
                    dry_run_only=dry_run_only,
                    candles_live_smoke_allowed=True,
                )
                self.assertFalse(result.success)
                self.assertEqual(calls, [])

    def test_no_other_business_endpoint_is_called(self) -> None:
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path == OAUTH_TOKEN_PATH:
                return self._token_response(request)
            if request.url.path == CANDLES_PATH:
                return self._candles_response(request)
            raise AssertionError(f"unexpected endpoint: {request.url.path}")

        result = self._execute(self.make_client(handler))

        self.assertTrue(result.success)
        self.assertEqual(calls, [OAUTH_TOKEN_PATH, CANDLES_PATH])
        self.assertNotIn("/api/v1/prices", calls)
        self.assertNotIn("/api/v1/stocks", calls)
        self.assertNotIn("/api/v1/stocks/005930/warnings", calls)

    def test_rejects_non_approved_query_without_endpoint_calls(self) -> None:
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            raise AssertionError(f"unexpected request: {request.url.path}")

        result = execute_candles_single_symbol_smoke(
            self.make_client(handler),
            self._request(),
            LiveApiSafetyGate(),
            allow_live_api=True,
            allow_real_order=False,
            dry_run_only=True,
            candles_live_smoke_allowed=True,
            interval="1m",
        )

        self.assertFalse(result.success)
        self.assertEqual(result.phase, CandlesSmokePhase.CONFIG_VALIDATION)
        self.assertEqual(calls, [])
        self._assert_safe(result)

    def _execute(
        self,
        client: httpx.Client,
        *,
        gate: LiveApiSafetyGate | None = None,
    ):
        return execute_candles_single_symbol_smoke(
            client,
            self._request(),
            gate or LiveApiSafetyGate(),
            allow_live_api=True,
            allow_real_order=False,
            dry_run_only=True,
            candles_live_smoke_allowed=True,
            symbol=DEFAULT_CANDLE_SYMBOL,
            interval=DEFAULT_CANDLE_INTERVAL,
            count=DEFAULT_CANDLE_COUNT,
            adjusted=DEFAULT_CANDLE_ADJUSTED,
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

    def _candles_response(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "result": {
                    "candles": [
                        {
                            "timestamp": "2026-06-26T00:00:00+09:00",
                            "openPrice": "70000",
                            "highPrice": "71000",
                            "lowPrice": "69000",
                            "closePrice": "70500",
                            "volume": "1234567",
                            "currency": "KRW",
                        }
                    ],
                    "nextBefore": None,
                }
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
