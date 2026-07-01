"""Offline tests for the local snapshot latest read model."""

from decimal import Decimal
from pathlib import Path
import sqlite3
import unittest
from uuid import uuid4

from ai_stock.storage.local_snapshot_latest_read_model import (
    DEFAULT_BASE_CURRENCY,
    DEFAULT_SYMBOL,
    LocalSnapshotLatestReadModel,
    build_local_snapshot_latest_read_model,
)


class LocalSnapshotLatestReadModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = Path("tests") / f"_latest_{uuid4().hex}.sqlite3"
        self._create_fixture()

    def tearDown(self) -> None:
        if self.path.exists():
            self.path.unlink()

    def _create_fixture(self) -> None:
        connection = sqlite3.connect(self.path)
        connection.executescript(
            """
            CREATE TABLE stocks(
                symbol TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                market TEXT,
                currency TEXT,
                updated_at TEXT NOT NULL
            );
            CREATE TABLE price_snapshots(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                price TEXT NOT NULL,
                currency TEXT
            );
            CREATE TABLE candles(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                symbol TEXT NOT NULL,
                interval TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                open TEXT NOT NULL,
                high TEXT NOT NULL,
                low TEXT NOT NULL,
                close TEXT NOT NULL,
                volume TEXT NOT NULL,
                currency TEXT
            );
            CREATE TABLE exchange_rates(
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                base_currency TEXT NOT NULL,
                quote_currency TEXT NOT NULL,
                exchange_rate TEXT NOT NULL,
                date_time TEXT
            );

            INSERT INTO stocks VALUES(
                '005930', 'Safe Stock', 'KRX', 'KRW', '2026-01-02T00:00:00Z'
            );
            INSERT INTO price_snapshots(symbol, timestamp, price, currency) VALUES
                ('005930', '2026-01-01T00:00:00Z', '100.10', 'KRW'),
                ('005930', '2026-01-02T00:00:00Z', '101.20', 'KRW');
            INSERT INTO candles(
                symbol, interval, timestamp, open, high, low, close, volume, currency
            ) VALUES
                ('005930', '1d', '2026-01-01T00:00:00Z',
                 '100.00', '102.00', '99.00', '101.00', '1000', 'KRW'),
                ('005930', '1d', '2026-01-02T00:00:00Z',
                 '101.00', '103.00', '100.00', '102.00', '1100', 'KRW');
            INSERT INTO exchange_rates(
                base_currency, quote_currency, exchange_rate, date_time
            ) VALUES
                ('USD', 'KRW', '1300.10', '2026-01-01T00:00:00Z'),
                ('USD', 'KRW', '1310.20', '2026-01-02T00:00:00Z');
            """
        )
        connection.close()

    def test_builds_complete_latest_model_without_modifying_database(self) -> None:
        before = self.path.stat()
        result = build_local_snapshot_latest_read_model(self.path)
        after = self.path.stat()

        self.assertTrue(result.success)
        self.assertEqual(result.symbol, DEFAULT_SYMBOL)
        self.assertEqual(result.exchange_rate_pair, "USD/KRW")
        self.assertEqual(result.db_open_mode, "readonly")
        self.assertFalse(result.db_write_allowed_this_stage)
        self.assertFalse(result.actual_db_file_modified_this_stage)
        self.assertTrue(result.completeness.all_components_present)
        self.assertEqual(before.st_size, after.st_size)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)

    def test_selects_latest_rows_and_preserves_decimal_and_timestamp(self) -> None:
        result = build_local_snapshot_latest_read_model(self.path)

        self.assertEqual(result.stock.display_name, "Safe Stock")
        self.assertEqual(result.latest_price.price, Decimal("101.20"))
        self.assertEqual(
            result.latest_price.timestamp,
            "2026-01-02T00:00:00Z",
        )
        self.assertEqual(result.latest_candle.close, Decimal("102.00"))
        self.assertEqual(result.latest_candle.volume, Decimal("1100"))
        self.assertTrue(result.latest_candle.ohlcv_present)
        self.assertEqual(
            result.latest_exchange_rate.exchange_rate,
            Decimal("1310.20"),
        )
        self.assertEqual(
            result.latest_exchange_rate.timestamp,
            "2026-01-02T00:00:00Z",
        )
        self.assertEqual(result.source_counts.price_snapshots, 2)
        self.assertEqual(result.source_counts.candles, 2)
        self.assertEqual(result.source_counts.exchange_rates, 2)
        self.assertEqual(result.safe_dict()["latest_price"]["price"], "101.20")

    def test_partial_data_uses_completeness_flags_without_failure(self) -> None:
        connection = sqlite3.connect(self.path)
        connection.execute("DELETE FROM price_snapshots")
        connection.execute("DELETE FROM candles")
        connection.execute("DELETE FROM exchange_rates")
        connection.commit()
        connection.close()

        result = build_local_snapshot_latest_read_model(self.path)

        self.assertTrue(result.success)
        self.assertTrue(result.completeness.stock_info_present)
        self.assertFalse(result.completeness.price_snapshot_present)
        self.assertFalse(result.completeness.candle_present)
        self.assertFalse(result.completeness.exchange_rate_present)
        self.assertFalse(result.completeness.all_components_present)
        self.assertIsNone(result.latest_price)
        self.assertIsNone(result.latest_candle)
        self.assertIsNone(result.latest_exchange_rate)

    def test_missing_symbol_returns_safe_failure(self) -> None:
        result = build_local_snapshot_latest_read_model(
            self.path,
            symbol="000000",
        )

        self.assertFalse(result.success)
        self.assertEqual(result.safe_error_type, "symbol_not_found")
        self.assertFalse(result.completeness.stock_info_present)

    def test_missing_database_fails_without_creating_file(self) -> None:
        missing = self.path.with_name("missing.sqlite3")
        result = build_local_snapshot_latest_read_model(missing)

        self.assertFalse(result.success)
        self.assertEqual(result.safe_error_type, "database_not_found")
        self.assertFalse(missing.exists())

    def test_model_and_diagnostics_exclude_secret_and_raw_row_fields(self) -> None:
        result = build_local_snapshot_latest_read_model(self.path)
        text = repr(result.safe_dict()).casefold()

        self.assertIsInstance(result, LocalSnapshotLatestReadModel)
        self.assertEqual(DEFAULT_BASE_CURRENCY, "USD")
        self.assertFalse(result.stock_warnings_included)
        self.assertTrue(result.stock_warnings_deferred)
        for forbidden in (
            "access_token",
            "authorization",
            "client_secret",
            "raw_response",
            "request_body",
            "rows",
        ):
            self.assertNotIn(forbidden, text)

    def test_module_has_no_api_config_or_write_sql(self) -> None:
        import ai_stock.storage.local_snapshot_latest_read_model as latest

        source = Path(latest.__file__).read_text(encoding="utf-8").casefold()
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
            "initialize_schema",
        ):
            self.assertNotIn(forbidden, source)
        self.assertIn("mode=ro", source)
        self.assertIn("query_only", source)

    def test_pyproject_is_unchanged(self) -> None:
        before = Path("pyproject.toml").read_bytes()
        build_local_snapshot_latest_read_model(self.path)
        self.assertEqual(Path("pyproject.toml").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
