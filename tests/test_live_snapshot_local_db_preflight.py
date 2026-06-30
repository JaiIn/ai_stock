"""Offline tests for the live snapshot local SQLite file preflight."""

import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import socket
import sqlite3
import unittest
from unittest.mock import patch

from ai_stock.storage.live_snapshot_local_db_preflight import (
    REQUIRED_IGNORE_PATTERNS,
    build_live_snapshot_local_db_preflight,
    validate_live_snapshot_local_db_preflight,
)


class LiveSnapshotLocalDbPreflightTests(unittest.TestCase):
    def test_plan_fixes_path_and_stage_safety_flags(self) -> None:
        plan = build_live_snapshot_local_db_preflight()

        self.assertEqual(plan.stage, "MS-06.08")
        self.assertEqual(
            plan.planned_db_relative_path,
            "data/local/ai_stock.sqlite3",
        )
        self.assertFalse(plan.db_file_write_allowed_this_stage)
        self.assertFalse(plan.actual_db_file_modified_this_stage)
        self.assertTrue(plan.existing_db_file_allowed)
        self.assertFalse(plan.db_file_git_tracked_allowed)
        self.assertFalse(plan.data_directory_git_tracked_allowed)
        self.assertFalse(plan.api_call_allowed_this_stage)
        self.assertFalse(plan.oauth_token_endpoint_allowed_this_stage)
        self.assertFalse(plan.live_smoke_execution_allowed_this_stage)
        self.assertFalse(plan.env_file_read_allowed_this_stage)
        self.assertFalse(plan.credential_required_this_stage)
        self.assertEqual(
            plan.next_stage_credential_source,
            "existing .env.local only",
        )
        self.assertFalse(plan.account_seq_allowed)
        self.assertFalse(plan.real_order_related_call_allowed)
        self.assertFalse(plan.stock_warnings_included)
        self.assertTrue(plan.stock_warnings_deferred)

    def test_plan_is_immutable(self) -> None:
        plan = build_live_snapshot_local_db_preflight()

        with self.assertRaises(FrozenInstanceError):
            plan.existing_db_file_allowed = False  # type: ignore[misc]

    def test_next_stage_call_scope_is_fixed(self) -> None:
        plan = build_live_snapshot_local_db_preflight()
        endpoints = {
            (endpoint.method, endpoint.path): endpoint
            for endpoint in plan.allowed_business_endpoints
        }

        self.assertEqual(plan.expected_oauth_token_endpoint_calls, 1)
        self.assertEqual(plan.expected_business_api_calls, 4)
        self.assertEqual(plan.expected_total_network_calls, 5)
        self.assertEqual(
            set(endpoints),
            {
                ("GET", "/api/v1/stocks"),
                ("GET", "/api/v1/prices"),
                ("GET", "/api/v1/candles"),
                ("GET", "/api/v1/exchange-rate"),
            },
        )
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
        for endpoint in endpoints.values():
            self.assertTrue(endpoint.is_read_only)
            self.assertTrue(endpoint.requires_auth)
            self.assertFalse(endpoint.requires_account_seq)

    def test_denied_endpoint_and_stock_warning_policy_is_fixed(self) -> None:
        plan = build_live_snapshot_local_db_preflight()

        for endpoint in (
            "GET /api/v1/stocks/{symbol}/warnings",
            "POST /api/v1/orders",
            "GET /api/v1/orders",
            "GET /api/v1/accounts",
            "GET /api/v1/assets",
            "GET /api/v1/balance",
            "GET /api/v1/fills",
            "PATCH /api/v1/prices",
        ):
            self.assertIn(endpoint, plan.denied_endpoints)
        self.assertFalse(plan.stock_warnings_included)
        self.assertTrue(plan.stock_warnings_deferred)

    def test_append_upsert_policy_preserves_existing_database(self) -> None:
        policy = build_live_snapshot_local_db_preflight().append_upsert_policy

        self.assertTrue(policy.schema_initialization_idempotent_required)
        self.assertFalse(policy.existing_db_delete_allowed)
        self.assertFalse(policy.existing_db_overwrite_allowed)
        self.assertEqual(policy.stock_info_write_mode, "upsert")
        self.assertEqual(policy.price_snapshot_write_mode, "insert")
        self.assertEqual(policy.candle_write_mode, "insert")
        self.assertEqual(policy.exchange_rate_write_mode, "insert")
        self.assertEqual(
            policy.post_write_verification,
            "repository_count_delta_or_minimum_presence_and_timestamp",
        )
        self.assertFalse(policy.raw_response_body_storage_allowed)
        self.assertFalse(policy.credential_storage_allowed)
        self.assertFalse(policy.access_token_storage_allowed)
        self.assertFalse(policy.authorization_header_storage_allowed)
        self.assertFalse(policy.db_content_dump_allowed)

    def test_validation_accepts_existing_or_absent_untracked_database(self) -> None:
        plan = build_live_snapshot_local_db_preflight()

        for observed_exists in (False, True):
            with self.subTest(observed_exists=observed_exists):
                result = validate_live_snapshot_local_db_preflight(
                    plan,
                    observed_ignore_patterns=REQUIRED_IGNORE_PATTERNS,
                    observed_db_file_exists=observed_exists,
                    observed_db_file_modified_this_stage=False,
                    observed_db_file_git_tracked=False,
                    observed_data_directory_git_tracked=False,
                )

                self.assertTrue(result.existing_db_state_allowed)
                self.assertTrue(result.db_write_disabled_this_stage)
                self.assertTrue(result.db_file_unmodified_this_stage)
                self.assertTrue(result.git_tracking_policy_satisfied)
                self.assertTrue(result.git_ignore_policy_satisfied)
                self.assertTrue(result.preflight_contract_valid)
                self.assertTrue(result.ready_for_separately_approved_next_stage)
                self.assertEqual(result.observed_db_file_exists, observed_exists)

    def test_validation_blocks_modification_tracking_and_missing_ignore(self) -> None:
        plan = build_live_snapshot_local_db_preflight()
        cases = (
            {
                "observed_db_file_modified_this_stage": True,
                "observed_db_file_git_tracked": False,
                "observed_data_directory_git_tracked": False,
                "patterns": REQUIRED_IGNORE_PATTERNS,
            },
            {
                "observed_db_file_modified_this_stage": False,
                "observed_db_file_git_tracked": True,
                "observed_data_directory_git_tracked": False,
                "patterns": REQUIRED_IGNORE_PATTERNS,
            },
            {
                "observed_db_file_modified_this_stage": False,
                "observed_db_file_git_tracked": False,
                "observed_data_directory_git_tracked": True,
                "patterns": REQUIRED_IGNORE_PATTERNS,
            },
            {
                "observed_db_file_modified_this_stage": False,
                "observed_db_file_git_tracked": False,
                "observed_data_directory_git_tracked": False,
                "patterns": ("*.sqlite", "*.sqlite3", "*.db"),
            },
        )

        for case in cases:
            with self.subTest(case=case):
                result = validate_live_snapshot_local_db_preflight(
                    plan,
                    observed_ignore_patterns=case["patterns"],
                    observed_db_file_exists=True,
                    observed_db_file_modified_this_stage=case[
                        "observed_db_file_modified_this_stage"
                    ],
                    observed_db_file_git_tracked=case[
                        "observed_db_file_git_tracked"
                    ],
                    observed_data_directory_git_tracked=case[
                        "observed_data_directory_git_tracked"
                    ],
                )

                self.assertFalse(result.preflight_contract_valid)
                self.assertFalse(result.ready_for_separately_approved_next_stage)

    def test_validation_blocks_changed_plan_permissions_or_call_scope(self) -> None:
        plan = build_live_snapshot_local_db_preflight()
        unsafe_plans = (
            replace(plan, db_file_write_allowed_this_stage=True),
            replace(plan, actual_db_file_modified_this_stage=True),
            replace(plan, api_call_allowed_this_stage=True),
            replace(plan, oauth_token_endpoint_allowed_this_stage=True),
            replace(plan, env_file_read_allowed_this_stage=True),
            replace(plan, credential_required_this_stage=True),
            replace(plan, account_seq_allowed=True),
            replace(plan, real_order_related_call_allowed=True),
            replace(plan, expected_total_network_calls=6),
        )

        for unsafe_plan in unsafe_plans:
            with self.subTest(unsafe_plan=unsafe_plan):
                result = validate_live_snapshot_local_db_preflight(
                    unsafe_plan,
                    observed_ignore_patterns=REQUIRED_IGNORE_PATTERNS,
                    observed_db_file_exists=True,
                    observed_db_file_modified_this_stage=False,
                    observed_db_file_git_tracked=False,
                    observed_data_directory_git_tracked=False,
                )

                self.assertFalse(result.preflight_contract_valid)

    def test_repository_ignore_rules_satisfy_policy(self) -> None:
        patterns = {
            line.strip()
            for line in Path(".gitignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }
        plan = build_live_snapshot_local_db_preflight()
        result = validate_live_snapshot_local_db_preflight(
            plan,
            observed_ignore_patterns=patterns,
            observed_db_file_exists=True,
            observed_db_file_modified_this_stage=False,
            observed_db_file_git_tracked=False,
            observed_data_directory_git_tracked=False,
        )

        self.assertIn(".env.local", patterns)
        for required_pattern in REQUIRED_IGNORE_PATTERNS:
            self.assertIn(required_pattern, patterns)
        self.assertEqual(result.missing_ignore_patterns, ())
        self.assertTrue(result.git_ignore_policy_satisfied)
        self.assertTrue(result.preflight_contract_valid)

    def test_builder_and_validator_perform_no_network_env_or_database_io(
        self,
    ) -> None:
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
            patch(
                "builtins.open",
                side_effect=AssertionError("file access is forbidden"),
            ),
            patch.object(
                Path,
                "touch",
                side_effect=AssertionError("file modification is forbidden"),
            ),
            patch.object(
                Path,
                "write_bytes",
                side_effect=AssertionError("file modification is forbidden"),
            ),
            patch.object(
                Path,
                "write_text",
                side_effect=AssertionError("file modification is forbidden"),
            ),
        ):
            plan = build_live_snapshot_local_db_preflight()
            result = validate_live_snapshot_local_db_preflight(
                plan,
                observed_ignore_patterns=REQUIRED_IGNORE_PATTERNS,
                observed_db_file_exists=True,
                observed_db_file_modified_this_stage=False,
                observed_db_file_git_tracked=False,
                observed_data_directory_git_tracked=False,
            )

        self.assertTrue(result.preflight_contract_valid)

    def test_module_has_no_live_client_config_repository_or_sqlite_path(
        self,
    ) -> None:
        import ai_stock.storage.live_snapshot_local_db_preflight as preflight

        source = Path(preflight.__file__).read_text(encoding="utf-8")
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
            "socket",
            "sqlite3",
            "ai_stock.clients",
            "ai_stock.config",
            "ai_stock.repositories",
        }
        self.assertTrue(forbidden_imports.isdisjoint(imported_modules))
        for forbidden_call in (
            "load_settings",
            "os.environ",
            "create_connection",
            "initialize_schema",
            "sqlite3.connect",
            ".open(",
            ".touch(",
            ".write_bytes(",
            ".write_text(",
        ):
            self.assertNotIn(forbidden_call, source)

    def test_preflight_preserves_workspace_db_and_pyproject_metadata(self) -> None:
        target = Path("data/local/ai_stock.sqlite3")
        before_exists = target.exists()
        before_stat = target.stat() if before_exists else None
        pyproject = Path("pyproject.toml")
        pyproject_before = pyproject.read_bytes()

        plan = build_live_snapshot_local_db_preflight()
        result = validate_live_snapshot_local_db_preflight(
            plan,
            observed_ignore_patterns=REQUIRED_IGNORE_PATTERNS,
            observed_db_file_exists=before_exists,
            observed_db_file_modified_this_stage=False,
            observed_db_file_git_tracked=False,
            observed_data_directory_git_tracked=False,
        )

        after_exists = target.exists()
        after_stat = target.stat() if after_exists else None
        self.assertTrue(result.preflight_contract_valid)
        self.assertEqual(after_exists, before_exists)
        if before_stat is not None and after_stat is not None:
            self.assertEqual(after_stat.st_size, before_stat.st_size)
            self.assertEqual(after_stat.st_mtime_ns, before_stat.st_mtime_ns)
        self.assertEqual(pyproject.read_bytes(), pyproject_before)


if __name__ == "__main__":
    unittest.main()
