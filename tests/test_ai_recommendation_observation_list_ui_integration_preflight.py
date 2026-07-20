"""Tests for MS-13.03 observation-list UI integration preflight."""

from contextlib import ExitStack
from pathlib import Path
import builtins
import socket
import unittest
from unittest.mock import patch
import urllib.request

from streamlit.testing.v1 import AppTest


APP_PATH = Path("app/streamlit_app.py")


class ObservationListUIIntegrationPreflightTests(unittest.TestCase):
    def test_app_source_contains_observation_list_ui_preflight_section(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        section = self._observation_section_source(source)

        self.assertIn("_render_observation_list_ui_preflight", source)
        self.assertIn("_render_observation_list_ui_preflight()", source)
        self.assertIn("Observation List UI Preflight", section)
        self.assertIn("Fixture row preview", section)
        self.assertIn("Fixture coverage reference", section)

    def test_fixture_row_builder_and_summary_are_referenced(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")

        self.assertIn("build_observation_list_ui_rows_from_all_fixtures", source)
        self.assertIn("summarize_observation_list_ui_rows", source)
        self.assertIn("_OBSERVATION_LIST_UI_ROW_SOURCE", source)
        self.assertIn("_OBSERVATION_LIST_UI_SUMMARY_SOURCE", source)

    def test_hardening_check_is_referenced(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")

        self.assertIn("run_observation_list_ui_fixture_hardening_checks", source)
        self.assertIn("_OBSERVATION_LIST_UI_HARDENING_SOURCE", source)
        self.assertIn("hardening_state: fixture_contract_passed", source)

    def test_section_source_has_no_forbidden_controls_or_runtime_paths(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        section = self._observation_section_source(source).casefold()

        for forbidden in (
            "st.button",
            "button(",
            "session_state",
            "callback",
            "file_uploader",
            "download_button",
            "requests",
            "httpx",
            "urlopen",
            "socket",
            "dotenv",
            "getenv(",
            ".env.local",
            "text_input(",
            "selectbox(",
        ):
            self.assertNotIn(forbidden, section)

    def test_section_source_has_no_forbidden_visible_columns(self) -> None:
        source = APP_PATH.read_text(encoding="utf-8")
        section = self._observation_section_source(source).casefold()

        for forbidden in (
            '"rank"',
            '"ranking"',
            '"ranking_position"',
            '"priority"',
            '"order"',
            '"target_price"',
            '"expected_return"',
            '"profit_probability"',
            '"recommendation"',
            '"action"',
        ):
            self.assertNotIn(forbidden, section)

    def test_app_renders_observation_list_ui_preflight_section(self) -> None:
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
            "observation row 1",
            "status_badge",
            "score_snapshot_label",
            "display_bucket",
            "usability_label",
            "fixture_contract_passed",
            "external_capability_flags: all_false",
        ):
            self.assertIn(expected, rendered)

    def test_rendered_observation_values_are_not_directive_labels(self) -> None:
        with self._blocked_external_access():
            app = AppTest.from_file(str(APP_PATH))
            app.run(timeout=30)

        rendered = self._rendered_text(app).casefold()

        for expected in (
            "review_ready",
            "invalid_candidate",
            "sanitized_input",
            "quality_preflight_score=",
            "future_list_ready",
            "future_list_review_only",
        ):
            self.assertIn(expected, rendered)

        for forbidden in (
            "buy:",
            "sell:",
            "hold:",
            "strong_buy",
            "ranking_position",
            "target_price",
            "expected_return",
            "profit_probability",
            "must_buy",
            "must_sell",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_no_new_forbidden_buttons_or_inputs_are_rendered(self) -> None:
        with self._blocked_external_access():
            app = AppTest.from_file(str(APP_PATH))
            app.run(timeout=30)

        self.assertEqual(app.button, [])
        text_input_labels = tuple(
            getattr(widget, "label", "").casefold()
            for widget in app.text_input
        )
        for forbidden_label in (
            "credential",
            "api key",
            "secret",
            "token",
            "accountseq",
        ):
            self.assertFalse(
                any(forbidden_label in label for label in text_input_labels)
            )

    def test_imported_public_contracts_remain_callable(self) -> None:
        import app.streamlit_app as streamlit_app

        rows = streamlit_app._build_observation_list_ui_fixture_preview_rows()
        summary = (
            streamlit_app._summarize_observation_list_ui_fixture_preview_rows(
                rows
            )
        )

        self.assertEqual(len(rows), 3)
        self.assertEqual(summary["total_rows"], 3)
        self.assertEqual(summary["ready_rows"], 1)
        self.assertEqual(summary["needs_review_rows"], 2)
        self.assertEqual(
            streamlit_app._OBSERVATION_LIST_UI_ROW_SOURCE_NAME,
            "build_observation_list_ui_rows_from_all_fixtures",
        )
        self.assertEqual(
            streamlit_app._OBSERVATION_LIST_UI_HARDENING_SOURCE_NAME,
            "run_observation_list_ui_fixture_hardening_checks",
        )

    def test_existing_observation_modules_are_not_modified_by_this_test(self) -> None:
        changed_files = self._changed_files()

        for forbidden_path in (
            "src/ai_stock/recommendation/observation_list_ui_preflight.py",
            "src/ai_stock/recommendation/observation_list_ui_fixtures.py",
            "src/ai_stock/recommendation/observation_list_ui_fixture_hardening.py",
        ):
            self.assertNotIn(forbidden_path, changed_files)

    def _observation_section_source(self, source: str) -> str:
        start = source.index("def _render_observation_list_ui_preflight")
        end = source.index("\ndef main", start)
        return source[start:end]

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
