"""Offline tests for the MS-12.02 recommendation list fixture hardening."""

from dataclasses import FrozenInstanceError, fields
from types import FunctionType
import unittest

import ai_stock.recommendation.recommendation_list_fixture_hardening as hardening
from ai_stock.recommendation.recommendation_list_fixture_hardening import (
    FORBIDDEN_RECOMMENDATION_LIST_HARDENING_OUTPUT_KEYWORDS,
    RECOMMENDATION_LIST_FIXTURE_HARDENING_REQUIRED_FALSE_FLAGS,
    REQUIRED_RECOMMENDATION_LIST_DISPLAY_BUCKETS,
    RecommendationListFixtureHardeningResult,
    build_list_items_for_hardening_probe,
    build_recommendation_list_fixture_failure_probe,
    build_recommendation_list_fixture_hardening_policy,
    check_recommendation_list_fixture_component_names,
    check_recommendation_list_fixture_deterministic_repeated_runs,
    check_recommendation_list_fixture_display_buckets,
    check_recommendation_list_fixture_forbidden_output_absence,
    check_recommendation_list_fixture_required_flags_false,
    check_recommendation_list_fixture_scenarios_present,
    check_recommendation_list_fixture_score_snapshot_bounds,
    check_recommendation_list_fixture_summary_stability,
    evaluate_recommendation_list_fixture_failure_probe,
    run_recommendation_list_fixture_hardening_checks,
)
from ai_stock.recommendation.recommendation_list_fixtures import (
    ALLOWED_RECOMMENDATION_LIST_FIXTURE_SCENARIOS,
    build_list_basic_ready_for_review_fixture,
    evaluate_all_recommendation_list_fixtures,
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


class RecommendationListFixtureHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_recommendation_list_fixture_hardening_policy()

    def test_recommendation_list_fixture_hardening_policy_generation(self) -> None:
        self.assertEqual(self.policy.hardening_version, "MS-12.02")
        self.assertEqual(
            self.policy.hardening_scope,
            "recommendation_list_fixture_safety_determinism_guardrail",
        )
        self.assertEqual(
            self.policy.required_scenarios,
            ALLOWED_RECOMMENDATION_LIST_FIXTURE_SCENARIOS,
        )
        self.assertEqual(
            self.policy.required_item_statuses,
            ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES,
        )
        self.assertEqual(
            self.policy.required_display_buckets,
            REQUIRED_RECOMMENDATION_LIST_DISPLAY_BUCKETS,
        )
        self.assertEqual(
            self.policy.required_component_names,
            ALLOWED_SCORE_COMPONENT_NAMES,
        )
        self.assertEqual(self.policy.score_snapshot_min, 0)
        self.assertEqual(self.policy.score_snapshot_max, SCORE_SCALE)
        self.assertFalse(self.policy.recommendation_required)
        self.assertFalse(self.policy.ranking_required)
        self.assertFalse(self.policy.ui_required)
        with self.assertRaises(FrozenInstanceError):
            self.policy.ui_required = True

    def test_hardening_required_scenario_list(self) -> None:
        self.assertTrue(check_recommendation_list_fixture_scenarios_present(self.policy))
        self.assertIn("list_all_fixture_matrix", self.policy.required_scenarios)
        self.assertEqual(len(self.policy.required_scenarios), 8)

    def test_hardening_result_model_generation(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)
        field_names = tuple(
            field.name for field in fields(RecommendationListFixtureHardeningResult)
        )

        self.assertIn("checked_scenarios", field_names)
        self.assertIn("checked_item_count", field_names)
        self.assertIn("checked_display_buckets", field_names)
        self.assertIn("deterministic_repeated_run_passed", field_names)
        self.assertTrue(result.passed)
        with self.assertRaises(FrozenInstanceError):
            result.passed = False

    def test_run_recommendation_list_fixture_hardening_checks_passes(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)

        self.assertTrue(result.passed)
        self.assertEqual(result.failures, ())
        self.assertEqual(result.checked_item_count, 25)
        self.assertEqual(result.checked_score_snapshot_bounds, (0, SCORE_SCALE))

    def test_all_recommendation_list_fixture_evaluators_are_checked(self) -> None:
        evaluations = evaluate_all_recommendation_list_fixtures()
        result = run_recommendation_list_fixture_hardening_checks(self.policy)

        self.assertTrue(all(evaluation.passed for evaluation in evaluations))
        self.assertTrue(result.passed)
        self.assertEqual(
            result.checked_scenarios,
            tuple(evaluation.scenario for evaluation in evaluations),
        )

    def test_list_all_fixture_matrix_presence_is_checked(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)

        self.assertIn("list_all_fixture_matrix", result.checked_scenarios)
        self.assertGreaterEqual(result.checked_item_count, self.policy.min_item_count)

    def test_score_snapshot_bounds_hardening(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)

        self.assertTrue(
            check_recommendation_list_fixture_score_snapshot_bounds(self.policy)
        )
        self.assertGreaterEqual(result.checked_score_snapshot_bounds[0], 0)
        self.assertLessEqual(result.checked_score_snapshot_bounds[1], SCORE_SCALE)

    def test_display_bucket_guardrail_hardening(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)

        self.assertTrue(check_recommendation_list_fixture_display_buckets(self.policy))
        self.assertEqual(
            result.checked_display_buckets,
            REQUIRED_RECOMMENDATION_LIST_DISPLAY_BUCKETS,
        )
        for bucket in result.checked_display_buckets:
            self.assertNotIn("rank", bucket)
            self.assertNotIn("priority", bucket)
            self.assertNotIn("order", bucket)

    def test_component_names_hardening(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)

        self.assertTrue(check_recommendation_list_fixture_component_names(self.policy))
        self.assertEqual(result.checked_component_names, ALLOWED_SCORE_COMPONENT_NAMES)

    def test_allowed_item_statuses_only(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)

        self.assertTrue(
            set(result.checked_item_statuses).issubset(
                ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES
            )
        )
        self.assertIn("item_ready_for_review", result.checked_item_statuses)
        self.assertIn("item_empty_input", result.checked_item_statuses)

    def test_forbidden_item_status_is_not_used(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)
        produced_values = (
            result.checked_item_statuses
            + result.checked_display_buckets
            + result.checked_component_names
        )

        for forbidden in (
            *FORBIDDEN_RECOMMENDATION_LIST_ACTION_LABELS,
            *FORBIDDEN_RECOMMENDATION_LIST_RECOMMENDATION_LABELS,
            *FORBIDDEN_RECOMMENDATION_LIST_RANKING_LABELS,
            "ranking_position",
            "priority",
            "order",
        ):
            self.assertNotIn(forbidden, produced_values)

    def test_forbidden_output_field_absence(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)
        rendered = repr(result) + repr(evaluate_all_recommendation_list_fixtures())

        self.assertTrue(
            check_recommendation_list_fixture_forbidden_output_absence(self.policy)
        )
        self.assertTrue(result.checked_forbidden_output_absence)
        for keyword in FORBIDDEN_RECOMMENDATION_LIST_HARDENING_OUTPUT_KEYWORDS:
            self.assertNotIn(keyword, rendered)

    def test_required_flags_all_false(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)

        self.assertTrue(
            check_recommendation_list_fixture_required_flags_false(self.policy)
        )
        self.assertEqual(
            result.checked_required_false_flags,
            tuple(
                f"{flag}=false"
                for flag in RECOMMENDATION_LIST_FIXTURE_HARDENING_REQUIRED_FALSE_FLAGS
            ),
        )
        self.assertFalse(
            any(flag.endswith("=true") for flag in result.checked_required_false_flags)
        )

    def test_deterministic_repeated_run_passes(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)

        self.assertTrue(
            check_recommendation_list_fixture_deterministic_repeated_runs(self.policy)
        )
        self.assertTrue(result.deterministic_repeated_run_passed)
        self.assertEqual(
            run_recommendation_list_fixture_hardening_checks(self.policy),
            run_recommendation_list_fixture_hardening_checks(self.policy),
        )

    def test_summary_stability_passes(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)

        self.assertTrue(check_recommendation_list_fixture_summary_stability(self.policy))
        self.assertTrue(result.summary_stability_passed)

    def test_evaluator_mismatch_failure_probe_generates_failure(self) -> None:
        probe = build_recommendation_list_fixture_failure_probe()
        evaluation = evaluate_recommendation_list_fixture_failure_probe()

        self.assertEqual(probe.expected_item_statuses, ("item_empty_input",))
        self.assertFalse(evaluation.passed)
        self.assertIn("item_statuses_mismatch", evaluation.failures)
        self.assertTrue(
            run_recommendation_list_fixture_hardening_checks(
                self.policy
            ).evaluator_failure_injection_passed
        )

    def test_score_snapshot_is_not_directive_output(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)

        self.assertTrue(result.observation_only_guardrail_passed)
        self.assertIn(
            "score_snapshot_data_quality_preflight_only",
            result.diagnostics,
        )
        self.assertNotIn("recommendation", result.checked_item_statuses)
        self.assertNotIn("ranking", result.checked_item_statuses)
        self.assertNotIn("action", result.checked_item_statuses)

    def test_display_bucket_is_not_ranking_priority_or_order(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)

        self.assertIn("display_bucket_review_grouping_only", result.diagnostics)
        for bucket in result.checked_display_buckets:
            self.assertNotIn("rank", bucket)
            self.assertNotIn("priority", bucket)
            self.assertNotIn("order", bucket)

    def test_usable_for_future_list_is_not_ranking_flag(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)
        probe_items = build_list_items_for_hardening_probe(
            build_list_basic_ready_for_review_fixture()
        )

        self.assertTrue(result.observation_only_guardrail_passed)
        self.assertIn("usable_for_future_list_not_ranking_flag", result.diagnostics)
        for item in probe_items:
            self.assertIs(type(item.usable_for_future_list), bool)
            self.assertFalse(hasattr(item, "ranking_position"))
            self.assertFalse(hasattr(item, "rank"))

    def test_forbidden_action_status_is_not_generated_as_output(self) -> None:
        result = run_recommendation_list_fixture_hardening_checks(self.policy)
        produced_values = result.checked_item_statuses + result.checked_display_buckets

        for forbidden_label in (
            *FORBIDDEN_RECOMMENDATION_LIST_ACTION_LABELS,
            *FORBIDDEN_RECOMMENDATION_LIST_RECOMMENDATION_LABELS,
            *FORBIDDEN_RECOMMENDATION_LIST_RANKING_LABELS,
            "ranking_position",
            "priority",
            "order",
        ):
            self.assertNotIn(forbidden_label, produced_values)

    def test_module_structure_has_no_io_or_external_dependencies(self) -> None:
        runtime_modules = {
            getattr(value, "__module__", "") for value in vars(hardening).values()
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

        called_names = _hardening_module_code_names()
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
            for part in (*vars(hardening), *_hardening_module_constants())
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
        constants = _hardening_module_constants()

        self.assertNotIn("app/streamlit_app.py", constants)
        self.assertNotIn("recommendation_list_preflight.py", constants)
        self.assertNotIn("recommendation_list_fixtures.py", constants)
        self.assertNotIn("scoring_preflight.py", constants)
        self.assertNotIn("scoring_fixtures.py", constants)
        self.assertNotIn("scoring_fixture_hardening.py", constants)
        self.assertNotIn("scoring.py", constants)
        self.assertNotIn("feature_quality.py", constants)
        self.assertNotIn("feature_quality_fixtures.py", constants)
        self.assertNotIn("feature_extraction_preflight.py", constants)
        self.assertNotIn("feature_extraction_fixtures.py", constants)


def _hardening_module_code_names() -> set[str]:
    names: set[str] = set()
    for value in vars(hardening).values():
        if isinstance(value, FunctionType):
            names.update(value.__code__.co_names)
    return names


def _hardening_module_constants() -> tuple[object, ...]:
    constants: list[object] = []
    for value in vars(hardening).values():
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
