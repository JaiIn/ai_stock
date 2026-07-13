"""Pure feature/data quality contract for MS-10.00.

This module evaluates candidate/watchlist dashboard preflight rows for data
quality only. It performs no Streamlit, file, database, environment, network,
model, account, order, clock, or random I/O. It does not score, rank,
recommend, trade, load features, or render UI.
"""

from dataclasses import dataclass, fields
from enum import Enum

from ai_stock.recommendation.candidate_input_preflight import (
    FORBIDDEN_CANDIDATE_LABELS,
)
from ai_stock.recommendation.dashboard_preflight import (
    DashboardPreflightRow,
    DashboardPreflightViewModel,
    build_dashboard_preflight_from_fixture,
)
from ai_stock.recommendation.watchlist_fixtures import (
    WatchlistFixtureRecord,
    build_all_watchlist_source_fixtures,
)
from ai_stock.recommendation.watchlist_model import FORBIDDEN_WATCHLIST_FIELDS
from ai_stock.recommendation.watchlist_source import (
    FORBIDDEN_WATCHLIST_SOURCE_FIELDS,
)


class FeatureQualityStatus(str, Enum):
    """Allowed non-directive quality states for MS-10.00."""

    QUALITY_OK = "quality_ok"
    QUALITY_MISSING_DATA = "quality_missing_data"
    QUALITY_INSUFFICIENT_DATA = "quality_insufficient_data"
    QUALITY_INVALID_CANDIDATE = "quality_invalid_candidate"
    QUALITY_DUPLICATE_CANDIDATE = "quality_duplicate_candidate"
    QUALITY_DISABLED_CANDIDATE = "quality_disabled_candidate"
    QUALITY_FORBIDDEN_SOURCE = "quality_forbidden_source"
    QUALITY_FORBIDDEN_FIELD_SANITIZED = "quality_forbidden_field_sanitized"
    QUALITY_NEEDS_REVIEW = "quality_needs_review"
    QUALITY_EMPTY_INPUT = "quality_empty_input"


ALLOWED_FEATURE_NAMES: tuple[str, ...] = (
    "symbol_identity",
    "market_identity",
    "source_integrity",
    "enabled_state",
    "selectability_state",
    "validation_status",
    "data_availability_hint",
    "warning_presence",
    "diagnostic_presence",
)

FORBIDDEN_FEATURE_NAMES: tuple[str, ...] = (
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
    "position_size",
    "order_quantity",
    "accountSeq",
    "access_token",
    "api_key",
    "secret_key",
    "account_balance",
    "holdings",
    "fills",
    "order_id",
    *FORBIDDEN_WATCHLIST_FIELDS,
    *FORBIDDEN_WATCHLIST_SOURCE_FIELDS,
)

ALLOWED_QUALITY_STATUSES: tuple[str, ...] = tuple(
    status.value for status in FeatureQualityStatus
)

FORBIDDEN_FEATURE_ACTION_LABELS: tuple[str, ...] = (
    *FORBIDDEN_CANDIDATE_LABELS,
    "rank",
    "recommendation",
    "action",
    "expected_return",
    "profit_probability",
)

FEATURE_QUALITY_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    "credential_required",
    "db_read_required",
    "db_write_required",
    "file_read_required",
    "file_write_required",
    "toss_api_required",
    "openai_required",
    "oauth_required",
    "account_seq_required",
    "real_order_required",
    "scoring_required",
    "ranking_required",
    "recommendation_required",
    "ui_required",
    "streamlit_required",
    "http_smoke_required",
)


@dataclass(frozen=True)
class FeatureQualitySummaryFlags:
    """All required external capability flags remain false for MS-10.00."""

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
class FeatureQualityPolicy:
    """Immutable fail-closed policy for feature/data quality preflight."""

    stage_name: str = "MS-10.00"
    mode: str = "feature_data_quality_model_preflight"
    allowed_feature_names: tuple[str, ...] = ALLOWED_FEATURE_NAMES
    forbidden_feature_names: tuple[str, ...] = FORBIDDEN_FEATURE_NAMES
    allowed_quality_statuses: tuple[str, ...] = ALLOWED_QUALITY_STATUSES
    forbidden_action_labels: tuple[str, ...] = FORBIDDEN_FEATURE_ACTION_LABELS
    required_false_flags: tuple[str, ...] = FEATURE_QUALITY_REQUIRED_FALSE_FLAGS
    observation_only_policy: str = (
        "quality_only_not_recommendation_or_scoring"
    )
    no_scoring_policy: str = "no_score_rank_or_model_output"
    no_recommendation_policy: str = "no_action_label_or_recommendation_output"
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
class FeatureRecord:
    """One non-directive quality feature derived from a dashboard row."""

    symbol: str
    market: str
    feature_name: str
    feature_value: str | bool | int | None
    feature_source: str
    source_label: str
    data_availability_hint: str
    quality_status: str
    quality_warnings: tuple[str, ...]
    diagnostics: tuple[str, ...]
    needs_review: bool
    usable_for_future_scoring: bool


