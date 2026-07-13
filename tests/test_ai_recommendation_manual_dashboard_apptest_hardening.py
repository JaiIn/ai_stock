"""AppTest hardening for the MS-09.06 manual dashboard preflight UI."""

from contextlib import ExitStack
from pathlib import Path
import builtins
import socket
import unittest
from unittest.mock import patch
import urllib.request

from streamlit.testing.v1 import AppTest


APP_PATH = "app/streamlit_app.py"
LOCAL_DB_PATH = Path("data/local/ai_stock.sqlite3")


class ManualDashboardAppTestHardeningTests(unittest.TestCase):
    def test_app_render_keeps_manual_preflight_section_and_db_metadata_safe(
        self,
    ) -> None:
        before_db_stat = self._stat_if_exists(LOCAL_DB_PATH)

        with self._blocked_external_access():
            app = AppTest.from_file(APP_PATH)
            app.run(timeout=10)

        after_db_stat = self._stat_if_exists(LOCAL_DB_PATH)

        self.assertEqual(app.exception, [])
        self.assertEqual(before_db_stat, after_db_stat)

        rendered = self._rendered_text(app).casefold()
        for expected in (
            "manual watchlist dashboard preflight",
            "observation-only",
            "manual-or-fixture watchlist",
            "not investment advice",
            "observation and validation only",
            "not an investment recommendation",
            "there is no order function",
            "toss api",
            "account access",
            "oauth",
            "llm",
            "db write",
            "in-memory fixture/manual preflight",
            "fixture scenario",
            "fixture scenario coverage",
        ):
            self.assertIn(expected, rendered)

    def test_safety_badges_metrics_warnings_and_rows_are_visible(self) -> None:
        with self._blocked_external_access():
            app = AppTest.from_file(APP_PATH)
            app.run(timeout=10)

        rendered = self._rendered_text(app).casefold()
        for expected in (
            "watchlist status",
            "total",
            "valid",
            "needs review",
            "disabled",
            "manual preflight safety badges",
            "observation_only",
            "mock_or_manual_input_only",
            "no_real_order",
            "no_account_access",
            "no_live_api",
            "no_llm",
            "no_db_write",
            "manual preflight warnings",
            "manual preflight rows",
            "row 1",
            "validation_status",
            "valid_candidate",
            "selectable",
        ):
            self.assertIn(expected, rendered)

    def test_fixture_scenario_selectbox_covers_every_fixture_state(self) -> None:
        scenario_expectations = {
            "Fixture Basic Manual Symbols": (
                "valid_watchlist",
                "valid_candidate",
                "no manual preflight warnings",
            ),
            "Fixture Mixed Symbols": (
                "contains_invalid_candidates",
                "invalid_symbol",
                "invalid_candidates_need_review",
            ),
            "Fixture Duplicates And Disabled": (
                "contains_duplicate_candidates",
                "duplicate_candidate",
                "disabled_candidate",
                "duplicate_candidates_need_review",
                "disabled_candidates_not_selectable",
                "selectable: false",
            ),
            "Fixture Insufficient Data Review": (
                "needs_review",
                "insufficient_data",
                "insufficient_data_review",
            ),
            "Fixture Forbidden Fields Sanitized": (
                "valid_watchlist",
                "forbidden_fields_reported_in_diagnostics_only",
                "forbidden_field",
            ),
            "Fixture Empty Watchlist": (
                "empty_watchlist",
                "safe empty watchlist state",
                "review_empty_watchlist_input",
            ),
        }

        with self._blocked_external_access():
            app = AppTest.from_file(APP_PATH)
            app.run(timeout=10)

            selector = self._fixture_selector(app)
            self.assertEqual(tuple(selector.options), tuple(scenario_expectations))

            for scenario, expected_values in scenario_expectations.items():
                selector = self._fixture_selector(app)
                selector.set_value(scenario)
                app.run(timeout=10)
                self.assertEqual(app.exception, [])

                rendered = self._rendered_text(app).casefold()
                for expected in expected_values:
                    self.assertIn(expected, rendered)

    def test_fixture_coverage_expander_lists_all_scenarios(self) -> None:
        with self._blocked_external_access():
            app = AppTest.from_file(APP_PATH)
            app.run(timeout=10)

        rendered = self._rendered_text(app).casefold()
        for expected in (
            "fixture basic manual symbols",
            "fixture mixed symbols",
            "fixture duplicates and disabled",
            "fixture insufficient data review",
            "fixture forbidden fields sanitized",
            "fixture empty watchlist",
            "duplicate_candidate",
            "disabled_candidate",
            "insufficient_data",
            "empty_watchlist",
        ):
            self.assertIn(expected, rendered)

    def test_forbidden_fields_are_sanitized_from_visible_row_output(self) -> None:
        with self._blocked_external_access():
            app = AppTest.from_file(APP_PATH)
            app.run(timeout=10)

            selector = self._fixture_selector(app)
            selector.set_value("Fixture Forbidden Fields Sanitized")
            app.run(timeout=10)

        rendered = self._rendered_text(app)
        rendered_lower = rendered.casefold()

        for forbidden_value in (
            "redacted-not-output",
            "authorization bearer",
            "access token",
            "api key",
            "secret key",
            "client secret",
            "raw api response",
            "raw response body",
            "raw db row",
            "raw database row",
        ):
            self.assertNotIn(forbidden_value, rendered_lower)

        for forbidden_row_field in (
            "accountseq:",
            "access_token:",
            "authorization:",
            "target_price:",
            "expected_return:",
            "score:",
        ):
            self.assertNotIn(forbidden_row_field, rendered_lower)

    def test_forbidden_buttons_actions_and_inputs_are_absent(self) -> None:
        with self._blocked_external_access():
            app = AppTest.from_file(APP_PATH)
            app.run(timeout=10)

        rendered = self._rendered_text(app).casefold()
        forbidden_visible_text = (
            "buy recommendation",
            "sell recommendation",
            "hold recommendation",
            "strong buy",
            "target price",
            "profit expected",
            "must buy",
            "must sell",
            "buy now",
            "sell now",
            "hold now",
            "order button",
            "order ticket",
            "submit order",
            "real order button",
            "api refresh button",
            "live api refresh",
            "oauth login",
            "credential input",
            "accountseq input",
            "file upload",
            "file path input",
            "db refresh",
            "raw api response panel",
            "raw db row panel",
        )
        for forbidden in forbidden_visible_text:
            self.assertNotIn(forbidden, rendered)

        self.assertEqual(app.button, [])
        self.assertEqual(getattr(app, "file_uploader", []), [])

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
            "oauth",
            "file path",
        ):
            self.assertFalse(
                any(forbidden_label in label for label in text_input_labels)
            )

    def test_app_source_remains_free_of_new_live_or_write_paths(self) -> None:
        source = Path(APP_PATH).read_text(encoding="utf-8").casefold()

        for forbidden in (
            "streamlit run",
            "httpx",
            "requests",
            "openai",
            "dotenv",
            "getenv(",
            ".env.local",
            "oauth2/token",
            "access token",
            "authorization bearer",
            "accountseq",
            "raw api response",
            "raw db row",
            "insert into",
            "update ",
            "delete from",
            "create table",
            "initialize_schema",
            "submit order",
            "real order button",
            "live api refresh",
            "oauth login",
            "credential input",
            "file_uploader",
            "download_button",
            "api refresh button",
            "db refresh",
        ):
            self.assertNotIn(forbidden, source)

    def _fixture_selector(self, app: AppTest):
        for selector in app.selectbox:
            if getattr(selector, "label", "") == "Fixture scenario":
                return selector
        self.fail("Fixture scenario selector was not rendered.")

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

    def _stat_if_exists(self, path: Path) -> tuple[int, int] | None:
        if not path.exists():
            return None
        stat_result = path.stat()
        return (stat_result.st_size, stat_result.st_mtime_ns)


if __name__ == "__main__":
    unittest.main()
