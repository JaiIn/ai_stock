"""Pure feature quality fixture expansion for MS-10.01.

This module defines deterministic in-memory feature quality fixtures on top of
the MS-10.00 quality contract. It performs no Streamlit, file, database,
environment, network, model, account, order, clock, or random I/O. It does not
score, rank, recommend, trade, load features, or render UI.
"""

from dataclasses import dataclass
from enum import Enum

from ai_stock.recommendation.feature_quality import (
    ALLOWED_QUALITY_STATUSES,
    FEATURE_QUALITY_REQUIRED_FALSE_FLAGS,
    FORBIDDEN_FEATURE_ACTION_LABELS,
    FeatureQualityAssessment,
    build_all_fixture_feature_quality_assessments,
    build_feature_quality_from_fixture,
    build_feature_quality_policy,
    validate_feature_quality_assessment,
)
from ai_stock.recommendation.watchlist_fixtures import (
    WatchlistFixtureRecord,
    build_basic_manual_symbols_fixture,
    build_duplicates_and_disabled_fixture,
    build_empty_watchlist_fixture,
    build_forbidden_fields_sanitized_fixture,
    build_insufficient_data_review_fixture,
    build_mixed_valid_invalid_symbols_fixture,
)


class FeatureQualityFixtureScenario(str, Enum):
    """Allowed deterministic fixture expansion scenarios for MS-10.01."""

    QUALITY_BASIC_OK = "quality_basic_ok"
    QUALITY_MIXED_INVALID_AND_REVIEW = "quality_mixed_invalid_and_review"
    QUALITY_DUPLICATES_BLOCKED = "quality_duplicates_blocked"
    QUALITY_DISABLED_BLOCKED = "quality_disabled_blocked"
    QUALITY_INSUFFICIENT_DATA_BLOCKED = "quality_insufficient_data_blocked"
    QUALITY_FORBIDDEN_FIELD_SANITIZED = "quality_forbidden_field_sanitized"
    QUALITY_EMPTY_INPUT = "quality_empty_input"
    QUALITY_ALL_FIXTURE_MATRIX = "quality_all_fixture_matrix"


ALLOWED_FEATURE_QUALITY_FIXTURE_SCENARIOS: tuple[str, ...] = tuple(
    scenario.value for scenario in FeatureQualityFixtureScenario
)

FORBIDDEN_FEATURE_QUALITY_FIXTURE_SCENARIOS: tuple[str, ...] = (
    "real_account_holdings_fixture",
    "real_balance_fixture",
    "real_fills_fixture",
    "real_order_history_fixture",
    "toss_api_response_fixture",
    "oauth_response_fixture",
    "accountSeq_based_fixture",
    "raw_api_response_fixture",
    "raw_db_row_fixture",
    "db_table_row_fixture",
    "file_path_fixture",
    "credential_token_fixture",
    "openai_llm_response_fixture",
)

FEATURE_QUALITY_FIXTURE_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    FEATURE_QUALITY_REQUIRED_FALSE_FLAGS
)

FORBIDDEN_FEATURE_QUALITY_OUTPUT_KEYWORDS: tuple[str, ...] = (
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
)


@dataclass(frozen=True)
class FeatureQualityFixturePolicy:
    """Immutable fail-closed policy for MS-10.01 fixture expansion."""

    stage_name: str = "MS-10.01"
    mode: str = "feature_quality_fixture_expansion"
    allowed_scenarios: tuple[str, ...] = ALLOWED_FEATURE_QUALITY_FIXTURE_SCENARIOS
    forbidden_scenarios: tuple[str, ...] = (
        FORBIDDEN_FEATURE_QUALITY_FIXTURE_SCENARIOS
    )
    allowed_quality_statuses: tuple[str, ...] = ALLOWED_QUALITY_STATUSES
    forbidden_action_labels: tuple[str, ...] = FORBIDDEN_FEATURE_ACTION_LABELS
    required_false_flags: tuple[str, ...] = FEATURE_QUALITY_FIXTURE_REQUIRED_FALSE_FLAGS
    forbidden_absent_keywords: tuple[str, ...] = (
        FORBIDDEN_FEATURE_QUALITY_OUTPUT_KEYWORDS
    )
    actual_recommendation_allowed: bool = False
    scoring_allowed: bool = False
    ranking_allowed: bool = False
    watchlist_persistence_allowed: bool = False
    feature_file_loader_allowed: bool = False
    watchlist_file_loader_allowed: bool = False
    fixture_file_loader_allowed: bool = False
    ui_change_allowed: bool = False
    credential_required: bool = False
    db_read_required: bool = False
    db_write_required: bool = False
    file_read_required: bool = False
    file_write_required: bool = False
    toss_api_required: bool = False
    openai_required: bool = False
    oauth_required: bool = False
    account_seq_required: bool = False
    real_order_required: bool = False
    scoring_required: bool = False
    ranking_required: bool = False
    recommendation_required: bool = False
    ui_required: bool = False
    streamlit_required: bool = False
    http_smoke_required: bool = False


