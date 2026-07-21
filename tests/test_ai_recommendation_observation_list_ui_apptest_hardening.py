"""AppTest hardening for the MS-13.03 observation-list UI section."""

from contextlib import ExitStack
from pathlib import Path
import builtins
import socket
import unittest
from unittest.mock import patch
import urllib.request

from streamlit.testing.v1 import AppTest


APP_PATH = Path("app/streamlit_app.py")
ALLOWED_OBSERVATION_FIELDS = (
    "symbol",
    "market",
    "item_status",
    "status_badge",
    "display_bucket",
    "score_snapshot_label",
    "score_scale_label",
    "component_summary",
    "needs_review_label",
    "usability_label",
    "blocked_reason_summary",
    "warning_summary",
    "diagnostic_summary",
    "disclaimer_labels",
    "guardrail_flags",
)
FORBIDDEN_VISIBLE_SECTION_LABELS = (
    "buy",
    "sell",
    "hold",
    "strong_buy",
    "must_buy",
    "must_sell",
    "recommendation",
    "action",
    "rank",
    "ranking",
    "ranking_position",
    "priority",
    "order",
    "target_price",
    "target price",
    "expected_return",
    "expected return",
    "profit_probability",
    "profit probability",
    "api refresh",
    "oauth login",
    "credential",
    "accountseq",
    "access_token",
    "authorization",
    "bearer",
    "api_key",
    "secret_key",
    "client_secret",
    "account_balance",
    "holdings",
    "fills",
    "order_id",
    "raw_response",
    "raw_request",
    "db_row",
    "file_path",
    "env_path",
    ".env.local",
)


