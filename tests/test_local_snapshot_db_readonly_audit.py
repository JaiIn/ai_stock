"""Offline tests for the local snapshot DB read-only audit."""

from pathlib import Path
import sqlite3
import unittest
from uuid import uuid4

from ai_stock.storage.local_snapshot_db_audit import (
    audit_local_snapshot_db_readonly,
)


class LocalSnapshotDbReadonlyAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = Path("tests") / f"_audit_{uuid4().hex}.sqlite3"
        connection = sqlite3.connect(self.path)
        connection.executescript(
            """
            CREATE TABLE stocks(symbol TEXT PRIMARY KEY, currency TEXT);
            CREATE TABLE price_snapshots(
                symbol TEXT, timestamp TEXT, price TEXT, currency TEXT
            );
            CREATE TABLE candles(
                symbol TEXT, interval TEXT, timestamp TEXT, open TEXT,
                high TEXT, low TEXT, close TEXT, volume TEXT, currency TEXT
            );
            CREATE TABLE exchange_rates(
                base_currency TEXT, quote_currency TEXT,
                exchange_rate TEXT, date_time TEXT
            );
            INSERT INTO stocks VALUES ('005930', 'KRW');
            INSERT INTO price_snapshots VALUES
                ('005930', '2026-01-01T00:00:00Z', '1', 'KRW'),
                ('005930', '2026-01-02T00:00:00Z', '2', 'KRW');
            INSERT INTO candles VALUES
                ('005930', '1d', '2026-01-01T00:00:00Z',
                 '1', '2', '1', '2', '10', 'KRW'),
                ('005930', '1d', '2026-01-02T00:00:00Z',
                 '2', '3', '2', '3', '20', 'KRW');
            INSERT INTO exchange_rates VALUES
                ('USD', 'KRW', '1300', '2026-01-01T00:00:00Z'),
                ('USD', 'KRW', '1310', '2026-01-02T00:00:00Z');
            """
        )
        connection.close()

    def tearDown(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def test_audit_returns_safe_minimum_summary_without_modifying_file(self) -> None:
        before = self.path.stat()
        result = audit_local_snapshot_db_readonly(self.path)
        after = self.path.stat()

        self.assertTrue(result.success)
        self.assertEqual(result.db_open_mode, "readonly")
        self.assertFalse(result.db_write_allowed_this_stage)
        self.assertFalse(result.actual_db_file_modified_this_stage)
        self.assertEqual(result.stocks.count, 1)
        self.assertEqual(result.price_snapshots.count, 2)
        self.assertEqual(result.candles.count, 2)
        self.assertEqual(result.exchange_rates.count, 2)
        self.assertTrue(result.minimum_expected_state_valid)
        self.assertTrue(result.requested_symbol_present)
        self.assertTrue(result.exchange_rate_pair_present)
        self.assertEqual(before.st_size, after.st_size)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)

    def test_summary_has_no_row_or_secret_fields(self) -> None:
        result = audit_local_snapshot_db_readonly(self.path)
        text = repr(result.safe_dict()).casefold()

        for forbidden in (
            "access_token",
            "authorization",
            "client_secret",
            "raw_response",
            "rows",
        ):
            self.assertNotIn(forbidden, text)
        self.assertFalse(result.stock_warnings_included)
        self.assertTrue(result.stock_warnings_deferred)

    def test_missing_database_fails_without_creating_file(self) -> None:
        missing = self.path.with_name(f"_missing_{uuid4().hex}.sqlite3")
        result = audit_local_snapshot_db_readonly(missing)

        self.assertFalse(result.success)
        self.assertEqual(result.safe_error_type, "database_not_found")
        self.assertFalse(missing.exists())

    def test_minimum_validator_rejects_insufficient_counts(self) -> None:
        connection = sqlite3.connect(self.path)
        connection.execute("DELETE FROM exchange_rates")
        connection.commit()
        connection.close()

        result = audit_local_snapshot_db_readonly(self.path)

        self.assertFalse(result.success)
        self.assertFalse(result.minimum_expected_state_valid)

    def test_module_has_no_api_config_or_write_sql(self) -> None:
        import ai_stock.storage.local_snapshot_db_audit as audit

        source = Path(audit.__file__).read_text(encoding="utf-8")
        lowered = source.casefold()
        for forbidden in (
            "ai_stock.clients",
            "ai_stock.config",
            "httpx",
            "oauthclient",
            "oauth_client",
            "insert into",
            "update ",
            "delete from",
            "replace into",
            "create table",
            "drop table",
            "alter table",
        ):
            self.assertNotIn(forbidden, lowered)
        self.assertIn("mode=ro", source)
        self.assertIn("query_only", source)

    def test_pyproject_is_unchanged(self) -> None:
        before = Path("pyproject.toml").read_bytes()
        audit_local_snapshot_db_readonly(self.path)
        self.assertEqual(Path("pyproject.toml").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
