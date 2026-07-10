"""Pure candidate input contract preflight for MS-09.01.

This module defines safe candidate input sources and validation contracts before
any recommendation, scoring, watchlist persistence, UI, API, DB, credential, or
account/order integration exists. It performs no file, database, environment,
network, UI, model, account, order, clock, or random I/O.
"""

from dataclasses import dataclass
from enum import Enum


class CandidateInputSource(str, Enum):
    """Candidate sources allowed by the MS-09.01 preflight contract."""

    DASHBOARD_SELECTOR = "dashboard_selector"
    LOCAL_SNAPSHOT_SUMMARY = "local_snapshot_summary"
    MANUAL_WATCHLIST = "manual_watchlist"
    FUTURE_WATCHLIST_FILE = "future_watchlist_file"
    TEST_FIXTURE = "test_fixture"


class CandidateInputStatus(str, Enum):
    """Non-directive validation statuses for candidate inputs."""

    VALID_CANDIDATE = "valid_candidate"
    INSUFFICIENT_DATA = "insufficient_data"
    UNSUPPORTED_SOURCE = "unsupported_source"
    INVALID_SYMBOL = "invalid_symbol"
    DISABLED_CANDIDATE = "disabled_candidate"
    DUPLICATE_CANDIDATE = "duplicate_candidate"
    NEEDS_REVIEW = "needs_review"


ALLOWED_CANDIDATE_SOURCES: tuple[str, ...] = tuple(
    source.value for source in CandidateInputSource
)

FORBIDDEN_CANDIDATE_SOURCES: tuple[str, ...] = (
    "real_account_holdings",
    "real_account_balance",
    "real_order_history",
    "real_fills",
    "live_api_refresh",
    "oauth_account_scope",
    "accountSeq_based_source",
    "raw_api_response",
    "raw_db_rows",
    "credential_based_source",
)

SAFE_CANDIDATE_STATUSES: tuple[str, ...] = tuple(
    status.value for status in CandidateInputStatus
)

FORBIDDEN_CANDIDATE_LABELS: tuple[str, ...] = (
    "buy",
    "sell",
    "hold",
    "strong_buy",
    "target_price",
    "profit_expected",
    "must_buy",
    "must_sell",
)

KNOWN_MARKETS: tuple[str, ...] = (
    "KOSPI",
    "KOSDAQ",
    "KRX",
    "NASDAQ",
    "NYSE",
    "AMEX",
    "UNKNOWN",
)

INSUFFICIENT_DATA_HINTS: tuple[str, ...] = (
    "insufficient_data",
    "missing_data",
    "partial_data",
    "no_snapshot",
)

NEEDS_REVIEW_HINTS: tuple[str, ...] = (
    "needs_review",
    "needs_data_review",
    "stale_data",
    "risk_review",
)


@dataclass(frozen=True)
class CandidateInputPreflightPolicy:
    """Immutable fail-closed policy for MS-09.01 candidate inputs."""

    stage_name: str = "MS-09.01"
    mode: str = "candidate_input_contract_preflight"
    allowed_sources: tuple[str, ...] = ALLOWED_CANDIDATE_SOURCES
    forbidden_sources: tuple[str, ...] = FORBIDDEN_CANDIDATE_SOURCES
    safe_statuses: tuple[str, ...] = SAFE_CANDIDATE_STATUSES
    forbidden_labels: tuple[str, ...] = FORBIDDEN_CANDIDATE_LABELS
    known_markets: tuple[str, ...] = KNOWN_MARKETS
    max_symbol_length: int = 32
    duplicate_handling_policy: str = (
        "mark_duplicate_candidate_without_persistence"
    )
    actual_recommendation_allowed: bool = False
    scoring_allowed: bool = False
    watchlist_write_allowed: bool = False
    ui_change_allowed: bool = False
    credential_required: bool = False
    db_read_required: bool = False
    db_write_required: bool = False
    toss_api_required: bool = False
    openai_required: bool = False
    oauth_required: bool = False
    account_seq_required: bool = False
    real_order_required: bool = False


