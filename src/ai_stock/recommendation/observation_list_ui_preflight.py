"""Pure observation-list UI preflight shapes for MS-13.00.

This module defines Streamlit-safe, observation-only row/view model contracts
from already in-memory MS-12 recommendation list preflight items. It performs
no Streamlit import, rendering, callback, session state, file, database,
environment, network, model, account, order, clock, or random I/O. It does not
create an actual recommendation list, rank candidates, issue trade actions,
load features, or modify UI code.
"""

from dataclasses import dataclass, fields
from functools import lru_cache

from ai_stock.recommendation.recommendation_list_fixture_hardening import (
    build_recommendation_list_fixture_hardening_policy,
    run_recommendation_list_fixture_hardening_checks,
)
from ai_stock.recommendation.recommendation_list_fixtures import (
    build_all_recommendation_list_fixtures,
    build_recommendation_list_fixture_policy,
    evaluate_all_recommendation_list_fixtures,
)
from ai_stock.recommendation.recommendation_list_preflight import (
    ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES,
    FORBIDDEN_RECOMMENDATION_LIST_ACTION_LABELS,
    FORBIDDEN_RECOMMENDATION_LIST_INPUT_SOURCES,
    FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_FIELDS,
    FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_KEYWORDS,
    FORBIDDEN_RECOMMENDATION_LIST_RANKING_LABELS,
    FORBIDDEN_RECOMMENDATION_LIST_RECOMMENDATION_LABELS,
    RECOMMENDATION_LIST_PREFLIGHT_REQUIRED_FALSE_FLAGS,
    RecommendationListPreflightItem,
    build_recommendation_list_items_from_all_fixtures,
    build_recommendation_list_preflight_policy,
    summarize_recommendation_list_preflight_items,
    validate_recommendation_list_preflight_item,
)


ALLOWED_OBSERVATION_LIST_VIEW_MODES: tuple[str, ...] = (
    "table_preview",
    "grouped_review",
    "compact_audit",
)

ALLOWED_OBSERVATION_LIST_COLUMN_KEYS: tuple[str, ...] = (
    "symbol",
    "market",
    "item_status",
    "status_badge",
    "display_bucket",
    "score_snapshot_label",
    "score_scale_label",
    "component_summary",
    "needs_review_label",
    "usability_label",
    "blocked_reason_summary",
    "warning_summary",
    "diagnostic_summary",
    "disclaimer_labels",
    "guardrail_flags",
)

FORBIDDEN_OBSERVATION_LIST_COLUMN_KEYS: tuple[str, ...] = (
    *FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_FIELDS,
    "button",
    "callback",
    "session_state",
    "api_refresh",
    "oauth_login",
    "credential_input",
    "accountSeq_input",
    "order_ui",
    "trade_ui",
    "account_ui",
    "holdings_ui",
    "balance_ui",
    "fills_ui",
    "priority",
    "order",
)

ALLOWED_OBSERVATION_LIST_BADGE_LABELS: tuple[str, ...] = (
    "review_ready",
    "review_needed",
    "quality_blocked",
    "missing_data",
    "invalid_candidate",
    "duplicate_candidate",
    "disabled_candidate",
    "sanitized_input",
    "empty_input",
)

FORBIDDEN_OBSERVATION_LIST_BADGE_LABELS: tuple[str, ...] = (
    *FORBIDDEN_RECOMMENDATION_LIST_ACTION_LABELS,
    *FORBIDDEN_RECOMMENDATION_LIST_RECOMMENDATION_LABELS,
    *FORBIDDEN_RECOMMENDATION_LIST_RANKING_LABELS,
    "ranking_position",
    "priority",
    "order",
    "target_price",
    "expected_return",
    "profit_probability",
)

OBSERVATION_LIST_UI_REQUIRED_DISCLAIMER_LABELS: tuple[str, ...] = (
    "observation_only_preflight",
    "not_trade_directive",
    "no_live_refresh",
    "score_snapshot_quality_only",
)

OBSERVATION_LIST_UI_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    *RECOMMENDATION_LIST_PREFLIGHT_REQUIRED_FALSE_FLAGS,
    "ui_integration_required",
)

