"""Offline flow tests for OAuth plus the one approved read-only endpoint."""

import unittest

import httpx

from ai_stock.clients import (
    EXCHANGE_RATE_PATH,
    OAUTH_TOKEN_PATH,
    TossReadOnlySmokeClient,
)
from ai_stock.clients.readonly_smoke import (
    ReadOnlySmokeFailure,
    ReadOnlySmokePhase,
    execute_readonly_exchange_rate_smoke,
)
from ai_stock.models import OAuthTokenRequest, OAuthTokenResponse
from ai_stock.risk import LiveApiSafetyGate, TossEndpointMetadata


class RecordingSafetyGate(LiveApiSafetyGate):
    def __init__(self, events: list[str]) -> None:
        self.events = events

    def evaluate(self, *args, **kwargs):
        self.events.append("safety_gate")
        return super().evaluate(*args, **kwargs)


class ReadOnlyLiveSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.events: list[str] = []
        self.raw_token = "synthetic-readonly-live-token-value"

    def make_client(self, handler) -> httpx.Client:
        client = httpx.Client(
            base_url="https://mock.invalid",
            transport=httpx.MockTransport(handler),
        )
        self.addCleanup(client.close)
        return client

    def test_oauth_then_safety_gate_then_exchange_rate_flow(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == OAUTH_TOKEN_PATH:
                self.events.append("oauth")
                return httpx.Response(
                    200,
                    json={
                        "access_token": self.raw_token,
                        "token_type": "Bearer",
                        "expires_in": 3600,
                    },
                    request=request,
                )
            if request.url.path == EXCHANGE_RATE_PATH:
                self.events.append("exchange_rate")
                self.assertEqual(request.method, "GET")
                self.assertEqual(request.url.params["baseCurrency"], "USD")
                self.assertEqual(request.url.params["quoteCurrency"], "KRW")
                self.assertNotIn(self.raw_token, repr(request))
                return httpx.Response(
                    200,
                    json={
                        "result": {
                            "baseCurrency": "USD",
                            "quoteCurrency": "KRW",
                            "rate": "1375.25",
                            "midRate": "1370.00",
                            "basisPoint": "38.3211678832",
                            "rateChangeType": "UP",
                            "validFrom": "2026-06-25T00:00:00Z",
                            "validUntil": "2026-06-25T00:05:00Z",
                        }
                    },
                    request=request,
                )
            raise AssertionError(f"unexpected endpoint: {request.url.path}")

        http_client = self.make_client(handler)
        result = execute_readonly_exchange_rate_smoke(
            http_client,
            OAuthTokenRequest(
                client_id="synthetic-client-id",
                client_secret="synthetic-client-secret",
            ),
            RecordingSafetyGate(self.events),
            allow_live_api=True,
            allow_real_order=False,
            dry_run_only=True,
            read_only_live_smoke_allowed=True,
        )

        self.assertEqual(self.events, ["oauth", "safety_gate", "exchange_rate"])
        self.assertTrue(result.success)
        self.assertEqual(result.http_status_code, 200)
        self.assertEqual(result.token_type, "Bearer")
        self.assertEqual(result.expires_in, 3600)
        self.assertIsNotNone(result.exchange_rate)
        assert result.exchange_rate is not None
        self.assertEqual(result.exchange_rate.base_currency, "USD")
        self.assertEqual(result.exchange_rate.quote_currency, "KRW")
        self.assertEqual(str(result.exchange_rate.rate), "1375.25")
        self.assertEqual(str(result.exchange_rate.mid_rate), "1370.00")
        self.assertEqual(str(result.exchange_rate.basis_point), "38.3211678832")
        self.assertEqual(result.exchange_rate.rate_change_type, "UP")
        self.assertTrue(result.safe_dict()["mid_rate_present"])
        self.assertTrue(result.safe_dict()["basis_point_present"])
        self.assertTrue(result.safe_dict()["rate_change_type_present"])
        self.assertNotIn(self.raw_token, repr(result))

    def test_explicit_smoke_approval_is_required_before_transport(self) -> None:
        called = False

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal called
            called = True
            raise AssertionError(f"unexpected request: {request.url}")

        client = self.make_client(handler)
        with self.assertRaises(ReadOnlySmokeFailure) as caught:
            TossReadOnlySmokeClient(
                client,
                LiveApiSafetyGate(),
                allow_live_api=True,
                allow_real_order=False,
                dry_run_only=True,
                read_only_live_smoke_allowed=False,
            ).get_exchange_rate_once(OAuthTokenResponse(access_token=self.raw_token))

        self.assertFalse(called)
        self.assertEqual(
            caught.exception.diagnostic.phase,
            ReadOnlySmokePhase.CONFIG_VALIDATION,
        )

    def test_oauth_401_preserves_safe_phase_and_status(self) -> None:
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            return httpx.Response(
                401,
                json={"error": {"code": "INVALID_CLIENT", "message": self.raw_token}},
                request=request,
            )

        result = self._execute(self.make_client(handler))

        self.assertFalse(result.success)
        self.assertEqual(result.phase, ReadOnlySmokePhase.OAUTH_TOKEN)
        self.assertEqual(result.http_status_code, 401)
        self.assertEqual(result.safe_error_type, "http_unauthorized")
        self.assertEqual(result.safe_error_message, "HTTP 401 unauthorized.")
        self.assertEqual(calls, [OAUTH_TOKEN_PATH])
        self._assert_no_sensitive_diagnostic(result)

    def test_exchange_rate_403_preserves_safe_phase_and_status(self) -> None:
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path == OAUTH_TOKEN_PATH:
                return self._token_response(request)
            return httpx.Response(
                403,
                json={"error": {"code": "FORBIDDEN", "message": self.raw_token}},
                request=request,
            )

        result = self._execute(self.make_client(handler))

        self.assertFalse(result.success)
        self.assertEqual(result.phase, ReadOnlySmokePhase.READONLY_EXCHANGE_RATE)
        self.assertEqual(result.http_status_code, 403)
        self.assertEqual(result.safe_error_type, "http_forbidden")
        self.assertEqual(
            calls,
            [OAUTH_TOKEN_PATH, EXCHANGE_RATE_PATH],
        )
        self._assert_no_sensitive_diagnostic(result)

    def test_exchange_rate_404_preserves_safe_status(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            if request.url.path == OAUTH_TOKEN_PATH:
                return self._token_response(request)
            return httpx.Response(404, json={"error": {}}, request=request)

        result = self._execute(self.make_client(handler))

        self.assertEqual(result.phase, ReadOnlySmokePhase.READONLY_EXCHANGE_RATE)
        self.assertEqual(result.http_status_code, 404)
        self.assertEqual(result.safe_error_type, "http_not_found")
        self.assertEqual(result.safe_error_message, "HTTP 404 not found.")

    def test_response_parse_failure_has_safe_phase(self) -> None:
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path == OAUTH_TOKEN_PATH:
                return self._token_response(request)
            return httpx.Response(
                200,
                json={"result": {"baseCurrency": "USD"}},
                request=request,
            )

        result = self._execute(self.make_client(handler))

        self.assertFalse(result.success)
        self.assertEqual(result.phase, ReadOnlySmokePhase.RESPONSE_PARSE)
        self.assertEqual(result.http_status_code, 200)
        self.assertEqual(result.safe_error_type, "response_parse_failed")
        self.assertEqual(result.safe_error_message, "Response parse failed.")
        self.assertEqual(calls, [OAUTH_TOKEN_PATH, EXCHANGE_RATE_PATH])
        self._assert_no_sensitive_diagnostic(result)

    def test_pending_endpoint_is_blocked_by_safety_gate(self) -> None:
        decision = LiveApiSafetyGate().evaluate(
            TossEndpointMetadata(
                method="GET",
                path="/api/v1/prices",
                endpoint_category="market_data",
                requires_auth=True,
                requires_account_seq=False,
            ),
            live_api_enabled=True,
            real_order_allowed=False,
            dry_run_only=True,
        )

        self.assertTrue(decision.allowed)

        pending = LiveApiSafetyGate().evaluate(
            TossEndpointMetadata(
                method="GET",
                path="/api/v1/orderbook",
                endpoint_category="market_data",
                requires_auth=True,
                requires_account_seq=False,
            ),
            live_api_enabled=True,
            real_order_allowed=False,
            dry_run_only=True,
        )
        self.assertFalse(pending.allowed)

    def test_account_scoped_and_order_metadata_remain_blocked(self) -> None:
        gate = LiveApiSafetyGate()
        account = gate.evaluate(
            TossEndpointMetadata(
                method="GET",
                path="/api/v1/holdings",
                endpoint_category="asset",
                requires_auth=True,
                requires_account_seq=True,
            ),
            live_api_enabled=True,
            real_order_allowed=False,
            dry_run_only=True,
        )
        order = gate.evaluate(
            TossEndpointMetadata(
                method="POST",
                path="/api/v1/orders",
                endpoint_category="order",
                requires_auth=True,
                requires_account_seq=True,
            ),
            live_api_enabled=True,
            real_order_allowed=False,
            dry_run_only=True,
        )

        self.assertFalse(account.allowed)
        self.assertFalse(order.allowed)

    def _execute(
        self,
        client: httpx.Client,
    ):
        return execute_readonly_exchange_rate_smoke(
            client,
            OAuthTokenRequest(
                client_id="synthetic-client-id",
                client_secret="synthetic-client-secret",
            ),
            LiveApiSafetyGate(),
            allow_live_api=True,
            allow_real_order=False,
            dry_run_only=True,
            read_only_live_smoke_allowed=True,
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

    def _assert_no_sensitive_diagnostic(self, result) -> None:
        diagnostic_text = repr(result.safe_dict())
        self.assertNotIn(self.raw_token, diagnostic_text)
        self.assertNotIn("synthetic-client-secret", diagnostic_text)
        self.assertNotIn("Authorization", diagnostic_text)

if __name__ == "__main__":
    unittest.main()
