"""Offline tests for the local snapshot SQLite file preflight."""

import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import socket
import sqlite3
import unittest
from unittest.mock import patch

from ai_stock.storage.local_snapshot_db_preflight import (
    REQUIRED_IGNORE_PATTERNS,
    build_local_snapshot_db_file_preflight,
    validate_local_snapshot_db_file_preflight,
)


class LocalSnapshotDbFilePreflightTests(unittest.TestCase):
    def test_plan_fixes_path_policy_and_all_safety_flags(self) -> None:
        plan = build_local_snapshot_db_file_preflight()

        self.assertEqual(plan.stage, "MS-06.05")
        self.assertEqual(plan.storage_mode, "local_sqlite_file_preflight")
        self.assertEqual(
            plan.planned_db_relative_path,
            "data/local/ai_stock.sqlite3",
        )
        self.assertTrue(plan.git_ignore_required)
        self.assertEqual(
            plan.required_ignore_patterns,
            ("data/", "*.sqlite", "*.sqlite3", "*.db"),
        )
        for value in (
            plan.db_file_creation_allowed_this_stage,
            plan.actual_db_file_created,
            plan.data_directory_creation_allowed,
            plan.schema_initialization_allowed,
            plan.repository_file_connection_allowed,
            plan.api_call_allowed,
            plan.oauth_token_endpoint_allowed,
            plan.live_smoke_execution_allowed,
            plan.env_file_read_allowed,
            plan.credential_required,
            plan.account_seq_allowed,
            plan.real_order_related_call_allowed,
        ):
            self.assertFalse(value)

    def test_plan_is_immutable(self) -> None:
        plan = build_local_snapshot_db_file_preflight()

        with self.assertRaises(FrozenInstanceError):
            plan.storage_mode = "local_sqlite_file"  # type: ignore[misc]

    def test_validation_accepts_complete_policy_without_enabling_creation(
        self,
    ) -> None:
        plan = build_local_snapshot_db_file_preflight()

        result = validate_local_snapshot_db_file_preflight(
            plan,
            observed_ignore_patterns=REQUIRED_IGNORE_PATTERNS,
            actual_db_file_exists=False,
        )

        self.assertTrue(result.planned_path_is_expected)
        self.assertTrue(result.planned_path_is_repo_relative)
        self.assertFalse(result.planned_path_is_credential_path)
        self.assertTrue(result.db_file_creation_disabled)
        self.assertTrue(result.actual_db_file_absent)
        self.assertTrue(result.git_ignore_policy_satisfied)
        self.assertEqual(result.missing_ignore_patterns, ())
        self.assertTrue(result.external_actions_disabled)
        self.assertTrue(result.preflight_contract_valid)
        self.assertFalse(result.ready_for_file_db_creation)
        self.assertFalse(result.actual_db_file_created)

    def test_validation_rejects_unsafe_or_credential_paths(self) -> None:
        plan = build_local_snapshot_db_file_preflight()

        for unsafe_path in (
            ".env.local",
            "credentials/client-secret.sqlite3",
            "../data/local/ai_stock.sqlite3",
            "outside/ai_stock.sqlite3",
        ):
            with self.subTest(unsafe_path=unsafe_path):
                result = validate_local_snapshot_db_file_preflight(
                    replace(plan, planned_db_relative_path=unsafe_path),
                    observed_ignore_patterns=REQUIRED_IGNORE_PATTERNS,
                    actual_db_file_exists=False,
                )

                self.assertFalse(result.preflight_contract_valid)
                self.assertFalse(result.ready_for_file_db_creation)

    def test_validation_rejects_missing_ignore_rules_and_existing_db(self) -> None:
        plan = build_local_snapshot_db_file_preflight()

        result = validate_local_snapshot_db_file_preflight(
            plan,
            observed_ignore_patterns=("*.sqlite", "*.sqlite3", "*.db"),
            actual_db_file_exists=True,
        )

        self.assertFalse(result.git_ignore_policy_satisfied)
        self.assertEqual(result.missing_ignore_patterns, ("data/",))
        self.assertFalse(result.actual_db_file_absent)
        self.assertTrue(result.actual_db_file_created)
        self.assertFalse(result.preflight_contract_valid)
        self.assertFalse(result.ready_for_file_db_creation)

    def test_validation_rejects_each_external_or_creation_permission(self) -> None:
        plan = build_local_snapshot_db_file_preflight()
        unsafe_fields = (
            "db_file_creation_allowed_this_stage",
            "actual_db_file_created",
            "data_directory_creation_allowed",
            "schema_initialization_allowed",
            "repository_file_connection_allowed",
            "api_call_allowed",
            "oauth_token_endpoint_allowed",
            "live_smoke_execution_allowed",
            "env_file_read_allowed",
            "credential_required",
            "account_seq_allowed",
            "real_order_related_call_allowed",
        )

        for field_name in unsafe_fields:
            with self.subTest(field_name=field_name):
                result = validate_local_snapshot_db_file_preflight(
                    replace(plan, **{field_name: True}),
                    observed_ignore_patterns=REQUIRED_IGNORE_PATTERNS,
                    actual_db_file_exists=False,
                )

                self.assertFalse(result.preflight_contract_valid)
                self.assertFalse(result.ready_for_file_db_creation)

    def test_current_repository_rules_satisfy_required_ignore_policy(self) -> None:
        plan = build_local_snapshot_db_file_preflight()
        gitignore_patterns = {
            line.strip()
            for line in Path(".gitignore").read_text(encoding="utf-8").splitlines()
            if line.strip() and not line.lstrip().startswith("#")
        }

        result = validate_local_snapshot_db_file_preflight(
            plan,
            observed_ignore_patterns=gitignore_patterns,
            actual_db_file_exists=False,
        )

        self.assertIn("*.sqlite", gitignore_patterns)
        self.assertIn("*.sqlite3", gitignore_patterns)
        self.assertIn("*.db", gitignore_patterns)
        self.assertIn("data/", gitignore_patterns)
        self.assertEqual(result.missing_ignore_patterns, ())
        self.assertTrue(result.git_ignore_policy_satisfied)
        self.assertTrue(result.preflight_contract_valid)
        self.assertFalse(result.ready_for_file_db_creation)

    def test_builder_and_validator_perform_no_file_db_env_or_network_io(self) -> None:
        with (
            patch.object(
                socket,
                "socket",
                side_effect=AssertionError("network access is forbidden"),
            ),
            patch.object(
                sqlite3,
                "connect",
                side_effect=AssertionError("SQLite access is forbidden"),
            ),
            patch(
                "builtins.open",
                side_effect=AssertionError("file access is forbidden"),
            ),
            patch.object(
                Path,
                "mkdir",
                side_effect=AssertionError("directory creation is forbidden"),
            ),
            patch.object(
                Path,
                "touch",
                side_effect=AssertionError("file creation is forbidden"),
            ),
        ):
            plan = build_local_snapshot_db_file_preflight()
            result = validate_local_snapshot_db_file_preflight(
                plan,
                observed_ignore_patterns=REQUIRED_IGNORE_PATTERNS,
                actual_db_file_exists=False,
            )

        self.assertTrue(result.preflight_contract_valid)
        self.assertFalse(result.actual_db_file_created)

    def test_module_has_no_live_client_repository_or_sqlite_execution_path(
        self,
    ) -> None:
        import ai_stock.storage.local_snapshot_db_preflight as preflight

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
            "socket",
            "sqlite3",
            "ai_stock.clients",
            "ai_stock.config",
            "ai_stock.repositories",
            "ai_stock.services.live_readonly_snapshot_ingestion_smoke",
        }
        self.assertTrue(forbidden_imports.isdisjoint(imported_modules))
        for forbidden_call in (
            "create_connection",
            "initialize_schema",
            "sqlite3.connect",
            ".mkdir(",
            ".touch(",
        ):
            self.assertNotIn(forbidden_call, source)

    def test_preflight_does_not_change_pyproject_or_create_data_or_db_files(
        self,
    ) -> None:
        pyproject = Path("pyproject.toml")
        pyproject_before = pyproject.read_bytes()
        data_existed = Path("data").exists()
        candidate_existed = Path("data/local/ai_stock.sqlite3").exists()
        db_files_before = _workspace_db_files()

        plan = build_local_snapshot_db_file_preflight()
        result = validate_local_snapshot_db_file_preflight(
            plan,
            observed_ignore_patterns=REQUIRED_IGNORE_PATTERNS,
            actual_db_file_exists=candidate_existed,
        )

        self.assertTrue(result.preflight_contract_valid)
        self.assertEqual(pyproject.read_bytes(), pyproject_before)
        self.assertEqual(Path("data").exists(), data_existed)
        self.assertEqual(
            Path("data/local/ai_stock.sqlite3").exists(),
            candidate_existed,
        )
        self.assertEqual(_workspace_db_files(), db_files_before)


def _workspace_db_files() -> set[Path]:
    return {
        path
        for directory in (Path.cwd(), Path("data"), Path("data/local"))
        if directory.exists()
        for pattern in ("*.sqlite", "*.sqlite3", "*.db")
        for path in directory.glob(pattern)
    }


if __name__ == "__main__":
    unittest.main()