class ObservationListUIAppTestHardeningTests(unittest.TestCase):
    def test_apptest_renders_observation_only_section(self) -> None:
        with self._blocked_external_access():
            app = AppTest.from_file(str(APP_PATH))
            app.run(timeout=30)

        self.assertEqual(app.exception, [])
        rendered = self._rendered_text(app).casefold()

        for expected in (
            "observation list ui preflight",
            "fixture-based observation rows",
            "observation-only",
            "preflight",
            "fixture-based display preview only",
            "not investment advice",
            "no live api or trading controls are used",
            "fixture row preview",
            "fixture coverage reference",
        ):
            self.assertIn(expected, rendered)

    def test_apptest_renders_fixture_rows_and_hardening_reference(
        self,
    ) -> None:
        with self._blocked_external_access():
            app = AppTest.from_file(str(APP_PATH))
            app.run(timeout=30)

        rendered = self._rendered_text(app).casefold()

        for expected in (
            "observation row 1",
            "observation row 2",
            "observation row 3",
            "review_ready",
            "invalid_candidate",
            "sanitized_input",
            "quality_preflight_score=100",
            "quality_preflight_score=0",
            "quality_preflight_score=70",
            "fixture_contract_passed",
            "external_capability_flags: all_false",
            "run_observation_list_ui_fixture_hardening_checks",
        ):
            self.assertIn(expected, rendered)

    def test_section_source_limits_visible_fields_to_observation_row_fields(
        self,
    ) -> None:
        section = self._observation_section_source()
        summary_source = self._safe_row_summary_source()

        for field in ALLOWED_OBSERVATION_FIELDS:
            self.assertIn(f'"{field}"', summary_source)

        self.assertNotIn("dataframe(", section)
        self.assertNotIn("table(", section)
        self.assertNotIn("column_config", section)

    def test_section_source_has_no_forbidden_ui_controls_or_state(self) -> None:
        section = self._observation_section_source().casefold()

        for forbidden in (
            "button(",
            "st.button",
            "callback",
            "session_state",
            "text_input(",
            "selectbox(",
            "file_uploader(",
            "download_button(",
            "form(",
            "form_submit_button(",
        ):
            self.assertNotIn(forbidden, section)

    def test_section_output_labels_do_not_use_forbidden_ui_terms(self) -> None:
        rows = self._preview_rows()
        rendered_section_values = self._section_value_text(rows).casefold()
        section_source = self._observation_section_source().casefold()

        for forbidden in FORBIDDEN_VISIBLE_SECTION_LABELS:
            self.assertNotIn(forbidden, rendered_section_values)

        for forbidden_column in (
            '"recommendation"',
            '"action"',
            '"rank"',
            '"ranking"',
            '"ranking_position"',
            '"priority"',
            '"order"',
            '"target_price"',
            '"expected_return"',
            '"profit_probability"',
        ):
            self.assertNotIn(forbidden_column, section_source)

    def test_observation_semantics_are_not_trade_or_ranking_semantics(
        self,
    ) -> None:
        rows = self._preview_rows()

        self.assertEqual(rows[0]["status_badge"], "review_ready")
        self.assertEqual(rows[1]["status_badge"], "invalid_candidate")
        self.assertEqual(rows[2]["status_badge"], "sanitized_input")

        for row in rows:
            self.assertNotIn(row["status_badge"], {"buy", "sell", "hold"})
            self.assertNotIn("recommendation", row["score_snapshot_label"])
            self.assertNotIn("ranking", row["score_snapshot_label"])
            self.assertNotIn("action", row["score_snapshot_label"])
            self.assertNotIn("ranking", row["display_bucket"])
            self.assertNotIn("priority", row["display_bucket"])
            self.assertNotIn("order", row["display_bucket"])
            self.assertNotIn("ranking", row["usability_label"])

    def test_static_section_has_no_runtime_api_db_file_or_env_access(self) -> None:
        section = self._observation_section_source().casefold()

        for forbidden in (
            "requests",
            "httpx",
            "urlopen",
            "socket",
            "sqlite",
            "connect(",
            "read_text(",
            "read_bytes(",
            "open(",
            "write_text(",
            "write_bytes(",
            "getenv(",
            "environ",
            "dotenv",
            ".env.local",
            "accountseq",
        ):
            self.assertNotIn(forbidden, section)

    def test_app_file_is_not_modified_by_ms_13_04(self) -> None:
        self.assertNotIn("app/streamlit_app.py", self._changed_files())

    def test_existing_contract_modules_are_not_modified_by_ms_13_04(self) -> None:
        changed_files = self._changed_files()

        for forbidden_path in (
            "src/ai_stock/recommendation/__init__.py",
            "src/ai_stock/recommendation/observation_list_ui_preflight.py",
            "src/ai_stock/recommendation/observation_list_ui_fixtures.py",
            "src/ai_stock/recommendation/observation_list_ui_fixture_hardening.py",
            "src/ai_stock/recommendation/recommendation_list_preflight.py",
            "src/ai_stock/recommendation/recommendation_list_fixtures.py",
            "src/ai_stock/recommendation/recommendation_list_fixture_hardening.py",
        ):
            self.assertNotIn(forbidden_path, changed_files)

    def _observation_section_source(self) -> str:
        source = APP_PATH.read_text(encoding="utf-8")
        start = source.index("def _render_observation_list_ui_preflight")
        end = source.index("\ndef main", start)
        return source[start:end]

    def _safe_row_summary_source(self) -> str:
        source = APP_PATH.read_text(encoding="utf-8")
        start = source.index("def _safe_observation_list_ui_row_summary")
        end = source.index("\ndef _render_observation_list_ui_preflight", start)
        return source[start:end]

    def _preview_rows(self) -> tuple[dict[str, object], ...]:
        import app.streamlit_app as streamlit_app

        return streamlit_app._build_observation_list_ui_fixture_preview_rows()

    def _section_value_text(self, rows: tuple[dict[str, object], ...]) -> str:
        values: list[str] = []
        for row in rows:
            for field in ALLOWED_OBSERVATION_FIELDS:
                value = row[field]
                if isinstance(value, tuple):
                    values.extend(str(item) for item in value)
                else:
                    values.append(str(value))
        return "\n".join(values)

    def _blocked_external_access(self) -> ExitStack:
        stack = ExitStack()
        original_open = builtins.open
        original_path_open = Path.open
        original_path_read_text = Path.read_text
        original_path_read_bytes = Path.read_bytes

        def is_env_local(target: object) -> bool:
            try:
                return Path(target).name == ".env.local"
            except TypeError:
                return False

        def guarded_open(file, *args, **kwargs):
            if is_env_local(file):
                raise AssertionError(".env.local must not be read")
            return original_open(file, *args, **kwargs)

        def guarded_path_open(path_self: Path, *args, **kwargs):
            if path_self.name == ".env.local":
                raise AssertionError(".env.local must not be read")
            return original_path_open(path_self, *args, **kwargs)

        def guarded_path_read_text(path_self: Path, *args, **kwargs):
            if path_self.name == ".env.local":
                raise AssertionError(".env.local must not be read")
            return original_path_read_text(path_self, *args, **kwargs)

        def guarded_path_read_bytes(path_self: Path, *args, **kwargs):
            if path_self.name == ".env.local":
                raise AssertionError(".env.local must not be read")
            return original_path_read_bytes(path_self, *args, **kwargs)

        stack.enter_context(patch("builtins.open", guarded_open))
        stack.enter_context(patch("pathlib.Path.open", guarded_path_open))
        stack.enter_context(
            patch("pathlib.Path.read_text", guarded_path_read_text)
        )
        stack.enter_context(
            patch("pathlib.Path.read_bytes", guarded_path_read_bytes)
        )
        stack.enter_context(
            patch.object(
                socket,
                "create_connection",
                side_effect=AssertionError("network access is forbidden"),
            )
        )
        stack.enter_context(
            patch.object(
                urllib.request,
                "urlopen",
                side_effect=AssertionError("HTTP access is forbidden"),
            )
        )
        return stack

    def _rendered_text(self, app: AppTest) -> str:
        values: list[str] = []
        for collection_name in (
            "title",
            "caption",
            "subheader",
            "markdown",
            "info",
            "warning",
            "success",
            "error",
            "metric",
            "text_input",
            "selectbox",
            "expander",
        ):
            collection = getattr(app, collection_name, ())
            for element in collection:
                for attribute_name in ("value", "label", "body", "help"):
                    value = getattr(element, attribute_name, None)
                    if value is not None:
                        values.append(str(value))
        return "\n".join(values)

    def _changed_files(self) -> tuple[str, ...]:
        import subprocess

        result = subprocess.run(
            ["git", "diff", "--name-only"],
            check=True,
            capture_output=True,
            text=True,
        )
        return tuple(
            line.strip()
            for line in result.stdout.splitlines()
            if line.strip()
        )


if __name__ == "__main__":
    unittest.main()
