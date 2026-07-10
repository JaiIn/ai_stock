"""Pure dashboard preflight view model contract for MS-09.05.

This module converts in-memory watchlist source results and fixtures into a
dashboard-ready view model. It performs no Streamlit, file, database,
environment, network, model, account, order, clock, or random I/O. It does not
load, store, score, recommend, trade, or render dashboard UI.
"""

from dataclasses import dataclass, fields
from enum import Enum

from ai_stock.recommendation.candidate_input_preflight import (
    FORBIDDEN_CANDIDATE_LABELS,
)
from ai_stock.recommendation.watchlist_fixtures import (
    WatchlistFixtureRecord,
    build_all_watchlist_source_fixtures,
)
from ai_stock.recommendation.watchlist_model import (
    FORBIDDEN_WATCHLIST_FIELDS,
    WatchlistItemValidationResult,
)
from ai_stock.recommendation.watchlist_source import (
    FORBIDDEN_WATCHLIST_SOURCE_FIELDS,
    WatchlistSourceResult,
    build_watchlist_source_result,
)


class DashboardSafetyBadge(str, Enum):
    """Allowed non-directive safety badges for dashboard preflight output."""

    OBSERVATION_ONLY = "observation_only"
    MOCK_OR_MANUAL_INPUT_ONLY = "mock_or_manual_input_only"
    NO_REAL_ORDER = "no_real_order"
    NO_ACCOUNT_ACCESS = "no_account_access"
    NO_LIVE_API = "no_live_api"
    NO_LLM = "no_llm"
    NO_DB_WRITE = "no_db_write"
    NEEDS_REVIEW = "needs_review"
    INSUFFICIENT_DATA = "insufficient_data"


ALLOWED_DASHBOARD_SAFETY_BADGES: tuple[str, ...] = tuple(
    badge.value for badge in DashboardSafetyBadge
)

FORBIDDEN_DASHBOARD_BADGES: tuple[str, ...] = FORBIDDEN_CANDIDATE_LABELS

DASHBOARD_PREFLIGHT_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
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
    "ui_required",
    "streamlit_required",
    "http_smoke_required",
)

FORBIDDEN_DASHBOARD_ROW_FIELDS: tuple[str, ...] = (
    "real_holding_quantity",
    "real_average_buy_price",
    "real_valuation_amount",
    "real_orderable_quantity",
    "real_account_balance",
    "real_fill_information",
    "real_order_id",
    "accountSeq",
    "access_token",
    "authorization",
    "authorization_header",
    "api_key",
    "secret_key",
    "recommendation_score",
    "buy_sell_hold_label",
    "target_price",
    "expected_return",
    "score",
    "buy",
    "sell",
    "hold",
    *FORBIDDEN_WATCHLIST_FIELDS,
    *FORBIDDEN_WATCHLIST_SOURCE_FIELDS,
)


@dataclass(frozen=True)
class DashboardPreflightPolicy:
    """Immutable fail-closed policy for MS-09.05 dashboard preflight."""

    stage_name: str = "MS-09.05"
    mode: str = "manual_dashboard_preflight"
    allowed_safety_badges: tuple[str, ...] = ALLOWED_DASHBOARD_SAFETY_BADGES
    forbidden_badges: tuple[str, ...] = FORBIDDEN_DASHBOARD_BADGES
    forbidden_row_fields: tuple[str, ...] = FORBIDDEN_DASHBOARD_ROW_FIELDS
    required_false_flags: tuple[str, ...] = DASHBOARD_PREFLIGHT_REQUIRED_FALSE_FLAGS
    actual_recommendation_allowed: bool = False
    scoring_allowed: bool = False
    watchlist_persistence_allowed: bool = False
    file_loader_allowed: bool = False
    ui_change_allowed: bool = False
    streamlit_change_allowed: bool = False
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
    ui_required: bool = False
    streamlit_required: bool = False
    http_smoke_required: bool = False


