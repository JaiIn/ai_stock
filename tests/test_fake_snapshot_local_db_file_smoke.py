"""Tests for fake-only snapshot persistence to a temporary SQLite file."""

import ast
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path
import socket
import unittest
from unittest.mock import patch
from uuid import uuid4

import scripts.fake_snapshot_local_db_file_smoke as smoke_script
import ai_stock.storage.local_snapshot_db_smoke as smoke


class StaticGitTrackingInspector:
    def __init__(
        self,
        *,
        tracked: bool = False,
        ignored: bool = True,
        directory_tracked: bool = False,
    ) -> None:
        self.tracked = tracked
        self.ignored = ignored
        self.directory_tracked = directory_tracked

    def is_tracked(self, path: Path) -> bool:
        del path
        return self.tracked

    def is_ignored(self, path: Path) -> bool:
        del path
        return self.ignored

    def directory_has_tracked_files(self, path: Path) -> bool:
        del path
        return self.directory_tracked


class FakeSnapshotLocalDbFileSmokeTests(unittest.TestCase):
    def test_smoke_persists_and_reopens_all_snapshot_types(self) -> None:
        with _temporary_database_path(".sqlite3") as database_path:
            result = smoke.run_fake_snapshot_local_db_file_smoke(
                database_path,
                git_inspector=StaticGitTrackingInspector(),
            )

            self.assertTrue(result.success)
            self.assertTrue(database_path.is_file())
            self.assertGreater(database_path.stat().st_size, 0)
            self.assertEqual(result.requested_symbol, "005930")
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

    def test_result_records_file_creation_and_git_exclusion(self) -> None:
        with _temporary_database_path(".db") as database_path:
            result = smoke.run_fake_snapshot_local_db_file_smoke(
                database_path,
                git_inspector=StaticGitTrackingInspector(),
            )

        self.assertTrue(result.db_file_creation_allowed_this_stage)
        self.assertTrue(result.actual_db_file_created)
        self.assertEqual(
            result.planned_db_relative_path,
            "data/local/ai_stock.sqlite3",
        )
        self.assertFalse(result.db_file_git_tracked)
        self.assertFalse(result.data_directory_git_tracked)
        self.assertTrue(result.sqlite_file_ignored_by_git)

    def test_smoke_reports_no_network_oauth_env_account_or_order_use(self) -> None:
        with (
            _temporary_database_path(".sqlite") as database_path,
            patch.object(
                socket,
                "socket",
                side_effect=AssertionError("network access is forbidden"),
            ),
        ):
            result = smoke.run_fake_snapshot_local_db_file_smoke(
                database_path,
                git_inspector=StaticGitTrackingInspector(),
            )

        self.assertFalse(result.actual_network_call_performed)
        self.assertFalse(result.oauth_token_endpoint_called)
        self.assertFalse(result.env_file_read)
        self.assertFalse(result.account_seq_used)
        self.assertFalse(result.real_order_related_call_performed)

    def test_smoke_rejects_memory_non_sqlite_and_existing_paths(self) -> None:
        with (
            _temporary_database_path(".txt") as non_sqlite_path,
            _temporary_database_path(".sqlite3", create=True) as existing_path,
        ):
            with self.assertRaises(ValueError):
                smoke.run_fake_snapshot_local_db_file_smoke(
                    ":memory:",
                    git_inspector=StaticGitTrackingInspector(),
                )
            with self.assertRaises(ValueError):
                smoke.run_fake_snapshot_local_db_file_smoke(
                    non_sqlite_path,
                    git_inspector=StaticGitTrackingInspector(),
                )
            with self.assertRaises(FileExistsError):
                smoke.run_fake_snapshot_local_db_file_smoke(
                    existing_path,
                    git_inspector=StaticGitTrackingInspector(),
                )

    def test_git_safety_failure_blocks_file_creation(self) -> None:
        with _temporary_database_path(".sqlite3") as database_path:
            with self.assertRaises(RuntimeError):
                smoke.run_fake_snapshot_local_db_file_smoke(
                    database_path,
                    git_inspector=StaticGitTrackingInspector(
                        tracked=True,
                        ignored=False,
                        directory_tracked=True,
                    ),
                )

            self.assertFalse(database_path.exists())

    def test_modules_have_no_live_client_oauth_or_config_imports(self) -> None:
        for module in (smoke, smoke_script):
            source = Path(module.__file__).read_text(encoding="utf-8")
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
                "ai_stock.clients",
                "ai_stock.config",
            }
            self.assertTrue(forbidden_imports.isdisjoint(imported_modules))
            self.assertNotIn("load_settings", source)
            self.assertNotIn("os.environ", source)
            self.assertNotIn("authorization_header", source)
            self.assertNotIn(".env.local", source)

    def test_script_has_fixed_path_without_runtime_input(self) -> None:
        source = Path(smoke_script.__file__).read_text(encoding="utf-8")

        self.assertEqual(
            smoke.PLANNED_DB_RELATIVE_PATH,
            "data/local/ai_stock.sqlite3",
        )
        self.assertNotIn("argparse", source)
        self.assertNotIn("input(", source)

    def test_temporary_smoke_does_not_touch_repo_data_or_pyproject(self) -> None:
        pyproject = Path("pyproject.toml")
        pyproject_before = pyproject.read_bytes()
        repo_data_existed = Path("data").exists()

        with _temporary_database_path(".sqlite3") as database_path:
            result = smoke.run_fake_snapshot_local_db_file_smoke(
                database_path,
                git_inspector=StaticGitTrackingInspector(),
            )

        self.assertTrue(result.success)
        self.assertEqual(Path("data").exists(), repo_data_existed)
        self.assertEqual(pyproject.read_bytes(), pyproject_before)


@contextmanager
def _temporary_database_path(
    suffix: str,
    *,
    create: bool = False,
) -> Iterator[Path]:
    path = Path("tests") / f".ms-06-07-{uuid4().hex}{suffix}"
    try:
        if create:
            path.touch()
        yield path
    finally:
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
