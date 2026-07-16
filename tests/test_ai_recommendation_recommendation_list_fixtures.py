"""Offline tests for the MS-12.01 recommendation list fixture expansion."""

from dataclasses import FrozenInstanceError, replace
from types import FunctionType
import unittest

import ai_stock.recommendation.recommendation_list_fixtures as list_fixtures
from ai_stock.recommendation.recommendation_list_fixtures import (
    ALLOWED_RECOMMENDATION_LIST_FIXTURE_SCENARIOS,
    FORBIDDEN_RECOMMENDATION_LIST_FIXTURE_OUTPUT_KEYWORDS,
    FORBIDDEN_RECOMMENDATION_LIST_FIXTURE_SCENARIOS,
    RECOMMENDATION_LIST_FIXTURE_REQUIRED_FALSE_FLAGS,
    RecommendationListFixtureScenario,
    build_all_recommendation_list_fixtures,
    build_list_all_fixture_matrix,
    build_list_basic_ready_for_review_fixture,
    build_list_disabled_blocked_fixture,
    build_list_duplicates_blocked_fixture,
    build_list_empty_input_fixture,
    build_list_forbidden_field_sanitized_fixture,
    build_list_missing_data_blocked_fixture,
    build_list_mixed_review_fixture,
    build_recommendation_list_fixture_policy,
    build_recommendation_list_items_from_all_list_fixtures,
    build_recommendation_list_items_from_fixture,
    evaluate_all_recommendation_list_fixtures,
    evaluate_recommendation_list_fixture,
)
from ai_stock.recommendation.recommendation_list_preflight import (
    ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES,
    FORBIDDEN_RECOMMENDATION_LIST_ACTION_LABELS,
    FORBIDDEN_RECOMMENDATION_LIST_RANKING_LABELS,
    FORBIDDEN_RECOMMENDATION_LIST_RECOMMENDATION_LABELS,
)
from ai_stock.recommendation.scoring_preflight import (
    ALLOWED_SCORE_COMPONENT_NAMES,
    SCORE_SCALE,
)


class RecommendationListFixtureExpansionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_recommendation_list_fixture_policy()

    def test_recommendation_list_fixture_policy_generation(self) -> None:
        self.assertEqual(self.policy.stage_name, "MS-12.01")
        self.assertEqual(self.policy.mode, "recommendation_list_fixture_expansion")
        self.assertEqual(
            self.policy.allowed_scenarios,
            ALLOWED_RECOMMENDATION_LIST_FIXTURE_SCENARIOS,
        )
        self.assertEqual(
            self.policy.allowed_item_statuses,
            ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES,
        )
        self.assertIn(
            "actual_recommendation_fixture",
            FORBIDDEN_RECOMMENDATION_LIST_FIXTURE_SCENARIOS,
        )
        self.assertFalse(self.policy.actual_recommendation_list_allowed)
        self.assertFalse(self.policy.ranking_required)
        self.assertFalse(self.policy.ui_required)
        with self.assertRaises(FrozenInstanceError):
            self.policy.ui_required = True

    def test_all_recommendation_list_fixture_scenarios_are_generated(self) -> None:
        fixtures = build_all_recommendation_list_fixtures()

        self.assertEqual(
            tuple(fixture.scenario for fixture in fixtures),
            tuple(scenario.value for scenario in RecommendationListFixtureScenario),
        )
        self.assertEqual(len(fixtures), 8)
        for fixture in fixtures:
            self.assertEqual(
                fixture.expected_required_false_flags,
                tuple(
                    f"{flag}=false"
                    for flag in RECOMMENDATION_LIST_FIXTURE_REQUIRED_FALSE_FLAGS
                ),
            )

    def test_all_recommendation_list_fixture_scenarios_are_deterministic(self) -> None:
        self.assertEqual(
            build_all_recommendation_list_fixtures(),
            build_all_recommendation_list_fixtures(),
        )
        self.assertEqual(
            evaluate_all_recommendation_list_fixtures(),
            evaluate_all_recommendation_list_fixtures(),
        )
        self.assertEqual(
            build_recommendation_list_items_from_all_list_fixtures(),
            build_recommendation_list_items_from_all_list_fixtures(),
        )

    def test_all_recommendation_list_fixture_evaluators_pass(self) -> None:
        evaluations = evaluate_all_recommendation_list_fixtures()

        self.assertEqual(len(evaluations), 8)
        self.assertTrue(all(evaluation.passed for evaluation in evaluations))
        self.assertTrue(all(not evaluation.failures for evaluation in evaluations))

    def test_list_basic_ready_for_review_processing(self) -> None:
        evaluation = evaluate_recommendation_list_fixture(
            build_list_basic_ready_for_review_fixture()
        )

        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.actual_item_statuses,
            ("item_ready_for_review", "item_ready_for_review"),
        )
        self.assertEqual(evaluation.actual_ready_for_review_count, 2)
        self.assertEqual(evaluation.actual_needs_review_count, 0)
        self.assertEqual(evaluation.actual_usable_for_future_list_count, 2)
        self.assertEqual(evaluation.actual_score_snapshots, (SCORE_SCALE, SCORE_SCALE))
        self.assertEqual(evaluation.actual_display_buckets, ("review_ready",))

    def test_list_mixed_review_processing(self) -> None:
        evaluation = evaluate_recommendation_list_fixture(
            build_list_mixed_review_fixture()
        )

        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.actual_item_statuses,
            (
                "item_ready_for_review",
                "item_invalid_candidate",
                "item_invalid_candidate",
            ),
        )
        self.assertEqual(evaluation.actual_needs_review_count, 2)
        self.assertIn("invalid_candidate_review", evaluation.actual_display_buckets)
        self.assertIn("invalid_symbol_review", evaluation.actual_warnings)

    def test_list_duplicates_blocked_processing(self) -> None:
        evaluation = evaluate_recommendation_list_fixture(
            build_list_duplicates_blocked_fixture()
        )

        self.assertTrue(evaluation.passed)
        self.assertIn("item_duplicate_candidate", evaluation.actual_item_statuses)
        self.assertIn("duplicate_candidate_review", evaluation.actual_display_buckets)
        self.assertIn("duplicate_symbol", evaluation.actual_diagnostics)

    def test_list_disabled_blocked_processing(self) -> None:
        evaluation = evaluate_recommendation_list_fixture(
            build_list_disabled_blocked_fixture()
        )

        self.assertTrue(evaluation.passed)
        self.assertIn("item_disabled_candidate", evaluation.actual_item_statuses)
        self.assertIn("disabled_candidate_review", evaluation.actual_display_buckets)
        self.assertIn("candidate_disabled", evaluation.actual_diagnostics)

    def test_list_missing_data_blocked_processing(self) -> None:
        evaluation = evaluate_recommendation_list_fixture(
            build_list_missing_data_blocked_fixture()
        )

        self.assertTrue(evaluation.passed)
        self.assertEqual(evaluation.actual_item_statuses, ("item_missing_data",))
        self.assertEqual(evaluation.actual_score_snapshots, (20,))
        self.assertIn("missing_data_review", evaluation.actual_display_buckets)

    def test_list_forbidden_field_sanitized_processing(self) -> None:
        evaluation = evaluate_recommendation_list_fixture(
            build_list_forbidden_field_sanitized_fixture()
        )
        rendered = repr(evaluation)

        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.actual_item_statuses,
            ("item_forbidden_field_sanitized",),
        )
        self.assertEqual(evaluation.actual_score_snapshots, (0,))
        self.assertTrue(evaluation.forbidden_absent_check_passed)
        self.assertIn(
            "forbidden_field_detected:accountSeq",
            evaluation.actual_diagnostics,
        )
        for keyword in FORBIDDEN_RECOMMENDATION_LIST_FIXTURE_OUTPUT_KEYWORDS:
            self.assertNotIn(keyword, rendered)

    def test_list_empty_input_processing(self) -> None:
        evaluation = evaluate_recommendation_list_fixture(
            build_list_empty_input_fixture()
        )

        self.assertTrue(evaluation.passed)
        self.assertEqual(evaluation.actual_item_statuses, ("item_empty_input",))
        self.assertEqual(evaluation.actual_needs_review_count, 1)
        self.assertIn("empty_input_review", evaluation.actual_display_buckets)
        self.assertIn("empty_source_items", evaluation.actual_diagnostics)

    def test_list_all_fixture_matrix_processing(self) -> None:
        evaluation = evaluate_recommendation_list_fixture(
            build_list_all_fixture_matrix()
        )

        self.assertTrue(evaluation.passed)
        self.assertEqual(len(evaluation.actual_item_statuses), 11)
        self.assertEqual(evaluation.actual_ready_for_review_count, 4)
        self.assertEqual(evaluation.actual_needs_review_count, 7)
        self.assertEqual(evaluation.actual_usable_for_future_list_count, 4)
        self.assertIn(
            "item_forbidden_field_sanitized",
            evaluation.actual_item_statuses,
        )
        self.assertEqual(min(evaluation.actual_score_snapshots), 0)
        self.assertEqual(max(evaluation.actual_score_snapshots), SCORE_SCALE)

    def test_expected_vs_actual_mismatch_generates_failure(self) -> None:
        fixture = build_list_basic_ready_for_review_fixture()
        mismatched = replace(
            fixture,
            expected_item_statuses=("item_empty_input",),
        )
        evaluation = evaluate_recommendation_list_fixture(mismatched)

        self.assertFalse(evaluation.passed)
        self.assertIn("item_statuses_mismatch", evaluation.failures)

    def test_score_snapshot_bounds_are_validated(self) -> None:
        fixture = replace(
            build_list_basic_ready_for_review_fixture(),
            expected_score_snapshot_max=10,
        )
        evaluation = evaluate_recommendation_list_fixture(fixture)

        self.assertFalse(evaluation.passed)
        self.assertIn("score_snapshot_max_mismatch", evaluation.failures)
        for evaluation in evaluate_all_recommendation_list_fixtures():
            self.assertTrue(
                all(
                    0 <= snapshot <= SCORE_SCALE
                    for snapshot in evaluation.actual_score_snapshots
                )
            )

    def test_display_bucket_guardrail_is_validated(self) -> None:
        fixture = replace(
            build_list_basic_ready_for_review_fixture(),
            expected_display_buckets=("ranking_bucket",),
        )
        evaluation = evaluate_recommendation_list_fixture(fixture)

        self.assertFalse(evaluation.passed)
        self.assertIn("display_buckets_mismatch", evaluation.failures)
        for evaluation in evaluate_all_recommendation_list_fixtures():
            for bucket in evaluation.actual_display_buckets:
                self.assertNotIn("rank", bucket)
                self.assertNotIn("priority", bucket)

    def test_component_names_are_validated(self) -> None:
        fixture = replace(
            build_list_basic_ready_for_review_fixture(),
            expected_component_names=("data_completeness",),
        )
        evaluation = evaluate_recommendation_list_fixture(fixture)

        self.assertFalse(evaluation.passed)
        self.assertIn("component_names_mismatch", evaluation.failures)
        for evaluation in evaluate_all_recommendation_list_fixtures():
            self.assertEqual(
                evaluation.actual_component_names,
                ALLOWED_SCORE_COMPONENT_NAMES,
            )

    def test_required_flags_are_all_false(self) -> None:
        for evaluation in evaluate_all_recommendation_list_fixtures():
            self.assertEqual(
                evaluation.actual_required_flags,
                tuple(
                    f"{flag}=false"
                    for flag in RECOMMENDATION_LIST_FIXTURE_REQUIRED_FALSE_FLAGS
                ),
            )
            self.assertFalse(
                any(flag.endswith("=true") for flag in evaluation.actual_required_flags)
            )

    def test_forbidden_output_fields_are_not_copied_to_output_model(self) -> None:
        rendered = repr(evaluate_all_recommendation_list_fixtures())

        for keyword in FORBIDDEN_RECOMMENDATION_LIST_FIXTURE_OUTPUT_KEYWORDS:
            self.assertNotIn(keyword, rendered)

    def test_forbidden_action_status_is_not_generated_as_output(self) -> None:
        produced_values: list[str] = []
        for evaluation in evaluate_all_recommendation_list_fixtures():
            produced_values.extend(evaluation.actual_item_statuses)
            produced_values.extend(evaluation.actual_display_buckets)
            produced_values.extend(evaluation.actual_component_names)
            produced_values.extend(evaluation.actual_blocked_reasons)

        for forbidden_label in (
            *FORBIDDEN_RECOMMENDATION_LIST_ACTION_LABELS,
            *FORBIDDEN_RECOMMENDATION_LIST_RECOMMENDATION_LABELS,
            *FORBIDDEN_RECOMMENDATION_LIST_RANKING_LABELS,
            "ranking_position",
            "priority",
        ):
            self.assertNotIn(forbidden_label, produced_values)

    def test_fixture_items_are_available_without_actual_list_generation(self) -> None:
        items = build_recommendation_list_items_from_fixture(
            build_list_basic_ready_for_review_fixture()
        )
        grouped_items = build_recommendation_list_items_from_all_list_fixtures()

        self.assertEqual(len(items), 2)
        self.assertEqual(len(grouped_items), 8)
        for group in grouped_items:
            for item in group:
                self.assertFalse(hasattr(item, "ranking_position"))
                self.assertFalse(hasattr(item, "rank"))
                self.assertFalse(hasattr(item, "action"))

    def test_module_structure_has_no_io_or_external_dependencies(self) -> None:
        runtime_modules = {
            getattr(value, "__module__", "") for value in vars(list_fixtures).values()
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

        called_names = _fixture_module_code_names()
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
            for part in (*vars(list_fixtures), *_fixture_module_constants())
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
            ".env.local=",
            "local_snapshot_latest_read_model",
        ):
            self.assertNotIn(forbidden, module_symbols)

    def test_existing_contract_modules_are_not_referenced_as_paths(self) -> None:
        constants = _fixture_module_constants()

        self.assertNotIn("app/streamlit_app.py", constants)
        self.assertNotIn("recommendation_list_preflight.py", constants)
        self.assertNotIn("scoring_preflight.py", constants)
        self.assertNotIn("scoring_fixtures.py", constants)
        self.assertNotIn("scoring_fixture_hardening.py", constants)
        self.assertNotIn("scoring.py", constants)
        self.assertNotIn("feature_quality.py", constants)
        self.assertNotIn("feature_quality_fixtures.py", constants)
        self.assertNotIn("feature_extraction_preflight.py", constants)
        self.assertNotIn("feature_extraction_fixtures.py", constants)


def _fixture_module_code_names() -> set[str]:
    names: set[str] = set()
    for value in vars(list_fixtures).values():
        if isinstance(value, FunctionType):
            names.update(value.__code__.co_names)
    return names


def _fixture_module_constants() -> tuple[object, ...]:
    constants: list[object] = []
    for value in vars(list_fixtures).values():
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