@dataclass(frozen=True)
class FeatureQualityFixtureRecord:
    """Fixture expectation record without raw account/API/DB payload fields."""

    scenario: str
    description: str
    source_fixture_name: str
    expected_quality_statuses: tuple[str, ...]
    expected_needs_review_count: int
    expected_usable_for_future_scoring_count: int
    expected_blocked_reason_keywords: tuple[str, ...]
    expected_warning_keywords: tuple[str, ...]
    expected_diagnostic_keywords: tuple[str, ...]
    expected_required_false_flags: tuple[str, ...]
    expected_forbidden_absent_keywords: tuple[str, ...]


@dataclass(frozen=True)
class FeatureQualityFixtureEvaluationResult:
    """Expected-vs-actual evaluation result for one fixture expansion."""

    scenario: str
    passed: bool
    failures: tuple[str, ...]
    actual_quality_statuses: tuple[str, ...]
    actual_needs_review_count: int
    actual_usable_for_future_scoring_count: int
    actual_blocked_reasons: tuple[str, ...]
    actual_warnings: tuple[str, ...]
    actual_diagnostics: tuple[str, ...]
    actual_required_flags: tuple[str, ...]
    forbidden_absent_check_passed: bool


def build_feature_quality_fixture_policy() -> FeatureQualityFixturePolicy:
    """Build the fixed MS-10.01 feature quality fixture policy."""

    return FeatureQualityFixturePolicy()


def _expected_false_flags() -> tuple[str, ...]:
    return tuple(
        f"{flag}=false" for flag in FEATURE_QUALITY_FIXTURE_REQUIRED_FALSE_FLAGS
    )


def _fixture_record(
    *,
    scenario: FeatureQualityFixtureScenario,
    description: str,
    source_fixture_name: str,
    expected_quality_statuses: tuple[str, ...],
    expected_needs_review_count: int,
    expected_usable_for_future_scoring_count: int,
    expected_blocked_reason_keywords: tuple[str, ...] = (),
    expected_warning_keywords: tuple[str, ...] = (),
    expected_diagnostic_keywords: tuple[str, ...] = (),
) -> FeatureQualityFixtureRecord:
    return FeatureQualityFixtureRecord(
        scenario=scenario.value,
        description=description,
        source_fixture_name=source_fixture_name,
        expected_quality_statuses=expected_quality_statuses,
        expected_needs_review_count=expected_needs_review_count,
        expected_usable_for_future_scoring_count=(
            expected_usable_for_future_scoring_count
        ),
        expected_blocked_reason_keywords=expected_blocked_reason_keywords,
        expected_warning_keywords=expected_warning_keywords,
        expected_diagnostic_keywords=expected_diagnostic_keywords,
        expected_required_false_flags=_expected_false_flags(),
        expected_forbidden_absent_keywords=(
            FORBIDDEN_FEATURE_QUALITY_OUTPUT_KEYWORDS
        ),
    )


def build_quality_basic_ok_fixture() -> FeatureQualityFixtureRecord:
    """Build expectations for valid manual input quality."""

    return _fixture_record(
        scenario=FeatureQualityFixtureScenario.QUALITY_BASIC_OK,
        description="Valid manual symbols produce quality_ok states only.",
        source_fixture_name="basic_manual_symbols",
        expected_quality_statuses=("quality_ok", "quality_ok"),
        expected_needs_review_count=0,
        expected_usable_for_future_scoring_count=2,
    )


