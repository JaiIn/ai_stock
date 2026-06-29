"""E2E smoke tests for fake-only read-only snapshot ingestion."""

import ast
from decimal import Decimal
from pathlib import Path
import socket
import unittest
from unittest.mock import patch

import scripts.readonly_snapshot_ingestion_smoke as smoke


class FakeReadOnlySnapshotIngestionE2ESmokeTests(unittest.TestCase):
    def test_smoke_persists_and_reads_back_all_snapshots(self) -> None:
        result = smoke.run_fake_readonly_snapshot_ingestion_smoke()

        self.assertTrue(result.success)
        self.assertEqual(result.requested_symbol, "005930")
        self.assertEqual(result.saved_stock_count, 1)
        self.assertEqual(result.saved_price_snapshot_count, 1)
        self.assertEqual(result.saved_candle_count, 1)
        self.assertEqual(result.saved_exchange_rate_count, 1)
        self.assertTrue(result.repository_round_trip_verified)
        self.assertTrue(result.decimal_values_preserved)
        self.assertTrue(result.timestamp_values_preserved)
        self.assertTrue(result.stock_warnings_deferred)

    def test_smoke_uses_only_in_memory_sqlite(self) -> None:
        real_create_connection = smoke.create_connection
        connection_targets: list[str] = []

        def recording_create_connection(database_path):
            connection_targets.append(database_path)
            return real_create_connection(database_path)

        with patch.object(
            smoke,
            "create_connection",
            side_effect=recording_create_connection,
        ):
            result = smoke.run_fake_readonly_snapshot_ingestion_smoke()

        self.assertTrue(result.success)
        self.assertEqual(connection_targets, [":memory:"])
        self.assertFalse(result.actual_db_file_created)

    def test_smoke_blocks_network_and_reports_safe_flags(self) -> None:
        with patch.object(
            socket,
            "socket",
            side_effect=AssertionError("network access is forbidden"),
        ):
            result = smoke.run_fake_readonly_snapshot_ingestion_smoke()

        self.assertTrue(result.success)
        self.assertFalse(result.actual_network_call_performed)
        self.assertFalse(result.oauth_token_endpoint_called)
        self.assertFalse(result.account_seq_used)
        self.assertFalse(result.real_order_related_call_performed)

    def test_fake_providers_return_parsed_models_with_preserved_values(self) -> None:
        stock = smoke.FakeStockInfoProvider().get_stock_info("005930")
        price = smoke.FakePriceSnapshotProvider().get_price_snapshots("005930")
        candle_page = smoke.FakeCandlePageProvider().get_candles(
            "005930",
            interval="1d",
            count=1,
            adjusted=True,
        )
        rate = smoke.FakeExchangeRateProvider().get_exchange_rates("USD", "KRW")

        self.assertEqual(stock[0].stock_code, "005930")
        self.assertEqual(price[0].price, Decimal("70123.4500"))
        self.assertEqual(price[0].timestamp, "2026-06-29T09:00:00+09:00")
        self.assertEqual(candle_page.candles[0].close, Decimal("70500.30"))
        self.assertEqual(
            candle_page.candles[0].timestamp,
            "2026-06-29T00:00:00+09:00",
        )
        self.assertEqual(rate[0].exchange_rate, Decimal("1375.2500"))
        self.assertEqual(rate[0].date_time, "2026-06-29T00:00:00+09:00")

    def test_smoke_creates_no_files_and_does_not_modify_pyproject(self) -> None:
        pyproject_path = Path("pyproject.toml")
        pyproject_before = pyproject_path.read_bytes()
        data_directory_existed = Path("data").exists()
        db_files_before = _workspace_db_files()

        result = smoke.run_fake_readonly_snapshot_ingestion_smoke()

        self.assertTrue(result.success)
        self.assertFalse(result.actual_db_file_created)
        self.assertEqual(_workspace_db_files(), db_files_before)
        self.assertEqual(Path("data").exists(), data_directory_existed)
        self.assertEqual(pyproject_path.read_bytes(), pyproject_before)

    def test_smoke_module_has_no_live_client_or_network_imports(self) -> None:
        module_path = Path(smoke.__file__)
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
            "ai_stock.clients",
            "ai_stock.config",
        }
        self.assertTrue(forbidden_imports.isdisjoint(imported_modules))
        self.assertNotIn("load_settings", source)
        self.assertNotIn("os.environ", source)
        self.assertNotIn("authorization_header", source)

def _workspace_db_files() -> set[Path]:
    return {
        path
        for pattern in ("*.sqlite", "*.sqlite3", "*.db")
        for path in Path.cwd().glob(pattern)
    }


if __name__ == "__main__":
    unittest.main()
