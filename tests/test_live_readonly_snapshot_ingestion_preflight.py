"""Offline tests for the live read-only snapshot ingestion preflight plan."""

import ast
from pathlib import Path
import socket
import sqlite3
import unittest
from unittest.mock import patch

from ai_stock.risk import LiveApiSafetyGate, TossEndpointMetadata
from ai_stock.services.readonly_snapshot_ingestion_preflight import (
    build_live_readonly_snapshot_ingestion_preflight,
)


class RecordingSafetyGate(LiveApiSafetyGate):
    def __init__(self) -> None:
        self.metadata: list[TossEndpointMetadata] = []

    def evaluate(self, metadata, *args, **kwargs):
        self.metadata.append(metadata)
        return super().evaluate(metadata, *args, **kwargs)


class LiveReadOnlySnapshotIngestionPreflightTests(unittest.TestCase):
    def test_plan_fixes_expected_inputs_and_call_counts(self) -> None:
        plan = build_live_readonly_snapshot_ingestion_preflight()

        self.assertEqual(plan.symbol, "005930")
        self.assertEqual(plan.exchange_rate_pair, "USD/KRW")
        self.assertEqual(plan.candle_interval, "1d")
        self.assertEqual(plan.candle_count, 1)
        self.assertTrue(plan.candle_adjusted)
        self.assertFalse(plan.candle_before_used)
        self.assertEqual(plan.expected_oauth_token_endpoint_calls, 1)
        self.assertEqual(plan.expected_business_api_calls, 4)
        self.assertEqual(plan.expected_total_network_calls, 5)

    def test_plan_allows_only_fixed_read_only_account_free_endpoints(self) -> None:
        plan = build_live_readonly_snapshot_ingestion_preflight()
        endpoints = {
            (endpoint.method, endpoint.path): endpoint
            for endpoint in plan.allowed_business_endpoints
        }

        self.assertEqual(
            set(endpoints),
            {
                ("GET", "/api/v1/stocks"),
                ("GET", "/api/v1/prices"),
                ("GET", "/api/v1/candles"),
                ("GET", "/api/v1/exchange-rate"),
            },
        )
        for endpoint in endpoints.values():
            self.assertTrue(endpoint.is_read_only)
            self.assertTrue(endpoint.requires_auth)
            self.assertFalse(endpoint.requires_account_seq)
        self.assertEqual(
            endpoints[("GET", "/api/v1/stocks")].query,
            (("symbols", "005930"),),
        )
        self.assertEqual(
            endpoints[("GET", "/api/v1/prices")].query,
            (("symbols", "005930"),),
        )
        self.assertEqual(
            endpoints[("GET", "/api/v1/candles")].query,
            (
                ("symbol", "005930"),
                ("interval", "1d"),
                ("count", "1"),
                ("adjusted", "true"),
            ),
        )
        self.assertEqual(
            endpoints[("GET", "/api/v1/exchange-rate")].query,
            (("baseCurrency", "USD"), ("quoteCurrency", "KRW")),
        )

    def test_stock_warnings_and_sensitive_endpoint_groups_are_denied(self) -> None:
        plan = build_live_readonly_snapshot_ingestion_preflight()

        self.assertFalse(plan.stock_warnings_included)
        self.assertTrue(plan.stock_warnings_deferred)
        self.assertIn(
            "GET /api/v1/stocks/{symbol}/warnings",
            plan.denied_endpoints,
        )
        for endpoint in (
            "POST /api/v1/orders",
            "GET /api/v1/orders",
            "GET /api/v1/accounts",
            "GET /api/v1/assets",
            "GET /api/v1/balance",
            "GET /api/v1/fills",
            "PATCH /api/v1/prices",
        ):
            self.assertIn(endpoint, plan.denied_endpoints)
        self.assertFalse(plan.requires_account_seq)
        self.assertFalse(plan.account_seq_used)
        self.assertFalse(plan.real_order_related_call_allowed)

    def test_storage_plan_is_in_memory_without_actual_storage(self) -> None:
        plan = build_live_readonly_snapshot_ingestion_preflight()

        self.assertEqual(plan.storage_mode, "in_memory_sqlite")
        self.assertEqual(plan.storage_connection_target, ":memory:")
        self.assertFalse(plan.actual_db_file_created)
        self.assertFalse(plan.actual_storage_performed)

    def test_preflight_performs_no_network_oauth_env_or_database_io(self) -> None:
        with (
            patch.object(
                socket,
                "socket",
                side_effect=AssertionError("network access is forbidden"),
            ),
            patch.object(
                sqlite3,
                "connect",
                side_effect=AssertionError("database access is forbidden"),
            ),
            patch.object(
                Path,
                "open",
                side_effect=AssertionError("file access is forbidden"),
            ),
        ):
            plan = build_live_readonly_snapshot_ingestion_preflight()

        self.assertTrue(plan.safety_gate_preflight_passed)
        self.assertFalse(plan.actual_network_call_performed)
        self.assertFalse(plan.oauth_token_endpoint_called)
        self.assertFalse(plan.env_file_read)
        self.assertFalse(plan.actual_db_file_created)

    def test_safety_gate_allows_four_candidates_and_blocks_unsafe_metadata(
        self,
    ) -> None:
        gate = RecordingSafetyGate()
        plan = build_live_readonly_snapshot_ingestion_preflight(gate)

        self.assertEqual(len(plan.safety_gate_decisions), 4)
        self.assertTrue(all(item.allowed for item in plan.safety_gate_decisions))
        self.assertTrue(all(item.is_read_only for item in plan.safety_gate_decisions))
        self.assertTrue(
            all(not item.requires_account_seq for item in plan.safety_gate_decisions)
        )
        self.assertEqual(len(gate.metadata), 10)
        denied_metadata = gate.metadata[4:]
        self.assertTrue(any(item.method == "POST" for item in denied_metadata))
        self.assertTrue(any(item.endpoint_category == "mutation" for item in denied_metadata))
        self.assertTrue(any(item.requires_account_seq for item in denied_metadata))

    def test_preflight_source_has_no_client_config_or_storage_imports(self) -> None:
        import ai_stock.services.readonly_snapshot_ingestion_preflight as preflight

        module_path = Path(preflight.__file__)
        source = module_path.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules = {
            alias.name
            for node in ast.walk(tree)
            if isinstance(node, ast.Import)
            for alias in node.names
        }
        imported_modules.update(
            node.module
            for node in ast.walk(tree)
            if isinstance(node, ast.ImportFrom) and node.module is not None
        )

        forbidden_imports = {
            "httpx",
            "requests",
            "urllib.request",
            "sqlite3",
            "ai_stock.clients",
            "ai_stock.config",
            "ai_stock.repositories",
        }
        self.assertTrue(forbidden_imports.isdisjoint(imported_modules))
        self.assertNotIn("load_settings", source)
        self.assertNotIn("os.environ", source)
        self.assertNotIn("create_connection", source)

    def test_preflight_does_not_modify_pyproject_or_create_database_files(self) -> None:
        pyproject = Path("pyproject.toml")
        pyproject_before = pyproject.read_bytes()
        data_existed = Path("data").exists()
        db_files_before = _workspace_db_files()

        plan = build_live_readonly_snapshot_ingestion_preflight()

        self.assertTrue(plan.safety_gate_preflight_passed)
        self.assertEqual(pyproject.read_bytes(), pyproject_before)
        self.assertEqual(Path("data").exists(), data_existed)
        self.assertEqual(_workspace_db_files(), db_files_before)


def _workspace_db_files() -> set[Path]:
    return {
        path
        for pattern in ("*.sqlite", "*.sqlite3", "*.db")
        for path in Path.cwd().glob(pattern)
    }


if __name__ == "__main__":
    unittest.main()
