"""Offline integration tests for the live snapshot file DB smoke."""

from pathlib import Path
import unittest
from uuid import uuid4

import httpx

from ai_stock.models import OAuthTokenRequest
from ai_stock.risk import LiveApiSafetyGate
from ai_stock.storage.live_snapshot_local_db_smoke import (
    execute_live_snapshot_local_db_file_smoke,
)
from ai_stock.storage.local_snapshot_db_smoke import (
    run_fake_snapshot_local_db_file_smoke,
)


class FakeGitInspector:
    def is_tracked(self, path: Path) -> bool:
        return False

    def is_ignored(self, path: Path) -> bool:
        return True

    def directory_has_tracked_files(self, path: Path) -> bool:
        return False


class RejectingGitInspector(FakeGitInspector):
    def is_tracked(self, path: Path) -> bool:
        return True


class LiveSnapshotLocalDbFileSmokeTests(unittest.TestCase):
    client_id = "fake-client-id"
    client_secret = "fake-client-secret"
    raw_token = "fake-access-token-value"

    def setUp(self) -> None:
        self.path = Path("tests") / f"_ms0609_{uuid4().hex}.sqlite3"
        run_fake_snapshot_local_db_file_smoke(
            self.path,
            git_inspector=FakeGitInspector(),
        )

    def tearDown(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def test_success_appends_three_rows_and_upserts_stock(self) -> None:
        calls: list[tuple[str, str]] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append((request.method, request.url.path))
            return self._response(request)

        result = self._execute(self._client(handler))

        self.assertTrue(result.success)
        self.assertEqual(result.phase, "live_snapshot_local_db_file_smoke")
        self.assertEqual(result.oauth_token_endpoint_call_count, 1)
        self.assertEqual(result.business_api_call_count, 4)
        self.assertEqual(result.total_network_call_count, 5)
        self.assertEqual(result.repository_counts_before.stocks, 1)
        self.assertEqual(result.repository_counts_after.stocks, 1)
        self.assertEqual(result.repository_counts_before.price_snapshots, 1)
        self.assertEqual(result.repository_counts_after.price_snapshots, 2)
        self.assertEqual(result.repository_counts_before.candles, 1)
        self.assertEqual(result.repository_counts_after.candles, 2)
        self.assertEqual(result.repository_counts_before.exchange_rates, 1)
        self.assertEqual(result.repository_counts_after.exchange_rates, 2)
        self.assertTrue(result.repository_round_trip_verified)
        self.assertTrue(result.decimal_values_preserved)
        self.assertTrue(result.timestamp_values_preserved)
        self.assertTrue(result.actual_db_file_modified_this_stage)
        self.assertEqual(
            calls,
            [
                ("POST", "/oauth2/token"),
                ("GET", "/api/v1/stocks"),
                ("GET", "/api/v1/prices"),
                ("GET", "/api/v1/candles"),
                ("GET", "/api/v1/exchange-rate"),
            ],
        )

    def test_queries_exclude_before_warnings_and_account_header(self) -> None:
        queries: dict[str, dict[str, str]] = {}

        def handler(request: httpx.Request) -> httpx.Response:
            if request.method == "GET":
                queries[request.url.path] = dict(request.url.params)
                self.assertNotIn("X-Tossinvest-Account", request.headers)
            return self._response(request)

        result = self._execute(self._client(handler))

        self.assertTrue(result.success)
        self.assertEqual(queries["/api/v1/stocks"], {"symbols": "005930"})
        self.assertEqual(queries["/api/v1/prices"], {"symbols": "005930"})
        self.assertEqual(
            queries["/api/v1/candles"],
            {
                "symbol": "005930",
                "interval": "1d",
                "count": "1",
                "adjusted": "true",
            },
        )
        self.assertNotIn("before", queries["/api/v1/candles"])
        self.assertNotIn("/api/v1/stocks/005930/warnings", queries)

    def test_safe_diagnostic_excludes_secret_values(self) -> None:
        result = self._execute(self._client(self._response))
        text = repr(result.safe_dict())

        self.assertTrue(result.success)
        self.assertNotIn(self.client_id, text)
        self.assertNotIn(self.client_secret, text)
        self.assertNotIn(self.raw_token, text)
        self.assertFalse(result.token_raw_output_or_storage)
        self.assertFalse(result.credential_raw_output_or_storage)
        self.assertFalse(result.authorization_bearer_raw_output_or_storage)
        self.assertFalse(result.raw_response_body_stored)

    def test_failure_stops_without_retry_and_does_not_write(self) -> None:
        before = self.path.stat()
        calls: list[str] = []

        def handler(request: httpx.Request) -> httpx.Response:
            calls.append(request.url.path)
            if request.url.path == "/oauth2/token":
                return self._response(request)
            return httpx.Response(
                500,
                json={"error": {"code": "server-error", "message": "safe"}},
                request=request,
            )

        result = self._execute(self._client(handler))
        after = self.path.stat()

        self.assertFalse(result.success)
        self.assertEqual(calls, ["/oauth2/token", "/api/v1/stocks"])
        self.assertFalse(result.db_write_performed)
        self.assertFalse(result.actual_db_file_modified_this_stage)
        self.assertEqual(after.st_size, before.st_size)
        self.assertEqual(after.st_mtime_ns, before.st_mtime_ns)

    def test_unsafe_config_or_git_state_performs_no_network(self) -> None:
        for approved, inspector in (
            (False, FakeGitInspector()),
            (True, RejectingGitInspector()),
        ):
            calls: list[str] = []

            def handler(request: httpx.Request) -> httpx.Response:
                calls.append(request.url.path)
                raise AssertionError("Network must remain unused.")

            result = self._execute(
                self._client(handler),
                approved=approved,
                inspector=inspector,
            )

            self.assertFalse(result.success)
            self.assertEqual(calls, [])
            self.assertFalse(result.db_write_performed)

    def test_script_fixes_target_and_has_no_retry_loop(self) -> None:
        source = Path("scripts/live_snapshot_local_db_file_smoke.py").read_text(
            encoding="utf-8"
        )

        self.assertIn("PLANNED_DB_RELATIVE_PATH", source)
        self.assertNotIn("argparse", source)
        self.assertNotIn("retry", source.casefold())
        self.assertNotIn("while ", source)

    def _execute(
        self,
        client: httpx.Client,
        *,
        approved: bool = True,
        inspector: FakeGitInspector | None = None,
    ):
        return execute_live_snapshot_local_db_file_smoke(
            client,
            OAuthTokenRequest(
                client_id=self.client_id,
                client_secret=self.client_secret,
            ),
            LiveApiSafetyGate(),
            self.path,
            allow_live_api=True,
            allow_real_order=False,
            dry_run_only=True,
            live_file_smoke_allowed=approved,
            git_inspector=inspector or FakeGitInspector(),
        )

    def _client(self, handler) -> httpx.Client:
        return httpx.Client(
            base_url="https://example.invalid",
            transport=httpx.MockTransport(handler),
            follow_redirects=False,
        )

    def _response(self, request: httpx.Request) -> httpx.Response:
        payloads = {
            "/oauth2/token": {
                "access_token": self.raw_token,
                "token_type": "Bearer",
                "expires_in": 3600,
            },
            "/api/v1/stocks": {
                "result": [
                    {
                        "symbol": "005930",
                        "name": "Live Test",
                        "englishName": "LIVE TEST",
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
            "/api/v1/prices": {
                "result": [
                    {
                        "symbol": "005930",
                        "lastPrice": "72000.25",
                        "currency": "KRW",
                        "timestamp": "2026-06-30T09:00:00+09:00",
                    }
                ]
            },
            "/api/v1/candles": {
                "result": {
                    "candles": [
                        {
                            "timestamp": "2026-06-30T00:00:00+09:00",
                            "openPrice": "71000",
                            "highPrice": "72500",
                            "lowPrice": "70500",
                            "closePrice": "72000",
                            "volume": "1000000",
                            "currency": "KRW",
                        }
                    ],
                    "nextBefore": None,
                }
            },
            "/api/v1/exchange-rate": {
                "result": {
                    "baseCurrency": "USD",
                    "quoteCurrency": "KRW",
                    "rate": "1380.25",
                    "midRate": "1375.00",
                    "basisPoint": "38.1818181818",
                    "rateChangeType": "UP",
                    "validFrom": "2026-06-30T00:00:00Z",
                    "validUntil": "2026-06-30T00:05:00Z",
                }
            },
        }
        return httpx.Response(200, json=payloads[request.url.path], request=request)


if __name__ == "__main__":
    unittest.main()