@dataclass(frozen=True)
class CandidateInput:
    """Caller-supplied candidate item; this module never loads candidates."""

    symbol: str
    source: str
    name: str = ""
    market: str = "unknown"
    source_label: str = ""
    enabled: bool = True
    reason: str = ""
    tags: tuple[str, ...] = ()
    data_availability_hint: str = ""


@dataclass(frozen=True)
class CandidateInputValidationResult:
    """Deterministic validation result for one candidate item."""

    symbol: str
    name: str
    market: str
    source: str
    source_label: str
    enabled: bool
    reason: str
    tags: tuple[str, ...]
    data_availability_hint: str
    validation_status: str
    selectable: bool
    rejection_reasons: tuple[str, ...]


@dataclass(frozen=True)
class CandidateInputPreflightSummary:
    """Aggregate preflight summary for a caller-supplied candidate batch."""

    stage_name: str
    mode: str
    total_candidates: int
    valid_candidates: int
    rejected_candidates: int
    disabled_candidates: int
    insufficient_data_candidates: int
    forbidden_source_candidates: int
    duplicate_candidates: int
    needs_review_candidates: int
    credential_required: bool
    db_read_required: bool
    db_write_required: bool
    toss_api_required: bool
    openai_required: bool
    oauth_required: bool
    account_seq_required: bool
    real_order_required: bool
    candidates: tuple[CandidateInputValidationResult, ...]


def build_candidate_input_preflight_policy() -> CandidateInputPreflightPolicy:
    """Build the fixed MS-09.01 candidate input preflight policy."""

    return CandidateInputPreflightPolicy()


def _normalize_source(source: str) -> str:
    return source.strip()


def _normalize_symbol(symbol: str) -> str:
    return symbol.strip()


def _normalize_market(market: str, policy: CandidateInputPreflightPolicy) -> str:
    normalized = market.strip().upper()
    if not normalized:
        return "UNKNOWN"
    if normalized in policy.known_markets:
        return normalized
    return "UNKNOWN"


def _is_safe_symbol(symbol: str, policy: CandidateInputPreflightPolicy) -> bool:
    if not symbol:
        return False
    if len(symbol) > policy.max_symbol_length:
        return False
    return all(
        character.isascii()
        and (character.isalnum() or character in "._-")
        for character in symbol
    )