FORBIDDEN_OBSERVATION_LIST_UI_OUTPUT_KEYWORDS: tuple[str, ...] = (
    *FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_KEYWORDS,
    "button=",
    "callback=",
    "session_state=",
    "api_refresh=",
    "oauth_login=",
    "credential_input=",
    "accountSeq_input=",
    "order_ui=",
    "trade_ui=",
    "account_ui=",
    "holdings_ui=",
    "balance_ui=",
    "fills_ui=",
    "priority=",
    "order=",
)


@dataclass(frozen=True)
class ObservationListUIPreflightPolicy:
    """Immutable fail-closed policy for observation-list UI preflight."""

    preflight_version: str = "MS-13.00"
    preflight_scope: str = "observation_list_ui_preflight_shape_only"
    allowed_view_modes: tuple[str, ...] = ALLOWED_OBSERVATION_LIST_VIEW_MODES
    allowed_column_keys: tuple[str, ...] = ALLOWED_OBSERVATION_LIST_COLUMN_KEYS
    forbidden_column_keys: tuple[str, ...] = FORBIDDEN_OBSERVATION_LIST_COLUMN_KEYS
    allowed_badge_labels: tuple[str, ...] = ALLOWED_OBSERVATION_LIST_BADGE_LABELS
    forbidden_badge_labels: tuple[str, ...] = (
        FORBIDDEN_OBSERVATION_LIST_BADGE_LABELS
    )
    required_disclaimer_labels: tuple[str, ...] = (
        OBSERVATION_LIST_UI_REQUIRED_DISCLAIMER_LABELS
    )
    required_false_flags: tuple[str, ...] = OBSERVATION_LIST_UI_REQUIRED_FALSE_FLAGS
    allowed_item_statuses: tuple[str, ...] = (
        ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES
    )
    forbidden_input_sources: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_INPUT_SOURCES
    )
    forbidden_output_fields: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_FIELDS
    )
    forbidden_output_keywords: tuple[str, ...] = (
        FORBIDDEN_OBSERVATION_LIST_UI_OUTPUT_KEYWORDS
    )
    observation_only_policy: str = "display_safe_observation_preflight_only"
    no_action_policy: str = "no_trade_directive_controls_or_labels"
    no_ranking_policy: str = "no_rank_priority_order_columns_or_labels"
    no_trade_directive_policy: str = "no_buy_sell_hold_badges_or_actions"
    no_live_refresh_policy: str = "no_api_refresh_oauth_or_credential_controls"
    deterministic_only_policy: str = "in_memory_list_preflight_items_only"
    streamlit_import_allowed: bool = False
    actual_ui_render_allowed: bool = False
    button_allowed: bool = False
    callback_allowed: bool = False
    session_state_allowed: bool = False
    live_refresh_allowed: bool = False
    credential_input_allowed: bool = False
    account_seq_input_allowed: bool = False
    actual_recommendation_allowed: bool = False
    actual_recommendation_list_allowed: bool = False
    ranking_allowed: bool = False
    action_allowed: bool = False
    watchlist_persistence_allowed: bool = False
    feature_file_loader_allowed: bool = False
    watchlist_file_loader_allowed: bool = False
    fixture_file_loader_allowed: bool = False
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
    recommendation_required: bool = False
    ranking_required: bool = False
    ui_integration_required: bool = False
    streamlit_required: bool = False
    http_smoke_required: bool = False


@dataclass(frozen=True)
class ObservationListUIRow:
    """Observation-only UI row shape without rendering or directive fields."""

    symbol: str
    market: str
    item_status: str
    status_badge: str
    display_bucket: str
    score_snapshot_label: str
    score_scale_label: str
    component_summary: tuple[str, ...]
    needs_review_label: str
    usability_label: str
    blocked_reason_summary: tuple[str, ...]
    warning_summary: tuple[str, ...]
    diagnostic_summary: tuple[str, ...]
    disclaimer_labels: tuple[str, ...]
    guardrail_flags: tuple[str, ...]


