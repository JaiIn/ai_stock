"""Pure manual/local watchlist source adapter for MS-09.03.

This module normalizes caller-supplied manual/local records into the MS-09.02
watchlist model. It performs no file, database, environment, network, UI,
model, account, order, clock, or random I/O. It does not load, store, score,
recommend, trade, or display watchlists.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from enum import Enum

from ai_stock.recommendation.candidate_input_preflight import (
    FORBIDDEN_CANDIDATE_LABELS,
    FORBIDDEN_CANDIDATE_SOURCES,
    CandidateInput,
)
from ai_stock.recommendation.watchlist_model import (
    FORBIDDEN_WATCHLIST_FIELDS,
    Watchlist,
    WatchlistItem,
    WatchlistSummary,
    WatchlistValidationResult,
    build_watchlist_policy,
    validate_watchlist,
    watchlist_items_to_candidate_inputs,
)


class ManualWatchlistSourceType(str, Enum):
    """Allowed caller-supplied source types for MS-09.03."""

    MANUAL_SYMBOLS = "manual_symbols"
    MANUAL_WATCHLIST_ITEMS = "manual_watchlist_items"
    LOCAL_STATIC_CANDIDATES = "local_static_candidates"
    TEST_FIXTURE_SOURCE = "test_fixture_source"


class WatchlistSourceConfigStatus(str, Enum):
    """Non-directive source config validation statuses."""

    VALID_SOURCE_CONFIG = "valid_source_config"
    UNSUPPORTED_SOURCE_TYPE = "unsupported_source_type"
    EMPTY_SOURCE_ITEMS = "empty_source_items"
    NEEDS_REVIEW = "needs_review"


ALLOWED_MANUAL_WATCHLIST_SOURCE_TYPES: tuple[str, ...] = tuple(
    source_type.value for source_type in ManualWatchlistSourceType
)

FORBIDDEN_MANUAL_WATCHLIST_SOURCE_TYPES: tuple[str, ...] = (
    "file_path",
    "database_table",
    "sqlite_query",
    "toss_api_endpoint",
    "oauth_account_scope",
    "accountSeq_source",
    "real_account_holdings",
    "real_account_balance",
    "real_order_history",
    "real_fills",
    "raw_api_response",
    "raw_db_rows",
    "credential_based_source",
)

SOURCE_TYPE_TO_CANDIDATE_SOURCE: tuple[tuple[str, str], ...] = (
    (ManualWatchlistSourceType.MANUAL_SYMBOLS.value, "manual_watchlist"),
    (
        ManualWatchlistSourceType.MANUAL_WATCHLIST_ITEMS.value,
        "manual_watchlist",
    ),
    (
        ManualWatchlistSourceType.LOCAL_STATIC_CANDIDATES.value,
        "local_snapshot_summary",
    ),
    (ManualWatchlistSourceType.TEST_FIXTURE_SOURCE.value, "test_fixture"),
)

ALLOWED_WATCHLIST_SOURCE_ITEM_FIELDS: tuple[str, ...] = (
    "symbol",
    "name",
    "market",
    "source",
    "enabled",
    "reason",
    "tags",
    "group",
    "priority",
    "note",
    "data_availability_hint",
)

FORBIDDEN_WATCHLIST_SOURCE_FIELDS: tuple[str, ...] = (
    "accountSeq",
    "access_token",
    "authorization",
    "authorization_header",
    "api_key",
    "secret_key",
    "client_secret",
    "holdings",
    "balance",
    "fills",
    "order",
    "order_id",
    "avg_buy_price",
    "quantity",
    "target_price",
    "expected_return",
    "score",
    "buy",
    "sell",
    "hold",
    *FORBIDDEN_WATCHLIST_FIELDS,
)


@dataclass(frozen=True)
class ManualWatchlistSourcePolicy:
    """Immutable fail-closed policy for MS-09.03 source normalization."""

    stage_name: str = "MS-09.03"
    mode: str = "manual_local_watchlist_source"
    allowed_source_types: tuple[str, ...] = ALLOWED_MANUAL_WATCHLIST_SOURCE_TYPES
    forbidden_source_types: tuple[str, ...] = FORBIDDEN_MANUAL_WATCHLIST_SOURCE_TYPES
    allowed_item_fields: tuple[str, ...] = ALLOWED_WATCHLIST_SOURCE_ITEM_FIELDS
    forbidden_item_fields: tuple[str, ...] = FORBIDDEN_WATCHLIST_SOURCE_FIELDS
    forbidden_candidate_sources: tuple[str, ...] = FORBIDDEN_CANDIDATE_SOURCES
    forbidden_labels: tuple[str, ...] = FORBIDDEN_CANDIDATE_LABELS
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
class WatchlistSourceConfig:
    """Caller-supplied manual/local source config; no path or endpoint fields."""

    source_type: str
    source_label: str = ""
    watchlist_name: str = "Manual Watchlist"
    watchlist_description: str = ""
    default_market: str = "unknown"
    default_enabled: bool = True
    default_tags: tuple[str, ...] = ()
    default_group: str = ""
    default_reason: str = ""
    raw_items: tuple[object, ...] = ()


@dataclass(frozen=True)
class WatchlistSourceConfigValidationResult:
    """Deterministic validation result for one manual/local source config."""

    source_type: str
    source_label: str
    validation_status: str
    valid: bool
    rejection_reasons: tuple[str, ...]
    diagnostics: tuple[str, ...]


@dataclass(frozen=True)
class WatchlistSourceResult:
    """Normalized source result with all required flags false."""

    source_type: str
    source_label: str
    watchlist: Watchlist
    candidate_inputs: tuple[CandidateInput, ...]
    validation: WatchlistValidationResult
    summary: WatchlistSummary
    diagnostics: tuple[str, ...]
    rejection_reasons: tuple[str, ...]
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


def build_manual_watchlist_source_policy() -> ManualWatchlistSourcePolicy:
    """Build the fixed MS-09.03 manual/local source policy."""

    return ManualWatchlistSourcePolicy()


def _normalize_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_bool(value: object, default: bool = True) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    normalized = str(value).strip().casefold()
    if normalized in ("false", "0", "no", "n", "disabled", "off"):
        return False
    if normalized in ("true", "1", "yes", "y", "enabled", "on"):
        return True
    return default


def _normalize_priority(value: object) -> int | None:
    if isinstance(value, bool) or value is None:
        return None
    if isinstance(value, int):
        return value
    normalized = str(value).strip()
    if normalized.isdecimal():
        return int(normalized)
    return None


def _normalize_tags(value: object) -> tuple[str, ...]:
    if value is None:
        return ()
    if isinstance(value, str):
        normalized = value.strip()
        return (normalized,) if normalized else ()
    if isinstance(value, tuple | list):
        return tuple(
            normalized
            for item in value
            if (normalized := _normalize_text(item))
        )
    return ()


def _mapping_value(
    record: Mapping[object, object],
    key: str,
    default: object,
) -> object:
    if key in record:
        return record[key]
    return default


def _default_candidate_source(source_type: str) -> str:
    normalized_source_type = _normalize_text(source_type)
    for candidate_source_type, candidate_source in SOURCE_TYPE_TO_CANDIDATE_SOURCE:
        if normalized_source_type == candidate_source_type:
            return candidate_source
    return "manual_watchlist"


def _is_forbidden_key(
    key: object,
    policy: ManualWatchlistSourcePolicy,
) -> bool:
    normalized_key = _normalize_text(key).casefold()
    if not normalized_key:
        return False
    forbidden_keys = tuple(
        forbidden.casefold() for forbidden in policy.forbidden_item_fields
    )
    return any(forbidden in normalized_key for forbidden in forbidden_keys)


def _detect_forbidden_fields(
    record: Mapping[object, object],
    policy: ManualWatchlistSourcePolicy,
) -> tuple[str, ...]:
    return tuple(
        _normalize_text(key)
        for key in record
        if _is_forbidden_key(key, policy)
    )


def _base_rejection_reasons(
    config_validation: WatchlistSourceConfigValidationResult,
) -> tuple[str, ...]:
    if config_validation.valid:
        return ()
    return config_validation.rejection_reasons


def validate_watchlist_source_config(
    config: WatchlistSourceConfig,
    policy: ManualWatchlistSourcePolicy | None = None,
) -> WatchlistSourceConfigValidationResult:
    """Validate source config without using files, databases, or endpoints."""

    active_policy = policy or build_manual_watchlist_source_policy()
    source_type = _normalize_text(config.source_type)
    diagnostics: list[str] = []
    rejection_reasons: list[str] = []

    if source_type in active_policy.forbidden_source_types:
        validation_status = WatchlistSourceConfigStatus.UNSUPPORTED_SOURCE_TYPE.value
        rejection_reasons.append("forbidden_source_type")
    elif source_type not in active_policy.allowed_source_types:
        validation_status = WatchlistSourceConfigStatus.UNSUPPORTED_SOURCE_TYPE.value
        rejection_reasons.append("unsupported_source_type")
    elif not config.raw_items:
        validation_status = WatchlistSourceConfigStatus.EMPTY_SOURCE_ITEMS.value
        diagnostics.append("empty_source_items")
    else:
        validation_status = WatchlistSourceConfigStatus.VALID_SOURCE_CONFIG.value

    return WatchlistSourceConfigValidationResult(
        source_type=source_type,
        source_label=_normalize_text(config.source_label),
        validation_status=validation_status,
        valid=validation_status
        in (
            WatchlistSourceConfigStatus.VALID_SOURCE_CONFIG.value,
            WatchlistSourceConfigStatus.EMPTY_SOURCE_ITEMS.value,
        ),
        rejection_reasons=tuple(rejection_reasons),
        diagnostics=tuple(diagnostics),
    )


def normalize_manual_symbol_record(
    symbol: object,
    config: WatchlistSourceConfig | None = None,
) -> WatchlistItem:
    """Normalize one caller-supplied symbol into a watchlist item."""

    active_config = config or WatchlistSourceConfig(
        source_type=ManualWatchlistSourceType.MANUAL_SYMBOLS.value
    )
    return WatchlistItem(
        symbol=_normalize_text(symbol),
        source=_default_candidate_source(active_config.source_type),
        market=_normalize_text(active_config.default_market),
        enabled=active_config.default_enabled,
        reason=_normalize_text(active_config.default_reason),
        tags=_normalize_tags(active_config.default_tags),
        group=_normalize_text(active_config.default_group),
    )


def _watchlist_item_from_mapping(
    record: Mapping[object, object],
    config: WatchlistSourceConfig,
) -> WatchlistItem:
    default_source = _default_candidate_source(config.source_type)
    source_value = _normalize_text(
        _mapping_value(record, "source", default_source)
    )
    return WatchlistItem(
        symbol=_normalize_text(_mapping_value(record, "symbol", "")),
        name=_normalize_text(_mapping_value(record, "name", "")),
        market=_normalize_text(
            _mapping_value(record, "market", config.default_market)
        ),
        source=source_value or default_source,
        enabled=_normalize_bool(
            _mapping_value(record, "enabled", None),
            config.default_enabled,
        ),
        reason=_normalize_text(
            _mapping_value(record, "reason", config.default_reason)
        ),
        tags=_normalize_tags(_mapping_value(record, "tags", config.default_tags)),
        group=_normalize_text(
            _mapping_value(record, "group", config.default_group)
        ),
        priority=_normalize_priority(_mapping_value(record, "priority", None)),
        note=_normalize_text(_mapping_value(record, "note", "")),
        data_availability_hint=_normalize_text(
            _mapping_value(record, "data_availability_hint", "")
        ),
    )


def _normalize_source_record(
    record: object,
    config: WatchlistSourceConfig,
    policy: ManualWatchlistSourcePolicy,
) -> tuple[WatchlistItem, tuple[str, ...], tuple[str, ...]]:
    if isinstance(record, Mapping):
        forbidden_fields = _detect_forbidden_fields(record, policy)
        rejection_reasons = tuple(
            f"forbidden_field:{field}" for field in forbidden_fields
        )
        diagnostics = tuple(
            f"forbidden_field_detected:{field}" for field in forbidden_fields
        )
        return (
            _watchlist_item_from_mapping(record, config),
            rejection_reasons,
            diagnostics,
        )

    return normalize_manual_symbol_record(record, config), (), ()


def build_manual_watchlist_from_symbols(
    symbols: tuple[object, ...],
    source_label: str = "",
    watchlist_name: str = "Manual Symbol Watchlist",
    watchlist_description: str = "",
    default_market: str = "unknown",
    default_enabled: bool = True,
    default_tags: tuple[str, ...] = (),
    default_group: str = "",
    default_reason: str = "",
) -> Watchlist:
    """Build a watchlist from caller-supplied symbols without I/O."""

    config = WatchlistSourceConfig(
        source_type=ManualWatchlistSourceType.MANUAL_SYMBOLS.value,
        source_label=source_label,
        watchlist_name=watchlist_name,
        watchlist_description=watchlist_description,
        default_market=default_market,
        default_enabled=default_enabled,
        default_tags=default_tags,
        default_group=default_group,
        default_reason=default_reason,
        raw_items=symbols,
    )
    items = tuple(
        normalize_manual_symbol_record(symbol, config)
        for symbol in config.raw_items
    )
    return Watchlist(
        name=config.watchlist_name,
        description=config.watchlist_description,
        items=items,
        source_label=config.source_label,
        default_enabled=config.default_enabled,
    )


def build_manual_watchlist_from_items(
    raw_items: tuple[object, ...],
    source_label: str = "",
    watchlist_name: str = "Manual Item Watchlist",
    watchlist_description: str = "",
    default_market: str = "unknown",
    default_enabled: bool = True,
    default_tags: tuple[str, ...] = (),
    default_group: str = "",
    default_reason: str = "",
) -> Watchlist:
    """Build a watchlist from caller-supplied item records without I/O."""

    config = WatchlistSourceConfig(
        source_type=ManualWatchlistSourceType.MANUAL_WATCHLIST_ITEMS.value,
        source_label=source_label,
        watchlist_name=watchlist_name,
        watchlist_description=watchlist_description,
        default_market=default_market,
        default_enabled=default_enabled,
        default_tags=default_tags,
        default_group=default_group,
        default_reason=default_reason,
        raw_items=raw_items,
    )
    items = tuple(
        _normalize_source_record(
            record,
            config,
            build_manual_watchlist_source_policy(),
        )[0]
        for record in config.raw_items
    )
    return Watchlist(
        name=config.watchlist_name,
        description=config.watchlist_description,
        items=items,
        source_label=config.source_label,
        default_enabled=config.default_enabled,
    )


def _build_watchlist_from_config(
    config: WatchlistSourceConfig,
    policy: ManualWatchlistSourcePolicy,
) -> tuple[Watchlist, tuple[str, ...], tuple[str, ...]]:
    items: list[WatchlistItem] = []
    rejection_reasons: list[str] = []
    diagnostics: list[str] = []

    for record in config.raw_items:
        item, record_rejections, record_diagnostics = _normalize_source_record(
            record,
            config,
            policy,
        )
        items.append(item)
        rejection_reasons.extend(record_rejections)
        diagnostics.extend(record_diagnostics)

    watchlist = Watchlist(
        name=config.watchlist_name,
        description=config.watchlist_description,
        items=tuple(items),
        source_label=config.source_label,
        default_enabled=config.default_enabled,
    )
    return watchlist, tuple(rejection_reasons), tuple(diagnostics)


def build_watchlist_source_result(
    config: WatchlistSourceConfig,
    policy: ManualWatchlistSourcePolicy | None = None,
) -> WatchlistSourceResult:
    """Normalize, validate, and summarize a caller-supplied source config."""

    active_policy = policy or build_manual_watchlist_source_policy()
    config_validation = validate_watchlist_source_config(config, active_policy)
    if config_validation.validation_status == (
        WatchlistSourceConfigStatus.UNSUPPORTED_SOURCE_TYPE.value
    ):
        watchlist = Watchlist(
            name=config.watchlist_name,
            description=config.watchlist_description,
            source_label=config.source_label,
        )
        record_rejections: tuple[str, ...] = ()
        record_diagnostics: tuple[str, ...] = ()
    else:
        watchlist, record_rejections, record_diagnostics = (
            _build_watchlist_from_config(config, active_policy)
        )

    watchlist_policy = build_watchlist_policy()
    validation = validate_watchlist(watchlist, watchlist_policy)
    candidate_inputs = watchlist_items_to_candidate_inputs(
        watchlist.items,
        source_label=watchlist.source_label,
    )

    return WatchlistSourceResult(
        source_type=config_validation.source_type,
        source_label=config_validation.source_label,
        watchlist=watchlist,
        candidate_inputs=candidate_inputs,
        validation=validation,
        summary=validation.summary,
        diagnostics=(
            config_validation.diagnostics
            + record_diagnostics
            + validation.diagnostics
        ),
        rejection_reasons=(
            _base_rejection_reasons(config_validation)
            + record_rejections
            + validation.rejection_reasons
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


def build_local_static_watchlist_source(
    config: WatchlistSourceConfig,
    policy: ManualWatchlistSourcePolicy | None = None,
) -> WatchlistSourceResult:
    """Build a local static source result from caller-supplied records only."""

    local_static_config = WatchlistSourceConfig(
        source_type=ManualWatchlistSourceType.LOCAL_STATIC_CANDIDATES.value,
        source_label=config.source_label,
        watchlist_name=config.watchlist_name,
        watchlist_description=config.watchlist_description,
        default_market=config.default_market,
        default_enabled=config.default_enabled,
        default_tags=config.default_tags,
        default_group=config.default_group,
        default_reason=config.default_reason,
        raw_items=config.raw_items,
    )
    return build_watchlist_source_result(local_static_config, policy)
