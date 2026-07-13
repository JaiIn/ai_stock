"""Offline tests for the MS-10.02 feature extraction preflight contract."""

from dataclasses import FrozenInstanceError, replace
from types import FunctionType
import unittest

import ai_stock.recommendation.feature_extraction_preflight as extraction
from ai_stock.recommendation.feature_extraction_preflight import (
    ALLOWED_EXTRACTION_STATUSES,
    ALLOWED_FEATURE_EXTRACTION_SOURCES,
    FEATURE_EXTRACTION_REQUIRED_FALSE_FLAGS,
    FORBIDDEN_EXTRACTION_FEATURE_NAMES,
    FORBIDDEN_EXTRACTION_OUTPUT_LABELS,
    FORBIDDEN_FEATURE_EXTRACTION_SOURCES,
    FeatureExtractionStatus,
    build_feature_extraction_input_from_quality_assessment,
    build_feature_extraction_policy,
    extract_feature_set_from_quality_assessment,
    extract_feature_sets_from_all_feature_quality_fixtures,
    extract_feature_sets_from_all_fixtures,
    extract_feature_sets_from_feature_quality_fixture,
    extract_feature_sets_from_fixture,
    summarize_feature_extraction_results,
    validate_extracted_feature_set,
)
from ai_stock.recommendation.feature_quality import (
    ALLOWED_FEATURE_NAMES,
    FORBIDDEN_FEATURE_ACTION_LABELS,
    build_feature_quality_from_fixture,
)
from ai_stock.recommendation.feature_quality_fixtures import (
    build_all_feature_quality_fixtures,
    build_quality_all_fixture_matrix,
)
from ai_stock.recommendation.watchlist_fixtures import (
    build_basic_manual_symbols_fixture,
    build_duplicates_and_disabled_fixture,
    build_empty_watchlist_fixture,
    build_forbidden_fields_sanitized_fixture,
    build_insufficient_data_review_fixture,
)


class FeatureExtractionPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_feature_extraction_policy()

    def test_feature_extraction_policy_generation_and_immutability(self) -> None:
        self.assertEqual(self.policy.stage_name, "MS-10.02")
        self.assertEqual(
            self.policy.mode,
            "deterministic_feature_extraction_preflight",
        )
        self.assertIn(
            "feature_quality_assessment",
            ALLOWED_FEATURE_EXTRACTION_SOURCES,
        )
        self.assertIn("file_path", FORBIDDEN_FEATURE_EXTRACTION_SOURCES)
        self.assertIn("extraction_ready", ALLOWED_EXTRACTION_STATUSES)
        self.assertIn("target_price", FORBIDDEN_EXTRACTION_OUTPUT_LABELS)
        self.assertIn("api_key", FORBIDDEN_EXTRACTION_FEATURE_NAMES)
        self.assertFalse(self.policy.scoring_required)
        self.assertFalse(self.policy.ranking_required)
        self.assertFalse(self.policy.recommendation_required)
        with self.assertRaises(FrozenInstanceError):
            self.policy.scoring_required = True

    def test_allowed_and_forbidden_extraction_statuses_are_safe(self) -> None:
        self.assertEqual(
            ALLOWED_EXTRACTION_STATUSES,
            tuple(status.value for status in FeatureExtractionStatus),
        )
        for forbidden_label in FORBIDDEN_EXTRACTION_OUTPUT_LABELS:
            self.assertNotIn(forbidden_label, ALLOWED_EXTRACTION_STATUSES)

    def test_feature_quality_assessment_builds_extraction_input(self) -> None:
        assessment = build_feature_quality_from_fixture(
            build_basic_manual_symbols_fixture()
        )[0]
        extraction_input = build_feature_extraction_input_from_quality_assessment(
            assessment
        )

        self.assertEqual(extraction_input.symbol, "005930")
        self.assertEqual(extraction_input.quality_status, "quality_ok")
        self.assertFalse(extraction_input.needs_review)
        self.assertTrue(extraction_input.usable_for_future_scoring)
        self.assertEqual(
            tuple(record.feature_name for record in extraction_input.feature_records),
            ALLOWED_FEATURE_NAMES,
        )

    def test_feature_quality_assessment_builds_extracted_feature_set(self) -> None:
        assessment = build_feature_quality_from_fixture(
            build_basic_manual_symbols_fixture()
        )[0]
        feature_set = extract_feature_set_from_quality_assessment(assessment)

        self.assertEqual(feature_set.extraction_status, "extraction_ready")
        self.assertTrue(feature_set.usable_for_future_scoring)
        self.assertEqual(feature_set.missing_features, ())
        self.assertEqual(feature_set.blocked_features, ())
        self.assertEqual(
            tuple(feature.feature_name for feature in feature_set.extracted_features),
            ALLOWED_FEATURE_NAMES,
        )
        self.assertTrue(validate_extracted_feature_set(feature_set).valid)

    def test_fixture_based_extracted_feature_set_generation(self) -> None:
        feature_sets = extract_feature_sets_from_fixture(
            build_basic_manual_symbols_fixture()
        )

        self.assertEqual(len(feature_sets), 2)
        self.assertTrue(
            all(
                feature_set.extraction_status == "extraction_ready"
                for feature_set in feature_sets
            )
        )
        self.assertTrue(
            all(
                validate_extracted_feature_set(feature_set).valid
                for feature_set in feature_sets
            )
        )

    def test_all_fixture_based_extraction_generation(self) -> None:
        grouped = extract_feature_sets_from_all_fixtures()
        flattened = tuple(feature_set for group in grouped for feature_set in group)

        self.assertEqual(len(grouped), 6)
        self.assertEqual(len(flattened), 11)
        self.assertEqual(
            tuple(feature_set.extraction_status for feature_set in flattened),
            (
                "extraction_ready",
                "extraction_ready",
                "extraction_ready",
                "extraction_invalid_candidate",
                "extraction_invalid_candidate",
                "extraction_ready",
                "extraction_duplicate_candidate",
                "extraction_disabled_candidate",
                "extraction_missing_data",
                "extraction_forbidden_field_sanitized",
                "extraction_empty_input",
            ),
        )

    def test_feature_quality_fixture_based_extraction_generation(self) -> None:
        fixtures = build_all_feature_quality_fixtures()
        grouped = extract_feature_sets_from_all_feature_quality_fixtures()

        self.assertEqual(len(grouped), len(fixtures))
        self.assertEqual(
            len(extract_feature_sets_from_feature_quality_fixture(fixtures[0])),
            2,
        )
        matrix_sets = extract_feature_sets_from_feature_quality_fixture(
            build_quality_all_fixture_matrix()
        )
        self.assertEqual(len(matrix_sets), 11)

    def test_extraction_output_is_deterministic(self) -> None:
        self.assertEqual(
            extract_feature_sets_from_all_fixtures(),
            extract_feature_sets_from_all_fixtures(),
        )
        self.assertEqual(
            extract_feature_sets_from_all_feature_quality_fixtures(),
            extract_feature_sets_from_all_feature_quality_fixtures(),
        )

    def test_quality_ok_extraction_policy(self) -> None:
        feature_sets = extract_feature_sets_from_fixture(
            build_basic_manual_symbols_fixture()
        )

        self.assertTrue(
            all(
                feature_set.extraction_status == "extraction_ready"
                for feature_set in feature_sets
            )
        )
        self.assertTrue(
            all(feature_set.usable_for_future_scoring for feature_set in feature_sets)
        )

    def test_duplicate_extraction_policy(self) -> None:
        feature_sets = extract_feature_sets_from_fixture(
            build_duplicates_and_disabled_fixture()
        )
        duplicate = [
            feature_set
            for feature_set in feature_sets
            if feature_set.extraction_status == "extraction_duplicate_candidate"
        ][0]

        self.assertFalse(duplicate.usable_for_future_scoring)
        self.assertEqual(duplicate.extracted_features, ())
        self.assertIn("quality_duplicate_candidate", duplicate.blocked_reasons)

    def test_disabled_extraction_policy(self) -> None:
        feature_sets = extract_feature_sets_from_fixture(
            build_duplicates_and_disabled_fixture()
        )
        disabled = [
            feature_set
            for feature_set in feature_sets
            if feature_set.extraction_status == "extraction_disabled_candidate"
        ][0]

        self.assertFalse(disabled.usable_for_future_scoring)
        self.assertEqual(disabled.extracted_features, ())
        self.assertIn("quality_disabled_candidate", disabled.blocked_reasons)

    def test_insufficient_data_extraction_policy(self) -> None:
        feature_sets = extract_feature_sets_from_fixture(
            build_insufficient_data_review_fixture()
        )

        self.assertEqual(len(feature_sets), 1)
        self.assertEqual(feature_sets[0].extraction_status, "extraction_missing_data")
        self.assertFalse(feature_sets[0].usable_for_future_scoring)
        self.assertEqual(feature_sets[0].extracted_features, ())

    def test_forbidden_field_sanitized_extraction_policy(self) -> None:
        feature_sets = extract_feature_sets_from_fixture(
            build_forbidden_fields_sanitized_fixture()
        )
        rendered = repr(feature_sets)

        self.assertEqual(len(feature_sets), 1)
        self.assertEqual(
            feature_sets[0].extraction_status,
            "extraction_forbidden_field_sanitized",
        )
        self.assertEqual(feature_sets[0].extracted_features, ())
        self.assertIn("forbidden_field", "".join(feature_sets[0].diagnostics))
        for keyword in (
            "redacted-not-output",
            "accountSeq=",
            "access_token=",
            "authorization=",
            "target_price=",
            "expected_return=",
            "score=",
            "buy=",
            "sell=",
            "hold=",
            ".env.local",
        ):
            self.assertNotIn(keyword, rendered)

    def test_empty_input_extraction_policy(self) -> None:
        feature_sets = extract_feature_sets_from_fixture(build_empty_watchlist_fixture())

        self.assertEqual(len(feature_sets), 1)
        self.assertEqual(feature_sets[0].extraction_status, "extraction_empty_input")
        self.assertEqual(feature_sets[0].extracted_features, ())
        self.assertEqual(feature_sets[0].missing_features, ALLOWED_FEATURE_NAMES)

    def test_forbidden_action_status_is_not_generated(self) -> None:
        produced_values: list[str] = []
        for group in extract_feature_sets_from_all_fixtures():
            for feature_set in group:
                produced_values.append(feature_set.extraction_status)
                produced_values.append(feature_set.quality_status)
                produced_values.extend(
                    feature.feature_name for feature in feature_set.extracted_features
                )

        for forbidden_label in FORBIDDEN_FEATURE_ACTION_LABELS:
            self.assertNotIn(forbidden_label, produced_values)
        for forbidden_label in FORBIDDEN_EXTRACTION_OUTPUT_LABELS:
            self.assertNotIn(forbidden_label, produced_values)

    def test_forbidden_output_fields_are_not_model_fields(self) -> None:
        feature_set_fields = tuple(
            field.name for field in extraction.fields(extraction.ExtractedFeatureSet)
        )
        feature_value_fields = tuple(
            field.name for field in extraction.fields(extraction.ExtractedFeatureValue)
        )

        for forbidden_field in (
            "score",
            "rank",
            "recommendation",
            "action",
            "buy",
            "sell",
            "hold",
            "target_price",
            "expected_return",
            "profit_probability",
            "order_quantity",
            "position_size",
            "accountSeq",
            "access_token",
            "api_key",
            "secret_key",
        ):
            self.assertNotIn(forbidden_field, feature_set_fields)
            self.assertNotIn(forbidden_field, feature_value_fields)

    def test_validation_rejects_forbidden_source_and_status(self) -> None:
        feature_set = extract_feature_sets_from_fixture(
            build_basic_manual_symbols_fixture()
        )[0]
        forbidden_source = replace(feature_set, extraction_source="file_path")
        forbidden_status = replace(feature_set, extraction_status="buy")

        self.assertFalse(validate_extracted_feature_set(forbidden_source).valid)
        self.assertFalse(validate_extracted_feature_set(forbidden_status).valid)
        self.assertIn(
            "forbidden_extraction_source:file_path",
            validate_extracted_feature_set(forbidden_source).rejection_reasons,
        )
        self.assertIn(
            "unknown_extraction_status:buy",
            validate_extracted_feature_set(forbidden_status).rejection_reasons,
        )

    def test_required_flags_are_all_false(self) -> None:
        feature_set = extract_feature_sets_from_fixture(
            build_basic_manual_symbols_fixture()
        )[0]
        validation = validate_extracted_feature_set(feature_set)

        for flag in FEATURE_EXTRACTION_REQUIRED_FALSE_FLAGS:
            self.assertFalse(getattr(feature_set.summary_flags, flag))
            self.assertFalse(getattr(validation, flag))

    def test_summary_counts_feature_extraction_results(self) -> None:
        flattened = tuple(
            feature_set
            for group in extract_feature_sets_from_all_fixtures()
            for feature_set in group
        )
        summary = summarize_feature_extraction_results(flattened)

        self.assertEqual(summary.total_sets, 11)
        self.assertEqual(summary.ready_sets, 4)
        self.assertEqual(summary.needs_review_sets, 7)
        self.assertEqual(summary.usable_for_future_scoring_sets, 4)
        self.assertFalse(summary.scoring_required)
        self.assertFalse(summary.recommendation_required)

    def test_module_structure_has_no_io_or_external_dependencies(self) -> None:
        runtime_modules = {
            getattr(value, "__module__", "")
            for value in vars(extraction).values()
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

        called_names = _extraction_module_code_names()
        for forbidden_call in (
            "open",
            "read_text",
            "read_bytes",
            "write_text",
            "write_bytes",
            "connect",
            "getenv",
            "request",
            "post",
            "now",
            "random",
        ):
            self.assertNotIn(forbidden_call, called_names)

    def test_module_has_no_forbidden_runtime_imports_or_paths(self) -> None:
        module_symbols = {
            str(part).casefold()
            for part in (*vars(extraction), *_extraction_module_constants())
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

    def test_existing_ui_and_quality_modules_are_not_referenced_as_paths(self) -> None:
        constants = _extraction_module_constants()

        self.assertNotIn("app/streamlit_app.py", constants)
        self.assertNotIn("feature_quality.py", constants)
        self.assertNotIn("feature_quality_fixtures.py", constants)
        self.assertNotIn("dashboard_preflight.py", constants)
        self.assertNotIn("watchlist_fixtures.py", constants)


def _extraction_module_code_names() -> set[str]:
    names: set[str] = set()
    for value in vars(extraction).values():
        if isinstance(value, FunctionType):
            names.update(value.__code__.co_names)
    return names


def _extraction_module_constants() -> tuple[object, ...]:
    constants: list[object] = []
    for value in vars(extraction).values():
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
