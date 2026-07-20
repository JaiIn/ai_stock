"""Offline tests for the MS-13.01 observation-list UI fixtures."""

from dataclasses import FrozenInstanceError, fields
from types import FunctionType
import unittest

import ai_stock.recommendation.observation_list_ui_fixtures as ui_fixtures
from ai_stock.recommendation.observation_list_ui_fixtures import (
    ALLOWED_OBSERVATION_LIST_UI_FIXTURE_SCENARIOS,
    FORBIDDEN_OBSERVATION_LIST_UI_FIXTURE_SCENARIOS,
    OBSERVATION_LIST_UI_FIXTURE_REQUIRED_FALSE_FLAGS,
    ObservationListUIFixtureEvaluationResult,
    ObservationListUIFixturePolicy,
    ObservationListUIFixtureRecord,
    build_all_observation_list_ui_fixtures,
    build_observation_list_ui_fixture_failure_probe,
    build_observation_list_ui_fixture_policy,
    build_observation_list_ui_rows_from_fixture,
    build_ui_all_fixture_matrix,
    build_ui_basic_ready_for_review_fixture,
    build_ui_disabled_blocked_fixture,
    build_ui_duplicates_blocked_fixture,
    build_ui_empty_input_fixture,
    build_ui_forbidden_field_sanitized_fixture,
    build_ui_missing_data_blocked_fixture,
    build_ui_mixed_review_fixture,
    evaluate_all_observation_list_ui_fixtures,
    evaluate_observation_list_ui_fixture,
)
from ai_stock.recommendation.observation_list_ui_preflight import (
    ALLOWED_OBSERVATION_LIST_BADGE_LABELS,
    FORBIDDEN_OBSERVATION_LIST_BADGE_LABELS,
    FORBIDDEN_OBSERVATION_LIST_UI_OUTPUT_KEYWORDS,
    OBSERVATION_LIST_UI_REQUIRED_FALSE_FLAGS,
    build_observation_list_ui_rows_from_all_fixtures,
    validate_observation_list_ui_row,
)


class ObservationListUIFixturesTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = build_observation_list_ui_fixture_policy()
        cls.fixtures = build_all_observation_list_ui_fixtures()
        cls.evaluations = evaluate_all_observation_list_ui_fixtures()
        cls.rows = build_observation_list_ui_rows_from_all_fixtures()

    def test_observation_list_ui_fixture_policy_generation(self) -> None:
        self.assertIsInstance(self.policy, ObservationListUIFixturePolicy)
        self.assertEqual(self.policy.stage_name, "MS-13.01")
        self.assertEqual(self.policy.mode, "observation_list_ui_fixture_expansion")
        self.assertEqual(
            self.policy.allowed_scenarios,
            ALLOWED_OBSERVATION_LIST_UI_FIXTURE_SCENARIOS,
        )
        self.assertEqual(
            self.policy.allowed_status_badges,
            ALLOWED_OBSERVATION_LIST_BADGE_LABELS,
        )
        self.assertEqual(
            self.policy.forbidden_status_badges,
            FORBIDDEN_OBSERVATION_LIST_BADGE_LABELS,
        )
        self.assertFalse(self.policy.streamlit_import_allowed)
        self.assertFalse(self.policy.actual_ui_render_allowed)
        self.assertFalse(self.policy.recommendation_required)
        self.assertFalse(self.policy.ranking_required)
        with self.assertRaises(FrozenInstanceError):
            self.policy.streamlit_import_allowed = True

    def test_all_ui_fixture_scenarios_are_created(self) -> None:
        scenarios = tuple(fixture.scenario for fixture in self.fixtures)

        self.assertEqual(scenarios, ALLOWED_OBSERVATION_LIST_UI_FIXTURE_SCENARIOS)
        self.assertEqual(len(self.fixtures), 8)
        self.assertTrue(
            all(isinstance(fixture, ObservationListUIFixtureRecord) for fixture in self.fixtures)
        )
        for forbidden in FORBIDDEN_OBSERVATION_LIST_UI_FIXTURE_SCENARIOS:
            self.assertNotIn(forbidden, scenarios)

    def test_all_ui_fixture_scenarios_are_deterministic(self) -> None:
        self.assertEqual(
            build_all_observation_list_ui_fixtures(),
            build_all_observation_list_ui_fixtures(),
        )
        self.assertEqual(
            evaluate_all_observation_list_ui_fixtures(),
            evaluate_all_observation_list_ui_fixtures(),
        )

    def test_evaluator_result_model_generation(self) -> None:
        result = self.evaluations[0]
        field_names = tuple(field.name for field in fields(result))

        self.assertIsInstance(result, ObservationListUIFixtureEvaluationResult)
        self.assertEqual(
            field_names,
            (
                "scenario",
                "passed",
                "failures",
                "actual_row_count",
                "actual_status_badges",
                "actual_display_buckets",
                "actual_score_snapshot_labels",
                "actual_component_summaries",
                "actual_warning_summaries",
                "actual_diagnostic_summaries",
                "actual_disclaimer_labels",
                "actual_guardrail_flags",
                "forbidden_absent_check_passed",
            ),
        )
        with self.assertRaises(FrozenInstanceError):
            result.passed = False

    def test_all_ui_fixtures_evaluator_passes(self) -> None:
        self.assertEqual(len(self.evaluations), 8)
        for result in self.evaluations:
            self.assertTrue(result.passed, result)
            self.assertEqual(result.failures, ())
            self.assertTrue(result.forbidden_absent_check_passed)

    def test_ui_basic_ready_for_review_processing(self) -> None:
        fixture = build_ui_basic_ready_for_review_fixture()
        result = evaluate_observation_list_ui_fixture(fixture)

        self.assertTrue(result.passed, result.failures)
        self.assertEqual(result.actual_row_count, 2)
        self.assertEqual(result.actual_status_badges, ("review_ready", "review_ready"))
        self.assertEqual(result.actual_display_buckets, ("review_ready",))

    def test_ui_mixed_review_processing(self) -> None:
        fixture = build_ui_mixed_review_fixture()
        result = evaluate_observation_list_ui_fixture(fixture)

        self.assertTrue(result.passed, result.failures)
        self.assertEqual(result.actual_row_count, 3)
        self.assertEqual(
            result.actual_status_badges,
            ("review_ready", "invalid_candidate", "invalid_candidate"),
        )
        self.assertIn("invalid_candidate_review", result.actual_display_buckets)

    def test_ui_duplicates_blocked_processing(self) -> None:
        result = evaluate_observation_list_ui_fixture(
            build_ui_duplicates_blocked_fixture()
        )

        self.assertTrue(result.passed, result.failures)
        self.assertIn("duplicate_candidate", result.actual_status_badges)
        self.assertIn("duplicate_candidate_review", result.actual_display_buckets)

    def test_ui_disabled_blocked_processing(self) -> None:
        result = evaluate_observation_list_ui_fixture(
            build_ui_disabled_blocked_fixture()
        )

        self.assertTrue(result.passed, result.failures)
        self.assertIn("disabled_candidate", result.actual_status_badges)
        self.assertIn("disabled_candidate_review", result.actual_display_buckets)

    def test_ui_missing_data_blocked_processing(self) -> None:
        result = evaluate_observation_list_ui_fixture(
            build_ui_missing_data_blocked_fixture()
        )

        self.assertTrue(result.passed, result.failures)
        self.assertEqual(result.actual_row_count, 1)
        self.assertEqual(result.actual_status_badges, ("missing_data",))

    def test_ui_forbidden_field_sanitized_processing(self) -> None:
        result = evaluate_observation_list_ui_fixture(
            build_ui_forbidden_field_sanitized_fixture()
        )

        self.assertTrue(result.passed, result.failures)
        self.assertEqual(result.actual_status_badges, ("sanitized_input",))
        self.assertIn(
            "sanitized_observation_detail",
            result.actual_component_summaries,
        )

    def test_ui_empty_input_processing(self) -> None:
        result = evaluate_observation_list_ui_fixture(build_ui_empty_input_fixture())

        self.assertTrue(result.passed, result.failures)
        self.assertEqual(result.actual_row_count, 1)
        self.assertEqual(result.actual_status_badges, ("empty_input",))

    def test_ui_all_fixture_matrix_processing(self) -> None:
        result = evaluate_observation_list_ui_fixture(build_ui_all_fixture_matrix())

        self.assertTrue(result.passed, result.failures)
        self.assertEqual(result.actual_row_count, 11)
        self.assertEqual(
            result.actual_display_buckets,
            (
                "review_ready",
                "invalid_candidate_review",
                "duplicate_candidate_review",
                "disabled_candidate_review",
                "missing_data_review",
                "sanitized_candidate_review",
                "empty_input_review",
            ),
        )

    def test_expected_vs_actual_mismatch_creates_failure(self) -> None:
        result = evaluate_observation_list_ui_fixture(
            build_observation_list_ui_fixture_failure_probe()
        )

        self.assertFalse(result.passed)
        self.assertIn("status_badges_mismatch", result.failures)

    def test_rows_can_be_built_from_fixture_records(self) -> None:
        for fixture in self.fixtures:
            rows = build_observation_list_ui_rows_from_fixture(fixture)
            self.assertEqual(len(rows), fixture.expected_row_count)
            self.assertTrue(all(validate_observation_list_ui_row(row).valid for row in rows))

    def test_status_badge_is_not_trade_directive(self) -> None:
        for result in self.evaluations:
            for status_badge in result.actual_status_badges:
                self.assertNotIn(status_badge, ("buy", "sell", "hold", "strong_buy"))
                self.assertIn(status_badge, ALLOWED_OBSERVATION_LIST_BADGE_LABELS)

    def test_score_snapshot_label_is_not_directive_output(self) -> None:
        for result in self.evaluations:
            for score_snapshot_label in result.actual_score_snapshot_labels:
                self.assertIn("quality_preflight_score:", score_snapshot_label)
                for forbidden in ("recommendation", "ranking", "action"):
                    self.assertNotIn(forbidden, score_snapshot_label)

    def test_display_bucket_is_not_ranking_priority_or_order(self) -> None:
        for result in self.evaluations:
            for display_bucket in result.actual_display_buckets:
                self.assertNotIn("rank", display_bucket)
                self.assertNotIn("priority", display_bucket)
                self.assertNotIn("order", display_bucket)

    def test_usability_label_is_not_ranking_flag(self) -> None:
        for row in self.rows:
            self.assertIn(
                row.usability_label,
                ("future_list_ready", "future_list_review_only"),
            )
            self.assertNotIn("rank", row.usability_label)
            self.assertNotIn("priority", row.usability_label)
            self.assertNotIn("order", row.usability_label)

    def test_forbidden_output_field_is_not_copied_to_ui_row(self) -> None:
        rendered_rows = repr(self.rows)
        rendered_evaluations = repr(self.evaluations)
        for keyword in FORBIDDEN_OBSERVATION_LIST_UI_OUTPUT_KEYWORDS:
            self.assertNotIn(keyword, rendered_rows)
            self.assertNotIn(keyword, rendered_evaluations)
        for keyword in (
            "accountSeq",
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
        ):
            self.assertNotIn(keyword, rendered_rows)
            self.assertNotIn(keyword, rendered_evaluations)

    def test_required_flags_all_false(self) -> None:
        expected = tuple(
            f"{flag}=false" for flag in OBSERVATION_LIST_UI_REQUIRED_FALSE_FLAGS
        )

        self.assertEqual(
            OBSERVATION_LIST_UI_FIXTURE_REQUIRED_FALSE_FLAGS,
            OBSERVATION_LIST_UI_REQUIRED_FALSE_FLAGS,
        )
        for result in self.evaluations:
            self.assertEqual(result.actual_guardrail_flags, expected)
            self.assertTrue(all(flag.endswith("=false") for flag in result.actual_guardrail_flags))

    def test_no_file_network_env_or_db_access(self) -> None:
        forbidden_names = {
            "open",
            "read",
            "read_text",
            "write",
            "write_text",
            "connect",
            "execute",
            "sqlite3",
            "getenv",
            "environ",
            "requests",
            "urllib",
            "httpx",
            "urlopen",
            "socket",
        }
        for name, value in vars(ui_fixtures).items():
            if isinstance(value, FunctionType):
                self.assertTrue(
                    forbidden_names.isdisjoint(value.__code__.co_names),
                    name,
                )

    def test_streamlit_import_absent(self) -> None:
        self.assertNotIn("streamlit", ui_fixtures.__dict__)
        self.assertNotIn("streamlit", ui_fixtures.__name__)

    def test_app_streamlit_and_preflight_modules_are_not_referenced_as_paths(self) -> None:
        rendered_module_constants = repr(
            tuple(
                value
                for value in vars(ui_fixtures).values()
                if isinstance(value, (str, tuple))
            )
        )

        self.assertNotIn("app/streamlit_app.py", rendered_module_constants)
        self.assertNotIn("observation_list_ui_preflight.py", rendered_module_constants)


if __name__ == "__main__":
    unittest.main()
