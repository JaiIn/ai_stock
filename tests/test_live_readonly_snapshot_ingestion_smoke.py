"""Offline contract tests for the five-call live ingestion smoke path."""

from pathlib import Path
import unittest
from unittest.mock import patch

import httpx

from ai_stock.models import OAuthTokenRequest
from ai_stock.risk import LiveApiSafetyGate, TossEndpointMetadata
from ai_stock.services.live_readonly_snapshot_ingestion_smoke import (
    CANDLES_PATH,
    EXCHANGE_RATE_PATH,
    PRICES_PATH,
    STOCKS_PATH,
    LiveSnapshotIngestionPhase,
    execute_live_readonly_snapshot_ingestion_smoke,
)


class RecordingSafetyGate(LiveApiSafetyGate):
    def __init__(self) -> None:
        self.metadata: list[TossEndpointMetadata] = []

    def evaluate(self, metadata, *args, **kwargs):
        self.metadata.append(metadata)
        return super().evaluate(metadata, *args, **kwargs)


class LiveReadOnlySnapshotIngestionSmokeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.raw_token = "synthetic-live-ingestion-token"
        self.client_id = "synthetic-live-client-id"
        self.client_secret = "synthetic-live-client-secret"

    def make_client(self, handler) -> httpx.Client:
        client = httpx.Client(
            base_url="https://openapi.tossinvest.com",
            transport=httpx.MockTransport(handler),
            follow_redirects=False,
        )
        self.addCleanup(client.close)
        return client

    def test_success_runs_exactly_five_calls_and_round_trips_models(self) -> None:
        calls: list[tuple[str, str]] = []
        gate = RecordingSafetyGate()

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append((request.method, request.url.path))
            self._assert_business_request_safety(request)
            return self._response_for(request)

        result = self._execute(self.make_client(handler), gate=gate)

        self.assertTrue(result.success)
        self.assertEqual(result.phase, LiveSnapshotIngestionPhase.COMPLETE)
        self.assertEqual(
            calls,
            [
                ("POST", "/oauth2/token"),
                ("GET", STOCKS_PATH),
                ("GET", PRICES_PATH),
                ("GET", CANDLES_PATH),
                ("GET", EXCHANGE_RATE_PATH),
            ],
        )
        self.assertEqual(result.oauth_token_endpoint_call_count, 1)
        self.assertEqual(result.business_api_call_count, 4)
        self.assertEqual(result.total_network_call_count, 5)
        self.assertEqual(result.saved_stock_count, 1)
        self.assertEqual(result.saved_price_snapshot_count, 1)
        self.assertEqual(result.saved_candle_count, 1)
        self.assertEqual(result.saved_exchange_rate_count, 1)
        self.assertTrue(result.repository_round_trip_verified)
        self.assertTrue(result.decimal_values_preserved)
        self.assertTrue(result.timestamp_values_preserved)
        self.assertTrue(result.currency_fields_present)
        self.assertTrue(result.candle_ohlcv_present)
        self.assertTrue(result.stock_warnings_deferred)
        self.assertFalse(result.actual_db_file_created)
        self.assertFalse(result.account_seq_used)
        self.assertFalse(result.real_order_related_call_performed)
        self.assertEqual(len(gate.metadata), 4)
        self.assertTrue(all(item.method == "GET" for item in gate.metadata))
        self.assertTrue(all(item.requires_auth for item in gate.metadata))
        self.assertTrue(
            all(not item.requires_account_seq for item in gate.metadata)
        )

    def test_fixed_queries_exclude_before_and_stock_warnings(self) -> None:
        seen_queries: dict[str, dict[str, str]] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                seen_queries[request.url.path] = dict(request.url.params)
            return self._response_for(request)

        result = self._execute(self.make_client(handler))

        self.assertTrue(result.success)
        self.assertEqual(seen_queries[STOCKS_PATH], {"symbols": "005930"})
        self.assertEqual(seen_queries[PRICES_PATH], {"symbols": "005930"})
        self.assertEqual(
            seen_queries[CANDLES_PATH],
            {
                "symbol": "005930",
                "interval": "1d",
                "count": "1",
                "adjusted": "true",
            },
        )
        self.assertNotIn("before", seen_queries[CANDLES_PATH])
        self.assertEqual(
            seen_queries[EXCHANGE_RATE_PATH],
            {"baseCurrency": "USD", "quoteCurrency": "KRW"},
        )
        self.assertNotIn("/api/v1/stocks/005930/warnings", seen_queries)

    def test_endpoint_statuses_and_safe_diagnostics_exclude_secrets(self) -> None:
        result = self._execute(self.make_client(self._response_for))
        safe = result.safe_dict()
        text = repr(safe)

        self.assertEqual(
            safe["endpoint_http_status_codes"],
            {
                "POST /oauth2/token": 200,
                "GET /api/v1/stocks": 200,
                "GET /api/v1/prices": 200,
                "GET /api/v1/candles": 200,
                "GET /api/v1/exchange-rate": 200,
            },
        )
        self.assertNotIn(self.raw_token, text)
        self.assertNotIn(self.client_id, text)
        self.assertNotIn(self.client_secret, text)
        self.assertFalse(result.token_raw_output_or_storage)
        self.assertFalse(result.credential_raw_output_or_storage)
        self.assertFalse(result.authorization_bearer_raw_output_or_storage)
        self.assertFalse(result.raw_response_body_stored)

    def test_failure_stops_without_retry_or_later_business_calls(self) -> None:
        calls: list[tuple[str, str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append((request.method, request.url.path))
            if request.url.path == "/oauth2/token":
                return self._oauth_response(request)
            return httpx.Response(
                500,
                json={
                    "error": {
                        "requestId": "safe-request-id",
                        "code": "server-error",
                        "message": self.raw_token,
                    }
                },
                request=request,
            )

        result = self._execute(self.make_client(handler))

        self.assertFalse(result.success)
        self.assertEqual(result.phase, LiveSnapshotIngestionPhase.STOCKS)
        self.assertEqual(result.failed_endpoint, "GET /api/v1/stocks")
        self.assertEqual(result.safe_error_code, "server-error")
        self.assertEqual(result.safe_error_type, "server_error")
        self.assertEqual(result.oauth_token_endpoint_call_count, 1)
        self.assertEqual(result.business_api_call_count, 1)
        self.assertEqual(result.total_network_call_count, 2)
        self.assertEqual(
            calls,
            [
                ("POST", "/oauth2/token"),
                ("GET", "/api/v1/stocks"),
            ],
        )
        self.assertNotIn(self.raw_token, repr(result.safe_dict()))

    def test_unsafe_configuration_performs_no_network_or_storage(self) -> None:
        for allow_live_api, allow_real_order, dry_run_only, approved in (
            (False, False, True, True),
            (True, True, True, True),
            (True, False, False, True),
            (True, False, True, False),
        ):
            calls: list[str] = []

            def handler(request: httpx.Request) -> httpx.Response:
                calls.append(request.url.path)
                raise AssertionError("No request is allowed.")

            with self.subTest(
                allow_live_api=allow_live_api,
                allow_real_order=allow_real_order,
                dry_run_only=dry_run_only,
                approved=approved,
            ):
                result = execute_live_readonly_snapshot_ingestion_smoke(
                    self.make_client(handler),
                    self._oauth_request(),
                    LiveApiSafetyGate(),
                    allow_live_api=allow_live_api,
                    allow_real_order=allow_real_order,
                    dry_run_only=dry_run_only,
                    live_ingestion_smoke_allowed=approved,
                )
                self.assertFalse(result.success)
                self.assertEqual(result.total_network_call_count, 0)
                self.assertEqual(calls, [])

    def test_only_memory_connection_is_created(self) -> None:
        import ai_stock.services.live_readonly_snapshot_ingestion_smoke as smoke

        real_create_connection = smoke.create_connection
        targets: list[str] = []

        def recording_create_connection(database_path):
            targets.append(database_path)
            return real_create_connection(database_path)

        with patch.object(
            smoke,
            "create_connection",
            side_effect=recording_create_connection,
        ):
            result = self._execute(self.make_client(self._response_for))

        self.assertTrue(result.success)
        self.assertEqual(targets, [":memory:"])
        self.assertFalse(result.actual_db_file_created)

    def test_smoke_creates_no_db_file_and_does_not_modify_pyproject(self) -> None:
        pyproject = Path("pyproject.toml")
        pyproject_before = pyproject.read_bytes()
        data_existed = Path("data").exists()
        db_files_before = _workspace_db_files()

        result = self._execute(self.make_client(self._response_for))

        self.assertTrue(result.success)
        self.assertEqual(pyproject.read_bytes(), pyproject_before)
        self.assertEqual(Path("data").exists(), data_existed)
        self.assertEqual(_workspace_db_files(), db_files_before)

    def _execute(
        self,
        client: httpx.Client,
        *,
        gate: LiveApiSafetyGate | None = None,
    ):
        return execute_live_readonly_snapshot_ingestion_smoke(
            client,
            self._oauth_request(),
            gate or LiveApiSafetyGate(),
            allow_live_api=True,
            allow_real_order=False,
            dry_run_only=True,
            live_ingestion_smoke_allowed=True,
        )

    def _oauth_request(self) -> OAuthTokenRequest:
        return OAuthTokenRequest(
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

    def _assert_business_request_safety(self, request: httpx.Request) -> None:
        if request.url.path == "/oauth2/token":
            return
        self.assertEqual(request.method, "GET")
        self.assertNotIn("X-Tossinvest-Account", request.headers)
        self.assertEqual(
            request.headers.get("Authorization"),
            f"Bearer {self.raw_token}",
        )

    def _response_for(self, request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path == "/oauth2/token":
            return self._oauth_response(request)
        if path == STOCKS_PATH:
            return httpx.Response(
                200,
                json={
                    "result": [
                        {
                            "symbol": "005930",
                            "name": "Test Stock",
                            "englishName": "TEST STOCK",
                            "isinCode": "FAKE-ISIN",
                            "market": "KOSPI",
                            "securityType": "STOCK",
                            "isCommonShare": True,
                            "status": "ACTIVE",
                            "currency": "KRW",
                            "sharesOutstanding": "5919637922",
                        }
                    ]
                },
                request=request,
            )
        if path == PRICES_PATH:
            return httpx.Response(
                200,
                json={
                    "result": [
                        {
                            "symbol": "005930",
                            "lastPrice": "70123.45",
                            "currency": "KRW",
                            "timestamp": "2026-06-29T09:00:00+09:00",
                        }
                    ]
                },
                request=request,
            )
        if path == CANDLES_PATH:
            return httpx.Response(
                200,
                json={
                    "result": {
                        "candles": [
                            {
                                "timestamp": "2026-06-29T00:00:00+09:00",
                                "openPrice": "70000.00",
                                "highPrice": "71000.10",
                                "lowPrice": "69900.20",
                                "closePrice": "70500.30",
                                "volume": "1234567",
                                "currency": "KRW",
                            }
                        ],
                        "nextBefore": None,
                    }
                },
                request=request,
            )
        if path == EXCHANGE_RATE_PATH:
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
                        "validFrom": "2026-06-29T00:00:00Z",
                        "validUntil": "2026-06-29T00:05:00Z",
                    }
                },
                request=request,
            )
        raise AssertionError(f"Unexpected endpoint: {path}")

    def _oauth_response(self, request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "access_token": self.raw_token,
                "token_type": "Bearer",
                "expires_in": 3600,
            },
            request=request,
        )


def _workspace_db_files() -> set[Path]:
    return {
        path
        for pattern in ("*.sqlite", "*.sqlite3", "*.db")
        for path in Path.cwd().glob(pattern)
    }


if __name__ == "__main__":
    unittest.main()