def build_quality_mixed_invalid_and_review_fixture() -> (
    FeatureQualityFixtureRecord
):
    """Build expectations for mixed valid and invalid manual input."""

    return _fixture_record(
        scenario=FeatureQualityFixtureScenario.QUALITY_MIXED_INVALID_AND_REVIEW,
        description="Invalid symbols are blocked for future scoring review.",
        source_fixture_name="mixed_valid_invalid_symbols",
        expected_quality_statuses=(
            "quality_ok",
            "quality_invalid_candidate",
            "quality_invalid_candidate",
        ),
        expected_needs_review_count=2,
        expected_usable_for_future_scoring_count=1,
        expected_blocked_reason_keywords=("quality_invalid_candidate",),
        expected_warning_keywords=("invalid_symbol_review",),
        expected_diagnostic_keywords=(
            "symbol_required",
            "symbol_must_be_safe_ascii_identifier",
        ),
    )


def build_quality_duplicates_blocked_fixture() -> FeatureQualityFixtureRecord:
    """Build expectations for duplicate candidate blocking."""

    return _fixture_record(
        scenario=FeatureQualityFixtureScenario.QUALITY_DUPLICATES_BLOCKED,
        description="Duplicate candidates require review and are not usable.",
        source_fixture_name="duplicates_and_disabled",
        expected_quality_statuses=(
            "quality_ok",
            "quality_duplicate_candidate",
            "quality_disabled_candidate",
        ),
        expected_needs_review_count=2,
        expected_usable_for_future_scoring_count=1,
        expected_blocked_reason_keywords=("quality_duplicate_candidate",),
        expected_warning_keywords=("duplicate_candidate_needs_review",),
        expected_diagnostic_keywords=("duplicate_symbol",),
    )


def build_quality_disabled_blocked_fixture() -> FeatureQualityFixtureRecord:
    """Build expectations for disabled candidate blocking."""

    return _fixture_record(
        scenario=FeatureQualityFixtureScenario.QUALITY_DISABLED_BLOCKED,
        description="Disabled candidates are non-selectable review states.",
        source_fixture_name="duplicates_and_disabled",
        expected_quality_statuses=(
            "quality_ok",
            "quality_duplicate_candidate",
            "quality_disabled_candidate",
        ),
        expected_needs_review_count=2,
        expected_usable_for_future_scoring_count=1,
        expected_blocked_reason_keywords=("quality_disabled_candidate",),
        expected_warning_keywords=("disabled_candidate_not_selectable",),
        expected_diagnostic_keywords=("candidate_disabled",),
    )


def build_quality_insufficient_data_blocked_fixture() -> (
    FeatureQualityFixtureRecord
):
    """Build expectations for insufficient data blocking."""

    return _fixture_record(
        scenario=FeatureQualityFixtureScenario.QUALITY_INSUFFICIENT_DATA_BLOCKED,
        description="Partial data remains a review-only quality state.",
        source_fixture_name="insufficient_data_review",
        expected_quality_statuses=("quality_insufficient_data",),
        expected_needs_review_count=1,
        expected_usable_for_future_scoring_count=0,
        expected_blocked_reason_keywords=("quality_insufficient_data",),
        expected_warning_keywords=("insufficient_data_review",),
    )


def build_quality_forbidden_field_sanitized_fixture() -> (
    FeatureQualityFixtureRecord
):
    """Build expectations for forbidden field sanitization."""

    return _fixture_record(
        scenario=FeatureQualityFixtureScenario.QUALITY_FORBIDDEN_FIELD_SANITIZED,
        description=(
            "Forbidden fields remain diagnostics-only and do not become output "
            "feature fields."
        ),
        source_fixture_name="forbidden_fields_sanitized",
        expected_quality_statuses=("quality_forbidden_field_sanitized",),
        expected_needs_review_count=1,
        expected_usable_for_future_scoring_count=0,
        expected_blocked_reason_keywords=("quality_forbidden_field_sanitized",),
        expected_diagnostic_keywords=(
            "forbidden_field_detected:accountSeq",
            "forbidden_field_detected:target_price",
            "forbidden_field_detected:score",
            "forbidden_fields_reported_in_diagnostics_only",
        ),
    )