@dataclass(frozen=True)
class FeatureQualityAssessment:
    """Quality assessment for a candidate row without score/rank/action data."""

    symbol: str
    market: str
    source: str
    source_label: str
    validation_status: str
    candidate_enabled: bool
    candidate_selectable: bool
    data_availability_hint: str
    feature_records: tuple[FeatureRecord, ...]
    quality_status: str
    quality_warnings: tuple[str, ...]
    diagnostics: tuple[str, ...]
    needs_review: bool
    blocked_reasons: tuple[str, ...]
    summary_flags: FeatureQualitySummaryFlags


@dataclass(frozen=True)
class FeatureQualityValidationResult:
    """Validation result for one feature quality assessment."""

    valid: bool
    rejection_reasons: tuple[str, ...]
    diagnostics: tuple[str, ...]
    forbidden_feature_present: bool
    forbidden_action_label_present: bool
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


def build_feature_quality_policy() -> FeatureQualityPolicy:
    """Build the fixed MS-10.00 feature/data quality policy."""

    return FeatureQualityPolicy()


def _false_flags() -> FeatureQualitySummaryFlags:
    return FeatureQualitySummaryFlags()


def _contains_forbidden_field(values: tuple[str, ...]) -> bool:
    return any("forbidden_field" in value for value in values)


def _quality_status_from_row(
    row: DashboardPreflightRow,
    extra_diagnostics: tuple[str, ...] = (),
) -> str:
    combined = row.warnings + row.diagnostics + extra_diagnostics
    if _contains_forbidden_field(combined):
        return FeatureQualityStatus.QUALITY_FORBIDDEN_FIELD_SANITIZED.value
    if row.validation_status == "unsupported_source":
        return FeatureQualityStatus.QUALITY_FORBIDDEN_SOURCE.value
    if row.validation_status == "invalid_symbol":
        return FeatureQualityStatus.QUALITY_INVALID_CANDIDATE.value
    if row.validation_status == "duplicate_candidate":
        return FeatureQualityStatus.QUALITY_DUPLICATE_CANDIDATE.value
    if row.validation_status == "disabled_candidate":
        return FeatureQualityStatus.QUALITY_DISABLED_CANDIDATE.value
    if row.validation_status == "insufficient_data":
        return FeatureQualityStatus.QUALITY_INSUFFICIENT_DATA.value
    if row.validation_status == "needs_review":
        return FeatureQualityStatus.QUALITY_NEEDS_REVIEW.value
    if not row.data_availability_hint and row.validation_status != "valid_candidate":
        return FeatureQualityStatus.QUALITY_MISSING_DATA.value
    return FeatureQualityStatus.QUALITY_OK.value


def _needs_review(quality_status: str) -> bool:
    return quality_status != FeatureQualityStatus.QUALITY_OK.value


def _usable_for_future_scoring(quality_status: str) -> bool:
    return quality_status == FeatureQualityStatus.QUALITY_OK.value


def _blocked_reasons(quality_status: str) -> tuple[str, ...]:
    if quality_status == FeatureQualityStatus.QUALITY_OK.value:
        return ()
    return (quality_status,)


def _record(
    row: DashboardPreflightRow,
    feature_name: str,
    feature_value: str | bool | int | None,
    quality_status: str,
    extra_diagnostics: tuple[str, ...] = (),
) -> FeatureRecord:
    return FeatureRecord(
        symbol=row.symbol,
        market=row.market,
        feature_name=feature_name,
        feature_value=feature_value,
        feature_source=row.source,
        source_label=row.source_label,
        data_availability_hint=row.data_availability_hint,
        quality_status=quality_status,
        quality_warnings=row.warnings,
        diagnostics=row.diagnostics + extra_diagnostics,
        needs_review=_needs_review(quality_status),
        usable_for_future_scoring=_usable_for_future_scoring(quality_status),
    )


