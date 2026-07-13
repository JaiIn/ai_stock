"""Offline tests for the MS-10.00 feature/data quality contract."""

from dataclasses import FrozenInstanceError, replace
from types import FunctionType
import unittest

import ai_stock.recommendation.feature_quality as feature_quality
from ai_stock.recommendation.candidate_input_preflight import (
    FORBIDDEN_CANDIDATE_LABELS,
)
from ai_stock.recommendation.dashboard_preflight import (
    build_dashboard_preflight_from_fixture,
    build_dashboard_preflight_from_source_result,
)
from ai_stock.recommendation.feature_quality import (
    ALLOWED_FEATURE_NAMES,
    ALLOWED_QUALITY_STATUSES,
    FEATURE_QUALITY_REQUIRED_FALSE_FLAGS,
    FORBIDDEN_FEATURE_ACTION_LABELS,
    FORBIDDEN_FEATURE_NAMES,
    FeatureQualityStatus,
    assess_dashboard_preflight_feature_quality,
    assess_dashboard_row_feature_quality,
    build_all_fixture_feature_quality_assessments,
    build_feature_quality_from_fixture,
    build_feature_quality_policy,
    build_feature_records_from_dashboard_row,
    validate_feature_quality_assessment,
)
from ai_stock.recommendation.watchlist_fixtures import (
    build_all_watchlist_source_fixtures,
    build_basic_manual_symbols_fixture,
    build_duplicates_and_disabled_fixture,
    build_empty_watchlist_fixture,
    build_forbidden_fields_sanitized_fixture,
    build_insufficient_data_review_fixture,
    build_mixed_valid_invalid_symbols_fixture,
)
from ai_stock.recommendation.watchlist_source import (
    WatchlistSourceConfig,
    build_watchlist_source_result,
)


class FeatureQualityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_feature_quality_policy()

    def test_feature_quality_policy_generation_and_immutability(self) -> None:
        self.assertEqual(self.policy.stage_name, "MS-10.00")
        self.assertEqual(self.policy.mode, "feature_data_quality_model_preflight")
        self.assertIn("symbol_identity", self.policy.allowed_feature_names)
        self.assertIn("score", self.policy.forbidden_feature_names)
        self.assertIn("buy", self.policy.forbidden_action_labels)
        with self.assertRaises(FrozenInstanceError):
            self.policy.scoring_required = True

    def test_feature_record_generation_from_dashboard_row(self) -> None:
        result = build_watchlist_source_result(
            WatchlistSourceConfig(
                source_type="manual_symbols",
                source_label="quality source",
                raw_items=(" 005930 ",),
            )
        )
        preflight = build_dashboard_preflight_from_source_result(result)
        records = build_feature_records_from_dashboard_row(preflight.rows[0])

        self.assertEqual(tuple(record.feature_name for record in records), ALLOWED_FEATURE_NAMES)
        self.assertTrue(all(record.quality_status == "quality_ok" for record in records))
        self.assertTrue(all(record.usable_for_future_scoring for record in records))

    def test_dashboard_row_based_feature_quality_assessment_generation(self) -> None:
        preflight = build_dashboard_preflight_from_fixture(
            build_basic_manual_symbols_fixture()
        )
        assessment = assess_dashboard_row_feature_quality(preflight.rows[0])

        self.assertEqual(assessment.symbol, "005930")
        self.assertEqual(assessment.quality_status, "quality_ok")
        self.assertFalse(assessment.needs_review)
        self.assertTrue(validate_feature_quality_assessment(assessment).valid)

    def test_dashboard_preflight_based_feature_quality_assessment_generation(self) -> None:
        preflight = build_dashboard_preflight_from_fixture(
            build_mixed_valid_invalid_symbols_fixture()
        )
        assessments = assess_dashboard_preflight_feature_quality(preflight)

        self.assertEqual(
            tuple(assessment.quality_status for assessment in assessments),
            (
                "quality_ok",
                "quality_invalid_candidate",
                "quality_invalid_candidate",
            ),
        )
        self.assertTrue(all(assessment.needs_review for assessment in assessments[1:]))

    def test_fixture_based_feature_quality_assessment_generation(self) -> None:
        assessments = build_feature_quality_from_fixture(
            build_basic_manual_symbols_fixture()
        )

        self.assertEqual(len(assessments), 2)
        self.assertTrue(all(assessment.quality_status == "quality_ok" for assessment in assessments))
        self.assertTrue(all(validate_feature_quality_assessment(assessment).valid for assessment in assessments))

    def test_all_six_fixture_scenarios_generate_assessments(self) -> None:
        fixtures = build_all_watchlist_source_fixtures()
        grouped_assessments = build_all_fixture_feature_quality_assessments()

        self.assertEqual(len(grouped_assessments), 6)
        self.assertEqual(len(grouped_assessments), len(fixtures))
        self.assertTrue(all(group for group in grouped_assessments))
        for group in grouped_assessments:
            for assessment in group:
                self.assertTrue(validate_feature_quality_assessment(assessment).valid)

    def test_feature_quality_output_is_deterministic(self) -> None:
        self.assertEqual(
            build_all_fixture_feature_quality_assessments(),
            build_all_fixture_feature_quality_assessments(),
        )

    def test_valid_candidate_quality_processing(self) -> None:
        assessments = build_feature_quality_from_fixture(
            build_basic_manual_symbols_fixture()
        )

        self.assertEqual(
            tuple(assessment.quality_status for assessment in assessments),
            ("quality_ok", "quality_ok"),
        )
        self.assertTrue(
            all(
                record.usable_for_future_scoring
                for assessment in assessments
                for record in assessment.feature_records
            )
        )

    def test_duplicate_candidate_quality_processing(self) -> None:
        assessments = build_feature_quality_from_fixture(
            build_duplicates_and_disabled_fixture()
        )

        self.assertIn(
            FeatureQualityStatus.QUALITY_DUPLICATE_CANDIDATE.value,
            tuple(assessment.quality_status for assessment in assessments),
        )
        duplicate = [
            assessment
            for assessment in assessments
            if assessment.quality_status == "quality_duplicate_candidate"
        ][0]
        self.assertTrue(duplicate.needs_review)
        self.assertIn("quality_duplicate_candidate", duplicate.blocked_reasons)

    def test_disabled_candidate_quality_processing(self) -> None:
        assessments = build_feature_quality_from_fixture(
            build_duplicates_and_disabled_fixture()
        )
        disabled = [
            assessment
            for assessment in assessments
            if assessment.quality_status == "quality_disabled_candidate"
        ][0]

        self.assertFalse(disabled.candidate_enabled)
        self.assertFalse(disabled.candidate_selectable)
        self.assertTrue(disabled.needs_review)

    def test_insufficient_data_quality_processing(self) -> None:
        assessments = build_feature_quality_from_fixture(
            build_insufficient_data_review_fixture()
        )

        self.assertEqual(len(assessments), 1)
        self.assertEqual(assessments[0].quality_status, "quality_insufficient_data")
        self.assertTrue(assessments[0].needs_review)
        self.assertFalse(
            any(record.usable_for_future_scoring for record in assessments[0].feature_records)
        )

    def test_forbidden_field_sanitized_quality_processing(self) -> None:
        assessments = build_feature_quality_from_fixture(
            build_forbidden_fields_sanitized_fixture()
        )
        output_model = repr(assessments)

        self.assertEqual(len(assessments), 1)
        self.assertEqual(
            assessments[0].quality_status,
            "quality_forbidden_field_sanitized",
        )
        self.assertTrue(assessments[0].needs_review)
        self.assertIn("forbidden_field", "".join(assessments[0].diagnostics))
        self.assertNotIn("redacted-not-output", output_model)
        self.assertNotIn("accountSeq=", output_model)
        self.assertNotIn("target_price=", output_model)
        self.assertNotIn("expected_return=", output_model)
        self.assertNotIn("score=", output_model)

    def test_empty_watchlist_quality_processing(self) -> None:
        assessments = build_feature_quality_from_fixture(
            build_empty_watchlist_fixture()
        )

        self.assertEqual(len(assessments), 1)
        self.assertEqual(assessments[0].quality_status, "quality_empty_input")
        self.assertEqual(assessments[0].feature_records, ())
        self.assertTrue(assessments[0].needs_review)

    def test_forbidden_field_names_are_documented_but_not_output_fields(self) -> None:
        self.assertIn("score", FORBIDDEN_FEATURE_NAMES)
        self.assertIn("target_price", FORBIDDEN_FEATURE_NAMES)
        assessment_field_names = tuple(
            field.name for field in feature_quality.fields(feature_quality.FeatureQualityAssessment)
        )

        for forbidden_field in (
            "score",
            "rank",
            "recommendation",
            "action",
            "target_price",
            "expected_return",
            "profit_probability",
            "accountSeq",
            "access_token",
            "api_key",
            "secret_key",
        ):
            self.assertNotIn(forbidden_field, assessment_field_names)

    def test_forbidden_action_labels_are_not_generated(self) -> None:
        produced_values: list[str] = []
        for group in build_all_fixture_feature_quality_assessments():
            for assessment in group:
                produced_values.append(assessment.quality_status)
                produced_values.append(assessment.validation_status)
                produced_values.extend(record.feature_name for record in assessment.feature_records)
                produced_values.extend(record.quality_status for record in assessment.feature_records)

        for forbidden_label in FORBIDDEN_CANDIDATE_LABELS:
            self.assertNotIn(forbidden_label, produced_values)
        for forbidden_label in FORBIDDEN_FEATURE_ACTION_LABELS:
            self.assertNotIn(forbidden_label, produced_values)

    def test_allowed_quality_statuses_are_safe(self) -> None:
        self.assertEqual(
            ALLOWED_QUALITY_STATUSES,
            tuple(status.value for status in FeatureQualityStatus),
        )
        for forbidden_label in FORBIDDEN_CANDIDATE_LABELS:
            self.assertNotIn(forbidden_label, ALLOWED_QUALITY_STATUSES)

    def test_required_flags_are_all_false(self) -> None:
        assessment = build_feature_quality_from_fixture(
            build_basic_manual_symbols_fixture()
        )[0]

        for flag in FEATURE_QUALITY_REQUIRED_FALSE_FLAGS:
            self.assertFalse(getattr(assessment.summary_flags, flag))

        validation = validate_feature_quality_assessment(assessment)
        self.assertFalse(validation.credential_required)
        self.assertFalse(validation.db_read_required)
        self.assertFalse(validation.db_write_required)
        self.assertFalse(validation.file_read_required)
        self.assertFalse(validation.file_write_required)
        self.assertFalse(validation.toss_api_required)
        self.assertFalse(validation.openai_required)
        self.assertFalse(validation.oauth_required)
        self.assertFalse(validation.account_seq_required)
        self.assertFalse(validation.real_order_required)
        self.assertFalse(validation.scoring_required)
        self.assertFalse(validation.ranking_required)
        self.assertFalse(validation.recommendation_required)
        self.assertFalse(validation.ui_required)
        self.assertFalse(validation.streamlit_required)
        self.assertFalse(validation.http_smoke_required)

    def test_validate_feature_quality_assessment_rejects_required_true_flag(self) -> None:
        assessment = build_feature_quality_from_fixture(
            build_basic_manual_symbols_fixture()
        )[0]
        invalid_flags = replace(assessment.summary_flags, scoring_required=True)
        invalid_assessment = replace(assessment, summary_flags=invalid_flags)
        validation = validate_feature_quality_assessment(invalid_assessment)

        self.assertFalse(validation.valid)
        self.assertTrue(validation.required_flag_true)
        self.assertIn(
            "required_flag_true:scoring_required",
            validation.rejection_reasons,
        )

    def test_policy_disables_scoring_ranking_recommendation_and_io(self) -> None:
        self.assertFalse(self.policy.actual_recommendation_allowed)
        self.assertFalse(self.policy.scoring_allowed)
        self.assertFalse(self.policy.ranking_allowed)
        self.assertFalse(self.policy.watchlist_persistence_allowed)
        self.assertFalse(self.policy.feature_file_loader_allowed)
        self.assertFalse(self.policy.watchlist_file_loader_allowed)
        self.assertFalse(self.policy.ui_change_allowed)
        self.assertFalse(self.policy.scoring_required)
        self.assertFalse(self.policy.ranking_required)
        self.assertFalse(self.policy.recommendation_required)

    def test_module_structure_has_no_io_or_external_dependencies(self) -> None:
        runtime_modules = {
            getattr(value, "__module__", "")
            for value in vars(feature_quality).values()
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

        called_names = _feature_quality_module_code_names()
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
            for part in (*vars(feature_quality), *_feature_quality_module_constants())
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

    def test_app_and_existing_recommendation_preflight_modules_are_not_modified(self) -> None:
        self.assertNotIn("app/streamlit_app.py", _feature_quality_module_constants())
        self.assertNotIn("dashboard_preflight.py", _feature_quality_module_constants())
        self.assertNotIn("watchlist_fixtures.py", _feature_quality_module_constants())


def _feature_quality_module_code_names() -> set[str]:
    names: set[str] = set()
    for value in vars(feature_quality).values():
        if isinstance(value, FunctionType):
            names.update(value.__code__.co_names)
    return names


def _feature_quality_module_constants() -> tuple[object, ...]:
    constants: list[object] = []
    for value in vars(feature_quality).values():
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
