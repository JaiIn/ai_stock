"""Pure watchlist data model and validation contract for MS-09.02.

This module defines local/manual watchlist DTOs on top of the MS-09.01
candidate input preflight contract. It performs no file, database,
environment, network, UI, model, account, order, clock, or random I/O.
It does not load, store, rank, recommend, trade, or display watchlists.
"""

from dataclasses import dataclass
from enum import Enum

from ai_stock.recommendation.candidate_input_preflight import (
    ALLOWED_CANDIDATE_SOURCES,
    FORBIDDEN_CANDIDATE_LABELS,
    FORBIDDEN_CANDIDATE_SOURCES,
    SAFE_CANDIDATE_STATUSES,
    CandidateInput,
    CandidateInputStatus,
    CandidateInputValidationResult,
    build_candidate_input_preflight_policy,
    validate_candidate_input,
)


class WatchlistStatus(str, Enum):
    """Safe collection-level statuses for MS-09.02 watchlists."""

    VALID_WATCHLIST = "valid_watchlist"
    EMPTY_WATCHLIST = "empty_watchlist"
    INVALID_WATCHLIST_NAME = "invalid_watchlist_name"
    CONTAINS_INVALID_CANDIDATES = "contains_invalid_candidates"
    CONTAINS_DUPLICATE_CANDIDATES = "contains_duplicate_candidates"
    CONTAINS_DISABLED_CANDIDATES = "contains_disabled_candidates"
    NEEDS_REVIEW = "needs_review"


WATCHLIST_STATUSES: tuple[str, ...] = tuple(
    status.value for status in WatchlistStatus
)

FORBIDDEN_WATCHLIST_FIELDS: tuple[str, ...] = (
    "real_holding_quantity",
    "real_average_buy_price",
    "real_valuation_amount",
    "real_orderable_quantity",
    "real_account_balance",
    "real_fill_information",
    "real_order_id",
    "accountSeq",
    "access_token",
    "authorization_header",
    "api_key",
    "secret_key",
    "recommendation_score",
    "buy_sell_hold_label",
    "target_price",
    "expected_return",
)


@dataclass(frozen=True)
class WatchlistPolicy:
    """Immutable fail-closed policy for MS-09.02 watchlist modeling."""

    stage_name: str = "MS-09.02"
    mode: str = "watchlist_data_model"
    allowed_sources: tuple[str, ...] = ALLOWED_CANDIDATE_SOURCES
    forbidden_sources: tuple[str, ...] = FORBIDDEN_CANDIDATE_SOURCES
    safe_candidate_statuses: tuple[str, ...] = SAFE_CANDIDATE_STATUSES
    watchlist_statuses: tuple[str, ...] = WATCHLIST_STATUSES
    forbidden_labels: tuple[str, ...] = FORBIDDEN_CANDIDATE_LABELS
    forbidden_fields: tuple[str, ...] = FORBIDDEN_WATCHLIST_FIELDS
    min_priority: int = 0
    max_priority: int = 100
    actual_recommendation_allowed: bool = False
    scoring_allowed: bool = False
    watchlist_persistence_allowed: bool = False
    file_loader_allowed: bool = False
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
    ui_required: bool = False


@dataclass(frozen=True)
class WatchlistItem:
    """Caller-supplied local/manual watchlist item."""

    symbol: str
    source: str
    name: str = ""
    market: str = "unknown"
    enabled: bool = True
    reason: str = ""
    tags: tuple[str, ...] = ()
    group: str = ""
    priority: int | None = None
    note: str = ""
    data_availability_hint: str = ""


@dataclass(frozen=True)
class Watchlist:
    """Caller-supplied watchlist collection; no storage path is used."""

    name: str
    description: str = ""
    items: tuple[WatchlistItem, ...] = ()
    source_label: str = ""
    default_enabled: bool = True
    validation_status: str = ""
    rejection_reasons: tuple[str, ...] = ()
    diagnostics: tuple[str, ...] = ()


