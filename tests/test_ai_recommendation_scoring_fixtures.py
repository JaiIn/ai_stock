"""Offline tests for the MS-11.01 scoring fixture expansion."""

from dataclasses import FrozenInstanceError, replace
from types import FunctionType
import unittest

import ai_stock.recommendation.scoring_fixtures as scoring_fixtures
from ai_stock.recommendation.scoring_fixtures import (
    ALLOWED_SCORING_FIXTURE_SCENARIOS,
    FORBIDDEN_SCORING_FIXTURE_SCENARIOS,
    FORBIDDEN_SCORING_OUTPUT_KEYWORDS,
    SCORING_FIXTURE_REQUIRED_FALSE_FLAGS,
    ScoringFixtureScenario,
    build_all_scoring_fixtures,
    build_scoring_all_fixture_matrix,
    build_scoring_basic_ready_fixture,
    build_scoring_disabled_blocked_fixture,
    build_scoring_duplicates_blocked_fixture,
    build_scoring_empty_input_fixture,
    build_scoring_fixture_policy,
    build_scoring_forbidden_field_sanitized_fixture,
    build_scoring_missing_data_blocked_fixture,
    build_scoring_mixed_review_fixture,
    evaluate_all_scoring_fixtures,
    evaluate_scoring_fixture,
)
from ai_stock.recommendation.scoring_preflight import (
    ALLOWED_SCORE_COMPONENT_NAMES,
    FORBIDDEN_SCORING_ACTION_LABELS,
    FORBIDDEN_SCORING_RECOMMENDATION_LABELS,
    SCORE_SCALE,
)


class ScoringFixtureExpansionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_scoring_fixture_policy()

    def test_scoring_fixture_policy_generation(self) -> None:
        self.assertEqual(self.policy.stage_name, "MS-11.01")
        self.assertEqual(self.policy.mode, "scoring_fixture_expansion")
        self.assertEqual(
            self.policy.allowed_scenarios,
            ALLOWED_SCORING_FIXTURE_SCENARIOS,
        )
        self.assertIn(
            "recommendation_fixture",
            FORBIDDEN_SCORING_FIXTURE_SCENARIOS,
        )
        self.assertEqual(
            self.policy.allowed_score_component_names,
            ALLOWED_SCORE_COMPONENT_NAMES,
        )
        self.assertFalse(self.policy.ranking_required)
        self.assertFalse(self.policy.recommendation_required)
        self.assertFalse(self.policy.ui_required)
        with self.assertRaises(FrozenInstanceError):
            self.policy.ui_required = True

    def test_all_scoring_fixture_scenarios_are_generated(self) -> None:
        fixtures = build_all_scoring_fixtures()

        self.assertEqual(
            tuple(fixture.scenario for fixture in fixtures),
            tuple(scenario.value for scenario in ScoringFixtureScenario),
        )
        self.assertEqual(len(fixtures), 8)
        for fixture in fixtures:
            self.assertEqual(
                fixture.expected_required_false_flags,
                tuple(
                    f"{flag}=false" for flag in SCORING_FIXTURE_REQUIRED_FALSE_FLAGS
                ),
            )

    def test_all_scoring_fixture_scenarios_are_deterministic(self) -> None:
        self.assertEqual(build_all_scoring_fixtures(), build_all_scoring_fixtures())
        self.assertEqual(
            evaluate_all_scoring_fixtures(),
            evaluate_all_scoring_fixtures(),
        )

    def test_all_scoring_fixture_evaluators_pass(self) -> None:
        evaluations = evaluate_all_scoring_fixtures()

        self.assertEqual(len(evaluations), 8)
        self.assertTrue(all(evaluation.passed for evaluation in evaluations))
        self.assertTrue(all(not evaluation.failures for evaluation in evaluations))

    def test_scoring_basic_ready_processing(self) -> None:
        evaluation = evaluate_scoring_fixture(build_scoring_basic_ready_fixture())

        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.actual_scoring_statuses,
            ("score_ready", "score_ready"),
        )
        self.assertEqual(evaluation.actual_ready_count, 2)
        self.assertEqual(evaluation.actual_needs_review_count, 0)
        self.assertEqual(evaluation.actual_usable_for_future_ranking_count, 2)
        self.assertEqual(evaluation.actual_total_scores, (SCORE_SCALE, SCORE_SCALE))

    def test_scoring_mixed_review_processing(self) -> None:
        evaluation = evaluate_scoring_fixture(build_scoring_mixed_review_fixture())

        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.actual_scoring_statuses,
            (
                "score_ready",
                "score_invalid_candidate",
                "score_invalid_candidate",
            ),
        )
        self.assertEqual(evaluation.actual_needs_review_count, 2)
        self.assertIn("invalid_symbol_review", evaluation.actual_warnings)

    def test_scoring_duplicates_blocked_processing(self) -> None:
        evaluation = evaluate_scoring_fixture(
            build_scoring_duplicates_blocked_fixture()
        )

        self.assertTrue(evaluation.passed)
        self.assertIn(
            "score_duplicate_candidate",
            evaluation.actual_scoring_statuses,
        )
        self.assertIn("duplicate_symbol", evaluation.actual_diagnostics)
        self.assertIn(
            "duplicate_candidate_needs_review",
            evaluation.actual_warnings,
        )

    def test_scoring_disabled_blocked_processing(self) -> None:
        evaluation = evaluate_scoring_fixture(build_scoring_disabled_blocked_fixture())

        self.assertTrue(evaluation.passed)
        self.assertIn(
            "score_disabled_candidate",
            evaluation.actual_scoring_statuses,
        )
        self.assertIn("candidate_disabled", evaluation.actual_diagnostics)
        self.assertIn(
            "disabled_candidate_not_selectable",
            evaluation.actual_warnings,
        )

    def test_scoring_missing_data_blocked_processing(self) -> None:
        evaluation = evaluate_scoring_fixture(
            build_scoring_missing_data_blocked_fixture()
        )

        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.actual_scoring_statuses,
            ("score_missing_data",),
        )
        self.assertEqual(evaluation.actual_ready_count, 0)
        self.assertEqual(evaluation.actual_total_scores, (20,))
        self.assertIn("insufficient_data_review", evaluation.actual_warnings)

    def test_scoring_forbidden_field_sanitized_processing(self) -> None:
        evaluation = evaluate_scoring_fixture(
            build_scoring_forbidden_field_sanitized_fixture()
        )
        rendered = repr(evaluation)

        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.actual_scoring_statuses,
            ("score_forbidden_field_sanitized",),
        )
        self.assertEqual(evaluation.actual_total_scores, (0,))
        self.assertTrue(evaluation.forbidden_absent_check_passed)
        self.assertIn(
            "forbidden_field_detected:accountSeq",
            evaluation.actual_diagnostics,
        )
        for keyword in FORBIDDEN_SCORING_OUTPUT_KEYWORDS:
            self.assertNotIn(keyword, rendered)

    def test_scoring_empty_input_processing(self) -> None:
        evaluation = evaluate_scoring_fixture(build_scoring_empty_input_fixture())

        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.actual_scoring_statuses,
            ("score_empty_input",),
        )
        self.assertEqual(evaluation.actual_needs_review_count, 1)
        self.assertIn("empty_source_items", evaluation.actual_diagnostics)

    def test_scoring_all_fixture_matrix_processing(self) -> None:
        evaluation = evaluate_scoring_fixture(build_scoring_all_fixture_matrix())

        self.assertTrue(evaluation.passed)
        self.assertEqual(len(evaluation.actual_scoring_statuses), 11)
        self.assertEqual(evaluation.actual_ready_count, 4)
        self.assertEqual(evaluation.actual_needs_review_count, 7)
        self.assertEqual(evaluation.actual_usable_for_future_ranking_count, 4)
        self.assertIn(
            "score_forbidden_field_sanitized",
            evaluation.actual_scoring_statuses,
        )

    def test_expected_vs_actual_mismatch_generates_failure(self) -> None:
        fixture = build_scoring_basic_ready_fixture()
        mismatched = replace(
            fixture,
            expected_scoring_statuses=("score_empty_input",),
        )
        evaluation = evaluate_scoring_fixture(mismatched)

        self.assertFalse(evaluation.passed)
        self.assertIn("scoring_statuses_mismatch", evaluation.failures)

    def test_total_score_bounds_are_validated(self) -> None:
        fixture = replace(
            build_scoring_basic_ready_fixture(),
            expected_total_score_max=10,
        )
        evaluation = evaluate_scoring_fixture(fixture)

        self.assertFalse(evaluation.passed)
        self.assertIn("total_score_max_mismatch", evaluation.failures)
        for evaluation in evaluate_all_scoring_fixtures():
            self.assertTrue(
                all(0 <= score <= SCORE_SCALE for score in evaluation.actual_total_scores)
            )

    def test_score_component_names_are_validated(self) -> None:
        fixture = replace(
            build_scoring_basic_ready_fixture(),
            expected_component_names=("data_completeness",),
        )
        evaluation = evaluate_scoring_fixture(fixture)

        self.assertFalse(evaluation.passed)
        self.assertIn("score_component_names_mismatch", evaluation.failures)
        for evaluation in evaluate_all_scoring_fixtures():
            self.assertEqual(
                evaluation.actual_score_components,
                ALLOWED_SCORE_COMPONENT_NAMES,
            )

    def test_required_flags_are_all_false(self) -> None:
        for evaluation in evaluate_all_scoring_fixtures():
            self.assertEqual(
                evaluation.actual_required_flags,
                tuple(
                    f"{flag}=false" for flag in SCORING_FIXTURE_REQUIRED_FALSE_FLAGS
                ),
            )
            self.assertFalse(
                any(flag.endswith("=true") for flag in evaluation.actual_required_flags)
            )

    def test_forbidden_output_fields_are_not_copied_to_output_model(self) -> None:
        rendered = repr(evaluate_all_scoring_fixtures())

        for keyword in FORBIDDEN_SCORING_OUTPUT_KEYWORDS:
            self.assertNotIn(keyword, rendered)

    def test_forbidden_action_status_is_not_generated_as_output(self) -> None:
        produced_values: list[str] = []
        for evaluation in evaluate_all_scoring_fixtures():
            produced_values.extend(evaluation.actual_scoring_statuses)
            produced_values.extend(evaluation.actual_score_components)
            produced_values.extend(evaluation.actual_blocked_reasons)

        for forbidden_label in (
            *FORBIDDEN_SCORING_ACTION_LABELS,
            *FORBIDDEN_SCORING_RECOMMENDATION_LABELS,
        ):
            self.assertNotIn(forbidden_label, produced_values)

    def test_module_structure_has_no_io_or_external_dependencies(self) -> None:
        runtime_modules = {
            getattr(value, "__module__", "")
            for value in vars(scoring_fixtures).values()
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
            for part in (*vars(scoring_fixtures), *_fixture_module_constants())
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
        self.assertNotIn("scoring_preflight.py", constants)
        self.assertNotIn("feature_quality.py", constants)
        self.assertNotIn("feature_quality_fixtures.py", constants)
        self.assertNotIn("feature_extraction_preflight.py", constants)
        self.assertNotIn("feature_extraction_fixtures.py", constants)


def _fixture_module_code_names() -> set[str]:
    names: set[str] = set()
    for value in vars(scoring_fixtures).values():
        if isinstance(value, FunctionType):
            names.update(value.__code__.co_names)
    return names


def _fixture_module_constants() -> tuple[object, ...]:
    constants: list[object] = []
    for value in vars(scoring_fixtures).values():
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
