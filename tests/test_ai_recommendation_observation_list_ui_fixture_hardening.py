"""Offline tests for the MS-13.02 observation-list UI fixture hardening."""

from dataclasses import FrozenInstanceError, fields
from types import FunctionType
import unittest

import ai_stock.recommendation.observation_list_ui_fixture_hardening as hardening
from ai_stock.recommendation.observation_list_ui_fixture_hardening import (
    FORBIDDEN_OBSERVATION_LIST_UI_HARDENING_OUTPUT_KEYWORDS,
    OBSERVATION_LIST_UI_FIXTURE_HARDENING_REQUIRED_FALSE_FLAGS,
    REQUIRED_OBSERVATION_LIST_UI_DISPLAY_BUCKETS,
    REQUIRED_OBSERVATION_LIST_UI_STATUS_BADGES,
    ObservationListUIFixtureHardeningPolicy,
    ObservationListUIFixtureHardeningResult,
    build_observation_list_ui_fixture_failure_probe,
    build_observation_list_ui_fixture_hardening_policy,
    check_observation_list_ui_fixture_deterministic_repeated_runs,
    check_observation_list_ui_fixture_disclaimers,
    check_observation_list_ui_fixture_display_buckets,
    check_observation_list_ui_fixture_forbidden_output_absence,
    check_observation_list_ui_fixture_required_flags_false,
    check_observation_list_ui_fixture_scenarios_present,
    check_observation_list_ui_fixture_status_badges,
    check_observation_list_ui_fixture_summary_stability,
    evaluate_observation_list_ui_fixture_failure_probe,
    run_observation_list_ui_fixture_hardening_checks,
)
from ai_stock.recommendation.observation_list_ui_fixtures import (
    ALLOWED_OBSERVATION_LIST_UI_FIXTURE_SCENARIOS,
    evaluate_all_observation_list_ui_fixtures,
)
from ai_stock.recommendation.observation_list_ui_preflight import (
    build_observation_list_ui_rows_from_all_fixtures,
)


class ObservationListUIFixtureHardeningTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = build_observation_list_ui_fixture_hardening_policy()
        cls.result = run_observation_list_ui_fixture_hardening_checks(cls.policy)

    def test_observation_list_ui_fixture_hardening_policy_generation(self) -> None:
        self.assertIsInstance(self.policy, ObservationListUIFixtureHardeningPolicy)
        self.assertEqual(self.policy.hardening_version, "MS-13.02")
        self.assertEqual(
            self.policy.hardening_scope,
            "observation_list_ui_fixture_safety_determinism_guardrail",
        )
        self.assertEqual(
            self.policy.required_scenarios,
            ALLOWED_OBSERVATION_LIST_UI_FIXTURE_SCENARIOS,
        )
        self.assertEqual(
            self.policy.required_status_badges,
            REQUIRED_OBSERVATION_LIST_UI_STATUS_BADGES,
        )
        self.assertEqual(
            self.policy.required_display_buckets,
            REQUIRED_OBSERVATION_LIST_UI_DISPLAY_BUCKETS,
        )
        self.assertFalse(self.policy.streamlit_required)
        self.assertFalse(self.policy.ui_integration_required)
        self.assertFalse(self.policy.recommendation_required)
        self.assertFalse(self.policy.ranking_required)
        with self.assertRaises(FrozenInstanceError):
            self.policy.streamlit_required = True

    def test_hardening_required_scenario_list(self) -> None:
        self.assertTrue(check_observation_list_ui_fixture_scenarios_present(self.policy))
        self.assertIn("ui_all_fixture_matrix", self.policy.required_scenarios)
        self.assertEqual(len(self.policy.required_scenarios), 8)

    def test_hardening_result_model_generation(self) -> None:
        field_names = tuple(
            field.name for field in fields(ObservationListUIFixtureHardeningResult)
        )

        self.assertIsInstance(self.result, ObservationListUIFixtureHardeningResult)
        self.assertEqual(
            field_names,
            (
                "passed",
                "failures",
                "checked_scenarios",
                "checked_row_count",
                "checked_status_badges",
                "checked_display_buckets",
                "checked_disclaimer_labels",
                "checked_guardrail_flags",
                "checked_forbidden_output_absence",
                "deterministic_repeated_run_passed",
                "summary_stability_passed",
                "evaluator_failure_injection_passed",
                "observation_only_guardrail_passed",
                "streamlit_absence_guardrail_passed",
                "diagnostics",
            ),
        )
        self.assertTrue(self.result.passed)
        with self.assertRaises(FrozenInstanceError):
            self.result.passed = False

    def test_run_observation_list_ui_fixture_hardening_checks_passes(self) -> None:
        self.assertTrue(self.result.passed)
        self.assertEqual(self.result.failures, ())
        self.assertEqual(self.result.checked_row_count, 25)

    def test_all_ui_fixture_evaluators_are_checked(self) -> None:
        evaluations = evaluate_all_observation_list_ui_fixtures()

        self.assertTrue(all(evaluation.passed for evaluation in evaluations))
        self.assertEqual(
            self.result.checked_scenarios,
            tuple(evaluation.scenario for evaluation in evaluations),
        )

    def test_ui_all_fixture_matrix_presence_is_checked(self) -> None:
        rows = build_observation_list_ui_rows_from_all_fixtures()

        self.assertIn("ui_all_fixture_matrix", self.result.checked_scenarios)
        self.assertEqual(len(rows), 11)
        self.assertGreaterEqual(len(rows), self.policy.min_row_count)

    def test_all_fixtures_based_ui_rows_are_created(self) -> None:
        rows = build_observation_list_ui_rows_from_all_fixtures()

        self.assertEqual(len(rows), 11)
        self.assertEqual(rows, build_observation_list_ui_rows_from_all_fixtures())

    def test_status_badge_is_not_buy_sell_hold(self) -> None:
        self.assertTrue(check_observation_list_ui_fixture_status_badges(self.policy))
        self.assertEqual(
            self.result.checked_status_badges,
            REQUIRED_OBSERVATION_LIST_UI_STATUS_BADGES,
        )
        for badge in self.result.checked_status_badges:
            self.assertNotIn(badge, ("buy", "sell", "hold", "strong_buy"))

    def test_score_snapshot_label_is_not_directive_output(self) -> None:
        self.assertTrue(self.result.observation_only_guardrail_passed)
        self.assertIn("all_fixture_matrix_rows_checked", self.result.diagnostics)
        rows = build_observation_list_ui_rows_from_all_fixtures()
        for row in rows:
            for forbidden in ("recommendation", "ranking", "action"):
                self.assertNotIn(forbidden, row.score_snapshot_label)

    def test_display_bucket_is_not_ranking_priority_or_order(self) -> None:
        self.assertTrue(
            check_observation_list_ui_fixture_display_buckets(self.policy)
        )
        self.assertEqual(
            self.result.checked_display_buckets,
            REQUIRED_OBSERVATION_LIST_UI_DISPLAY_BUCKETS,
        )
        for bucket in self.result.checked_display_buckets:
            self.assertNotIn("rank", bucket)
            self.assertNotIn("priority", bucket)
            self.assertNotIn("order", bucket)

    def test_usability_label_is_not_ranking_flag(self) -> None:
        rows = build_observation_list_ui_rows_from_all_fixtures()

        self.assertTrue(self.result.observation_only_guardrail_passed)
        for row in rows:
            self.assertIn(
                row.usability_label,
                ("future_list_ready", "future_list_review_only"),
            )
            self.assertNotIn("rank", row.usability_label)
            self.assertNotIn("priority", row.usability_label)
            self.assertNotIn("order", row.usability_label)

    def test_forbidden_output_field_is_not_copied_to_ui_row(self) -> None:
        rendered_rows = repr(build_observation_list_ui_rows_from_all_fixtures())
        rendered_result = repr(self.result)

        self.assertTrue(
            check_observation_list_ui_fixture_forbidden_output_absence(self.policy)
        )
        self.assertTrue(self.result.checked_forbidden_output_absence)
        for keyword in FORBIDDEN_OBSERVATION_LIST_UI_HARDENING_OUTPUT_KEYWORDS:
            self.assertNotIn(keyword, rendered_rows)
            self.assertNotIn(keyword, rendered_result)

    def test_required_flags_all_false(self) -> None:
        self.assertTrue(
            check_observation_list_ui_fixture_required_flags_false(self.policy)
        )
        self.assertEqual(
            OBSERVATION_LIST_UI_FIXTURE_HARDENING_REQUIRED_FALSE_FLAGS,
            self.policy.required_guardrail_false_flags,
        )
        self.assertEqual(
            self.result.checked_guardrail_flags,
            tuple(
                f"{flag}=false"
                for flag in OBSERVATION_LIST_UI_FIXTURE_HARDENING_REQUIRED_FALSE_FLAGS
            ),
        )
        self.assertFalse(
            any(flag.endswith("=true") for flag in self.result.checked_guardrail_flags)
        )

    def test_deterministic_repeated_run_passes(self) -> None:
        self.assertTrue(
            check_observation_list_ui_fixture_deterministic_repeated_runs(self.policy)
        )
        self.assertTrue(self.result.deterministic_repeated_run_passed)
        self.assertEqual(
            run_observation_list_ui_fixture_hardening_checks(self.policy),
            run_observation_list_ui_fixture_hardening_checks(self.policy),
        )

    def test_summary_stability_passes(self) -> None:
        self.assertTrue(check_observation_list_ui_fixture_summary_stability(self.policy))
        self.assertTrue(self.result.summary_stability_passed)

    def test_disclaimer_guardrail_passes(self) -> None:
        self.assertTrue(check_observation_list_ui_fixture_disclaimers(self.policy))
        for disclaimer in self.policy.required_disclaimer_keywords:
            self.assertIn(disclaimer, self.result.checked_disclaimer_labels)

    def test_evaluator_mismatch_failure_probe_generates_failure(self) -> None:
        probe = build_observation_list_ui_fixture_failure_probe()
        evaluation = evaluate_observation_list_ui_fixture_failure_probe()

        self.assertEqual(probe.expected_status_badges, ("empty_input",))
        self.assertFalse(evaluation.passed)
        self.assertIn("status_badges_mismatch", evaluation.failures)
        self.assertTrue(self.result.evaluator_failure_injection_passed)

    def test_streamlit_import_absent(self) -> None:
        self.assertTrue(self.result.streamlit_absence_guardrail_passed)
        self.assertNotIn("streamlit", hardening.__dict__)
        self.assertNotIn("streamlit", hardening.__name__)

    def test_no_file_network_env_or_db_access(self) -> None:
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
            "read",
            "read_text",
            "read_bytes",
            "write",
            "write_text",
            "write_bytes",
            "connect",
            "getenv",
            "environ",
            "request",
            "post",
            "now",
            "random",
        ):
            self.assertNotIn(forbidden_call, called_names)

    def test_existing_contract_modules_are_not_referenced_as_paths(self) -> None:
        constants = repr(_hardening_module_constants())

        self.assertNotIn("app/streamlit_app.py", constants)
        self.assertNotIn("observation_list_ui_preflight.py", constants)
        self.assertNotIn("observation_list_ui_fixtures.py", constants)
        self.assertNotIn("recommendation_list_preflight.py", constants)
        self.assertNotIn("recommendation_list_fixtures.py", constants)
        self.assertNotIn("recommendation_list_fixture_hardening.py", constants)


def _hardening_module_code_names() -> set[str]:
    names: set[str] = set()
    for value in vars(hardening).values():
        if isinstance(value, FunctionType) and value.__module__ == hardening.__name__:
            names.update(value.__code__.co_names)
    return names


def _hardening_module_constants() -> tuple[object, ...]:
    constants: list[object] = []
    for value in vars(hardening).values():
        if isinstance(value, FunctionType) and value.__module__ == hardening.__name__:
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
