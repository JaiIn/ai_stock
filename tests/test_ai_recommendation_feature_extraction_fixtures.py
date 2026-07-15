"""Offline tests for the MS-10.03 feature extraction fixture hardening."""

from dataclasses import FrozenInstanceError, replace
from types import FunctionType
import unittest

import ai_stock.recommendation.feature_extraction_fixtures as extraction_fixtures
from ai_stock.recommendation.feature_extraction_fixtures import (
    ALLOWED_FEATURE_EXTRACTION_FIXTURE_SCENARIOS,
    FEATURE_EXTRACTION_FIXTURE_REQUIRED_FALSE_FLAGS,
    FORBIDDEN_FEATURE_EXTRACTION_FIXTURE_SCENARIOS,
    FORBIDDEN_FEATURE_EXTRACTION_OUTPUT_KEYWORDS,
    FeatureExtractionFixtureScenario,
    build_all_feature_extraction_fixtures,
    build_extraction_all_fixture_matrix,
    build_extraction_basic_ready_fixture,
    build_extraction_disabled_blocked_fixture,
    build_extraction_duplicates_blocked_fixture,
    build_extraction_empty_input_fixture,
    build_extraction_forbidden_field_sanitized_fixture,
    build_extraction_missing_data_blocked_fixture,
    build_extraction_mixed_review_fixture,
    build_feature_extraction_fixture_policy,
    evaluate_all_feature_extraction_fixtures,
    evaluate_feature_extraction_fixture,
)
from ai_stock.recommendation.feature_extraction_preflight import (
    FORBIDDEN_EXTRACTION_OUTPUT_LABELS,
)


class FeatureExtractionFixtureHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_feature_extraction_fixture_policy()

    def test_feature_extraction_fixture_policy_generation(self) -> None:
        self.assertEqual(self.policy.stage_name, "MS-10.03")
        self.assertEqual(
            self.policy.mode,
            "feature_extraction_fixture_hardening",
        )
        self.assertEqual(
            self.policy.allowed_scenarios,
            ALLOWED_FEATURE_EXTRACTION_FIXTURE_SCENARIOS,
        )
        self.assertIn(
            "toss_api_response_fixture",
            FORBIDDEN_FEATURE_EXTRACTION_FIXTURE_SCENARIOS,
        )
        self.assertFalse(self.policy.scoring_required)
        self.assertFalse(self.policy.ranking_required)
        self.assertFalse(self.policy.recommendation_required)
        with self.assertRaises(FrozenInstanceError):
            self.policy.ui_required = True

    def test_all_extraction_fixture_scenarios_are_generated(self) -> None:
        fixtures = build_all_feature_extraction_fixtures()

        self.assertEqual(
            tuple(fixture.scenario for fixture in fixtures),
            tuple(scenario.value for scenario in FeatureExtractionFixtureScenario),
        )
        self.assertEqual(len(fixtures), 8)
        for fixture in fixtures:
            self.assertEqual(
                fixture.expected_required_false_flags,
                tuple(
                    f"{flag}=false"
                    for flag in FEATURE_EXTRACTION_FIXTURE_REQUIRED_FALSE_FLAGS
                ),
            )

    def test_all_extraction_fixture_scenarios_are_deterministic(self) -> None:
        self.assertEqual(
            build_all_feature_extraction_fixtures(),
            build_all_feature_extraction_fixtures(),
        )
        self.assertEqual(
            evaluate_all_feature_extraction_fixtures(),
            evaluate_all_feature_extraction_fixtures(),
        )

    def test_all_extraction_fixture_evaluators_pass(self) -> None:
        evaluations = evaluate_all_feature_extraction_fixtures()

        self.assertEqual(len(evaluations), 8)
        self.assertTrue(all(evaluation.passed for evaluation in evaluations))
        self.assertTrue(all(not evaluation.failures for evaluation in evaluations))

    def test_extraction_basic_ready_processing(self) -> None:
        evaluation = evaluate_feature_extraction_fixture(
            build_extraction_basic_ready_fixture()
        )

        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.actual_extraction_statuses,
            ("extraction_ready", "extraction_ready"),
        )
        self.assertEqual(evaluation.actual_ready_count, 2)
        self.assertEqual(evaluation.actual_needs_review_count, 0)
        self.assertEqual(evaluation.actual_usable_for_future_scoring_count, 2)

    def test_extraction_mixed_review_processing(self) -> None:
        evaluation = evaluate_feature_extraction_fixture(
            build_extraction_mixed_review_fixture()
        )

        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.actual_extraction_statuses,
            (
                "extraction_ready",
                "extraction_invalid_candidate",
                "extraction_invalid_candidate",
            ),
        )
        self.assertEqual(evaluation.actual_needs_review_count, 2)
        self.assertIn("invalid_symbol_review", evaluation.actual_warnings)

    def test_extraction_duplicates_blocked_processing(self) -> None:
        evaluation = evaluate_feature_extraction_fixture(
            build_extraction_duplicates_blocked_fixture()
        )

        self.assertTrue(evaluation.passed)
        self.assertIn(
            "extraction_duplicate_candidate",
            evaluation.actual_extraction_statuses,
        )
        self.assertIn("duplicate_symbol", evaluation.actual_diagnostics)
        self.assertIn(
            "duplicate_candidate_needs_review",
            evaluation.actual_warnings,
        )

    def test_extraction_disabled_blocked_processing(self) -> None:
        evaluation = evaluate_feature_extraction_fixture(
            build_extraction_disabled_blocked_fixture()
        )

        self.assertTrue(evaluation.passed)
        self.assertIn(
            "extraction_disabled_candidate",
            evaluation.actual_extraction_statuses,
        )
        self.assertIn("candidate_disabled", evaluation.actual_diagnostics)
        self.assertIn(
            "disabled_candidate_not_selectable",
            evaluation.actual_warnings,
        )

    def test_extraction_missing_data_blocked_processing(self) -> None:
        evaluation = evaluate_feature_extraction_fixture(
            build_extraction_missing_data_blocked_fixture()
        )

        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.actual_extraction_statuses,
            ("extraction_missing_data",),
        )
        self.assertEqual(evaluation.actual_ready_count, 0)
        self.assertIn("symbol_identity", evaluation.actual_missing_features)
        self.assertIn("insufficient_data_review", evaluation.actual_warnings)

    def test_extraction_forbidden_field_sanitized_processing(self) -> None:
        evaluation = evaluate_feature_extraction_fixture(
            build_extraction_forbidden_field_sanitized_fixture()
        )
        rendered = repr(evaluation)

        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.actual_extraction_statuses,
            ("extraction_forbidden_field_sanitized",),
        )
        self.assertTrue(evaluation.forbidden_absent_check_passed)
        self.assertIn(
            "forbidden_field_detected:accountSeq",
            evaluation.actual_diagnostics,
        )
        for keyword in FORBIDDEN_FEATURE_EXTRACTION_OUTPUT_KEYWORDS:
            self.assertNotIn(keyword, rendered)

    def test_extraction_empty_input_processing(self) -> None:
        evaluation = evaluate_feature_extraction_fixture(
            build_extraction_empty_input_fixture()
        )

        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.actual_extraction_statuses,
            ("extraction_empty_input",),
        )
        self.assertEqual(evaluation.actual_needs_review_count, 1)
        self.assertIn("symbol_identity", evaluation.actual_missing_features)
        self.assertIn("empty_source_items", evaluation.actual_diagnostics)

    def test_extraction_all_fixture_matrix_processing(self) -> None:
        evaluation = evaluate_feature_extraction_fixture(
            build_extraction_all_fixture_matrix()
        )

        self.assertTrue(evaluation.passed)
        self.assertEqual(len(evaluation.actual_extraction_statuses), 11)
        self.assertEqual(evaluation.actual_ready_count, 4)
        self.assertEqual(evaluation.actual_needs_review_count, 7)
        self.assertEqual(evaluation.actual_usable_for_future_scoring_count, 4)
        self.assertIn(
            "extraction_forbidden_field_sanitized",
            evaluation.actual_extraction_statuses,
        )

    def test_expected_vs_actual_mismatch_generates_failure(self) -> None:
        fixture = build_extraction_basic_ready_fixture()
        mismatched = replace(
            fixture,
            expected_extraction_statuses=("extraction_empty_input",),
        )
        evaluation = evaluate_feature_extraction_fixture(mismatched)

        self.assertFalse(evaluation.passed)
        self.assertIn("extraction_statuses_mismatch", evaluation.failures)

    def test_required_flags_are_all_false(self) -> None:
        for evaluation in evaluate_all_feature_extraction_fixtures():
            self.assertEqual(
                evaluation.actual_required_flags,
                tuple(
                    f"{flag}=false"
                    for flag in FEATURE_EXTRACTION_FIXTURE_REQUIRED_FALSE_FLAGS
                ),
            )
            self.assertFalse(
                any(flag.endswith("=true") for flag in evaluation.actual_required_flags)
            )

    def test_forbidden_output_fields_are_not_copied_to_output_model(self) -> None:
        rendered = repr(evaluate_all_feature_extraction_fixtures())

        for keyword in FORBIDDEN_FEATURE_EXTRACTION_OUTPUT_KEYWORDS:
            self.assertNotIn(keyword, rendered)

    def test_forbidden_action_status_is_not_generated_as_output(self) -> None:
        produced_values: list[str] = []
        for evaluation in evaluate_all_feature_extraction_fixtures():
            produced_values.extend(evaluation.actual_extraction_statuses)
            produced_values.extend(evaluation.actual_blocked_reasons)

        for forbidden_label in FORBIDDEN_EXTRACTION_OUTPUT_LABELS:
            self.assertNotIn(forbidden_label, produced_values)

    def test_module_structure_has_no_io_or_external_dependencies(self) -> None:
        runtime_modules = {
            getattr(value, "__module__", "")
            for value in vars(extraction_fixtures).values()
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
            for part in (*vars(extraction_fixtures), *_fixture_module_constants())
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
        self.assertNotIn("feature_quality.py", constants)
        self.assertNotIn("feature_quality_fixtures.py", constants)
        self.assertNotIn("feature_extraction_preflight.py", constants)
        self.assertNotIn("dashboard_preflight.py", constants)
        self.assertNotIn("watchlist_fixtures.py", constants)


def _fixture_module_code_names() -> set[str]:
    names: set[str] = set()
    for value in vars(extraction_fixtures).values():
        if isinstance(value, FunctionType):
            names.update(value.__code__.co_names)
    return names


def _fixture_module_constants() -> tuple[object, ...]:
    constants: list[object] = []
    for value in vars(extraction_fixtures).values():
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
