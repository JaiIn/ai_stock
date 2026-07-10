"""Offline tests for the MS-09.05 dashboard preflight view model contract."""

from dataclasses import FrozenInstanceError, replace
from types import FunctionType
import unittest

import ai_stock.recommendation.dashboard_preflight as dashboard_preflight
from ai_stock.recommendation.candidate_input_preflight import (
    FORBIDDEN_CANDIDATE_LABELS,
)
from ai_stock.recommendation.dashboard_preflight import (
    ALLOWED_DASHBOARD_SAFETY_BADGES,
    DASHBOARD_PREFLIGHT_REQUIRED_FALSE_FLAGS,
    FORBIDDEN_DASHBOARD_BADGES,
    DashboardSafetyBadge,
    build_all_fixture_dashboard_preflights,
    build_dashboard_preflight_from_fixture,
    build_dashboard_preflight_from_source_result,
    build_dashboard_preflight_policy,
    build_dashboard_row_from_watchlist_item,
    validate_dashboard_preflight,
)
from ai_stock.recommendation.watchlist_fixtures import (
    build_all_watchlist_source_fixtures,
    build_basic_manual_symbols_fixture,
    build_duplicates_and_disabled_fixture,
    build_empty_watchlist_fixture,
    build_forbidden_fields_sanitized_fixture,
    build_insufficient_data_review_fixture,
)
from ai_stock.recommendation.watchlist_source import (
    WatchlistSourceConfig,
    build_watchlist_source_result,
)


class DashboardPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_dashboard_preflight_policy()

    def test_default_policy_identity_and_immutability(self) -> None:
        self.assertEqual(self.policy.stage_name, "MS-09.05")
        self.assertEqual(self.policy.mode, "manual_dashboard_preflight")
        with self.assertRaises(FrozenInstanceError):
            self.policy.ui_required = True

    def test_dashboard_preflight_view_model_generation(self) -> None:
        result = build_watchlist_source_result(
            WatchlistSourceConfig(
                source_type="manual_symbols",
                source_label="manual dashboard source",
                watchlist_name="Manual Dashboard Candidates",
                raw_items=("005930", "000660"),
            )
        )
        view_model = build_dashboard_preflight_from_source_result(result)

        self.assertEqual(view_model.title, "Manual Watchlist Dashboard Preflight")
        self.assertEqual(view_model.mode_label, "manual_dashboard_preflight")
        self.assertEqual(view_model.source_label, "manual dashboard source")
        self.assertEqual(view_model.watchlist_status, "valid_watchlist")
        self.assertEqual(view_model.total_items, 2)
        self.assertEqual(view_model.valid_items, 2)
        self.assertEqual(len(view_model.rows), 2)
        self.assertIn(
            DashboardSafetyBadge.OBSERVATION_ONLY.value,
            view_model.safety_badges,
        )

    def test_dashboard_row_model_generation(self) -> None:
        result = build_watchlist_source_result(
            WatchlistSourceConfig(
                source_type="manual_symbols",
                source_label="manual rows",
                raw_items=(" 005930 ",),
            )
        )
        row = build_dashboard_row_from_watchlist_item(
            result.validation.items[0],
            source_label=result.source_label,
        )

        self.assertEqual(row.symbol, "005930")
        self.assertEqual(row.source_label, "manual rows")
        self.assertTrue(row.enabled)
        self.assertTrue(row.selectable)
        self.assertEqual(row.validation_status, "valid_candidate")
        self.assertEqual(row.warnings, ())

    def test_fixture_based_dashboard_preflight_generation(self) -> None:
        fixture = build_basic_manual_symbols_fixture()
        view_model = build_dashboard_preflight_from_fixture(fixture)

        self.assertEqual(view_model.watchlist_status, "valid_watchlist")
        self.assertEqual(view_model.total_items, 2)
        self.assertEqual(view_model.valid_items, 2)
        self.assertTrue(validate_dashboard_preflight(view_model).valid)

    def test_all_fixture_scenarios_generate_dashboard_preflight(self) -> None:
        fixtures = build_all_watchlist_source_fixtures()
        view_models = build_all_fixture_dashboard_preflights()

        self.assertEqual(len(view_models), len(fixtures))
        self.assertEqual(
            tuple(model.subtitle for model in view_models),
            tuple(fixture.description for fixture in fixtures),
        )
        for view_model in view_models:
            self.assertTrue(validate_dashboard_preflight(view_model).valid)

    def test_all_fixture_dashboard_preflights_are_deterministic(self) -> None:
        first = build_all_fixture_dashboard_preflights()
        second = build_all_fixture_dashboard_preflights()
        self.assertEqual(first, second)

    def test_empty_watchlist_safe_empty_state(self) -> None:
        view_model = build_dashboard_preflight_from_fixture(
            build_empty_watchlist_fixture()
        )
        self.assertEqual(view_model.watchlist_status, "empty_watchlist")
        self.assertEqual(view_model.total_items, 0)
        self.assertEqual(view_model.rows, ())
        self.assertIn("empty_watchlist_safe_state", view_model.warnings)
        self.assertEqual(view_model.next_action_hint, "review_empty_watchlist_input")

    def test_duplicate_candidate_warning_processing(self) -> None:
        view_model = build_dashboard_preflight_from_fixture(
            build_duplicates_and_disabled_fixture()
        )
        duplicate_rows = [
            row for row in view_model.rows if row.validation_status == "duplicate_candidate"
        ]

        self.assertEqual(view_model.duplicate_items, 1)
        self.assertIn("duplicate_candidates_need_review", view_model.warnings)
        self.assertEqual(len(duplicate_rows), 1)
        self.assertFalse(duplicate_rows[0].selectable)
        self.assertIn("duplicate_candidate_needs_review", duplicate_rows[0].warnings)

    def test_disabled_candidate_is_not_selectable(self) -> None:
        view_model = build_dashboard_preflight_from_fixture(
            build_duplicates_and_disabled_fixture()
        )
        disabled_rows = [
            row for row in view_model.rows if row.validation_status == "disabled_candidate"
        ]

        self.assertEqual(view_model.disabled_items, 1)
        self.assertEqual(len(disabled_rows), 1)
        self.assertFalse(disabled_rows[0].enabled)
        self.assertFalse(disabled_rows[0].selectable)
        self.assertIn("disabled_candidate_not_selectable", disabled_rows[0].warnings)

    def test_insufficient_data_review_warning_processing(self) -> None:
        view_model = build_dashboard_preflight_from_fixture(
            build_insufficient_data_review_fixture()
        )

        self.assertEqual(view_model.watchlist_status, "needs_review")
        self.assertEqual(view_model.insufficient_data_items, 1)
        self.assertIn("insufficient_data_review", view_model.warnings)
        self.assertIn(
            DashboardSafetyBadge.INSUFFICIENT_DATA.value,
            view_model.safety_badges,
        )
        self.assertFalse(view_model.rows[0].selectable)

    def test_forbidden_field_is_not_in_row_output_model(self) -> None:
        view_model = build_dashboard_preflight_from_fixture(
            build_forbidden_fields_sanitized_fixture()
        )
        row_output = repr(view_model.rows)

        self.assertNotIn("redacted-not-output", row_output)
        self.assertNotIn("accountSeq=", row_output)
        self.assertNotIn("target_price=", row_output)
        self.assertNotIn("expected_return=", row_output)
        self.assertNotIn("score=", row_output)

    def test_forbidden_field_is_reported_in_warning_or_diagnostics_only(self) -> None:
        view_model = build_dashboard_preflight_from_fixture(
            build_forbidden_fields_sanitized_fixture()
        )
        combined = view_model.warnings + view_model.diagnostics

        self.assertIn("forbidden_fields_reported_in_diagnostics_only", combined)
        self.assertTrue(
            any("forbidden_field:accountSeq" in value for value in combined)
        )
        self.assertTrue(
            any("forbidden_field_detected:target_price" in value for value in combined)
        )

    def test_forbidden_labels_are_not_generated_as_badges_actions_or_fields(self) -> None:
        for view_model in build_all_fixture_dashboard_preflights():
            produced_values = (
                view_model.next_action_hint,
                *view_model.safety_badges,
                *(row.validation_status for row in view_model.rows),
                *(row.source for row in view_model.rows),
            )
            for forbidden_label in FORBIDDEN_CANDIDATE_LABELS:
                self.assertNotIn(forbidden_label, produced_values)

    def test_safety_badges_express_observation_only_policy(self) -> None:
        view_model = build_dashboard_preflight_from_fixture(
            build_basic_manual_symbols_fixture()
        )
        for expected_badge in (
            "observation_only",
            "mock_or_manual_input_only",
            "no_real_order",
            "no_account_access",
            "no_live_api",
            "no_llm",
            "no_db_write",
        ):
            self.assertIn(expected_badge, view_model.safety_badges)
            self.assertIn(expected_badge, ALLOWED_DASHBOARD_SAFETY_BADGES)

    def test_forbidden_badges_are_documented(self) -> None:
        self.assertEqual(FORBIDDEN_DASHBOARD_BADGES, FORBIDDEN_CANDIDATE_LABELS)

    def test_required_flags_are_all_false(self) -> None:
        view_model = build_dashboard_preflight_from_fixture(
            build_basic_manual_symbols_fixture()
        )
        for flag in DASHBOARD_PREFLIGHT_REQUIRED_FALSE_FLAGS:
            self.assertFalse(getattr(view_model, flag))

    def test_validate_dashboard_preflight_rejects_forbidden_badge(self) -> None:
        view_model = build_dashboard_preflight_from_fixture(
            build_basic_manual_symbols_fixture()
        )
        invalid_view_model = replace(
            view_model,
            safety_badges=view_model.safety_badges + ("buy",),
        )
        validation = validate_dashboard_preflight(invalid_view_model, self.policy)

        self.assertFalse(validation.valid)
        self.assertTrue(validation.forbidden_badge_present)
        self.assertIn(
            "forbidden_badge_present:buy",
            validation.rejection_reasons,
        )

    def test_validate_dashboard_preflight_rejects_required_true_flag(self) -> None:
        view_model = build_dashboard_preflight_from_fixture(
            build_basic_manual_symbols_fixture()
        )
        invalid_view_model = replace(view_model, streamlit_required=True)
        validation = validate_dashboard_preflight(invalid_view_model, self.policy)

        self.assertFalse(validation.valid)
        self.assertIn(
            "required_flag_true:streamlit_required",
            validation.rejection_reasons,
        )

    def test_policy_disables_storage_loader_recommendation_scoring_and_ui(self) -> None:
        self.assertFalse(self.policy.actual_recommendation_allowed)
        self.assertFalse(self.policy.scoring_allowed)
        self.assertFalse(self.policy.watchlist_persistence_allowed)
        self.assertFalse(self.policy.file_loader_allowed)
        self.assertFalse(self.policy.ui_change_allowed)
        self.assertFalse(self.policy.streamlit_change_allowed)

    def test_module_structure_has_no_io_or_external_dependencies(self) -> None:
        runtime_modules = {
            getattr(value, "__module__", "")
            for value in vars(dashboard_preflight).values()
        }
        for forbidden_module in (
            "streamlit",
            "sqlite3",
            "sqlalchemy",
            "httpx",
            "requests",
            "openai",
            "dotenv",
            "os",
            "pathlib",
            "socket",
            "subprocess",
        ):
            self.assertNotIn(forbidden_module, runtime_modules)

        called_names = _dashboard_module_code_names()
        for forbidden_call in (
            "open",
            "read_text",
            "read_bytes",
            "write_text",
            "write_bytes",
            "connect",
            "getenv",
            "request",
            "get",
            "post",
            "now",
            "random",
        ):
            self.assertNotIn(forbidden_call, called_names)

    def test_module_has_no_forbidden_runtime_imports_or_paths(self) -> None:
        module_symbols = {
            str(part).casefold()
            for part in (*vars(dashboard_preflight), *_dashboard_module_constants())
        }
        for forbidden in (
            "import streamlit",
            "ai_stock.clients",
            "ai_stock.storage",
            "ai_stock.paper_trading",
            "sqlite3",
            "sqlalchemy",
            "httpx",
            "requests",
            "import openai",
            "dotenv",
            "os.environ",
            ".env.local",
            "local_snapshot_latest_read_model",
        ):
            self.assertNotIn(forbidden, module_symbols)

    def test_app_streamlit_app_is_not_part_of_dashboard_preflight_module(self) -> None:
        self.assertNotIn("app/streamlit_app.py", _dashboard_module_constants())


def _dashboard_module_code_names() -> set[str]:
    names: set[str] = set()
    for value in vars(dashboard_preflight).values():
        if isinstance(value, FunctionType):
            names.update(value.__code__.co_names)
    return names


def _dashboard_module_constants() -> tuple[object, ...]:
    constants: list[object] = []
    for value in vars(dashboard_preflight).values():
        if isinstance(value, FunctionType):
            constants.extend(_flatten_code_constants(value.__code__.co_consts))
    return tuple(constants)


def _flatten_code_constants(values: tuple[object, ...]) -> tuple[object, ...]:
    flattened: list[object] = []
    for value in values:
        if isinstance(value, tuple):
            flattened.extend(_flatten_code_constants(value))
        else:
            flattened.append(value)
    return tuple(flattened)


if __name__ == "__main__":
    unittest.main()