def build_feature_records_from_dashboard_row(
    row: DashboardPreflightRow,
    policy: FeatureQualityPolicy | None = None,
    extra_diagnostics: tuple[str, ...] = (),
) -> tuple[FeatureRecord, ...]:
    """Build quality-only feature records from one dashboard row."""

    active_policy = policy or build_feature_quality_policy()
    quality_status = _quality_status_from_row(row, extra_diagnostics)
    records = (
        _record(row, "symbol_identity", row.symbol, quality_status, extra_diagnostics),
        _record(row, "market_identity", row.market, quality_status, extra_diagnostics),
        _record(row, "source_integrity", row.source, quality_status, extra_diagnostics),
        _record(row, "enabled_state", row.enabled, quality_status, extra_diagnostics),
        _record(
            row,
            "selectability_state",
            row.selectable,
            quality_status,
            extra_diagnostics,
        ),
        _record(
            row,
            "validation_status",
            row.validation_status,
            quality_status,
            extra_diagnostics,
        ),
        _record(
            row,
            "data_availability_hint",
            row.data_availability_hint,
            quality_status,
            extra_diagnostics,
        ),
        _record(
            row,
            "warning_presence",
            bool(row.warnings),
            quality_status,
            extra_diagnostics,
        ),
        _record(
            row,
            "diagnostic_presence",
            bool(row.diagnostics or extra_diagnostics),
            quality_status,
            extra_diagnostics,
        ),
    )
    return tuple(
        record
        for record in records
        if record.feature_name in active_policy.allowed_feature_names
    )


def assess_dashboard_row_feature_quality(
    row: DashboardPreflightRow,
    policy: FeatureQualityPolicy | None = None,
    extra_diagnostics: tuple[str, ...] = (),
) -> FeatureQualityAssessment:
    """Assess one dashboard row for data quality without scoring it."""

    active_policy = policy or build_feature_quality_policy()
    quality_status = _quality_status_from_row(row, extra_diagnostics)
    records = build_feature_records_from_dashboard_row(
        row,
        active_policy,
        extra_diagnostics,
    )
    return FeatureQualityAssessment(
        symbol=row.symbol,
        market=row.market,
        source=row.source,
        source_label=row.source_label,
        validation_status=row.validation_status,
        candidate_enabled=row.enabled,
        candidate_selectable=row.selectable,
        data_availability_hint=row.data_availability_hint,
        feature_records=records,
        quality_status=quality_status,
        quality_warnings=row.warnings,
        diagnostics=row.diagnostics + extra_diagnostics,
        needs_review=_needs_review(quality_status),
        blocked_reasons=_blocked_reasons(quality_status),
        summary_flags=_false_flags(),
    )


def _empty_assessment(
    preflight: DashboardPreflightViewModel,
) -> FeatureQualityAssessment:
    quality_status = FeatureQualityStatus.QUALITY_EMPTY_INPUT.value
    return FeatureQualityAssessment(
        symbol="",
        market="UNKNOWN",
        source="",
        source_label=preflight.source_label,
        validation_status=preflight.watchlist_status,
        candidate_enabled=False,
        candidate_selectable=False,
        data_availability_hint="",
        feature_records=(),
        quality_status=quality_status,
        quality_warnings=preflight.warnings,
        diagnostics=preflight.diagnostics,
        needs_review=True,
        blocked_reasons=(quality_status,),
        summary_flags=_false_flags(),
    )


def assess_dashboard_preflight_feature_quality(
    preflight: DashboardPreflightViewModel,
    policy: FeatureQualityPolicy | None = None,
) -> tuple[FeatureQualityAssessment, ...]:
    """Assess every dashboard preflight row for data quality only."""

    active_policy = policy or build_feature_quality_policy()
    if not preflight.rows:
        return (_empty_assessment(preflight),)

    extra_diagnostics = tuple(
        value
        for value in preflight.diagnostics + preflight.warnings
        if "forbidden_field" in value
    )
    return tuple(
        assess_dashboard_row_feature_quality(
            row,
            active_policy,
            extra_diagnostics=extra_diagnostics,
        )
        for row in preflight.rows
    )