@dataclass(frozen=True)
class WatchlistItemValidationResult:
    """Deterministic validation result for one watchlist item."""

    symbol: str
    name: str
    market: str
    source: str
    enabled: bool
    reason: str
    tags: tuple[str, ...]
    group: str
    priority: int | None
    note: str
    data_availability_hint: str
    validation_status: str
    selectable: bool
    rejection_reasons: tuple[str, ...]
    candidate_result: CandidateInputValidationResult


@dataclass(frozen=True)
class WatchlistSummary:
    """Aggregate watchlist validation summary with all required flags false."""

    stage_name: str
    mode: str
    total_items: int
    valid_items: int
    invalid_items: int
    disabled_items: int
    duplicate_items: int
    insufficient_data_items: int
    forbidden_source_items: int
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


@dataclass(frozen=True)
class WatchlistValidationResult:
    """Deterministic validation result for a watchlist collection."""

    name: str
    description: str
    source_label: str
    default_enabled: bool
    validation_status: str
    rejection_reasons: tuple[str, ...]
    diagnostics: tuple[str, ...]
    items: tuple[WatchlistItemValidationResult, ...]
    summary: WatchlistSummary


def build_watchlist_policy() -> WatchlistPolicy:
    """Build the fixed MS-09.02 watchlist data model policy."""

    return WatchlistPolicy()


def _normalize_text(value: str) -> str:
    return value.strip()


