"""Pure deterministic feature extraction preflight for MS-10.02.

This module normalizes existing in-memory dashboard/quality fixture outputs
into future-scoring candidate feature sets. It performs no Streamlit, file,
database, environment, network, model, account, order, clock, or random I/O.
It does not score, rank, recommend, trade, load features, or render UI.
"""

from dataclasses import dataclass, fields
from enum import Enum

from ai_stock.recommendation.feature_quality import (
    ALLOWED_FEATURE_NAMES,
    FEATURE_QUALITY_REQUIRED_FALSE_FLAGS,
    FORBIDDEN_FEATURE_ACTION_LABELS,
    FORBIDDEN_FEATURE_NAMES,
    FeatureQualityAssessment,
    FeatureQualityStatus,
    FeatureRecord,
    build_feature_quality_from_fixture,
    validate_feature_quality_assessment,
)
from ai_stock.recommendation.feature_quality_fixtures import (
    FeatureQualityFixtureRecord,
    build_all_feature_quality_fixtures,
    evaluate_all_feature_quality_fixtures,
    evaluate_feature_quality_fixture,
)
from ai_stock.recommendation.watchlist_fixtures import (
    WatchlistFixtureRecord,
    build_all_watchlist_source_fixtures,
    build_basic_manual_symbols_fixture,
    build_duplicates_and_disabled_fixture,
    build_empty_watchlist_fixture,
    build_forbidden_fields_sanitized_fixture,
    build_insufficient_data_review_fixture,
    build_mixed_valid_invalid_symbols_fixture,
)


class FeatureExtractionStatus(str, Enum):
    """Allowed non-directive extraction states for MS-10.02."""

    EXTRACTION_READY = "extraction_ready"
    EXTRACTION_NEEDS_REVIEW = "extraction_needs_review"
    EXTRACTION_BLOCKED_QUALITY = "extraction_blocked_quality"
    EXTRACTION_MISSING_DATA = "extraction_missing_data"
    EXTRACTION_INVALID_CANDIDATE = "extraction_invalid_candidate"
    EXTRACTION_DUPLICATE_CANDIDATE = "extraction_duplicate_candidate"
    EXTRACTION_DISABLED_CANDIDATE = "extraction_disabled_candidate"
    EXTRACTION_FORBIDDEN_FIELD_SANITIZED = (
        "extraction_forbidden_field_sanitized"
    )
    EXTRACTION_EMPTY_INPUT = "extraction_empty_input"


ALLOWED_FEATURE_EXTRACTION_SOURCES: tuple[str, ...] = (
    "feature_quality_assessment",
    "dashboard_preflight_assessment",
    "watchlist_fixture_assessment",
    "feature_quality_fixture_evaluation",
    "all_fixture_feature_quality_assessments",
)

FORBIDDEN_FEATURE_EXTRACTION_SOURCES: tuple[str, ...] = (
    "file_path",
    "feature_file",
    "watchlist_file",
    "database",
    "sqlite",
    "db_table",
    "toss_api",
    "oauth",
    "openai",
    "llm",
    "account",
    "holdings",
    "order",
    "balance",
    "fills",
    "raw_api_response",
    "raw_db_row",
    "credential",
    "token",
    "accountSeq",
)

ALLOWED_EXTRACTION_STATUSES: tuple[str, ...] = tuple(
    status.value for status in FeatureExtractionStatus
)

FORBIDDEN_EXTRACTION_OUTPUT_LABELS: tuple[str, ...] = (
    *FORBIDDEN_FEATURE_ACTION_LABELS,
    "strong_buy",
    "target_price",
    "profit_expected",
    "must_buy",
    "must_sell",
)

FORBIDDEN_EXTRACTION_FEATURE_NAMES: tuple[str, ...] = (
    *FORBIDDEN_FEATURE_NAMES,
    "authorization",
    "bearer",
    "client_secret",
    "raw_response",
    "raw_request",
    "db_row",
    "file_path",
    "env_path",
    ".env.local",
)