@dataclass(frozen=True)
class ObservationListUIValidationResult:
    """Validation result for one observation-only UI row."""

    valid: bool
    rejection_reasons: tuple[str, ...]
    diagnostics: tuple[str, ...]
    forbidden_column_key_present: bool
    forbidden_badge_label_present: bool
    forbidden_output_field_present: bool
    forbidden_ui_control_present: bool
    required_flag_true: bool
    score_snapshot_label_directive_present: bool
    display_bucket_ranking_present: bool
    usability_label_ranking_present: bool
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
    recommendation_required: bool
    ranking_required: bool
    ui_integration_required: bool
    streamlit_required: bool
    http_smoke_required: bool


@dataclass(frozen=True)
class ObservationListUISummary:
    """Aggregate counts for observation-only UI rows."""

    total_rows: int
    ready_rows: int
    needs_review_rows: int
    blocked_rows: int
    usable_rows: int
    display_buckets: tuple[str, ...]
    status_badges: tuple[str, ...]
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
    recommendation_required: bool = False
    ranking_required: bool = False
    ui_integration_required: bool = False
    streamlit_required: bool = False
    http_smoke_required: bool = False


@lru_cache(maxsize=1)
def build_observation_list_ui_preflight_policy() -> (
    ObservationListUIPreflightPolicy
):
    """Build the fixed MS-13.00 observation-list UI preflight policy."""

    build_recommendation_list_preflight_policy()
    build_recommendation_list_fixture_policy()
    build_recommendation_list_fixture_hardening_policy()
    run_recommendation_list_fixture_hardening_checks()
    return ObservationListUIPreflightPolicy()


@lru_cache(maxsize=1)
def _list_preflight_policy() -> object:
    return build_recommendation_list_preflight_policy()


def _status_badge_from_item_status(item_status: str) -> str:
    if item_status == "item_ready_for_review":
        return "review_ready"
    if item_status == "item_needs_review":
        return "review_needed"
    if item_status == "item_missing_data":
        return "missing_data"
    if item_status == "item_invalid_candidate":
        return "invalid_candidate"
    if item_status == "item_duplicate_candidate":
        return "duplicate_candidate"
    if item_status == "item_disabled_candidate":
        return "disabled_candidate"
    if item_status == "item_forbidden_field_sanitized":
        return "sanitized_input"
    if item_status == "item_empty_input":
        return "empty_input"
    return "quality_blocked"


def _forbidden_text_terms(
    policy: ObservationListUIPreflightPolicy,
) -> tuple[str, ...]:
    return (
        policy.forbidden_output_fields
        + policy.forbidden_badge_labels
        + policy.forbidden_column_keys
    )


def _safe_text(value: str, policy: ObservationListUIPreflightPolicy) -> str:
    lowered = value.casefold()
    for term in _forbidden_text_terms(policy):
        if term and term.casefold() in lowered:
            return "sanitized_observation_detail"
    return value


def _safe_tuple(
    values: tuple[str, ...],
    policy: ObservationListUIPreflightPolicy,
) -> tuple[str, ...]:
    return tuple(_safe_text(value, policy) for value in values)


def _guardrail_flags(policy: ObservationListUIPreflightPolicy) -> tuple[str, ...]:
    return tuple(f"{flag}=false" for flag in policy.required_false_flags)


def build_observation_list_ui_row_from_item(
    item: RecommendationListPreflightItem,
    policy: ObservationListUIPreflightPolicy | None = None,
) -> ObservationListUIRow:
    """Build one observation-only UI row from a list preflight item."""

    active_policy = policy or build_observation_list_ui_preflight_policy()
    validate_recommendation_list_preflight_item(item, _list_preflight_policy())
    status_badge = _status_badge_from_item_status(item.item_status)
    needs_review_label = "needs_review" if item.needs_review else "review_not_required"
    usability_label = (
        "future_list_ready"
        if item.usable_for_future_list
        else "future_list_review_only"
    )
    return ObservationListUIRow(
        symbol=_safe_text(item.symbol, active_policy),
        market=_safe_text(item.market, active_policy),
        item_status=item.item_status,
        status_badge=status_badge,
        display_bucket=_safe_text(item.display_bucket, active_policy),
        score_snapshot_label=f"quality_preflight_score:{item.score_snapshot}",
        score_scale_label=f"score_scale:0..{item.score_scale}",
        component_summary=_safe_tuple(item.component_names, active_policy),
        needs_review_label=needs_review_label,
        usability_label=usability_label,
        blocked_reason_summary=_safe_tuple(item.blocked_reasons, active_policy),
        warning_summary=_safe_tuple(item.warnings, active_policy),
        diagnostic_summary=_safe_tuple(item.diagnostics, active_policy),
        disclaimer_labels=active_policy.required_disclaimer_labels,
        guardrail_flags=_guardrail_flags(active_policy),
    )