def build_quality_empty_input_fixture() -> FeatureQualityFixtureRecord:
    """Build expectations for safe empty input quality."""

    return _fixture_record(
        scenario=FeatureQualityFixtureScenario.QUALITY_EMPTY_INPUT,
        description="Empty watchlist input becomes a safe review state.",
        source_fixture_name="empty_watchlist",
        expected_quality_statuses=("quality_empty_input",),
        expected_needs_review_count=1,
        expected_usable_for_future_scoring_count=0,
        expected_blocked_reason_keywords=("quality_empty_input",),
        expected_warning_keywords=("empty_watchlist_safe_state",),
        expected_diagnostic_keywords=("empty_source_items",),
    )


def build_quality_all_fixture_matrix() -> FeatureQualityFixtureRecord:
    """Build expectations for the complete MS-09.04 fixture matrix."""

    return _fixture_record(
        scenario=FeatureQualityFixtureScenario.QUALITY_ALL_FIXTURE_MATRIX,
        description="All MS-09.04 fixtures produce conservative quality states.",
        source_fixture_name="all_ms09_fixture_matrix",
        expected_quality_statuses=(
            "quality_ok",
            "quality_ok",
            "quality_ok",
            "quality_invalid_candidate",
            "quality_invalid_candidate",
            "quality_ok",
            "quality_duplicate_candidate",
            "quality_disabled_candidate",
            "quality_insufficient_data",
            "quality_forbidden_field_sanitized",
            "quality_empty_input",
        ),
        expected_needs_review_count=7,
        expected_usable_for_future_scoring_count=4,
        expected_blocked_reason_keywords=(
            "quality_invalid_candidate",
            "quality_duplicate_candidate",
            "quality_disabled_candidate",
            "quality_insufficient_data",
            "quality_forbidden_field_sanitized",
            "quality_empty_input",
        ),
        expected_warning_keywords=(
            "invalid_symbol_review",
            "duplicate_candidate_needs_review",
            "disabled_candidate_not_selectable",
            "insufficient_data_review",
            "empty_watchlist_safe_state",
        ),
        expected_diagnostic_keywords=(
            "symbol_required",
            "duplicate_symbol",
            "candidate_disabled",
            "forbidden_field_detected:accountSeq",
            "empty_source_items",
        ),
    )


def build_all_feature_quality_fixtures() -> (
    tuple[FeatureQualityFixtureRecord, ...]
):
    """Build every deterministic MS-10.01 feature quality fixture."""

    return (
        build_quality_basic_ok_fixture(),
        build_quality_mixed_invalid_and_review_fixture(),
        build_quality_duplicates_blocked_fixture(),
        build_quality_disabled_blocked_fixture(),
        build_quality_insufficient_data_blocked_fixture(),
        build_quality_forbidden_field_sanitized_fixture(),
        build_quality_empty_input_fixture(),
        build_quality_all_fixture_matrix(),
    )


def _source_fixture_by_name(source_fixture_name: str) -> WatchlistFixtureRecord:
    if source_fixture_name == "basic_manual_symbols":
        return build_basic_manual_symbols_fixture()
    if source_fixture_name == "mixed_valid_invalid_symbols":
        return build_mixed_valid_invalid_symbols_fixture()
    if source_fixture_name == "duplicates_and_disabled":
        return build_duplicates_and_disabled_fixture()
    if source_fixture_name == "insufficient_data_review":
        return build_insufficient_data_review_fixture()
    if source_fixture_name == "forbidden_fields_sanitized":
        return build_forbidden_fields_sanitized_fixture()
    if source_fixture_name == "empty_watchlist":
        return build_empty_watchlist_fixture()
    raise ValueError(f"unknown_source_fixture:{source_fixture_name}")


def _flatten_assessment_groups(
    groups: tuple[tuple[FeatureQualityAssessment, ...], ...],
) -> tuple[FeatureQualityAssessment, ...]:
    return tuple(assessment for group in groups for assessment in group)


def _assessments_for_fixture(
    fixture: FeatureQualityFixtureRecord,
) -> tuple[FeatureQualityAssessment, ...]:
    policy = build_feature_quality_policy()
    if fixture.source_fixture_name == "all_ms09_fixture_matrix":
        return _flatten_assessment_groups(
            build_all_fixture_feature_quality_assessments(policy)
        )
    return build_feature_quality_from_fixture(
        _source_fixture_by_name(fixture.source_fixture_name),
        policy,
    )


