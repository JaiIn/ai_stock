"""Offline tests for the MS-09.04 watchlist source fixture contract."""

from dataclasses import FrozenInstanceError
from types import FunctionType
import unittest

import ai_stock.recommendation.watchlist_fixtures as watchlist_fixtures
from ai_stock.recommendation.candidate_input_preflight import (
    FORBIDDEN_CANDIDATE_LABELS,
)
from ai_stock.recommendation.watchlist_fixtures import (
    ALLOWED_WATCHLIST_FIXTURE_SCENARIOS,
    FIXTURE_REQUIRED_FALSE_FLAGS,
    FORBIDDEN_WATCHLIST_FIXTURE_SCENARIOS,
    WatchlistFixtureScenario,
    build_all_watchlist_source_fixtures,
    build_basic_manual_symbols_fixture,
    build_duplicates_and_disabled_fixture,
    build_empty_watchlist_fixture,
    build_forbidden_fields_sanitized_fixture,
    build_insufficient_data_review_fixture,
    build_mixed_valid_invalid_symbols_fixture,
    build_watchlist_fixture_policy,
    evaluate_watchlist_fixture,
)
from ai_stock.recommendation.watchlist_source import (
    WatchlistSourceConfig,
    build_watchlist_source_result,
)


class WatchlistFixtureTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_watchlist_fixture_policy()

    def test_default_policy_identity_and_immutability(self) -> None:
        self.assertEqual(self.policy.stage_name, "MS-09.04")
        self.assertEqual(self.policy.mode, "watchlist_source_test_fixtures")
        with self.assertRaises(FrozenInstanceError):
            self.policy.db_write_required = True

    def test_all_fixture_scenarios_are_generated(self) -> None:
        fixtures = build_all_watchlist_source_fixtures()
        self.assertEqual(len(fixtures), 6)
        self.assertEqual(
            tuple(fixture.scenario for fixture in fixtures),
            ALLOWED_WATCHLIST_FIXTURE_SCENARIOS,
        )
        for scenario in WatchlistFixtureScenario:
            self.assertIn(scenario.value, ALLOWED_WATCHLIST_FIXTURE_SCENARIOS)

    def test_forbidden_fixture_scenarios_are_documented(self) -> None:
        for forbidden in (
            "real_account_holdings_fixture",
            "real_account_balance_fixture",
            "real_fills_fixture",
            "toss_api_response_fixture",
            "db_row_fixture",
            "file_path_fixture",
            "credential_token_accountSeq_fixture",
        ):
            self.assertIn(forbidden, FORBIDDEN_WATCHLIST_FIXTURE_SCENARIOS)

    def test_fixture_builder_is_deterministic(self) -> None:
        first = build_all_watchlist_source_fixtures()
        second = build_all_watchlist_source_fixtures()
        self.assertEqual(first, second)
        self.assertEqual(
            tuple(evaluate_watchlist_fixture(fixture) for fixture in first),
            tuple(evaluate_watchlist_fixture(fixture) for fixture in second),
        )

    def test_basic_manual_symbols_fixture_generates_valid_result(self) -> None:
        fixture = build_basic_manual_symbols_fixture()
        evaluation = evaluate_watchlist_fixture(fixture)
        self.assertTrue(evaluation.passed)
        self.assertEqual(evaluation.actual_watchlist_status, "valid_watchlist")
        self.assertEqual(
            evaluation.actual_candidate_statuses,
            ("valid_candidate", "valid_candidate"),
        )

    def test_mixed_valid_invalid_symbols_fixture_is_safe(self) -> None:
        fixture = build_mixed_valid_invalid_symbols_fixture()
        evaluation = evaluate_watchlist_fixture(fixture)
        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.actual_watchlist_status,
            "contains_invalid_candidates",
        )
        self.assertEqual(
            evaluation.actual_candidate_statuses,
            ("valid_candidate", "invalid_symbol", "invalid_symbol"),
        )

    def test_duplicates_and_disabled_fixture_is_safe(self) -> None:
        fixture = build_duplicates_and_disabled_fixture()
        evaluation = evaluate_watchlist_fixture(fixture)
        self.assertTrue(evaluation.passed)
        self.assertEqual(
            evaluation.actual_watchlist_status,
            "contains_duplicate_candidates",
        )
        self.assertEqual(
            evaluation.actual_candidate_statuses,
            (
                "valid_candidate",
                "duplicate_candidate",
                "disabled_candidate",
            ),
        )

    def test_insufficient_data_review_fixture_is_safe(self) -> None:
        fixture = build_insufficient_data_review_fixture()
        evaluation = evaluate_watchlist_fixture(fixture)
        self.assertTrue(evaluation.passed)
        self.assertEqual(evaluation.actual_watchlist_status, "needs_review")
        self.assertEqual(
            evaluation.actual_candidate_statuses,
            ("insufficient_data",),
        )

    def test_forbidden_fields_sanitized_fixture_removes_output_values(self) -> None:
        fixture = build_forbidden_fields_sanitized_fixture()
        evaluation = evaluate_watchlist_fixture(fixture)
        result = build_watchlist_source_result(fixture.source_config)
        output_model = repr(result.watchlist) + repr(result.candidate_inputs)

        self.assertTrue(evaluation.passed)
        self.assertEqual(evaluation.actual_watchlist_status, "valid_watchlist")
        self.assertIn(
            "forbidden_field:accountSeq",
            result.rejection_reasons,
        )
        self.assertIn(
            "forbidden_field_detected:target_price",
            result.diagnostics,
        )
        self.assertNotIn("redacted-not-output", output_model)
        self.assertNotIn("accountSeq=", output_model)
        self.assertNotIn("target_price=", output_model)
        self.assertNotIn("expected_return=", output_model)
        self.assertNotIn("score=", output_model)

    def test_empty_watchlist_fixture_is_safe(self) -> None:
        fixture = build_empty_watchlist_fixture()
        evaluation = evaluate_watchlist_fixture(fixture)
        self.assertTrue(evaluation.passed)
        self.assertEqual(evaluation.actual_watchlist_status, "empty_watchlist")
        self.assertEqual(evaluation.actual_candidate_statuses, ())
        self.assertIn("empty_source_items", evaluation.diagnostics)

    def test_evaluate_watchlist_fixture_reports_expected_actual_mismatch(self) -> None:
        fixture = build_basic_manual_symbols_fixture()
        mismatch = type(fixture)(
            scenario=fixture.scenario,
            description=fixture.description,
            source_config=fixture.source_config,
            expected_watchlist_status="empty_watchlist",
            expected_candidate_statuses=fixture.expected_candidate_statuses,
            expected_summary_flags=fixture.expected_summary_flags,
        )
        evaluation = evaluate_watchlist_fixture(mismatch)
        self.assertFalse(evaluation.passed)
        self.assertIn("watchlist_status_mismatch", evaluation.failures)

    def test_all_evaluation_required_flags_are_false(self) -> None:
        for fixture in build_all_watchlist_source_fixtures():
            evaluation = evaluate_watchlist_fixture(fixture)
            self.assertTrue(evaluation.passed)
            self.assertFalse(evaluation.credential_required)
            self.assertFalse(evaluation.db_read_required)
            self.assertFalse(evaluation.db_write_required)
            self.assertFalse(evaluation.file_read_required)
            self.assertFalse(evaluation.file_write_required)
            self.assertFalse(evaluation.toss_api_required)
            self.assertFalse(evaluation.openai_required)
            self.assertFalse(evaluation.oauth_required)
            self.assertFalse(evaluation.account_seq_required)
            self.assertFalse(evaluation.real_order_required)
            self.assertFalse(evaluation.scoring_required)
            self.assertFalse(evaluation.ui_required)
            self.assertEqual(
                evaluation.actual_summary_flags,
                tuple(f"{flag}=false" for flag in FIXTURE_REQUIRED_FALSE_FLAGS),
            )

    def test_forbidden_labels_are_not_generated_as_action_labels(self) -> None:
        for fixture in build_all_watchlist_source_fixtures():
            evaluation = evaluate_watchlist_fixture(fixture)
            produced_statuses = (
                evaluation.actual_watchlist_status,
                *evaluation.actual_candidate_statuses,
            )
            for forbidden_label in FORBIDDEN_CANDIDATE_LABELS:
                self.assertNotIn(forbidden_label, produced_statuses)

    def test_fixture_records_use_only_caller_supplied_config(self) -> None:
        for fixture in build_all_watchlist_source_fixtures():
            self.assertIsInstance(fixture.source_config, WatchlistSourceConfig)
            self.assertNotIn(fixture.source_config.source_type, self.policy.forbidden_scenarios)

    def test_policy_disables_storage_loader_recommendation_scoring_and_ui(self) -> None:
        self.assertFalse(self.policy.actual_recommendation_allowed)
        self.assertFalse(self.policy.scoring_allowed)
        self.assertFalse(self.policy.watchlist_persistence_allowed)
        self.assertFalse(self.policy.file_loader_allowed)
        self.assertFalse(self.policy.ui_change_allowed)

    def test_module_structure_has_no_io_or_external_dependencies(self) -> None:
        runtime_modules = {
            getattr(value, "__module__", "")
            for value in vars(watchlist_fixtures).values()
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
            for part in (*vars(watchlist_fixtures), *_fixture_module_constants())
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

    def test_app_streamlit_app_is_not_part_of_fixture_module(self) -> None:
        self.assertNotIn("app/streamlit_app.py", _fixture_module_constants())


def _fixture_module_code_names() -> set[str]:
    names: set[str] = set()
    for value in vars(watchlist_fixtures).values():
        if isinstance(value, FunctionType):
            names.update(value.__code__.co_names)
    return names


def _fixture_module_constants() -> tuple[object, ...]:
    constants: list[object] = []
    for value in vars(watchlist_fixtures).values():
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