def build_observation_list_ui_rows_from_items(
    items: tuple[RecommendationListPreflightItem, ...],
    policy: ObservationListUIPreflightPolicy | None = None,
) -> tuple[ObservationListUIRow, ...]:
    """Build observation-only UI rows from list preflight items."""

    active_policy = policy or build_observation_list_ui_preflight_policy()
    return tuple(
        build_observation_list_ui_row_from_item(item, active_policy)
        for item in items
    )


@lru_cache(maxsize=1)
def _all_fixture_items() -> tuple[RecommendationListPreflightItem, ...]:
    build_all_recommendation_list_fixtures()
    evaluate_all_recommendation_list_fixtures()
    run_recommendation_list_fixture_hardening_checks()
    return build_recommendation_list_items_from_all_fixtures()


def build_observation_list_ui_rows_from_all_fixtures(
    policy: ObservationListUIPreflightPolicy | None = None,
) -> tuple[ObservationListUIRow, ...]:
    """Build observation-only UI rows from all in-memory fixtures."""

    active_policy = policy or build_observation_list_ui_preflight_policy()
    return build_observation_list_ui_rows_from_items(
        _all_fixture_items(),
        active_policy,
    )


def _required_flag_true(row: ObservationListUIRow) -> bool:
    return any(flag.endswith("=true") for flag in row.guardrail_flags)


def _forbidden_output_keyword_present(
    row: ObservationListUIRow,
    policy: ObservationListUIPreflightPolicy,
) -> bool:
    rendered = repr(row)
    return any(keyword in rendered for keyword in policy.forbidden_output_keywords)


def _forbidden_ui_control_present(row: ObservationListUIRow) -> bool:
    rendered = repr(row)
    return any(
        marker in rendered
        for marker in (
            "button=",
            "callback=",
            "session_state=",
            "api_refresh=",
            "oauth_login=",
            "credential_input=",
            "accountSeq_input=",
        )
    )


def _contains_any(value: str, terms: tuple[str, ...]) -> bool:
    return any(term and term in value for term in terms)