@dataclass(frozen=True)
class DashboardPreflightRow:
    """Dashboard row model without scores, actions, account, or order fields."""

    symbol: str
    name: str
    market: str
    source: str
    source_label: str
    enabled: bool
    selectable: bool
    validation_status: str
    data_availability_hint: str
    reason: str
    tags: tuple[str, ...]
    group: str
    priority: int | None
    note: str
    warnings: tuple[str, ...]
    diagnostics: tuple[str, ...]


@dataclass(frozen=True)
class DashboardPreflightViewModel:
    """Dashboard-ready preflight view model with all required flags false."""

    title: str
    subtitle: str
    mode_label: str
    source_label: str
    watchlist_name: str
    watchlist_status: str
    total_items: int
    valid_items: int
    invalid_items: int
    disabled_items: int
    duplicate_items: int
    insufficient_data_items: int
    needs_review_items: int
    forbidden_source_items: int
    rows: tuple[DashboardPreflightRow, ...]
    warnings: tuple[str, ...]
    diagnostics: tuple[str, ...]
    safety_badges: tuple[str, ...]
    next_action_hint: str
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
    ui_required: bool
    streamlit_required: bool
    http_smoke_required: bool


@dataclass(frozen=True)
class DashboardPreflightValidationResult:
    """Validation result for dashboard preflight view models."""

    valid: bool
    rejection_reasons: tuple[str, ...]
    diagnostics: tuple[str, ...]
    forbidden_badge_present: bool
    forbidden_row_field_present: bool
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
    ui_required: bool
    streamlit_required: bool
    http_smoke_required: bool


def build_dashboard_preflight_policy() -> DashboardPreflightPolicy:
    """Build the fixed MS-09.05 dashboard preflight policy."""

    return DashboardPreflightPolicy()


def _status_warnings(status: str) -> tuple[str, ...]:
    if status == "duplicate_candidate":
        return ("duplicate_candidate_needs_review",)
    if status == "disabled_candidate":
        return ("disabled_candidate_not_selectable",)
    if status == "insufficient_data":
        return ("insufficient_data_review",)
    if status == "needs_review":
        return ("candidate_needs_review",)
    if status == "invalid_symbol":
        return ("invalid_symbol_review",)
    if status == "unsupported_source":
        return ("unsupported_source_rejected",)
    return ()


def _row_selectable(item: WatchlistItemValidationResult) -> bool:
    non_selectable_statuses = (
        "duplicate_candidate",
        "disabled_candidate",
        "insufficient_data",
        "needs_review",
        "invalid_symbol",
        "unsupported_source",
    )
    return item.selectable and item.validation_status not in non_selectable_statuses


def build_dashboard_row_from_watchlist_item(
    item: WatchlistItemValidationResult,
    source_label: str = "",
    extra_diagnostics: tuple[str, ...] = (),
) -> DashboardPreflightRow:
    """Build one dashboard row from a validated watchlist item."""

    return DashboardPreflightRow(
        symbol=item.symbol,
        name=item.name,
        market=item.market,
        source=item.source,
        source_label=source_label,
        enabled=item.enabled,
        selectable=_row_selectable(item),
        validation_status=item.validation_status,
        data_availability_hint=item.data_availability_hint,
        reason=item.reason,
        tags=item.tags,
        group=item.group,
        priority=item.priority,
        note=item.note,
        warnings=_status_warnings(item.validation_status),
        diagnostics=item.rejection_reasons + extra_diagnostics,
    )


def _count_status(
    rows: tuple[DashboardPreflightRow, ...],
    status: str,
) -> int:
    return sum(1 for row in rows if row.validation_status == status)


