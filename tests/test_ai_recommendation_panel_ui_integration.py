"""Offline tests for the MS-08.04 mock-only recommendation panel UI."""

from pathlib import Path
import unittest
from unittest.mock import patch

from streamlit.testing.v1 import AppTest

from ai_stock.recommendation.mock_policy_model import MockRecommendationLabel
from ai_stock.ui.readonly_snapshot_dashboard import (
    build_readonly_snapshot_dashboard,
)

from app.streamlit_app import (
    _build_recommendation_explanation_view_model,
)


class MockOnlyRecommendationPanelUIIntegrationTests(unittest.TestCase):
    def test_app_renders_safe_recommendation_panel_copy(self) -> None:
        app = AppTest.from_file("app/streamlit_app.py")
        app.run(timeout=10)

        self.assertEqual(app.exception, [])
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

    def test_forbidden_directives_and_controls_are_not_rendered(self) -> None:
        app = AppTest.from_file("app/streamlit_app.py")
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
            "credential input",
            "accountseq input",
            "oauth login",
            "live api refresh",
            "raw db row",
            "raw api response",
            "auto trade",
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
        ):
            self.assertFalse(
                any(forbidden_label in label for label in text_input_labels)
            )

    def test_missing_database_builds_insufficient_data_view_model(self) -> None:
        missing_path = Path("tests") / "_missing_ms_08_04_panel.sqlite3"
        if missing_path.exists():
            self.fail("Unexpected test DB fixture already exists.")

        dashboard_view = build_readonly_snapshot_dashboard(missing_path)
        view_model = _build_recommendation_explanation_view_model(
            dashboard_view,
        )

        self.assertFalse(missing_path.exists())
        self.assertIsNotNone(view_model)
        self.assertEqual(
            view_model.label,
            MockRecommendationLabel.INSUFFICIENT_DATA.value,
        )
        combined = "\n".join(self._view_model_strings(view_model)).casefold()
        self.assertIn("insufficient_data", combined)
        self.assertIn("caller_supplied_mock_result_only=true", combined)

    def test_only_validation_passed_view_model_is_returned(self) -> None:
        dashboard_view = build_readonly_snapshot_dashboard(
            Path("tests") / "_missing_ms_08_04_validation.sqlite3"
        )

        with patch(
            "app.streamlit_app.validate_recommendation_explanation_view_model"
        ) as validate:
            validate.return_value.passed = False
            validate.return_value.violations = ("forced_failure",)

            view_model = _build_recommendation_explanation_view_model(
                dashboard_view,
            )

        self.assertIsNone(view_model)

    def test_app_source_has_no_forbidden_runtime_paths(self) -> None:
        source = Path("app/streamlit_app.py").read_text(
            encoding="utf-8",
        ).casefold()

        for forbidden in (
            "httpx",
            "requests",
            "openai",
            "dotenv",
            "getenv(",
            ".env.local",
            "access token",
            "authorization bearer",
            "accountseq",
            "raw db row",
            "raw api response",
            "submit order",
            "real order button",
            "live api refresh",
            "oauth login",
            "credential input",
            "insert into",
            "update ",
            "delete from",
            "create table",
            "initialize_schema",
        ):
            self.assertNotIn(forbidden, source)

    def test_app_render_does_not_modify_local_database(self) -> None:
        db_path = Path("data/local/ai_stock.sqlite3")
        before = db_path.stat() if db_path.exists() else None

        app = AppTest.from_file("app/streamlit_app.py")
        app.run(timeout=10)

        after = db_path.stat() if db_path.exists() else None
        if before is None:
            self.assertIsNone(after)
        else:
            self.assertIsNotNone(after)
            self.assertEqual(before.st_size, after.st_size)
            self.assertEqual(before.st_mtime_ns, after.st_mtime_ns)

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
        ):
            collection = getattr(app, collection_name, ())
            values.extend(
                str(value)
                for element in collection
                if (value := getattr(element, "value", None)) is not None
            )
        return "\n".join(values)

    def _view_model_strings(self, view_model) -> tuple[str, ...]:
        section_strings: list[str] = []
        for section in view_model.safe_sections:
            section_strings.append(section.name)
            section_strings.append(section.heading)
            section_strings.extend(section.lines)
        return (
            view_model.title,
            view_model.stage_name,
            view_model.label,
            *view_model.safe_summary,
            *section_strings,
            *view_model.disclaimers,
            *view_model.diagnostics,
        )


if __name__ == "__main__":
    unittest.main()
