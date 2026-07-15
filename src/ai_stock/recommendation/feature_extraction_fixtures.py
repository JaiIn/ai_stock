"""Pure feature extraction fixture hardening for MS-10.03.

This module defines deterministic in-memory fixture expectations on top of the
MS-10.02 extraction contract. It performs no Streamlit, file, database,
environment, network, model, account, order, clock, or random I/O. It does not
score, rank, recommend, trade, load features, or render UI.
"""

from dataclasses import dataclass
from enum import Enum

from ai_stock.recommendation.feature_extraction_preflight import (
    ALLOWED_EXTRACTION_STATUSES,
    FEATURE_EXTRACTION_REQUIRED_FALSE_FLAGS,
    FORBIDDEN_EXTRACTION_OUTPUT_LABELS,
    FORBIDDEN_FEATURE_EXTRACTION_SOURCES,
    ExtractedFeatureSet,
    build_feature_extraction_policy,
    extract_feature_sets_from_all_fixtures,
    extract_feature_sets_from_fixture,
    summarize_feature_extraction_results,
    validate_extracted_feature_set,
)
from ai_stock.recommendation.feature_quality_fixtures import (
    build_all_feature_quality_fixtures,
    evaluate_all_feature_quality_fixtures,
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


class FeatureExtractionFixtureScenario(str, Enum):
    """Allowed deterministic extraction hardening scenarios for MS-10.03."""

    EXTRACTION_BASIC_READY = "extraction_basic_ready"
    EXTRACTION_MIXED_REVIEW = "extraction_mixed_review"
    EXTRACTION_DUPLICATES_BLOCKED = "extraction_duplicates_blocked"
    EXTRACTION_DISABLED_BLOCKED = "extraction_disabled_blocked"
    EXTRACTION_MISSING_DATA_BLOCKED = "extraction_missing_data_blocked"
    EXTRACTION_FORBIDDEN_FIELD_SANITIZED = (
        "extraction_forbidden_field_sanitized"
    )
    EXTRACTION_EMPTY_INPUT = "extraction_empty_input"
    EXTRACTION_ALL_FIXTURE_MATRIX = "extraction_all_fixture_matrix"


ALLOWED_FEATURE_EXTRACTION_FIXTURE_SCENARIOS: tuple[str, ...] = tuple(
    scenario.value for scenario in FeatureExtractionFixtureScenario
)

FORBIDDEN_FEATURE_EXTRACTION_FIXTURE_SCENARIOS: tuple[str, ...] = (
    "real_account_holdings_fixture",
    "real_balance_fixture",
    "real_fills_fixture",
    "real_order_history_fixture",
    "toss_api_response_fixture",
    "oauth_response_fixture",
    "openai_llm_response_fixture",
    "accountSeq_based_fixture",
    "raw_api_response_fixture",
    "raw_db_row_fixture",
    "db_table_row_fixture",
    "file_path_fixture",
    "feature_file_fixture",
    "watchlist_file_fixture",
    "credential_token_key_fixture",
)

FEATURE_EXTRACTION_FIXTURE_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    FEATURE_EXTRACTION_REQUIRED_FALSE_FLAGS
)

FORBIDDEN_FEATURE_EXTRACTION_OUTPUT_KEYWORDS: tuple[str, ...] = (
    "redacted-not-output",
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
    "score=",
    "rank=",
    "recommendation=",
    "action=",
    "buy=",
    "sell=",
    "hold=",
    "target_price=",
    "expected_return=",
    "profit_probability=",
)