def validate_observation_list_ui_row(
    row: ObservationListUIRow,
    policy: ObservationListUIPreflightPolicy | None = None,
) -> ObservationListUIValidationResult:
    """Validate one observation-only UI row."""

    active_policy = policy or build_observation_list_ui_preflight_policy()
    field_names = tuple(field.name for field in fields(row))
    forbidden_column_key_present = any(
        key in field_names for key in active_policy.forbidden_column_keys
    )
    forbidden_badge_label_present = (
        row.status_badge in active_policy.forbidden_badge_labels
    )
    forbidden_output_field_present = _forbidden_output_keyword_present(
        row,
        active_policy,
    )
    forbidden_ui_control_present = _forbidden_ui_control_present(row)
    required_flag_true = _required_flag_true(row)
    score_snapshot_label_directive_present = _contains_any(
        row.score_snapshot_label,
        (
            *active_policy.forbidden_badge_labels,
            "recommendation",
            "ranking",
            "action",
        ),
    )
    display_bucket_ranking_present = _contains_any(
        row.display_bucket,
        ("rank", "ranking", "priority", "order"),
    )
    usability_label_ranking_present = _contains_any(
        row.usability_label,
        ("rank", "ranking", "priority", "order"),
    )

    rejection_reasons: list[str] = []
    if field_names != active_policy.allowed_column_keys:
        rejection_reasons.append("ui_row_fields_mismatch")
    if row.item_status not in active_policy.allowed_item_statuses:
        rejection_reasons.append("item_status_not_allowed")
    if row.status_badge not in active_policy.allowed_badge_labels:
        rejection_reasons.append("status_badge_not_allowed")
    if forbidden_column_key_present:
        rejection_reasons.append("forbidden_column_key_present")
    if forbidden_badge_label_present:
        rejection_reasons.append("forbidden_badge_label_present")
    if forbidden_output_field_present:
        rejection_reasons.append("forbidden_output_field_present")
    if forbidden_ui_control_present:
        rejection_reasons.append("forbidden_ui_control_present")
    if required_flag_true:
        rejection_reasons.append("required_flag_true")
    if score_snapshot_label_directive_present:
        rejection_reasons.append("score_snapshot_label_directive_present")
    if display_bucket_ranking_present:
        rejection_reasons.append("display_bucket_ranking_present")
    if usability_label_ranking_present:
        rejection_reasons.append("usability_label_ranking_present")
    for disclaimer in active_policy.required_disclaimer_labels:
        if disclaimer not in row.disclaimer_labels:
            rejection_reasons.append(f"missing_disclaimer:{disclaimer}")

    return ObservationListUIValidationResult(
        valid=not rejection_reasons,
        rejection_reasons=tuple(rejection_reasons),
        diagnostics=(
            "observation_list_ui_row_validated",
            "streamlit_import_not_required",
            "display_shape_only_no_rendering",
        ),
        forbidden_column_key_present=forbidden_column_key_present,
        forbidden_badge_label_present=forbidden_badge_label_present,
        forbidden_output_field_present=forbidden_output_field_present,
        forbidden_ui_control_present=forbidden_ui_control_present,
        required_flag_true=required_flag_true,
        score_snapshot_label_directive_present=(
            score_snapshot_label_directive_present
        ),
        display_bucket_ranking_present=display_bucket_ranking_present,
        usability_label_ranking_present=usability_label_ranking_present,
        credential_required=False,
        db_read_required=False,
        db_write_required=False,
        file_read_required=False,
        file_write_required=False,
        toss_api_required=False,
        openai_required=False,
        oauth_required=False,
        account_seq_required=False,
        real_order_required=False,
        recommendation_required=False,
        ranking_required=False,
        ui_integration_required=False,
        streamlit_required=False,
        http_smoke_required=False,
    )


def _unique_in_seen_order(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def summarize_observation_list_ui_rows(
    rows: tuple[ObservationListUIRow, ...],
) -> ObservationListUISummary:
    """Summarize observation-only UI rows without ordering or ranking them."""

    ready_rows = sum(row.status_badge == "review_ready" for row in rows)
    needs_review_rows = sum(row.needs_review_label == "needs_review" for row in rows)
    blocked_rows = sum(row.status_badge != "review_ready" for row in rows)
    usable_rows = sum(row.usability_label == "future_list_ready" for row in rows)
    summarize_recommendation_list_preflight_items(_all_fixture_items())
    return ObservationListUISummary(
        total_rows=len(rows),
        ready_rows=ready_rows,
        needs_review_rows=needs_review_rows,
        blocked_rows=blocked_rows,
        usable_rows=usable_rows,
        display_buckets=_unique_in_seen_order(
            tuple(row.display_bucket for row in rows)
        ),
        status_badges=_unique_in_seen_order(tuple(row.status_badge for row in rows)),
        diagnostics=(
            "observation_list_ui_summary_only",
            "no_streamlit_rendering",
            "no_live_refresh_control",
            "no_trade_directive_output",
        ),
    )


def validate_observation_list_ui_rows(
    rows: tuple[ObservationListUIRow, ...],
    policy: ObservationListUIPreflightPolicy | None = None,
) -> tuple[ObservationListUIValidationResult, ...]:
    """Validate multiple observation-only UI rows."""

    active_policy = policy or build_observation_list_ui_preflight_policy()
    return tuple(validate_observation_list_ui_row(row, active_policy) for row in rows)