def _actual_false_flags(
    assessments: tuple[FeatureQualityAssessment, ...],
) -> tuple[str, ...]:
    return tuple(
        f"{flag}={str(any(bool(getattr(assessment.summary_flags, flag)) for assessment in assessments)).lower()}"
        for flag in FEATURE_QUALITY_FIXTURE_REQUIRED_FALSE_FLAGS
    )


def _usable_assessment_count(
    assessments: tuple[FeatureQualityAssessment, ...],
) -> int:
    return sum(
        1
        for assessment in assessments
        if assessment.feature_records
        and all(record.usable_for_future_scoring for record in assessment.feature_records)
    )


def evaluate_feature_quality_fixture(
    fixture: FeatureQualityFixtureRecord,
) -> FeatureQualityFixtureEvaluationResult:
    """Compare MS-10.01 fixture expectations with MS-10.00 assessments."""

    assessments = _assessments_for_fixture(fixture)
    actual_quality_statuses = tuple(
        assessment.quality_status for assessment in assessments
    )
    actual_needs_review_count = sum(
        1 for assessment in assessments if assessment.needs_review
    )
    actual_usable_for_future_scoring_count = _usable_assessment_count(assessments)
    actual_blocked_reasons = tuple(
        reason for assessment in assessments for reason in assessment.blocked_reasons
    )
    actual_warnings = tuple(
        warning for assessment in assessments for warning in assessment.quality_warnings
    )
    actual_diagnostics = tuple(
        diagnostic for assessment in assessments for diagnostic in assessment.diagnostics
    )
    actual_required_flags = _actual_false_flags(assessments)
    validation_results = tuple(
        validate_feature_quality_assessment(assessment) for assessment in assessments
    )
    rendered_assessments = repr(assessments)
    forbidden_absent_check_passed = not any(
        keyword in rendered_assessments
        for keyword in fixture.expected_forbidden_absent_keywords
    )

    failures: list[str] = []
    if actual_quality_statuses != fixture.expected_quality_statuses:
        failures.append("quality_statuses_mismatch")
    if actual_needs_review_count != fixture.expected_needs_review_count:
        failures.append("needs_review_count_mismatch")
    if (
        actual_usable_for_future_scoring_count
        != fixture.expected_usable_for_future_scoring_count
    ):
        failures.append("usable_for_future_scoring_count_mismatch")
    if actual_required_flags != fixture.expected_required_false_flags:
        failures.append("required_false_flags_mismatch")
    if not forbidden_absent_check_passed:
        failures.append("forbidden_keyword_present")

    for expected_keyword in fixture.expected_blocked_reason_keywords:
        if not any(expected_keyword in value for value in actual_blocked_reasons):
            failures.append(f"missing_blocked_reason:{expected_keyword}")

    for expected_keyword in fixture.expected_warning_keywords:
        if not any(expected_keyword in value for value in actual_warnings):
            failures.append(f"missing_warning:{expected_keyword}")

    for expected_keyword in fixture.expected_diagnostic_keywords:
        if not any(expected_keyword in value for value in actual_diagnostics):
            failures.append(f"missing_diagnostic:{expected_keyword}")

    for validation in validation_results:
        if not validation.valid:
            failures.extend(
                f"invalid_assessment:{reason}"
                for reason in validation.rejection_reasons
            )

    return FeatureQualityFixtureEvaluationResult(
        scenario=fixture.scenario,
        passed=not failures,
        failures=tuple(failures),
        actual_quality_statuses=actual_quality_statuses,
        actual_needs_review_count=actual_needs_review_count,
        actual_usable_for_future_scoring_count=(
            actual_usable_for_future_scoring_count
        ),
        actual_blocked_reasons=actual_blocked_reasons,
        actual_warnings=actual_warnings,
        actual_diagnostics=actual_diagnostics,
        actual_required_flags=actual_required_flags,
        forbidden_absent_check_passed=forbidden_absent_check_passed,
    )


def evaluate_all_feature_quality_fixtures() -> (
    tuple[FeatureQualityFixtureEvaluationResult, ...]
):
    """Evaluate every deterministic MS-10.01 feature quality fixture."""

    return tuple(
        evaluate_feature_quality_fixture(fixture)
        for fixture in build_all_feature_quality_fixtures()
    )
