"""Safe presentation model for the minimal read-only snapshot dashboard."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import re
from typing import Literal

from ai_stock.storage.local_snapshot_latest_read_model import (
    DEFAULT_BASE_CURRENCY,
    DEFAULT_QUOTE_CURRENCY,
    DEFAULT_SYMBOL,
    LocalSnapshotLatestReadModel,
    build_local_snapshot_latest_read_model,
)
from ai_stock.ui.readonly_snapshot_dashboard_preflight import (
    DATA_SOURCE,
    PLANNED_DEFAULT_DB_RELATIVE_PATH,
    PLANNED_SECTIONS,
)

STAGE = "MS-07.04"
PHASE = "readonly_dashboard_symbol_pair_selector"
DASHBOARD_TITLE = "Local Snapshot Dashboard"
DEFAULT_DB_RELATIVE_PATH = PLANNED_DEFAULT_DB_RELATIVE_PATH
DEFAULT_EXCHANGE_PAIR = f"{DEFAULT_BASE_CURRENCY}/{DEFAULT_QUOTE_CURRENCY}"
_CURRENCY_CODE_PATTERN = re.compile(r"[A-Z]{3}")
_SYMBOL_PATTERN = re.compile(r"[A-Za-z0-9._-]{1,32}")

DISPLAYED_SECTIONS = (
    "dashboard_title",
    "data_health_summary",
    "safety_status",
    "data_source_summary",
    "db_path_summary",
    "selected_symbol_summary",
    "latest_stock_info_summary",
    "latest_price_snapshot_summary",
    "latest_candle_summary",
    "latest_exchange_rate_summary",
    "completeness_flags",
    "source_counts",
    "read_only_diagnostics",
    "last_db_audit_metadata",
)


@dataclass(frozen=True, slots=True)
class DashboardFileMetadata:
    exists: bool
    size_bytes: int | None
    modified_time_utc: str | None


@dataclass(frozen=True, slots=True)
class DashboardSelection:
    symbol: str
    base_currency: str
    quote_currency: str
    exchange_pair: str
    valid: bool
    safe_error_message: str | None


@dataclass(frozen=True, slots=True)
class ReadonlySnapshotDashboardView:
    success: bool
    stage: str
    phase: str
    title: str
    status_level: Literal["success", "warning", "error"]
    status_message: str
    data_source: str
    database_path: str
    symbol: str
    exchange_pair: str
    db_open_mode: str
    db_write_allowed_this_stage: bool
    actual_db_file_modified_this_stage: bool
    api_call_allowed_this_stage: bool
    oauth_token_endpoint_allowed_this_stage: bool
    env_file_read_allowed_this_stage: bool
    credential_required_this_stage: bool
    ai_recommendation_allowed_this_stage: bool
    real_order_related_call_allowed: bool
    db_file_exists: bool
    db_file_size_bytes: int | None
    db_file_modified_time_utc: str | None
    stock_info: dict[str, object] | None
    price_snapshot: dict[str, object] | None
    candle: dict[str, object] | None
    exchange_rate: dict[str, object] | None
    completeness: dict[str, bool]
    source_counts: dict[str, int]
    displayed_sections: tuple[str, ...]
    stock_warnings_included: bool
    stock_warnings_deferred: bool
    safe_error_type: str | None
    safe_error_message: str | None

    def safe_dict(self) -> dict[str, object]:
        """Return only display-safe values; no database row is exposed."""

        return asdict(self)


def build_readonly_snapshot_dashboard(
    database_path: str | Path = DEFAULT_DB_RELATIVE_PATH,
    *,
    symbol: str = DEFAULT_SYMBOL,
    base_currency: str = DEFAULT_BASE_CURRENCY,
    quote_currency: str = DEFAULT_QUOTE_CURRENCY,
) -> ReadonlySnapshotDashboardView:
    """Build a safe dashboard view through the existing read-only model."""

    selection = validate_dashboard_selection(
        symbol=symbol,
        base_currency=base_currency,
        quote_currency=quote_currency,
    )
    if not selection.valid:
        return _invalid_selection_view(database_path, selection)

    path = Path(database_path)
    before = _file_metadata(path)
    model = build_local_snapshot_latest_read_model(
        path,
        symbol=selection.symbol,
        base_currency=selection.base_currency,
        quote_currency=selection.quote_currency,
    )
    after = _file_metadata(path)
    metadata_changed = before != after
    modified = model.actual_db_file_modified_this_stage or metadata_changed
    status_level, status_message = _status(model, modified)
    safe_model = model.safe_dict()

    metadata = after or before or DashboardFileMetadata(
        exists=False,
        size_bytes=None,
        modified_time_utc=None,
    )
    completeness = dict(safe_model["completeness"])
    source_counts = dict(safe_model["source_counts"])

    return ReadonlySnapshotDashboardView(
        success=model.success and not modified,
        stage=STAGE,
        phase=PHASE,
        title=DASHBOARD_TITLE,
        status_level=status_level,
        status_message=status_message,
        data_source=DATA_SOURCE,
        database_path=str(database_path),
        symbol=model.symbol,
        exchange_pair=model.exchange_rate_pair,
        db_open_mode=model.db_open_mode,
        db_write_allowed_this_stage=False,
        actual_db_file_modified_this_stage=modified,
        api_call_allowed_this_stage=False,
        oauth_token_endpoint_allowed_this_stage=False,
        env_file_read_allowed_this_stage=False,
        credential_required_this_stage=False,
        ai_recommendation_allowed_this_stage=False,
        real_order_related_call_allowed=False,
        db_file_exists=metadata.exists,
        db_file_size_bytes=metadata.size_bytes,
        db_file_modified_time_utc=metadata.modified_time_utc,
        stock_info=_optional_mapping(safe_model["stock"]),
        price_snapshot=_optional_mapping(safe_model["latest_price"]),
        candle=_optional_mapping(safe_model["latest_candle"]),
        exchange_rate=_optional_mapping(safe_model["latest_exchange_rate"]),
        completeness=completeness,
        source_counts=source_counts,
        displayed_sections=DISPLAYED_SECTIONS,
        stock_warnings_included=False,
        stock_warnings_deferred=True,
        safe_error_type=model.safe_error_type,
        safe_error_message=model.safe_error_message,
    )


def validate_dashboard_selection(
    *,
    symbol: str,
    base_currency: str,
    quote_currency: str,
) -> DashboardSelection:
    """Normalize local query selectors without performing any I/O."""

    normalized_symbol = symbol.strip() or DEFAULT_SYMBOL
    normalized_base = base_currency.strip().upper()
    normalized_quote = quote_currency.strip().upper()

    if _SYMBOL_PATTERN.fullmatch(normalized_symbol) is None:
        return DashboardSelection(
            symbol=DEFAULT_SYMBOL,
            base_currency=DEFAULT_BASE_CURRENCY,
            quote_currency=DEFAULT_QUOTE_CURRENCY,
            exchange_pair=DEFAULT_EXCHANGE_PAIR,
            valid=False,
            safe_error_message=(
                "Symbol must contain 1-32 letters, digits, dots, hyphens, "
                "or underscores."
            ),
        )
    if (
        _CURRENCY_CODE_PATTERN.fullmatch(normalized_base) is None
        or _CURRENCY_CODE_PATTERN.fullmatch(normalized_quote) is None
    ):
        return DashboardSelection(
            symbol=normalized_symbol,
            base_currency=DEFAULT_BASE_CURRENCY,
            quote_currency=DEFAULT_QUOTE_CURRENCY,
            exchange_pair=DEFAULT_EXCHANGE_PAIR,
            valid=False,
            safe_error_message=(
                "Base and quote currency codes must each contain exactly "
                "three ASCII letters."
            ),
        )
    return DashboardSelection(
        symbol=normalized_symbol,
        base_currency=normalized_base,
        quote_currency=normalized_quote,
        exchange_pair=f"{normalized_base}/{normalized_quote}",
        valid=True,
        safe_error_message=None,
    )


def _invalid_selection_view(
    database_path: str | Path,
    selection: DashboardSelection,
) -> ReadonlySnapshotDashboardView:
    metadata = _file_metadata(Path(database_path)) or DashboardFileMetadata(
        exists=False,
        size_bytes=None,
        modified_time_utc=None,
    )
    return ReadonlySnapshotDashboardView(
        success=False,
        stage=STAGE,
        phase=PHASE,
        title=DASHBOARD_TITLE,
        status_level="warning",
        status_message=selection.safe_error_message or "Invalid local selection.",
        data_source=DATA_SOURCE,
        database_path=str(database_path),
        symbol=selection.symbol,
        exchange_pair=selection.exchange_pair,
        db_open_mode="readonly",
        db_write_allowed_this_stage=False,
        actual_db_file_modified_this_stage=False,
        api_call_allowed_this_stage=False,
        oauth_token_endpoint_allowed_this_stage=False,
        env_file_read_allowed_this_stage=False,
        credential_required_this_stage=False,
        ai_recommendation_allowed_this_stage=False,
        real_order_related_call_allowed=False,
        db_file_exists=metadata.exists,
        db_file_size_bytes=metadata.size_bytes,
        db_file_modified_time_utc=metadata.modified_time_utc,
        stock_info=None,
        price_snapshot=None,
        candle=None,
        exchange_rate=None,
        completeness={
            "stock_info_present": False,
            "price_snapshot_present": False,
            "candle_present": False,
            "exchange_rate_present": False,
            "all_components_present": False,
        },
        source_counts={
            "stocks": 0,
            "price_snapshots": 0,
            "candles": 0,
            "exchange_rates": 0,
        },
        displayed_sections=DISPLAYED_SECTIONS,
        stock_warnings_included=False,
        stock_warnings_deferred=True,
        safe_error_type="invalid_selector",
        safe_error_message=selection.safe_error_message,
    )


def _file_metadata(path: Path) -> DashboardFileMetadata | None:
    if not path.is_file():
        return None
    stat = path.stat()
    return DashboardFileMetadata(
        exists=True,
        size_bytes=stat.st_size,
        modified_time_utc=datetime.fromtimestamp(
            stat.st_mtime,
            timezone.utc,
        ).isoformat(),
    )


def _status(
    model: LocalSnapshotLatestReadModel,
    modified: bool,
) -> tuple[Literal["success", "warning", "error"], str]:
    if modified:
        return (
            "error",
            "The local database metadata changed; no data is displayed.",
        )
    if model.safe_error_type == "database_not_found":
        return (
            "warning",
            "The local snapshot database does not exist. No file was created.",
        )
    if model.safe_error_type == "symbol_not_found":
        return (
            "warning",
            "The selected symbol is not available in the local snapshot database.",
        )
    if not model.success:
        return (
            "error",
            model.safe_error_message or "The local snapshot could not be loaded.",
        )
    if not model.completeness.all_components_present:
        return (
            "warning",
            "The local snapshot is available with incomplete components.",
        )
    return "success", "A complete local snapshot was loaded in read-only mode."


def _optional_mapping(value: object) -> dict[str, object] | None:
    if value is None:
        return None
    if not isinstance(value, dict):
        raise TypeError("Safe snapshot sections must be dictionaries.")
    return dict(value)


assert set(PLANNED_SECTIONS).issubset(set(DISPLAYED_SECTIONS))