def _source_warnings(result: WatchlistSourceResult) -> tuple[str, ...]:
    warnings: list[str] = []
    summary = result.summary

    if result.validation.validation_status == "empty_watchlist":
        warnings.append("empty_watchlist_safe_state")
    if summary.invalid_items:
        warnings.append("invalid_candidates_need_review")
    if summary.duplicate_items:
        warnings.append("duplicate_candidates_need_review")
    if summary.disabled_items:
        warnings.append("disabled_candidates_not_selectable")
    if summary.insufficient_data_items:
        warnings.append("insufficient_data_review")
    if summary.forbidden_source_items:
        warnings.append("forbidden_source_candidates_rejected")
    if any("forbidden_field" in value for value in result.rejection_reasons):
        warnings.append("forbidden_fields_reported_in_diagnostics_only")

    return tuple(warnings)


def _safety_badges(
    result: WatchlistSourceResult,
    rows: tuple[DashboardPreflightRow, ...],
) -> tuple[str, ...]:
    badges = [
        DashboardSafetyBadge.OBSERVATION_ONLY.value,
        DashboardSafetyBadge.MOCK_OR_MANUAL_INPUT_ONLY.value,
        DashboardSafetyBadge.NO_REAL_ORDER.value,
        DashboardSafetyBadge.NO_ACCOUNT_ACCESS.value,
        DashboardSafetyBadge.NO_LIVE_API.value,
        DashboardSafetyBadge.NO_LLM.value,
        DashboardSafetyBadge.NO_DB_WRITE.value,
    ]
    if result.validation.validation_status == "needs_review" or any(
        row.validation_status in (
            "needs_review",
            "duplicate_candidate",
            "invalid_symbol",
            "unsupported_source",
        )
        for row in rows
    ):
        badges.append(DashboardSafetyBadge.NEEDS_REVIEW.value)
    if any(row.validation_status == "insufficient_data" for row in rows):
        badges.append(DashboardSafetyBadge.INSUFFICIENT_DATA.value)
    return tuple(dict.fromkeys(badges))


def _next_action_hint(result: WatchlistSourceResult) -> str:
    if result.validation.validation_status == "empty_watchlist":
        return "review_empty_watchlist_input"
    if result.summary.invalid_items or result.summary.duplicate_items:
        return "review_candidates_before_ui_integration"
    if result.summary.insufficient_data_items:
        return "review_data_availability_before_display"
    return "ready_for_manual_dashboard_ui_preflight_review"


def build_dashboard_preflight_from_source_result(
    result: WatchlistSourceResult,
    policy: DashboardPreflightPolicy | None = None,
    title: str = "Manual Watchlist Dashboard Preflight",
    subtitle: str = "Pure no-I/O view model for manual/local watchlist review.",
) -> DashboardPreflightViewModel:
    """Build a dashboard preflight view model from a source result."""

    active_policy = policy or build_dashboard_preflight_policy()
    rows = tuple(
        build_dashboard_row_from_watchlist_item(
            item,
            source_label=result.source_label,
        )
        for item in result.validation.items
    )
    warnings = _source_warnings(result)
    diagnostics = result.diagnostics + result.rejection_reasons

    return DashboardPreflightViewModel(
        title=title,
        subtitle=subtitle,
        mode_label=active_policy.mode,
        source_label=result.source_label,
        watchlist_name=result.watchlist.name,
        watchlist_status=result.validation.validation_status,
        total_items=result.summary.total_items,
        valid_items=result.summary.valid_items,
        invalid_items=result.summary.invalid_items,
        disabled_items=result.summary.disabled_items,
        duplicate_items=result.summary.duplicate_items,
        insufficient_data_items=result.summary.insufficient_data_items,
        needs_review_items=_count_status(rows, "needs_review"),
        forbidden_source_items=result.summary.forbidden_source_items,
        rows=rows,
        warnings=warnings,
        diagnostics=diagnostics,
        safety_badges=_safety_badges(result, rows),
        next_action_hint=_next_action_hint(result),
        credential_required=active_policy.credential_required,
        db_read_required=active_policy.db_read_required,
        db_write_required=active_policy.db_write_required,
        file_read_required=active_policy.file_read_required,
        file_write_required=active_policy.file_write_required,
        toss_api_required=active_policy.toss_api_required,
        openai_required=active_policy.openai_required,
        oauth_required=active_policy.oauth_required,
        account_seq_required=active_policy.account_seq_required,
        real_order_required=active_policy.real_order_required,
        scoring_required=active_policy.scoring_required,
        ui_required=active_policy.ui_required,
        streamlit_required=active_policy.streamlit_required,
        http_smoke_required=active_policy.http_smoke_required,
    )