FEATURE_EXTRACTION_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    FEATURE_QUALITY_REQUIRED_FALSE_FLAGS
)


@dataclass(frozen=True)
class FeatureExtractionSummaryFlags:
    """All required external capability flags remain false for MS-10.02."""

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
class FeatureExtractionPolicy:
    """Immutable fail-closed policy for deterministic feature extraction."""

    stage_name: str = "MS-10.02"
    mode: str = "deterministic_feature_extraction_preflight"
    allowed_extraction_sources: tuple[str, ...] = (
        ALLOWED_FEATURE_EXTRACTION_SOURCES
    )
    forbidden_extraction_sources: tuple[str, ...] = (
        FORBIDDEN_FEATURE_EXTRACTION_SOURCES
    )
    allowed_extraction_statuses: tuple[str, ...] = ALLOWED_EXTRACTION_STATUSES
    allowed_feature_names: tuple[str, ...] = ALLOWED_FEATURE_NAMES
    forbidden_feature_names: tuple[str, ...] = FORBIDDEN_EXTRACTION_FEATURE_NAMES
    forbidden_output_labels: tuple[str, ...] = FORBIDDEN_EXTRACTION_OUTPUT_LABELS
    required_false_flags: tuple[str, ...] = FEATURE_EXTRACTION_REQUIRED_FALSE_FLAGS
    observation_only_policy: str = "extraction_only_not_recommendation"
    no_scoring_policy: str = "no_score_rank_or_model_output"
    no_recommendation_policy: str = "no_action_label_or_recommendation_output"
    deterministic_only_policy: str = "in_memory_quality_assessment_only"
    actual_recommendation_allowed: bool = False
    scoring_allowed: bool = False
    ranking_allowed: bool = False
    watchlist_persistence_allowed: bool = False
    feature_file_loader_allowed: bool = False
    watchlist_file_loader_allowed: bool = False
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
class FeatureExtractionInput:
    """Normalized extraction input copied from quality assessment only."""

    symbol: str
    market: str
    source: str
    source_label: str
    quality_status: str
    data_availability_hint: str
    needs_review: bool
    usable_for_future_scoring: bool
    feature_records: tuple[FeatureRecord, ...]
    diagnostics: tuple[str, ...]
    warnings: tuple[str, ...]
    blocked_reasons: tuple[str, ...]


@dataclass(frozen=True)
class ExtractedFeatureValue:
    """One safe feature value transferred from MS-10.00 quality records."""

    feature_name: str
    feature_value: str | bool | int | None
    feature_source: str
    quality_status: str
    usable_for_future_scoring: bool


@dataclass(frozen=True)
class ExtractedFeatureSet:
    """Future-scoring candidate feature set without scoring or ranking."""

    symbol: str
    market: str
    extraction_source: str
    extraction_status: str
    extracted_features: tuple[ExtractedFeatureValue, ...]
    missing_features: tuple[str, ...]
    blocked_features: tuple[str, ...]
    quality_status: str
    quality_warnings: tuple[str, ...]
    diagnostics: tuple[str, ...]
    needs_review: bool
    usable_for_future_scoring: bool
    blocked_reasons: tuple[str, ...]
    summary_flags: FeatureExtractionSummaryFlags


@dataclass(frozen=True)
class FeatureExtractionValidationResult:
    """Validation result for one extracted feature set."""

    valid: bool
    rejection_reasons: tuple[str, ...]
    diagnostics: tuple[str, ...]
    forbidden_source_present: bool
    forbidden_feature_present: bool
    forbidden_output_label_present: bool
    required_flag_true: bool
    credential_required: bool
    db_read_required: bool
    db_write_required: bool
    file_read_required: bool
    file_write_required: bool
    toss_api_required: bool
    openai_required: bool
    oauth_required: bool
    account_seq_required: bool
    real_order_required: bool
    scoring_required: bool
    ranking_required: bool
    recommendation_required: bool
    ui_required: bool
    streamlit_required: bool
    http_smoke_required: bool