def _normalize_tags(tags: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(tag.strip() for tag in tags if tag.strip())


def _priority_is_valid(
    priority: int | None,
    policy: WatchlistPolicy,
) -> bool:
    if priority is None:
        return True
    return policy.min_priority <= priority <= policy.max_priority


def _candidate_from_item(
    item: WatchlistItem,
    source_label: str = "",
    enabled: bool | None = None,
) -> CandidateInput:
    effective_enabled = item.enabled if enabled is None else enabled
    return CandidateInput(
        symbol=item.symbol,
        source=item.source,
        name=item.name,
        market=item.market,
        source_label=source_label,
        enabled=effective_enabled,
        reason=item.reason,
        tags=item.tags,
        data_availability_hint=item.data_availability_hint,
    )


def watchlist_items_to_candidate_inputs(
    items: tuple[WatchlistItem, ...],
    source_label: str = "",
) -> tuple[CandidateInput, ...]:
    """Convert watchlist items to MS-09.01 candidate inputs without I/O."""

    normalized_source_label = _normalize_text(source_label)
    return tuple(
        _candidate_from_item(item, normalized_source_label)
        for item in items
    )


def validate_watchlist_item(
    item: WatchlistItem,
    policy: WatchlistPolicy | None = None,
    duplicate_symbols: tuple[str, ...] = (),
    source_label: str = "",
    default_enabled: bool = True,
) -> WatchlistItemValidationResult:
    """Validate one watchlist item through the MS-09.01 candidate contract."""

    active_policy = policy or build_watchlist_policy()
    candidate_policy = build_candidate_input_preflight_policy()
    effective_enabled = bool(default_enabled and item.enabled)
    candidate = _candidate_from_item(
        item,
        _normalize_text(source_label),
        enabled=effective_enabled,
    )
    candidate_result = validate_candidate_input(
        candidate,
        candidate_policy,
        duplicate_symbols=duplicate_symbols,
    )

    rejection_reasons = list(candidate_result.rejection_reasons)
    validation_status = candidate_result.validation_status

    if not _priority_is_valid(item.priority, active_policy):
        rejection_reasons.append("priority_out_of_range")
        if validation_status == CandidateInputStatus.VALID_CANDIDATE.value:
            validation_status = CandidateInputStatus.NEEDS_REVIEW.value

    selectable = validation_status == CandidateInputStatus.VALID_CANDIDATE.value

    return WatchlistItemValidationResult(
        symbol=candidate_result.symbol,
        name=candidate_result.name,
        market=candidate_result.market,
        source=candidate_result.source,
        enabled=effective_enabled,
        reason=candidate_result.reason,
        tags=_normalize_tags(item.tags),
        group=_normalize_text(item.group),
        priority=item.priority,
        note=_normalize_text(item.note),
        data_availability_hint=candidate_result.data_availability_hint,
        validation_status=validation_status,
        selectable=selectable,
        rejection_reasons=tuple(rejection_reasons),
        candidate_result=candidate_result,
    )


def _validate_watchlist_items(
    watchlist: Watchlist,
    policy: WatchlistPolicy,
) -> tuple[WatchlistItemValidationResult, ...]:
    seen_symbols: list[str] = []
    results: list[WatchlistItemValidationResult] = []
    for item in watchlist.items:
        normalized_symbol = item.symbol.strip().casefold()
        result = validate_watchlist_item(
            item,
            policy,
            duplicate_symbols=tuple(seen_symbols),
            source_label=watchlist.source_label,
            default_enabled=watchlist.default_enabled,
        )
        results.append(result)
        if normalized_symbol:
            seen_symbols.append(normalized_symbol)
    return tuple(results)


def build_watchlist_summary(
    watchlist: Watchlist,
    policy: WatchlistPolicy | None = None,
) -> WatchlistSummary:
    """Build a deterministic summary for a caller-supplied watchlist."""

    active_policy = policy or build_watchlist_policy()
    item_results = _validate_watchlist_items(watchlist, active_policy)
    invalid_statuses = (
        CandidateInputStatus.INVALID_SYMBOL.value,
        CandidateInputStatus.UNSUPPORTED_SOURCE.value,
    )

    return WatchlistSummary(
        stage_name=active_policy.stage_name,
        mode=active_policy.mode,
        total_items=len(item_results),
        valid_items=sum(
            result.validation_status == CandidateInputStatus.VALID_CANDIDATE.value
            for result in item_results
        ),
        invalid_items=sum(
            result.validation_status in invalid_statuses
            for result in item_results
        ),
        disabled_items=sum(
            result.validation_status
            == CandidateInputStatus.DISABLED_CANDIDATE.value
            for result in item_results
        ),
        duplicate_items=sum(
            result.validation_status
            == CandidateInputStatus.DUPLICATE_CANDIDATE.value
            for result in item_results
        ),
        insufficient_data_items=sum(
            result.validation_status
            == CandidateInputStatus.INSUFFICIENT_DATA.value
            for result in item_results
        ),
        forbidden_source_items=sum(
            "forbidden_source" in result.rejection_reasons
            for result in item_results
        ),
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
    )


def validate_watchlist(
    watchlist: Watchlist,
    policy: WatchlistPolicy | None = None,
) -> WatchlistValidationResult:
    """Validate a watchlist collection without loading or storing it."""

    active_policy = policy or build_watchlist_policy()
    normalized_name = _normalize_text(watchlist.name)
    item_results = _validate_watchlist_items(watchlist, active_policy)
    summary = build_watchlist_summary(watchlist, active_policy)
    rejection_reasons: list[str] = []
    diagnostics = tuple(
        _normalize_text(value)
        for value in watchlist.diagnostics
        if _normalize_text(value)
    )

    if not normalized_name:
        validation_status = WatchlistStatus.INVALID_WATCHLIST_NAME.value
        rejection_reasons.append("watchlist_name_required")
    elif not item_results:
        validation_status = WatchlistStatus.EMPTY_WATCHLIST.value
    elif summary.invalid_items:
        validation_status = WatchlistStatus.CONTAINS_INVALID_CANDIDATES.value
    elif summary.duplicate_items:
        validation_status = WatchlistStatus.CONTAINS_DUPLICATE_CANDIDATES.value
    elif summary.disabled_items:
        validation_status = WatchlistStatus.CONTAINS_DISABLED_CANDIDATES.value
    elif summary.insufficient_data_items or any(
        result.validation_status == CandidateInputStatus.NEEDS_REVIEW.value
        for result in item_results
    ):
        validation_status = WatchlistStatus.NEEDS_REVIEW.value
    else:
        validation_status = WatchlistStatus.VALID_WATCHLIST.value

    return WatchlistValidationResult(
        name=normalized_name,
        description=_normalize_text(watchlist.description),
        source_label=_normalize_text(watchlist.source_label),
        default_enabled=watchlist.default_enabled,
        validation_status=validation_status,
        rejection_reasons=tuple(rejection_reasons),
        diagnostics=diagnostics,
        items=item_results,
        summary=summary,
    )
