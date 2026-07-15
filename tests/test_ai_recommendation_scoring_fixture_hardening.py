"""Offline tests for the MS-11.02 scoring fixture hardening layer."""

from dataclasses import FrozenInstanceError, fields
from types import FunctionType
import unittest

import ai_stock.recommendation.scoring_fixture_hardening as hardening
from ai_stock.recommendation.scoring_fixture_hardening import (
    FORBIDDEN_SCORING_HARDENING_OUTPUT_KEYWORDS,
    SCORING_FIXTURE_HARDENING_REQUIRED_FALSE_FLAGS,
    ScoringFixtureHardeningResult,
    build_scoring_fixture_failure_probe,
    build_scoring_fixture_hardening_policy,
    check_scoring_fixture_component_names,
    check_scoring_fixture_deterministic_repeated_runs,
    check_scoring_fixture_forbidden_output_absence,
    check_scoring_fixture_required_flags_false,
    check_scoring_fixture_scenarios_present,
    check_scoring_fixture_summary_stability,
    check_scoring_fixture_total_score_bounds,
    evaluate_scoring_fixture_failure_probe,
    run_scoring_fixture_hardening_checks,
)
from ai_stock.recommendation.scoring_fixtures import (
    ALLOWED_SCORING_FIXTURE_SCENARIOS,
    evaluate_all_scoring_fixtures,
)
from ai_stock.recommendation.scoring_preflight import (
    ALLOWED_SCORE_COMPONENT_NAMES,
    ALLOWED_SCORING_STATUSES,
    FORBIDDEN_SCORING_ACTION_LABELS,
    FORBIDDEN_SCORING_RECOMMENDATION_LABELS,
    SCORE_SCALE,
)


class ScoringFixtureHardeningTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_scoring_fixture_hardening_policy()

    def test_scoring_fixture_hardening_policy_generation(self) -> None:
        self.assertEqual(self.policy.hardening_version, "MS-11.02")
        self.assertEqual(
            self.policy.hardening_scope,
            "scoring_fixture_safety_determinism_guardrail",
        )
        self.assertEqual(
            self.policy.required_scenarios,
            ALLOWED_SCORING_FIXTURE_SCENARIOS,
        )
        self.assertEqual(
            self.policy.required_component_names,
            ALLOWED_SCORE_COMPONENT_NAMES,
        )
        self.assertEqual(self.policy.required_statuses, ALLOWED_SCORING_STATUSES)
        self.assertEqual(self.policy.total_score_min, 0)
        self.assertEqual(self.policy.total_score_max, SCORE_SCALE)
        self.assertFalse(self.policy.recommendation_required)
        self.assertFalse(self.policy.ranking_required)
        self.assertFalse(self.policy.ui_required)
        with self.assertRaises(FrozenInstanceError):
            self.policy.ui_required = True

    def test_hardening_required_scenario_list(self) -> None:
        self.assertTrue(check_scoring_fixture_scenarios_present(self.policy))
        self.assertIn("scoring_all_fixture_matrix", self.policy.required_scenarios)
        self.assertEqual(len(self.policy.required_scenarios), 8)

    def test_hardening_result_model_generation(self) -> None:
        result = run_scoring_fixture_hardening_checks(self.policy)
        field_names = tuple(field.name for field in fields(ScoringFixtureHardeningResult))

        self.assertIn("checked_scenarios", field_names)
        self.assertIn("checked_result_count", field_names)
        self.assertIn("checked_total_score_bounds", field_names)
        self.assertIn("deterministic_repeated_run_passed", field_names)
        self.assertTrue(result.passed)
        with self.assertRaises(FrozenInstanceError):
            result.passed = False

    def test_run_scoring_fixture_hardening_checks_passes(self) -> None:
        result = run_scoring_fixture_hardening_checks(self.policy)

        self.assertTrue(result.passed)
        self.assertEqual(result.failures, ())
        self.assertEqual(result.checked_result_count, 11)
        self.assertEqual(result.checked_total_score_bounds, (0, SCORE_SCALE))

    def test_all_scoring_fixture_evaluators_are_checked(self) -> None:
        evaluations = evaluate_all_scoring_fixtures()
        result = run_scoring_fixture_hardening_checks(self.policy)

        self.assertTrue(all(evaluation.passed for evaluation in evaluations))
        self.assertTrue(result.passed)
        self.assertEqual(
            result.checked_scenarios,
            tuple(evaluation.scenario for evaluation in evaluations),
        )

    def test_scoring_all_fixture_matrix_presence_is_checked(self) -> None:
        result = run_scoring_fixture_hardening_checks(self.policy)

        self.assertIn("scoring_all_fixture_matrix", result.checked_scenarios)
        self.assertEqual(result.checked_result_count, 11)

    def test_total_score_bounds_hardening(self) -> None:
        result = run_scoring_fixture_hardening_checks(self.policy)

        self.assertTrue(check_scoring_fixture_total_score_bounds(self.policy))
        self.assertGreaterEqual(result.checked_total_score_bounds[0], 0)
        self.assertLessEqual(result.checked_total_score_bounds[1], SCORE_SCALE)

    def test_score_component_names_hardening(self) -> None:
        result = run_scoring_fixture_hardening_checks(self.policy)

        self.assertTrue(check_scoring_fixture_component_names(self.policy))
        self.assertEqual(result.checked_component_names, ALLOWED_SCORE_COMPONENT_NAMES)

    def test_allowed_scoring_statuses_only(self) -> None:
        result = run_scoring_fixture_hardening_checks(self.policy)

        self.assertTrue(set(result.checked_statuses).issubset(ALLOWED_SCORING_STATUSES))
        self.assertIn("score_ready", result.checked_statuses)
        self.assertIn("score_empty_input", result.checked_statuses)

    def test_forbidden_scoring_status_is_not_used(self) -> None:
        result = run_scoring_fixture_hardening_checks(self.policy)
        produced_values = result.checked_statuses + result.checked_component_names

        for forbidden in (
            *FORBIDDEN_SCORING_ACTION_LABELS,
            *FORBIDDEN_SCORING_RECOMMENDATION_LABELS,
        ):
            self.assertNotIn(forbidden, produced_values)

    def test_forbidden_output_field_absence(self) -> None:
        result = run_scoring_fixture_hardening_checks(self.policy)
        rendered = repr(result) + repr(evaluate_all_scoring_fixtures())

        self.assertTrue(check_scoring_fixture_forbidden_output_absence(self.policy))
        self.assertTrue(result.checked_forbidden_output_absence)
        for keyword in FORBIDDEN_SCORING_HARDENING_OUTPUT_KEYWORDS:
            self.assertNotIn(keyword, rendered)

    def test_required_flags_all_false(self) -> None:
        result = run_scoring_fixture_hardening_checks(self.policy)

        self.assertTrue(check_scoring_fixture_required_flags_false(self.policy))
        self.assertEqual(
            result.checked_required_false_flags,
            tuple(
                f"{flag}=false"
                for flag in SCORING_FIXTURE_HARDENING_REQUIRED_FALSE_FLAGS
            ),
        )
        self.assertFalse(
            any(flag.endswith("=true") for flag in result.checked_required_false_flags)
        )

    def test_deterministic_repeated_run_passes(self) -> None:
        result = run_scoring_fixture_hardening_checks(self.policy)

        self.assertTrue(check_scoring_fixture_deterministic_repeated_runs(self.policy))
        self.assertTrue(result.deterministic_repeated_run_passed)
        self.assertEqual(
            run_scoring_fixture_hardening_checks(self.policy),
            run_scoring_fixture_hardening_checks(self.policy),
        )

    def test_summary_stability_passes(self) -> None:
        result = run_scoring_fixture_hardening_checks(self.policy)

        self.assertTrue(check_scoring_fixture_summary_stability(self.policy))
        self.assertTrue(result.summary_stability_passed)

    def test_evaluator_mismatch_failure_probe_generates_failure(self) -> None:
        probe = build_scoring_fixture_failure_probe()
        evaluation = evaluate_scoring_fixture_failure_probe()

        self.assertEqual(probe.expected_scoring_statuses, ("score_empty_input",))
        self.assertFalse(evaluation.passed)
        self.assertIn("scoring_statuses_mismatch", evaluation.failures)
        self.assertTrue(
            run_scoring_fixture_hardening_checks(
                self.policy
            ).evaluator_failure_injection_passed
        )

    def test_total_score_is_not_directive_output(self) -> None:
        result = run_scoring_fixture_hardening_checks(self.policy)

        self.assertTrue(result.observation_only_guardrail_passed)
        self.assertIn(
            "total_score_data_quality_preflight_only",
            result.diagnostics,
        )
        self.assertNotIn("recommendation", result.checked_statuses)
        self.assertNotIn("ranking", result.checked_statuses)
        self.assertNotIn("action", result.checked_statuses)

    def test_forbidden_action_status_is_not_generated_as_output(self) -> None:
        result = run_scoring_fixture_hardening_checks(self.policy)
        produced_values = result.checked_statuses + result.checked_component_names

        for forbidden_label in (
            *FORBIDDEN_SCORING_ACTION_LABELS,
            *FORBIDDEN_SCORING_RECOMMENDATION_LABELS,
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
        self.assertNotIn("scoring_preflight.py", constants)
        self.assertNotIn("scoring_fixtures.py", constants)
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
