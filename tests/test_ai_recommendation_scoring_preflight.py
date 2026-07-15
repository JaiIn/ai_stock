"""Offline tests for the MS-11.00 scoring preflight contract."""

from dataclasses import FrozenInstanceError, replace
from types import FunctionType
import unittest

import ai_stock.recommendation.scoring_preflight as scoring
from ai_stock.recommendation.feature_extraction_fixtures import (
    build_all_feature_extraction_fixtures,
)
from ai_stock.recommendation.feature_extraction_preflight import (
    extract_feature_sets_from_fixture,
)
from ai_stock.recommendation.scoring_preflight import (
    ALLOWED_SCORE_COMPONENT_NAMES,
    ALLOWED_SCORING_SOURCES,
    ALLOWED_SCORING_STATUSES,
    FORBIDDEN_SCORE_COMPONENT_NAMES,
    FORBIDDEN_SCORING_ACTION_LABELS,
    FORBIDDEN_SCORING_OUTPUT_FIELDS,
    FORBIDDEN_SCORING_RECOMMENDATION_LABELS,
    FORBIDDEN_SCORING_SOURCES,
    SCORE_SCALE,
    SCORING_PREFLIGHT_REQUIRED_FALSE_FLAGS,
    ScoringPreflightStatus,
    build_score_components_from_scoring_input,
    build_scoring_input_from_extracted_feature_set,
    build_scoring_preflight_policy,
    score_extracted_feature_set_preflight,
    score_extracted_feature_sets_from_all_feature_extraction_fixtures,
    score_extracted_feature_sets_from_all_fixtures,
    score_extracted_feature_sets_from_feature_extraction_fixture,
    score_extracted_feature_sets_from_fixture,
    summarize_scoring_preflight_results,
    validate_scoring_preflight_result,
)
from ai_stock.recommendation.watchlist_fixtures import (
    build_basic_manual_symbols_fixture,
    build_duplicates_and_disabled_fixture,
    build_empty_watchlist_fixture,
    build_forbidden_fields_sanitized_fixture,
    build_insufficient_data_review_fixture,
)


class ScoringPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_scoring_preflight_policy()

    def test_scoring_preflight_policy_generation_and_immutability(self) -> None:
        self.assertEqual(self.policy.stage_name, "MS-11.00")
        self.assertEqual(
            self.policy.mode,
            "deterministic_scoring_model_preflight",
        )
        self.assertIn("in_memory_extracted_feature_set", ALLOWED_SCORING_SOURCES)
        self.assertIn("file_path", FORBIDDEN_SCORING_SOURCES)
        self.assertIn("score_ready", ALLOWED_SCORING_STATUSES)
        self.assertIn("data_completeness", ALLOWED_SCORE_COMPONENT_NAMES)
        self.assertIn("target_price", FORBIDDEN_SCORE_COMPONENT_NAMES)
        self.assertIn("buy", FORBIDDEN_SCORING_ACTION_LABELS)
        self.assertIn("recommendation", FORBIDDEN_SCORING_RECOMMENDATION_LABELS)
        self.assertIn("accountSeq", FORBIDDEN_SCORING_OUTPUT_FIELDS)
        self.assertFalse(self.policy.ranking_required)
        self.assertFalse(self.policy.recommendation_required)
        self.assertFalse(self.policy.ui_required)
        with self.assertRaises(FrozenInstanceError):
            self.policy.ui_required = True

    def test_allowed_and_forbidden_scoring_statuses_are_safe(self) -> None:
        self.assertEqual(
            ALLOWED_SCORING_STATUSES,
            tuple(status.value for status in ScoringPreflightStatus),
        )
        for forbidden_label in (
            *FORBIDDEN_SCORING_ACTION_LABELS,
            *FORBIDDEN_SCORING_RECOMMENDATION_LABELS,
        ):
            self.assertNotIn(forbidden_label, ALLOWED_SCORING_STATUSES)

    def test_extracted_feature_set_builds_scoring_input(self) -> None:
        feature_set = extract_feature_sets_from_fixture(
            build_basic_manual_symbols_fixture()
        )[0]
        scoring_input = build_scoring_input_from_extracted_feature_set(feature_set)

        self.assertEqual(scoring_input.symbol, "005930")
        self.assertEqual(scoring_input.scoring_source, "in_memory_extracted_feature_set")
        self.assertEqual(scoring_input.extraction_status, "extraction_ready")
        self.assertTrue(scoring_input.usable_for_future_scoring)
        self.assertFalse(scoring_input.needs_review)

    def test_extracted_feature_set_builds_score_components(self) -> None:
        feature_set = extract_feature_sets_from_fixture(
            build_basic_manual_symbols_fixture()
        )[0]
        scoring_input = build_scoring_input_from_extracted_feature_set(feature_set)
        components = build_score_components_from_scoring_input(scoring_input)

        self.assertEqual(
            tuple(component.component_name for component in components),
            ALLOWED_SCORE_COMPONENT_NAMES,
        )
        self.assertTrue(
            all(component.component_score == SCORE_SCALE for component in components)
        )
        self.assertTrue(
            all(component.component_scale == SCORE_SCALE for component in components)
        )

    def test_extracted_feature_set_builds_scoring_preflight_result(self) -> None:
        feature_set = extract_feature_sets_from_fixture(
            build_basic_manual_symbols_fixture()
        )[0]
        result = score_extracted_feature_set_preflight(feature_set)

        self.assertEqual(result.scoring_status, "score_ready")
        self.assertEqual(result.total_score, SCORE_SCALE)
        self.assertEqual(result.score_scale, SCORE_SCALE)
        self.assertFalse(result.needs_review)
        self.assertTrue(result.usable_for_future_ranking)
        self.assertTrue(validate_scoring_preflight_result(result).valid)

    def test_fixture_based_scoring_preflight_generation(self) -> None:
        results = score_extracted_feature_sets_from_fixture(
            build_basic_manual_symbols_fixture()
        )

        self.assertEqual(len(results), 2)
        self.assertTrue(
            all(result.scoring_status == "score_ready" for result in results)
        )
        self.assertTrue(
            all(validate_scoring_preflight_result(result).valid for result in results)
        )

    def test_all_fixture_based_scoring_generation(self) -> None:
        grouped = score_extracted_feature_sets_from_all_fixtures()
        flattened = tuple(result for group in grouped for result in group)

        self.assertEqual(len(grouped), 6)
        self.assertEqual(len(flattened), 11)
        self.assertEqual(
            tuple(result.scoring_status for result in flattened),
            (
                "score_ready",
                "score_ready",
                "score_ready",
                "score_invalid_candidate",
                "score_invalid_candidate",
                "score_ready",
                "score_duplicate_candidate",
                "score_disabled_candidate",
                "score_missing_data",
                "score_forbidden_field_sanitized",
                "score_empty_input",
            ),
        )

    def test_feature_extraction_fixture_based_scoring_generation(self) -> None:
        fixtures = build_all_feature_extraction_fixtures()
        grouped = score_extracted_feature_sets_from_all_feature_extraction_fixtures()

        self.assertEqual(len(grouped), len(fixtures))
        self.assertEqual(
            len(score_extracted_feature_sets_from_feature_extraction_fixture(fixtures[0])),
            2,
        )
        matrix_results = score_extracted_feature_sets_from_feature_extraction_fixture(
            fixtures[-1]
        )
        self.assertEqual(len(matrix_results), 11)

    def test_scoring_preflight_output_is_deterministic(self) -> None:
        self.assertEqual(
            score_extracted_feature_sets_from_all_fixtures(),
            score_extracted_feature_sets_from_all_fixtures(),
        )
        self.assertEqual(
            score_extracted_feature_sets_from_all_feature_extraction_fixtures(),
            score_extracted_feature_sets_from_all_feature_extraction_fixtures(),
        )

    def test_extraction_ready_scoring_policy(self) -> None:
        results = score_extracted_feature_sets_from_fixture(
            build_basic_manual_symbols_fixture()
        )

        self.assertTrue(all(result.scoring_status == "score_ready" for result in results))
        self.assertTrue(all(result.total_score == SCORE_SCALE for result in results))
        self.assertTrue(all(result.usable_for_future_ranking for result in results))

    def test_duplicate_scoring_policy(self) -> None:
        results = score_extracted_feature_sets_from_fixture(
            build_duplicates_and_disabled_fixture()
        )
        duplicate = [
            result
            for result in results
            if result.scoring_status == "score_duplicate_candidate"
        ][0]

        self.assertEqual(duplicate.total_score, 20)
        self.assertFalse(duplicate.usable_for_future_ranking)
        self.assertIn("quality_duplicate_candidate", duplicate.blocked_reasons)

    def test_disabled_scoring_policy(self) -> None:
        results = score_extracted_feature_sets_from_fixture(
            build_duplicates_and_disabled_fixture()
        )
        disabled = [
            result
            for result in results
            if result.scoring_status == "score_disabled_candidate"
        ][0]

        self.assertEqual(disabled.total_score, 20)
        self.assertFalse(disabled.usable_for_future_ranking)
        self.assertIn("quality_disabled_candidate", disabled.blocked_reasons)

    def test_missing_data_scoring_policy(self) -> None:
        results = score_extracted_feature_sets_from_fixture(
            build_insufficient_data_review_fixture()
        )

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].scoring_status, "score_missing_data")
        self.assertEqual(results[0].total_score, 20)
        self.assertFalse(results[0].usable_for_future_ranking)

    def test_forbidden_field_sanitized_scoring_policy(self) -> None:
        results = score_extracted_feature_sets_from_fixture(
            build_forbidden_fields_sanitized_fixture()
        )
        rendered = repr(results)

        self.assertEqual(len(results), 1)
        self.assertEqual(
            results[0].scoring_status,
            "score_forbidden_field_sanitized",
        )
        self.assertEqual(results[0].total_score, 0)
        self.assertIn("forbidden_field", "".join(results[0].diagnostics))
        for keyword in _forbidden_absent_assignment_keywords():
            self.assertNotIn(keyword, rendered)

    def test_empty_input_scoring_policy(self) -> None:
        results = score_extracted_feature_sets_from_fixture(build_empty_watchlist_fixture())

        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].scoring_status, "score_empty_input")
        self.assertEqual(results[0].total_score, 20)
        self.assertFalse(results[0].usable_for_future_ranking)

    def test_total_score_is_deterministic_and_in_scale(self) -> None:
        flattened = tuple(
            result
            for group in score_extracted_feature_sets_from_all_fixtures()
            for result in group
        )
        repeated = tuple(
            result
            for group in score_extracted_feature_sets_from_all_fixtures()
            for result in group
        )

        self.assertEqual(flattened, repeated)
        for result in flattened:
            self.assertGreaterEqual(result.total_score, 0)
            self.assertLessEqual(result.total_score, result.score_scale)

    def test_total_score_is_not_directive_output(self) -> None:
        result = score_extracted_feature_sets_from_fixture(
            build_basic_manual_symbols_fixture()
        )[0]
        result_fields = tuple(
            field.name for field in scoring.fields(scoring.ScoringPreflightResult)
        )

        self.assertIn("total_score", result_fields)
        self.assertNotIn("recommendation", result_fields)
        self.assertNotIn("rank", result_fields)
        self.assertNotIn("action", result_fields)
        self.assertNotIn(result.scoring_status, FORBIDDEN_SCORING_ACTION_LABELS)
        self.assertNotIn(result.scoring_status, FORBIDDEN_SCORING_RECOMMENDATION_LABELS)

    def test_forbidden_action_status_is_not_generated(self) -> None:
        produced_values: list[str] = []
        for group in score_extracted_feature_sets_from_all_fixtures():
            for result in group:
                produced_values.append(result.scoring_status)
                produced_values.extend(
                    component.component_name for component in result.score_components
                )
                produced_values.extend(
                    component.component_status for component in result.score_components
                )

        for forbidden_label in (
            *FORBIDDEN_SCORING_ACTION_LABELS,
            *FORBIDDEN_SCORING_RECOMMENDATION_LABELS,
        ):
            self.assertNotIn(forbidden_label, produced_values)

    def test_forbidden_output_fields_are_not_model_fields(self) -> None:
        result_fields = tuple(
            field.name for field in scoring.fields(scoring.ScoringPreflightResult)
        )
        component_fields = tuple(
            field.name for field in scoring.fields(scoring.ScoreComponent)
        )
        input_fields = tuple(field.name for field in scoring.fields(scoring.ScoringInput))

        for forbidden_field in FORBIDDEN_SCORING_OUTPUT_FIELDS:
            self.assertNotIn(forbidden_field, result_fields)
            self.assertNotIn(forbidden_field, component_fields)
            self.assertNotIn(forbidden_field, input_fields)

    def test_validation_rejects_forbidden_status_and_component(self) -> None:
        result = score_extracted_feature_sets_from_fixture(
            build_basic_manual_symbols_fixture()
        )[0]
        forbidden_status = replace(result, scoring_status="buy")
        forbidden_component = replace(
            result.score_components[0],
            component_name="target_price",
        )
        result_with_forbidden_component = replace(
            result,
            score_components=(forbidden_component, *result.score_components[1:]),
        )

        self.assertFalse(validate_scoring_preflight_result(forbidden_status).valid)
        self.assertFalse(
            validate_scoring_preflight_result(result_with_forbidden_component).valid
        )
        self.assertIn(
            "unknown_scoring_status:buy",
            validate_scoring_preflight_result(forbidden_status).rejection_reasons,
        )
        self.assertIn(
            "forbidden_score_component:target_price",
            validate_scoring_preflight_result(
                result_with_forbidden_component
            ).rejection_reasons,
        )

    def test_required_flags_are_all_false(self) -> None:
        result = score_extracted_feature_sets_from_fixture(
            build_basic_manual_symbols_fixture()
        )[0]
        validation = validate_scoring_preflight_result(result)

        for flag in SCORING_PREFLIGHT_REQUIRED_FALSE_FLAGS:
            self.assertFalse(getattr(result.summary_flags, flag))
            self.assertFalse(getattr(validation, flag))

    def test_summary_counts_scoring_preflight_results(self) -> None:
        flattened = tuple(
            result
            for group in score_extracted_feature_sets_from_all_fixtures()
            for result in group
        )
        summary = summarize_scoring_preflight_results(flattened)

        self.assertEqual(summary.total_results, 11)
        self.assertEqual(summary.ready_results, 4)
        self.assertEqual(summary.needs_review_results, 7)
        self.assertEqual(summary.usable_for_future_ranking_results, 4)
        self.assertGreater(summary.average_total_score, 0)
        self.assertFalse(summary.ranking_required)
        self.assertFalse(summary.recommendation_required)

    def test_module_structure_has_no_io_or_external_dependencies(self) -> None:
        runtime_modules = {
            getattr(value, "__module__", "")
            for value in vars(scoring).values()
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

        called_names = _scoring_module_code_names()
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
            for part in (*vars(scoring), *_scoring_module_constants())
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
        constants = _scoring_module_constants()

        self.assertNotIn("app/streamlit_app.py", constants)
        self.assertNotIn("feature_quality.py", constants)
        self.assertNotIn("feature_quality_fixtures.py", constants)
        self.assertNotIn("feature_extraction_preflight.py", constants)
        self.assertNotIn("feature_extraction_fixtures.py", constants)
        self.assertNotIn("dashboard_preflight.py", constants)
        self.assertNotIn("watchlist_fixtures.py", constants)


def _forbidden_absent_assignment_keywords() -> tuple[str, ...]:
    return (
        "accountSeq=",
        "access_token=",
        "authorization=",
        "bearer=",
        "api_key=",
        "secret_key=",
        "client_secret=",
        "account_balance=",
        "holdings=",
        "fills=",
        "order_id=",
        "raw_response=",
        "raw_request=",
        "db_row=",
        "file_path=",
        "env_path=",
        ".env.local=",
        "buy=",
        "sell=",
        "hold=",
        "strong_buy=",
        "recommendation=",
        "action=",
        "rank=",
        "target_price=",
        "expected_return=",
        "profit_probability=",
    )


def _scoring_module_code_names() -> set[str]:
    names: set[str] = set()
    for value in vars(scoring).values():
        if isinstance(value, FunctionType):
            names.update(value.__code__.co_names)
    return names


def _scoring_module_constants() -> tuple[object, ...]:
    constants: list[object] = []
    for value in vars(scoring).values():
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