@dataclass(frozen=True)
class FeatureExtractionSummary:
    """Aggregate deterministic extraction results without scoring output."""

    total_sets: int
    ready_sets: int
    needs_review_sets: int
    blocked_sets: int
    missing_data_sets: int
    usable_for_future_scoring_sets: int
    diagnostics: tuple[str, ...]
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


def build_feature_extraction_policy() -> FeatureExtractionPolicy:
    """Build the fixed MS-10.02 feature extraction preflight policy."""

    return FeatureExtractionPolicy()


def _false_flags() -> FeatureExtractionSummaryFlags:
    return FeatureExtractionSummaryFlags()


def _all_records_usable(records: tuple[FeatureRecord, ...]) -> bool:
    return bool(records) and all(record.usable_for_future_scoring for record in records)


def _input_usable_for_future_scoring(
    assessment: FeatureQualityAssessment,
) -> bool:
    return (
        assessment.quality_status == FeatureQualityStatus.QUALITY_OK.value
        and not assessment.needs_review
        and _all_records_usable(assessment.feature_records)
    )


def _extraction_status_from_quality(
    extraction_input: FeatureExtractionInput,
) -> str:
    quality_status = extraction_input.quality_status
    if (
        quality_status == FeatureQualityStatus.QUALITY_OK.value
        and extraction_input.usable_for_future_scoring
    ):
        return FeatureExtractionStatus.EXTRACTION_READY.value
    if quality_status == FeatureQualityStatus.QUALITY_DUPLICATE_CANDIDATE.value:
        return FeatureExtractionStatus.EXTRACTION_DUPLICATE_CANDIDATE.value
    if quality_status == FeatureQualityStatus.QUALITY_DISABLED_CANDIDATE.value:
        return FeatureExtractionStatus.EXTRACTION_DISABLED_CANDIDATE.value
    if quality_status in (
        FeatureQualityStatus.QUALITY_INSUFFICIENT_DATA.value,
        FeatureQualityStatus.QUALITY_MISSING_DATA.value,
    ):
        return FeatureExtractionStatus.EXTRACTION_MISSING_DATA.value
    if quality_status in (
        FeatureQualityStatus.QUALITY_INVALID_CANDIDATE.value,
        FeatureQualityStatus.QUALITY_FORBIDDEN_SOURCE.value,
    ):
        return FeatureExtractionStatus.EXTRACTION_INVALID_CANDIDATE.value
    if quality_status == FeatureQualityStatus.QUALITY_FORBIDDEN_FIELD_SANITIZED.value:
        return FeatureExtractionStatus.EXTRACTION_FORBIDDEN_FIELD_SANITIZED.value
    if quality_status == FeatureQualityStatus.QUALITY_EMPTY_INPUT.value:
        return FeatureExtractionStatus.EXTRACTION_EMPTY_INPUT.value
    if extraction_input.needs_review:
        return FeatureExtractionStatus.EXTRACTION_NEEDS_REVIEW.value
    return FeatureExtractionStatus.EXTRACTION_BLOCKED_QUALITY.value


def _safe_feature_value(
    record: FeatureRecord,
) -> ExtractedFeatureValue:
    return ExtractedFeatureValue(
        feature_name=record.feature_name,
        feature_value=record.feature_value,
        feature_source=record.feature_source,
        quality_status=record.quality_status,
        usable_for_future_scoring=record.usable_for_future_scoring,
    )


def _safe_feature_records(
    extraction_input: FeatureExtractionInput,
    policy: FeatureExtractionPolicy,
) -> tuple[ExtractedFeatureValue, ...]:
    return tuple(
        _safe_feature_value(record)
        for record in extraction_input.feature_records
        if record.feature_name in policy.allowed_feature_names
        and record.feature_name not in policy.forbidden_feature_names
        and record.usable_for_future_scoring
        and extraction_input.usable_for_future_scoring
    )