def build_dashboard_preflight_from_fixture(
    fixture: WatchlistFixtureRecord,
    policy: DashboardPreflightPolicy | None = None,
) -> DashboardPreflightViewModel:
    """Build a dashboard preflight view model from an in-memory fixture."""

    result = build_watchlist_source_result(fixture.source_config)
    return build_dashboard_preflight_from_source_result(
        result,
        policy,
        title=f"Fixture Dashboard Preflight: {fixture.scenario}",
        subtitle=fixture.description,
    )


def build_all_fixture_dashboard_preflights(
    policy: DashboardPreflightPolicy | None = None,
) -> tuple[DashboardPreflightViewModel, ...]:
    """Build dashboard preflights for all MS-09.04 in-memory fixtures."""

    active_policy = policy or build_dashboard_preflight_policy()
    return tuple(
        build_dashboard_preflight_from_fixture(fixture, active_policy)
        for fixture in build_all_watchlist_source_fixtures()
    )


def validate_dashboard_preflight(
    view_model: DashboardPreflightViewModel,
    policy: DashboardPreflightPolicy | None = None,
) -> DashboardPreflightValidationResult:
    """Validate a dashboard preflight view model without external I/O."""

    active_policy = policy or build_dashboard_preflight_policy()
    row_field_names = tuple(field.name for field in fields(DashboardPreflightRow))
    forbidden_badges = tuple(
        badge
        for badge in view_model.safety_badges
        if badge in active_policy.forbidden_badges
    )
    forbidden_row_fields = tuple(
        row_field
        for row_field in row_field_names
        if row_field in active_policy.forbidden_row_fields
    )
    required_true_flags = tuple(
        flag
        for flag in active_policy.required_false_flags
        if bool(getattr(view_model, flag))
    )

    rejection_reasons: list[str] = []
    diagnostics: list[str] = []
    if forbidden_badges:
        rejection_reasons.extend(
            f"forbidden_badge_present:{badge}" for badge in forbidden_badges
        )
    if forbidden_row_fields:
        rejection_reasons.extend(
            f"forbidden_row_field_present:{field}"
            for field in forbidden_row_fields
        )
    if required_true_flags:
        rejection_reasons.extend(
            f"required_flag_true:{flag}" for flag in required_true_flags
        )
    for badge in view_model.safety_badges:
        if badge not in active_policy.allowed_safety_badges:
            diagnostics.append(f"unknown_safety_badge:{badge}")

    return DashboardPreflightValidationResult(
        valid=not rejection_reasons,
        rejection_reasons=tuple(rejection_reasons),
        diagnostics=tuple(diagnostics),
        forbidden_badge_present=bool(forbidden_badges),
        forbidden_row_field_present=bool(forbidden_row_fields),
        credential_required=view_model.credential_required,
        db_read_required=view_model.db_read_required,
        db_write_required=view_model.db_write_required,
        file_read_required=view_model.file_read_required,
        file_write_required=view_model.file_write_required,
        toss_api_required=view_model.toss_api_required,
        openai_required=view_model.openai_required,
        oauth_required=view_model.oauth_required,
        account_seq_required=view_model.account_seq_required,
        real_order_required=view_model.real_order_required,
        scoring_required=view_model.scoring_required,
        ui_required=view_model.ui_required,
        streamlit_required=view_model.streamlit_required,
        http_smoke_required=view_model.http_smoke_required,
    )
