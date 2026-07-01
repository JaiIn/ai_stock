"""Offline contract tests for the read-only dashboard preflight."""

from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

from ai_stock.ui.readonly_snapshot_dashboard_preflight import (
    ALLOWED_ACTIONS,
    FORBIDDEN_ACTIONS,
    FORBIDDEN_SENSITIVE_FIELDS,
    PLANNED_SECTIONS,
    SAFE_DISPLAY_FIELDS,
    build_readonly_snapshot_dashboard_preflight,
)


class ReadonlySnapshotDashboardPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.plan = build_readonly_snapshot_dashboard_preflight()

    def test_fixed_identity_and_local_read_model_source(self) -> None:
        self.assertEqual(self.plan.stage, "MS-07.01")
        self.assertEqual(
            self.plan.phase,
            "readonly_streamlit_snapshot_dashboard_preflight",
        )
        self.assertEqual(self.plan.dashboard_type, "streamlit")
        self.assertEqual(
            self.plan.planned_default_db_relative_path,
            "data/local/ai_stock.sqlite3",
        )
        self.assertEqual(self.plan.planned_default_symbol, "005930")
        self.assertEqual(self.plan.planned_default_exchange_pair, "USD/KRW")
        self.assertEqual(
            self.plan.data_source,
            "local_snapshot_latest_read_model",
        )

    def test_plan_is_immutable_and_read_only(self) -> None:
        self.assertTrue(self.plan.ui_read_only)
        self.assertEqual(self.plan.db_open_mode_planned, "readonly")
        self.assertFalse(self.plan.db_write_allowed_this_stage)
        self.assertFalse(self.plan.actual_db_file_modified_this_stage)
        with self.assertRaises(FrozenInstanceError):
            self.plan.ui_read_only = False

    def test_external_and_sensitive_capabilities_are_disabled(self) -> None:
        self.assertFalse(self.plan.api_call_allowed_this_stage)
        self.assertFalse(self.plan.oauth_token_endpoint_allowed_this_stage)
        self.assertFalse(self.plan.env_file_read_allowed_this_stage)
        self.assertFalse(self.plan.credential_required_this_stage)
        self.assertFalse(self.plan.account_seq_allowed)
        self.assertFalse(self.plan.real_order_related_call_allowed)
        self.assertFalse(self.plan.ai_recommendation_allowed_this_stage)
        self.assertFalse(self.plan.streamlit_full_ui_allowed_this_stage)

    def test_planned_sections_and_safe_display_fields_are_fixed(self) -> None:
        self.assertEqual(self.plan.planned_sections, PLANNED_SECTIONS)
        self.assertEqual(self.plan.safe_display_fields, SAFE_DISPLAY_FIELDS)
        self.assertIn("data_health_summary", self.plan.planned_sections)
        self.assertIn("latest_price_snapshot_summary", self.plan.planned_sections)
        self.assertIn("completeness_flags", self.plan.planned_sections)
        self.assertIn("db_file_safe_metadata", self.plan.safe_display_fields)

    def test_allowed_actions_are_local_read_only_actions(self) -> None:
        self.assertEqual(self.plan.allowed_actions, ALLOWED_ACTIONS)
        self.assertIn(
            "refresh_local_db_read_only_view",
            self.plan.allowed_actions,
        )
        self.assertIn(
            "select_symbol_from_safe_local_options",
            self.plan.allowed_actions,
        )

    def test_forbidden_actions_cover_live_write_order_and_ai_paths(self) -> None:
        self.assertEqual(self.plan.forbidden_actions, FORBIDDEN_ACTIONS)
        for action in (
            "refresh_from_live_api",
            "issue_oauth_token",
            "read_env_local",
            "write_database",
            "run_database_migration",
            "initialize_schema",
            "query_order_asset_account_balance_fill",
            "submit_order",
            "generate_ai_recommendation",
            "show_final_buy_sell_hold_recommendation",
            "show_real_order_button",
        ):
            self.assertIn(action, self.plan.forbidden_actions)

    def test_sensitive_fields_and_stock_warnings_policy_are_fixed(self) -> None:
        self.assertEqual(
            self.plan.forbidden_sensitive_fields,
            FORBIDDEN_SENSITIVE_FIELDS,
        )
        for field in (
            "full_database_row",
            "raw_response_body",
            "credential",
            "access_token",
            "authorization_header",
            "account_seq",
        ):
            self.assertIn(field, self.plan.forbidden_sensitive_fields)
        self.assertFalse(self.plan.stock_warnings_included)
        self.assertTrue(self.plan.stock_warnings_deferred)

    def test_module_has_no_streamlit_database_api_or_config_io(self) -> None:
        import ai_stock.ui.readonly_snapshot_dashboard_preflight as preflight

        source = Path(preflight.__file__).read_text(encoding="utf-8").casefold()
        for forbidden in (
            "import streamlit",
            "import sqlite3",
            "ai_stock.clients",
            "ai_stock.config",
            "httpx",
            "dotenv",
            "getenv(",
            "open(",
            "insert into",
            "update ",
            "delete from",
            "create table",
            "initialize_schema(",
        ):
            self.assertNotIn(forbidden, source)

    def test_streamlit_entry_point_remains_deferred(self) -> None:
        source = Path("app/streamlit_app.py").read_text(encoding="utf-8")
        self.assertIn("intentionally deferred", source)
        self.assertNotIn("import streamlit", source)

    def test_pyproject_is_unchanged(self) -> None:
        before = Path("pyproject.toml").read_bytes()
        build_readonly_snapshot_dashboard_preflight()
        self.assertEqual(Path("pyproject.toml").read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