def _missing_features(
    extracted_features: tuple[ExtractedFeatureValue, ...],
    policy: FeatureExtractionPolicy,
) -> tuple[str, ...]:
    produced_names = tuple(feature.feature_name for feature in extracted_features)
    return tuple(
        feature_name
        for feature_name in policy.allowed_feature_names
        if feature_name not in produced_names
    )


def _blocked_features(
    extraction_input: FeatureExtractionInput,
    extracted_features: tuple[ExtractedFeatureValue, ...],
    policy: FeatureExtractionPolicy,
) -> tuple[str, ...]:
    extracted_names = tuple(feature.feature_name for feature in extracted_features)
    return tuple(
        record.feature_name
        for record in extraction_input.feature_records
        if record.feature_name in policy.allowed_feature_names
        and record.feature_name not in extracted_names
    )


def build_feature_extraction_input_from_quality_assessment(
    assessment: FeatureQualityAssessment,
) -> FeatureExtractionInput:
    """Normalize an MS-10.00 quality assessment for extraction preflight."""

    validation = validate_feature_quality_assessment(assessment)
    diagnostics = assessment.diagnostics + tuple(
        f"quality_validation:{reason}" for reason in validation.rejection_reasons
    )
    return FeatureExtractionInput(
        symbol=assessment.symbol,
        market=assessment.market,
        source=assessment.source,
        source_label=assessment.source_label,
        quality_status=assessment.quality_status,
        data_availability_hint=assessment.data_availability_hint,
        needs_review=assessment.needs_review,
        usable_for_future_scoring=_input_usable_for_future_scoring(assessment),
        feature_records=assessment.feature_records,
        diagnostics=diagnostics,
        warnings=assessment.quality_warnings,
        blocked_reasons=assessment.blocked_reasons,
    )


def extract_feature_set_from_quality_assessment(
    assessment: FeatureQualityAssessment,
    policy: FeatureExtractionPolicy | None = None,
    extraction_source: str = "feature_quality_assessment",
) -> ExtractedFeatureSet:
    """Build one safe extracted feature set from an in-memory assessment."""

    active_policy = policy or build_feature_extraction_policy()
    extraction_input = build_feature_extraction_input_from_quality_assessment(
        assessment
    )
    extracted_features = _safe_feature_records(extraction_input, active_policy)
    extraction_status = _extraction_status_from_quality(extraction_input)
    usable_for_future_scoring = (
        extraction_status == FeatureExtractionStatus.EXTRACTION_READY.value
        and bool(extracted_features)
    )
    return ExtractedFeatureSet(
        symbol=extraction_input.symbol,
        market=extraction_input.market,
        extraction_source=extraction_source,
        extraction_status=extraction_status,
        extracted_features=extracted_features,
        missing_features=_missing_features(extracted_features, active_policy),
        blocked_features=_blocked_features(
            extraction_input,
            extracted_features,
            active_policy,
        ),
        quality_status=extraction_input.quality_status,
        quality_warnings=extraction_input.warnings,
        diagnostics=extraction_input.diagnostics,
        needs_review=extraction_input.needs_review,
        usable_for_future_scoring=usable_for_future_scoring,
        blocked_reasons=extraction_input.blocked_reasons,
        summary_flags=_false_flags(),
    )


def extract_feature_sets_from_fixture(
    fixture: WatchlistFixtureRecord,
    policy: FeatureExtractionPolicy | None = None,
) -> tuple[ExtractedFeatureSet, ...]:
    """Extract feature sets from one MS-09.04 in-memory fixture."""

    active_policy = policy or build_feature_extraction_policy()
    assessments = build_feature_quality_from_fixture(fixture)
    return tuple(
        extract_feature_set_from_quality_assessment(
            assessment,
            active_policy,
            extraction_source="watchlist_fixture_assessment",
        )
        for assessment in assessments
    )