@dataclass(frozen=True)
class FeatureExtractionFixturePolicy:
    """Immutable fail-closed policy for MS-10.03 fixture hardening."""

    stage_name: str = "MS-10.03"
    mode: str = "feature_extraction_fixture_hardening"
    allowed_scenarios: tuple[str, ...] = (
        ALLOWED_FEATURE_EXTRACTION_FIXTURE_SCENARIOS
    )
    forbidden_scenarios: tuple[str, ...] = (
        FORBIDDEN_FEATURE_EXTRACTION_FIXTURE_SCENARIOS
    )
    allowed_extraction_statuses: tuple[str, ...] = ALLOWED_EXTRACTION_STATUSES
    forbidden_extraction_sources: tuple[str, ...] = (
        FORBIDDEN_FEATURE_EXTRACTION_SOURCES
    )
    forbidden_output_labels: tuple[str, ...] = FORBIDDEN_EXTRACTION_OUTPUT_LABELS
    required_false_flags: tuple[str, ...] = (
        FEATURE_EXTRACTION_FIXTURE_REQUIRED_FALSE_FLAGS
    )
    forbidden_absent_keywords: tuple[str, ...] = (
        FORBIDDEN_FEATURE_EXTRACTION_OUTPUT_KEYWORDS
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
class FeatureExtractionFixtureRecord:
    """Extraction fixture expectations without scoring or account fields."""

    scenario: str
    description: str
    source_fixture_name: str
    expected_extraction_statuses: tuple[str, ...]
    expected_ready_count: int
    expected_needs_review_count: int
    expected_usable_for_future_scoring_count: int
    expected_missing_feature_keywords: tuple[str, ...]
    expected_blocked_feature_keywords: tuple[str, ...]
    expected_blocked_reason_keywords: tuple[str, ...]
    expected_warning_keywords: tuple[str, ...]
    expected_diagnostic_keywords: tuple[str, ...]
    expected_required_false_flags: tuple[str, ...]
    expected_forbidden_absent_keywords: tuple[str, ...]


@dataclass(frozen=True)
class FeatureExtractionFixtureEvaluationResult:
    """Expected-vs-actual evaluation result for one extraction fixture."""

    scenario: str
    passed: bool
    failures: tuple[str, ...]
    actual_extraction_statuses: tuple[str, ...]
    actual_ready_count: int
    actual_needs_review_count: int
    actual_usable_for_future_scoring_count: int
    actual_missing_features: tuple[str, ...]
    actual_blocked_features: tuple[str, ...]
    actual_blocked_reasons: tuple[str, ...]
    actual_warnings: tuple[str, ...]
    actual_diagnostics: tuple[str, ...]
    actual_required_flags: tuple[str, ...]
    forbidden_absent_check_passed: bool


def build_feature_extraction_fixture_policy() -> (
    FeatureExtractionFixturePolicy
):
    """Build the fixed MS-10.03 extraction fixture hardening policy."""

    return FeatureExtractionFixturePolicy()


def _expected_false_flags() -> tuple[str, ...]:
    return tuple(
        f"{flag}=false"
        for flag in FEATURE_EXTRACTION_FIXTURE_REQUIRED_FALSE_FLAGS
    )


def _fixture_record(
    *,
    scenario: FeatureExtractionFixtureScenario,
    description: str,
    source_fixture_name: str,
    expected_extraction_statuses: tuple[str, ...],
    expected_ready_count: int,
    expected_needs_review_count: int,
    expected_usable_for_future_scoring_count: int,
    expected_missing_feature_keywords: tuple[str, ...] = (),
    expected_blocked_feature_keywords: tuple[str, ...] = (),
    expected_blocked_reason_keywords: tuple[str, ...] = (),
    expected_warning_keywords: tuple[str, ...] = (),
    expected_diagnostic_keywords: tuple[str, ...] = (),
) -> FeatureExtractionFixtureRecord:
    return FeatureExtractionFixtureRecord(
        scenario=scenario.value,
        description=description,
        source_fixture_name=source_fixture_name,
        expected_extraction_statuses=expected_extraction_statuses,
        expected_ready_count=expected_ready_count,
        expected_needs_review_count=expected_needs_review_count,
        expected_usable_for_future_scoring_count=(
            expected_usable_for_future_scoring_count
        ),
        expected_missing_feature_keywords=expected_missing_feature_keywords,
        expected_blocked_feature_keywords=expected_blocked_feature_keywords,
        expected_blocked_reason_keywords=expected_blocked_reason_keywords,
        expected_warning_keywords=expected_warning_keywords,
        expected_diagnostic_keywords=expected_diagnostic_keywords,
        expected_required_false_flags=_expected_false_flags(),
        expected_forbidden_absent_keywords=(
            FORBIDDEN_FEATURE_EXTRACTION_OUTPUT_KEYWORDS
        ),
    )


def build_extraction_basic_ready_fixture() -> (
    FeatureExtractionFixtureRecord
):
    """Build expectations for valid manual extraction readiness."""

    return _fixture_record(
        scenario=FeatureExtractionFixtureScenario.EXTRACTION_BASIC_READY,
        description="Valid manual symbols extract ready feature sets.",
        source_fixture_name="basic_manual_symbols",
        expected_extraction_statuses=(
            "extraction_ready",
            "extraction_ready",
        ),
        expected_ready_count=2,
        expected_needs_review_count=0,
        expected_usable_for_future_scoring_count=2,
    )


def build_extraction_mixed_review_fixture() -> (
    FeatureExtractionFixtureRecord
):
    """Build expectations for mixed valid and invalid extraction input."""

    return _fixture_record(
        scenario=FeatureExtractionFixtureScenario.EXTRACTION_MIXED_REVIEW,
        description="Invalid symbols remain review-only extraction states.",
        source_fixture_name="mixed_valid_invalid_symbols",
        expected_extraction_statuses=(
            "extraction_ready",
            "extraction_invalid_candidate",
            "extraction_invalid_candidate",
        ),
        expected_ready_count=1,
        expected_needs_review_count=2,
        expected_usable_for_future_scoring_count=1,
        expected_blocked_reason_keywords=("quality_invalid_candidate",),
        expected_warning_keywords=("invalid_symbol_review",),
        expected_diagnostic_keywords=(
            "symbol_required",
            "symbol_must_be_safe_ascii_identifier",
        ),
    )


def build_extraction_duplicates_blocked_fixture() -> (
    FeatureExtractionFixtureRecord
):
    """Build expectations for duplicate extraction blocking."""

    return _fixture_record(
        scenario=FeatureExtractionFixtureScenario.EXTRACTION_DUPLICATES_BLOCKED,
        description="Duplicate candidates are blocked for extraction readiness.",
        source_fixture_name="duplicates_and_disabled",
        expected_extraction_statuses=(
            "extraction_ready",
            "extraction_duplicate_candidate",
            "extraction_disabled_candidate",
        ),
        expected_ready_count=1,
        expected_needs_review_count=2,
        expected_usable_for_future_scoring_count=1,
        expected_blocked_reason_keywords=("quality_duplicate_candidate",),
        expected_warning_keywords=("duplicate_candidate_needs_review",),
        expected_diagnostic_keywords=("duplicate_symbol",),
    )


def build_extraction_disabled_blocked_fixture() -> (
    FeatureExtractionFixtureRecord
):
    """Build expectations for disabled extraction blocking."""

    return _fixture_record(
        scenario=FeatureExtractionFixtureScenario.EXTRACTION_DISABLED_BLOCKED,
        description="Disabled candidates are non-ready extraction states.",
        source_fixture_name="duplicates_and_disabled",
        expected_extraction_statuses=(
            "extraction_ready",
            "extraction_duplicate_candidate",
            "extraction_disabled_candidate",
        ),
        expected_ready_count=1,
        expected_needs_review_count=2,
        expected_usable_for_future_scoring_count=1,
        expected_blocked_reason_keywords=("quality_disabled_candidate",),
        expected_warning_keywords=("disabled_candidate_not_selectable",),
        expected_diagnostic_keywords=("candidate_disabled",),
    )


def build_extraction_missing_data_blocked_fixture() -> (
    FeatureExtractionFixtureRecord
):
    """Build expectations for missing data extraction blocking."""

    return _fixture_record(
        scenario=(
            FeatureExtractionFixtureScenario.EXTRACTION_MISSING_DATA_BLOCKED
        ),
        description="Insufficient data remains blocked for extraction.",
        source_fixture_name="insufficient_data_review",
        expected_extraction_statuses=("extraction_missing_data",),
        expected_ready_count=0,
        expected_needs_review_count=1,
        expected_usable_for_future_scoring_count=0,
        expected_missing_feature_keywords=("symbol_identity",),
        expected_blocked_feature_keywords=("symbol_identity",),
        expected_blocked_reason_keywords=("quality_insufficient_data",),
        expected_warning_keywords=("insufficient_data_review",),
    )


def build_extraction_forbidden_field_sanitized_fixture() -> (
    FeatureExtractionFixtureRecord
):
    """Build expectations for forbidden-field sanitization extraction."""

    return _fixture_record(
        scenario=(
            FeatureExtractionFixtureScenario
            .EXTRACTION_FORBIDDEN_FIELD_SANITIZED
        ),
        description="Forbidden fields remain diagnostics-only in extraction.",
        source_fixture_name="forbidden_fields_sanitized",
        expected_extraction_statuses=(
            "extraction_forbidden_field_sanitized",
        ),
        expected_ready_count=0,
        expected_needs_review_count=1,
        expected_usable_for_future_scoring_count=0,
        expected_blocked_reason_keywords=(
            "quality_forbidden_field_sanitized",
        ),
        expected_diagnostic_keywords=(
            "forbidden_field_detected:accountSeq",
            "forbidden_field_detected:target_price",
            "forbidden_field_detected:score",
            "forbidden_fields_reported_in_diagnostics_only",
        ),
    )


def build_extraction_empty_input_fixture() -> (
    FeatureExtractionFixtureRecord
):
    """Build expectations for safe empty input extraction."""

    return _fixture_record(
        scenario=FeatureExtractionFixtureScenario.EXTRACTION_EMPTY_INPUT,
        description="Empty watchlist input remains a safe extraction state.",
        source_fixture_name="empty_watchlist",
        expected_extraction_statuses=("extraction_empty_input",),
        expected_ready_count=0,
        expected_needs_review_count=1,
        expected_usable_for_future_scoring_count=0,
        expected_missing_feature_keywords=("symbol_identity",),
        expected_blocked_reason_keywords=("quality_empty_input",),
        expected_warning_keywords=("empty_watchlist_safe_state",),
        expected_diagnostic_keywords=("empty_source_items",),
    )


def build_extraction_all_fixture_matrix() -> (
    FeatureExtractionFixtureRecord
):
    """Build expectations for the complete extraction fixture matrix."""

    return _fixture_record(
        scenario=FeatureExtractionFixtureScenario.EXTRACTION_ALL_FIXTURE_MATRIX,
        description="All MS-09.04 fixtures produce safe extraction states.",
        source_fixture_name="all_ms09_fixture_matrix",
        expected_extraction_statuses=(
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
        expected_ready_count=4,
        expected_needs_review_count=7,
        expected_usable_for_future_scoring_count=4,
        expected_missing_feature_keywords=("symbol_identity",),
        expected_blocked_feature_keywords=("symbol_identity",),
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


def build_all_feature_extraction_fixtures() -> (
    tuple[FeatureExtractionFixtureRecord, ...]
):
    """Build every deterministic MS-10.03 extraction fixture."""

    return (
        build_extraction_basic_ready_fixture(),
        build_extraction_mixed_review_fixture(),
        build_extraction_duplicates_blocked_fixture(),
        build_extraction_disabled_blocked_fixture(),
        build_extraction_missing_data_blocked_fixture(),
        build_extraction_forbidden_field_sanitized_fixture(),
        build_extraction_empty_input_fixture(),
        build_extraction_all_fixture_matrix(),
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


def _flatten_feature_set_groups(
    groups: tuple[tuple[ExtractedFeatureSet, ...], ...],
) -> tuple[ExtractedFeatureSet, ...]:
    return tuple(feature_set for group in groups for feature_set in group)


def _feature_sets_for_fixture(
    fixture: FeatureExtractionFixtureRecord,
) -> tuple[ExtractedFeatureSet, ...]:
    policy = build_feature_extraction_policy()
    evaluate_all_feature_quality_fixtures()
    build_all_feature_quality_fixtures()
    if fixture.source_fixture_name == "all_ms09_fixture_matrix":
        return _flatten_feature_set_groups(
            extract_feature_sets_from_all_fixtures(policy)
        )
    return extract_feature_sets_from_fixture(
        _source_fixture_by_name(fixture.source_fixture_name),
        policy,
    )


def _actual_false_flags(
    feature_sets: tuple[ExtractedFeatureSet, ...],
) -> tuple[str, ...]:
    return tuple(
        f"{flag}={str(any(bool(getattr(feature_set.summary_flags, flag)) for feature_set in feature_sets)).lower()}"
        for flag in FEATURE_EXTRACTION_FIXTURE_REQUIRED_FALSE_FLAGS
    )


def _flatten_missing_features(
    feature_sets: tuple[ExtractedFeatureSet, ...],
) -> tuple[str, ...]:
    return tuple(
        missing
        for feature_set in feature_sets
        for missing in feature_set.missing_features
    )


def _flatten_blocked_features(
    feature_sets: tuple[ExtractedFeatureSet, ...],
) -> tuple[str, ...]:
    return tuple(
        blocked
        for feature_set in feature_sets
        for blocked in feature_set.blocked_features
    )


def evaluate_feature_extraction_fixture(
    fixture: FeatureExtractionFixtureRecord,
) -> FeatureExtractionFixtureEvaluationResult:
    """Compare MS-10.03 fixture expectations with extraction outputs."""

    feature_sets = _feature_sets_for_fixture(fixture)
    summary = summarize_feature_extraction_results(feature_sets)
    actual_extraction_statuses = tuple(
        feature_set.extraction_status for feature_set in feature_sets
    )
    actual_missing_features = _flatten_missing_features(feature_sets)
    actual_blocked_features = _flatten_blocked_features(feature_sets)
    actual_blocked_reasons = tuple(
        reason for feature_set in feature_sets for reason in feature_set.blocked_reasons
    )
    actual_warnings = tuple(
        warning for feature_set in feature_sets for warning in feature_set.quality_warnings
    )
    actual_diagnostics = tuple(
        diagnostic for feature_set in feature_sets for diagnostic in feature_set.diagnostics
    )
    actual_required_flags = _actual_false_flags(feature_sets)
    validation_results = tuple(
        validate_extracted_feature_set(feature_set) for feature_set in feature_sets
    )
    rendered_feature_sets = repr(feature_sets)
    forbidden_absent_check_passed = not any(
        keyword in rendered_feature_sets
        for keyword in fixture.expected_forbidden_absent_keywords
    )

    failures: list[str] = []
    if actual_extraction_statuses != fixture.expected_extraction_statuses:
        failures.append("extraction_statuses_mismatch")
    if summary.ready_sets != fixture.expected_ready_count:
        failures.append("ready_count_mismatch")
    if summary.needs_review_sets != fixture.expected_needs_review_count:
        failures.append("needs_review_count_mismatch")
    if (
        summary.usable_for_future_scoring_sets
        != fixture.expected_usable_for_future_scoring_count
    ):
        failures.append("usable_for_future_scoring_count_mismatch")
    if actual_required_flags != fixture.expected_required_false_flags:
        failures.append("required_false_flags_mismatch")
    if not forbidden_absent_check_passed:
        failures.append("forbidden_keyword_present")

    for expected_keyword in fixture.expected_missing_feature_keywords:
        if not any(expected_keyword in value for value in actual_missing_features):
            failures.append(f"missing_missing_feature:{expected_keyword}")

    for expected_keyword in fixture.expected_blocked_feature_keywords:
        if not any(expected_keyword in value for value in actual_blocked_features):
            failures.append(f"missing_blocked_feature:{expected_keyword}")

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
                f"invalid_extracted_feature_set:{reason}"
                for reason in validation.rejection_reasons
            )

    return FeatureExtractionFixtureEvaluationResult(
        scenario=fixture.scenario,
        passed=not failures,
        failures=tuple(failures),
        actual_extraction_statuses=actual_extraction_statuses,
        actual_ready_count=summary.ready_sets,
        actual_needs_review_count=summary.needs_review_sets,
        actual_usable_for_future_scoring_count=(
            summary.usable_for_future_scoring_sets
        ),
        actual_missing_features=actual_missing_features,
        actual_blocked_features=actual_blocked_features,
        actual_blocked_reasons=actual_blocked_reasons,
        actual_warnings=actual_warnings,
        actual_diagnostics=actual_diagnostics,
        actual_required_flags=actual_required_flags,
        forbidden_absent_check_passed=forbidden_absent_check_passed,
    )


def evaluate_all_feature_extraction_fixtures() -> (
    tuple[FeatureExtractionFixtureEvaluationResult, ...]
):
    """Evaluate every deterministic MS-10.03 extraction fixture."""

    return tuple(
        evaluate_feature_extraction_fixture(fixture)
        for fixture in build_all_feature_extraction_fixtures()
    )
