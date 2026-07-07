"""AppTest smoke checks for the MS-08.04 mock-only recommendation panel."""

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


class RecommendationPanelAppTestSmokeTests(unittest.TestCase):
    def test_apptest_renders_safe_mock_only_panel_with_io_guards(self) -> None:
        before_db_stat = self._stat_if_exists(LOCAL_DB_PATH)

        with self._blocked_external_access():
            app = AppTest.from_file(APP_PATH)
            app.run(timeout=10)

        after_db_stat = self._stat_if_exists(LOCAL_DB_PATH)

        self.assertEqual(app.exception, [])
        self.assertEqual(before_db_stat, after_db_stat)

        rendered = self._rendered_text(app).casefold()
        for expected in (
            "mock recommendation explanation",
            "mock-only",
            "observation-only",
            "not investment advice",
            "no real recommendation",
            "no order execution",
            "no account access",
            "no live api access",
            "no credential required",
        ):
            self.assertIn(expected, rendered)

        self.assertTrue(
            "insufficient_data" in rendered
            or "data completeness" in rendered
            or "mock_result_was_prepared_by_caller=true" in rendered
        )

    def test_forbidden_controls_and_sensitive_text_are_absent(self) -> None:
        with self._blocked_external_access():
            app = AppTest.from_file(APP_PATH)
            app.run(timeout=10)

        rendered = self._rendered_text(app).casefold()
        forbidden_visible_text = (
            "buy recommendation",
            "sell recommendation",
            "hold recommendation",
            "buy now",
            "sell now",
            "hold now",
            "order ticket",
            "submit order",
            "real order button",
            "credential input",
            "accountseq input",
            "oauth login",
            "live api refresh",
            "raw api response",
            "raw db row",
            "access token",
            "authorization bearer",
            "toss_client_id",
            "toss_client_secret",
            "openai_api_key",
            "client secret",
            "api key",
            "secret key",
        )
        for forbidden in forbidden_visible_text:
            self.assertNotIn(forbidden, rendered)

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
            "oauth",
        ):
            self.assertFalse(
                any(forbidden_label in label for label in text_input_labels)
            )

    def test_app_source_has_no_live_or_write_runtime_paths(self) -> None:
        source = Path(APP_PATH).read_text(encoding="utf-8").casefold()

        forbidden_source_tokens = (
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
            "buy recommendation",
            "sell recommendation",
            "hold recommendation",
        )
        for forbidden in forbidden_source_tokens:
            self.assertNotIn(forbidden, source)

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