def extract_feature_sets_from_all_fixtures(
    policy: FeatureExtractionPolicy | None = None,
) -> tuple[tuple[ExtractedFeatureSet, ...], ...]:
    """Extract feature sets from every MS-09.04 in-memory fixture."""

    active_policy = policy or build_feature_extraction_policy()
    return tuple(
        extract_feature_sets_from_fixture(fixture, active_policy)
        for fixture in build_all_watchlist_source_fixtures()
    )


def _flatten_feature_sets(
    groups: tuple[tuple[ExtractedFeatureSet, ...], ...],
) -> tuple[ExtractedFeatureSet, ...]:
    return tuple(feature_set for group in groups for feature_set in group)


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


def extract_feature_sets_from_feature_quality_fixture(
    fixture: FeatureQualityFixtureRecord,
    policy: FeatureExtractionPolicy | None = None,
) -> tuple[ExtractedFeatureSet, ...]:
    """Extract feature sets from an MS-10.01 fixture expectation record."""

    evaluate_feature_quality_fixture(fixture)
    active_policy = policy or build_feature_extraction_policy()
    if fixture.source_fixture_name == "all_ms09_fixture_matrix":
        return _flatten_feature_sets(
            extract_feature_sets_from_all_fixtures(active_policy)
        )
    return extract_feature_sets_from_fixture(
        _source_fixture_by_name(fixture.source_fixture_name),
        active_policy,
    )


def extract_feature_sets_from_all_feature_quality_fixtures(
    policy: FeatureExtractionPolicy | None = None,
) -> tuple[tuple[ExtractedFeatureSet, ...], ...]:
    """Extract feature sets from every MS-10.01 fixture record."""

    evaluate_all_feature_quality_fixtures()
    active_policy = policy or build_feature_extraction_policy()
    return tuple(
        extract_feature_sets_from_feature_quality_fixture(fixture, active_policy)
        for fixture in build_all_feature_quality_fixtures()
    )


def _required_true_flags(
    feature_set: ExtractedFeatureSet,
    policy: FeatureExtractionPolicy,
) -> tuple[str, ...]:
    return tuple(
        flag
        for flag in policy.required_false_flags
        if bool(getattr(feature_set.summary_flags, flag))
    )


