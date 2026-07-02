"""Offline tests for the minimal read-only Streamlit snapshot dashboard."""

from pathlib import Path
import sqlite3
import unittest
from uuid import uuid4

from ai_stock.ui.readonly_snapshot_dashboard import (
    DATA_SOURCE,
    DEFAULT_DB_RELATIVE_PATH,
    DEFAULT_EXCHANGE_PAIR,
    DISPLAYED_SECTIONS,
    build_readonly_snapshot_dashboard,
)


class ReadonlySnapshotDashboardTests(unittest.TestCase):
    def setUp(self) -> None:
        self.path = Path("tests") / f"_dashboard_{uuid4().hex}.sqlite3"
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
            INSERT INTO price_snapshots(symbol, timestamp, price, currency)
            VALUES('005930', '2026-01-02T00:00:00Z', '101.20', 'KRW');
            INSERT INTO candles(
                symbol, interval, timestamp, open, high, low, close, volume, currency
            ) VALUES(
                '005930', '1d', '2026-01-02T00:00:00Z',
                '101.00', '103.00', '100.00', '102.00', '1100', 'KRW'
            );
            INSERT INTO exchange_rates(
                base_currency, quote_currency, exchange_rate, date_time
            ) VALUES('USD', 'KRW', '1310.20', '2026-01-02T00:00:00Z');
            """
        )
        connection.close()

    def test_defaults_and_read_only_policy_are_fixed(self) -> None:
        view = build_readonly_snapshot_dashboard(self.path)

        self.assertEqual(DEFAULT_DB_RELATIVE_PATH, "data/local/ai_stock.sqlite3")
        self.assertEqual(view.symbol, "005930")
        self.assertEqual(DEFAULT_EXCHANGE_PAIR, "USD/KRW")
        self.assertEqual(view.exchange_pair, DEFAULT_EXCHANGE_PAIR)
        self.assertEqual(view.data_source, DATA_SOURCE)
        self.assertEqual(view.db_open_mode, "readonly")
        self.assertFalse(view.db_write_allowed_this_stage)
        self.assertFalse(view.actual_db_file_modified_this_stage)
        self.assertFalse(view.api_call_allowed_this_stage)
        self.assertFalse(view.oauth_token_endpoint_allowed_this_stage)
        self.assertFalse(view.env_file_read_allowed_this_stage)
        self.assertFalse(view.credential_required_this_stage)
        self.assertFalse(view.ai_recommendation_allowed_this_stage)
        self.assertFalse(view.real_order_related_call_allowed)

    def test_complete_safe_summary_preserves_database_metadata(self) -> None:
        before = self.path.stat()
        view = build_readonly_snapshot_dashboard(self.path)
        after = self.path.stat()

        self.assertTrue(view.success)
        self.assertEqual(view.status_level, "success")
        self.assertEqual(view.stock_info["symbol"], "005930")
        self.assertEqual(view.price_snapshot["price"], "101.20")
        self.assertEqual(view.candle["close"], "102.00")
        self.assertTrue(view.candle["ohlcv_present"])
        self.assertEqual(view.exchange_rate["exchange_rate"], "1310.20")
        self.assertEqual(before.st_size, after.st_size)
        self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)

    def test_sections_completeness_and_counts_are_safe(self) -> None:
        view = build_readonly_snapshot_dashboard(self.path)

        self.assertEqual(view.displayed_sections, DISPLAYED_SECTIONS)
        for section in (
            "data_health_summary",
            "safety_status",
            "latest_stock_info_summary",
            "latest_price_snapshot_summary",
            "latest_candle_summary",
            "latest_exchange_rate_summary",
            "completeness_flags",
            "source_counts",
            "read_only_diagnostics",
            "last_db_audit_metadata",
        ):
            self.assertIn(section, view.displayed_sections)
        self.assertTrue(view.completeness["all_components_present"])
        self.assertEqual(view.source_counts["stocks"], 1)
        self.assertEqual(view.source_counts["price_snapshots"], 1)
        self.assertEqual(view.source_counts["candles"], 1)
        self.assertEqual(view.source_counts["exchange_rates"], 1)

    def test_partial_snapshot_returns_warning_and_completeness_flags(self) -> None:
        connection = sqlite3.connect(self.path)
        connection.execute("DELETE FROM candles")
        connection.commit()
        connection.close()

        view = build_readonly_snapshot_dashboard(self.path)

        self.assertTrue(view.success)
        self.assertEqual(view.status_level, "warning")
        self.assertFalse(view.completeness["candle_present"])
        self.assertFalse(view.completeness["all_components_present"])
        self.assertIsNone(view.candle)

    def test_missing_database_returns_safe_warning_without_creating_file(
        self,
    ) -> None:
        missing = self.path.with_name(f"_missing_{uuid4().hex}.sqlite3")

        view = build_readonly_snapshot_dashboard(missing)

        self.assertFalse(view.success)
        self.assertEqual(view.status_level, "warning")
        self.assertEqual(view.safe_error_type, "database_not_found")
        self.assertFalse(view.db_file_exists)
        self.assertFalse(view.actual_db_file_modified_this_stage)
        self.assertFalse(missing.exists())

    def test_safe_dictionary_excludes_raw_and_sensitive_fields(self) -> None:
        view = build_readonly_snapshot_dashboard(self.path)
        text = repr(view.safe_dict()).casefold()

        for forbidden in (
            "full_database_row",
            "raw_response_body",
            "request_body",
            "access_token",
            "authorization_header",
            "client_secret",
            "account_seq",
        ):
            self.assertNotIn(forbidden, text)
        self.assertFalse(view.stock_warnings_included)
        self.assertTrue(view.stock_warnings_deferred)

    def test_helper_has_no_streamlit_api_oauth_env_or_write_path(self) -> None:
        import ai_stock.ui.readonly_snapshot_dashboard as dashboard

        source = Path(dashboard.__file__).read_text(encoding="utf-8").casefold()
        for forbidden in (
            "import streamlit",
            "ai_stock.clients",
            "ai_stock.config",
            "httpx",
            "dotenv",
            "getenv(",
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

    def test_entrypoint_is_minimal_and_has_no_forbidden_controls(self) -> None:
        source = Path("app/streamlit_app.py").read_text(
            encoding="utf-8",
        ).casefold()

        self.assertIn("set_page_config", source)
        self.assertIn("build_readonly_snapshot_dashboard", source)
        self.assertNotIn("import streamlit", source)
        for forbidden in (
            "dotenv",
            "getenv(",
            "httpx",
            "oauth",
            "api refresh",
            "access token",
            "accountseq",
            "buy button",
            "sell button",
            "submit order",
        ):
            self.assertNotIn(forbidden, source)

    def test_pyproject_is_unchanged(self) -> None:
        before = Path("pyproject.toml").read_bytes()
        build_readonly_snapshot_dashboard(self.path)
        self.assertEqual(Path("pyproject.toml").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