def _normalize_tags(tags: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(tag.strip() for tag in tags if tag.strip())


def _hint_status(hint: str) -> str | None:
    normalized = hint.strip().casefold()
    if normalized in INSUFFICIENT_DATA_HINTS:
        return CandidateInputStatus.INSUFFICIENT_DATA.value
    if normalized in NEEDS_REVIEW_HINTS:
        return CandidateInputStatus.NEEDS_REVIEW.value
    return None


def validate_candidate_input(
    candidate: CandidateInput,
    policy: CandidateInputPreflightPolicy | None = None,
    duplicate_symbols: tuple[str, ...] = (),
) -> CandidateInputValidationResult:
    """Validate one caller-supplied candidate without external access."""

    active_policy = policy or build_candidate_input_preflight_policy()
    symbol = _normalize_symbol(candidate.symbol)
    source = _normalize_source(candidate.source)
    market = _normalize_market(candidate.market, active_policy)
    source_label = candidate.source_label.strip()
    reason = candidate.reason.strip()
    tags = _normalize_tags(candidate.tags)
    data_hint = candidate.data_availability_hint.strip()

    rejection_reasons: list[str] = []
    validation_status = CandidateInputStatus.VALID_CANDIDATE.value

    if not symbol:
        validation_status = CandidateInputStatus.INVALID_SYMBOL.value
        rejection_reasons.append("symbol_required")
    elif not _is_safe_symbol(symbol, active_policy):
        validation_status = CandidateInputStatus.INVALID_SYMBOL.value
        rejection_reasons.append("symbol_must_be_safe_ascii_identifier")

    if source in active_policy.forbidden_sources:
        validation_status = CandidateInputStatus.UNSUPPORTED_SOURCE.value
        rejection_reasons.append("forbidden_source")
    elif source not in active_policy.allowed_sources:
        validation_status = CandidateInputStatus.UNSUPPORTED_SOURCE.value
        rejection_reasons.append("unsupported_source")

    if symbol and symbol.casefold() in duplicate_symbols:
        validation_status = CandidateInputStatus.DUPLICATE_CANDIDATE.value
        rejection_reasons.append("duplicate_symbol")

    if not candidate.enabled:
        validation_status = CandidateInputStatus.DISABLED_CANDIDATE.value
        rejection_reasons.append("candidate_disabled")

    safe_hint_status = _hint_status(data_hint)
    if (
        validation_status == CandidateInputStatus.VALID_CANDIDATE.value
        and safe_hint_status
    ):
        validation_status = safe_hint_status

    selectable = validation_status == CandidateInputStatus.VALID_CANDIDATE.value

    return CandidateInputValidationResult(
        symbol=symbol,
        name=candidate.name.strip(),
        market=market,
        source=source,
        source_label=source_label,
        enabled=candidate.enabled,
        reason=reason,
        tags=tags,
        data_availability_hint=data_hint,
        validation_status=validation_status,
        selectable=selectable,
        rejection_reasons=tuple(rejection_reasons),
    )


def validate_candidate_batch(
    candidates: tuple[CandidateInput, ...],
    policy: CandidateInputPreflightPolicy | None = None,
) -> tuple[CandidateInputValidationResult, ...]:
    """Validate a candidate batch with deterministic duplicate marking."""

    active_policy = policy or build_candidate_input_preflight_policy()
    seen_symbols: list[str] = []
    results: list[CandidateInputValidationResult] = []

    for candidate in candidates:
        normalized_symbol = _normalize_symbol(candidate.symbol).casefold()
        result = validate_candidate_input(
            candidate,
            active_policy,
            duplicate_symbols=tuple(seen_symbols),
        )
        results.append(result)
        if normalized_symbol:
            seen_symbols.append(normalized_symbol)

    return tuple(results)


def build_candidate_input_preflight_summary(
    candidates: tuple[CandidateInput, ...],
    policy: CandidateInputPreflightPolicy | None = None,
) -> CandidateInputPreflightSummary:
    """Build an aggregate summary from caller-supplied candidate inputs."""

    active_policy = policy or build_candidate_input_preflight_policy()
    validation_results = validate_candidate_batch(candidates, active_policy)
    rejected_statuses = (
        CandidateInputStatus.UNSUPPORTED_SOURCE.value,
        CandidateInputStatus.INVALID_SYMBOL.value,
        CandidateInputStatus.DISABLED_CANDIDATE.value,
        CandidateInputStatus.DUPLICATE_CANDIDATE.value,
    )

    return CandidateInputPreflightSummary(
        stage_name=active_policy.stage_name,
        mode=active_policy.mode,
        total_candidates=len(validation_results),
        valid_candidates=sum(
            result.validation_status
            == CandidateInputStatus.VALID_CANDIDATE.value
            for result in validation_results
        ),
        rejected_candidates=sum(
            result.validation_status in rejected_statuses
            for result in validation_results
        ),
        disabled_candidates=sum(
            result.validation_status
            == CandidateInputStatus.DISABLED_CANDIDATE.value
            for result in validation_results
        ),
        insufficient_data_candidates=sum(
            result.validation_status
            == CandidateInputStatus.INSUFFICIENT_DATA.value
            for result in validation_results
        ),
        forbidden_source_candidates=sum(
            "forbidden_source" in result.rejection_reasons
            for result in validation_results
        ),
        duplicate_candidates=sum(
            result.validation_status
            == CandidateInputStatus.DUPLICATE_CANDIDATE.value
            for result in validation_results
        ),
        needs_review_candidates=sum(
            result.validation_status == CandidateInputStatus.NEEDS_REVIEW.value
            for result in validation_results
        ),
        credential_required=active_policy.credential_required,
        db_read_required=active_policy.db_read_required,
        db_write_required=active_policy.db_write_required,
        toss_api_required=active_policy.toss_api_required,
        openai_required=active_policy.openai_required,
        oauth_required=active_policy.oauth_required,
        account_seq_required=active_policy.account_seq_required,
        real_order_required=active_policy.real_order_required,
        candidates=validation_results,
    )