def build_feature_quality_from_fixture(
    fixture: WatchlistFixtureRecord,
    policy: FeatureQualityPolicy | None = None,
) -> tuple[FeatureQualityAssessment, ...]:
    """Build feature quality assessments from one in-memory fixture."""

    active_policy = policy or build_feature_quality_policy()
    preflight = build_dashboard_preflight_from_fixture(fixture)
    return assess_dashboard_preflight_feature_quality(preflight, active_policy)


def build_all_fixture_feature_quality_assessments(
    policy: FeatureQualityPolicy | None = None,
) -> tuple[tuple[FeatureQualityAssessment, ...], ...]:
    """Build feature quality assessments for all MS-09.04 fixtures."""

    active_policy = policy or build_feature_quality_policy()
    return tuple(
        build_feature_quality_from_fixture(fixture, active_policy)
        for fixture in build_all_watchlist_source_fixtures()
    )


def validate_feature_quality_assessment(
    assessment: FeatureQualityAssessment,
    policy: FeatureQualityPolicy | None = None,
) -> FeatureQualityValidationResult:
    """Validate a feature quality assessment without external access."""

    active_policy = policy or build_feature_quality_policy()
    assessment_field_names = tuple(
        field.name for field in fields(FeatureQualityAssessment)
    )
    record_field_names = tuple(field.name for field in fields(FeatureRecord))
    produced_values = (
        assessment.quality_status,
        assessment.validation_status,
        *(record.feature_name for record in assessment.feature_records),
        *(record.quality_status for record in assessment.feature_records),
    )
    forbidden_features = tuple(
        name
        for name in (
            *assessment_field_names,
            *record_field_names,
            *(record.feature_name for record in assessment.feature_records),
        )
        if name in active_policy.forbidden_feature_names
    )
    forbidden_actions = tuple(
        value
        for value in produced_values
        if value in active_policy.forbidden_action_labels
    )
    unknown_statuses = tuple(
        status
        for status in (
            assessment.quality_status,
            *(record.quality_status for record in assessment.feature_records),
        )
        if status not in active_policy.allowed_quality_statuses
    )
    required_true_flags = tuple(
        flag
        for flag in active_policy.required_false_flags
        if bool(getattr(assessment.summary_flags, flag))
    )

    rejection_reasons: list[str] = []
    if forbidden_features:
        rejection_reasons.extend(
            f"forbidden_feature_present:{feature}"
            for feature in forbidden_features
        )
    if forbidden_actions:
        rejection_reasons.extend(
            f"forbidden_action_label_present:{action}"
            for action in forbidden_actions
        )
    if unknown_statuses:
        rejection_reasons.extend(
            f"unknown_quality_status:{status}" for status in unknown_statuses
        )
    if required_true_flags:
        rejection_reasons.extend(
            f"required_flag_true:{flag}" for flag in required_true_flags
        )

    return FeatureQualityValidationResult(
        valid=not rejection_reasons,
        rejection_reasons=tuple(rejection_reasons),
        diagnostics=assessment.diagnostics,
        forbidden_feature_present=bool(forbidden_features),
        forbidden_action_label_present=bool(forbidden_actions),
        required_flag_true=bool(required_true_flags),
        credential_required=assessment.summary_flags.credential_required,
        db_read_required=assessment.summary_flags.db_read_required,
        db_write_required=assessment.summary_flags.db_write_required,
        file_read_required=assessment.summary_flags.file_read_required,
        file_write_required=assessment.summary_flags.file_write_required,
        toss_api_required=assessment.summary_flags.toss_api_required,
        openai_required=assessment.summary_flags.openai_required,
        oauth_required=assessment.summary_flags.oauth_required,
        account_seq_required=assessment.summary_flags.account_seq_required,
        real_order_required=assessment.summary_flags.real_order_required,
        scoring_required=assessment.summary_flags.scoring_required,
        ranking_required=assessment.summary_flags.ranking_required,
        recommendation_required=assessment.summary_flags.recommendation_required,
        ui_required=assessment.summary_flags.ui_required,
        streamlit_required=assessment.summary_flags.streamlit_required,
        http_smoke_required=assessment.summary_flags.http_smoke_required,
    )