def validate_extracted_feature_set(
    feature_set: ExtractedFeatureSet,
    policy: FeatureExtractionPolicy | None = None,
) -> FeatureExtractionValidationResult:
    """Validate an extracted feature set without external access."""

    active_policy = policy or build_feature_extraction_policy()
    feature_set_field_names = tuple(field.name for field in fields(ExtractedFeatureSet))
    feature_value_field_names = tuple(field.name for field in fields(ExtractedFeatureValue))
    produced_values = (
        feature_set.extraction_source,
        feature_set.extraction_status,
        feature_set.quality_status,
        *(feature.feature_name for feature in feature_set.extracted_features),
        *(feature.quality_status for feature in feature_set.extracted_features),
        *feature_set.missing_features,
        *feature_set.blocked_features,
    )
    forbidden_sources = tuple(
        source
        for source in (
            feature_set.extraction_source,
            *(feature.feature_source for feature in feature_set.extracted_features),
        )
        if source in active_policy.forbidden_extraction_sources
    )
    forbidden_features = tuple(
        name
        for name in (
            *feature_set_field_names,
            *feature_value_field_names,
            *(feature.feature_name for feature in feature_set.extracted_features),
            *feature_set.missing_features,
            *feature_set.blocked_features,
        )
        if name in active_policy.forbidden_feature_names
    )
    forbidden_labels = tuple(
        value for value in produced_values if value in active_policy.forbidden_output_labels
    )
    unknown_statuses = tuple(
        value
        for value in (feature_set.extraction_status,)
        if value not in active_policy.allowed_extraction_statuses
    )
    required_true_flags = _required_true_flags(feature_set, active_policy)

    rejection_reasons: list[str] = []
    if feature_set.extraction_source not in active_policy.allowed_extraction_sources:
        rejection_reasons.append(
            f"unknown_extraction_source:{feature_set.extraction_source}"
        )
    if forbidden_sources:
        rejection_reasons.extend(
            f"forbidden_extraction_source:{source}" for source in forbidden_sources
        )
    if forbidden_features:
        rejection_reasons.extend(
            f"forbidden_feature_present:{feature}" for feature in forbidden_features
        )
    if forbidden_labels:
        rejection_reasons.extend(
            f"forbidden_output_label_present:{label}" for label in forbidden_labels
        )
    if unknown_statuses:
        rejection_reasons.extend(
            f"unknown_extraction_status:{status}" for status in unknown_statuses
        )
    if required_true_flags:
        rejection_reasons.extend(
            f"required_flag_true:{flag}" for flag in required_true_flags
        )

    return FeatureExtractionValidationResult(
        valid=not rejection_reasons,
        rejection_reasons=tuple(rejection_reasons),
        diagnostics=feature_set.diagnostics,
        forbidden_source_present=bool(forbidden_sources),
        forbidden_feature_present=bool(forbidden_features),
        forbidden_output_label_present=bool(forbidden_labels),
        required_flag_true=bool(required_true_flags),
        credential_required=feature_set.summary_flags.credential_required,
        db_read_required=feature_set.summary_flags.db_read_required,
        db_write_required=feature_set.summary_flags.db_write_required,
        file_read_required=feature_set.summary_flags.file_read_required,
        file_write_required=feature_set.summary_flags.file_write_required,
        toss_api_required=feature_set.summary_flags.toss_api_required,
        openai_required=feature_set.summary_flags.openai_required,
        oauth_required=feature_set.summary_flags.oauth_required,
        account_seq_required=feature_set.summary_flags.account_seq_required,
        real_order_required=feature_set.summary_flags.real_order_required,
        scoring_required=feature_set.summary_flags.scoring_required,
        ranking_required=feature_set.summary_flags.ranking_required,
        recommendation_required=feature_set.summary_flags.recommendation_required,
        ui_required=feature_set.summary_flags.ui_required,
        streamlit_required=feature_set.summary_flags.streamlit_required,
        http_smoke_required=feature_set.summary_flags.http_smoke_required,
    )


def summarize_feature_extraction_results(
    feature_sets: tuple[ExtractedFeatureSet, ...],
) -> FeatureExtractionSummary:
    """Summarize deterministic extraction status counts."""

    blocked_statuses = (
        FeatureExtractionStatus.EXTRACTION_BLOCKED_QUALITY.value,
        FeatureExtractionStatus.EXTRACTION_INVALID_CANDIDATE.value,
        FeatureExtractionStatus.EXTRACTION_DUPLICATE_CANDIDATE.value,
        FeatureExtractionStatus.EXTRACTION_DISABLED_CANDIDATE.value,
        FeatureExtractionStatus.EXTRACTION_FORBIDDEN_FIELD_SANITIZED.value,
        FeatureExtractionStatus.EXTRACTION_EMPTY_INPUT.value,
    )
    return FeatureExtractionSummary(
        total_sets=len(feature_sets),
        ready_sets=sum(
            1
            for feature_set in feature_sets
            if feature_set.extraction_status
            == FeatureExtractionStatus.EXTRACTION_READY.value
        ),
        needs_review_sets=sum(1 for feature_set in feature_sets if feature_set.needs_review),
        blocked_sets=sum(
            1
            for feature_set in feature_sets
            if feature_set.extraction_status in blocked_statuses
        ),
        missing_data_sets=sum(
            1
            for feature_set in feature_sets
            if feature_set.extraction_status
            == FeatureExtractionStatus.EXTRACTION_MISSING_DATA.value
        ),
        usable_for_future_scoring_sets=sum(
            1 for feature_set in feature_sets if feature_set.usable_for_future_scoring
        ),
        diagnostics=tuple(
            diagnostic for feature_set in feature_sets for diagnostic in feature_set.diagnostics
        ),
    )
