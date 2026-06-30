"""No-I/O preflight for a future live snapshot local SQLite file smoke.

This module builds and validates immutable metadata only. It does not inspect
the filesystem, load configuration, open SQLite, construct API clients, or
send network requests.
"""

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import PurePosixPath

STAGE = "MS-06.08"
PLANNED_DB_RELATIVE_PATH = "data/local/ai_stock.sqlite3"
NEXT_STAGE_CREDENTIAL_SOURCE = "existing .env.local only"
REQUIRED_IGNORE_PATTERNS = ("data/", "*.sqlite", "*.sqlite3", "*.db")

STOCK_SYMBOL = "005930"
EXCHANGE_RATE_PAIR = "USD/KRW"
CANDLE_INTERVAL = "1d"
CANDLE_COUNT = 1
CANDLE_ADJUSTED = True


@dataclass(frozen=True, slots=True)
class PlannedBusinessEndpoint:
    """Fixed read-only endpoint metadata for the separately approved stage."""

    method: str
    path: str
    endpoint_category: str
    query: tuple[tuple[str, str], ...]
    requires_auth: bool = True
    requires_account_seq: bool = False
    is_read_only: bool = True


@dataclass(frozen=True, slots=True)
class SnapshotAppendUpsertPolicy:
    """Persistence policy for a later live file DB smoke."""

    schema_initialization_idempotent_required: bool
    existing_db_delete_allowed: bool
    existing_db_overwrite_allowed: bool
    stock_info_write_mode: str
    price_snapshot_write_mode: str
    candle_write_mode: str
    exchange_rate_write_mode: str
    post_write_verification: str
    raw_response_body_storage_allowed: bool
    credential_storage_allowed: bool
    access_token_storage_allowed: bool
    authorization_header_storage_allowed: bool
    db_content_dump_allowed: bool


@dataclass(frozen=True, slots=True)
class LiveSnapshotLocalDbPreflightPlan:
    """Immutable MS-06.08 policy for a future live file DB smoke."""

    stage: str
    planned_db_relative_path: str
    db_file_write_allowed_this_stage: bool
    actual_db_file_modified_this_stage: bool
    existing_db_file_allowed: bool
    db_file_git_tracked_allowed: bool
    data_directory_git_tracked_allowed: bool
    api_call_allowed_this_stage: bool
    oauth_token_endpoint_allowed_this_stage: bool
    live_smoke_execution_allowed_this_stage: bool
    env_file_read_allowed_this_stage: bool
    credential_required_this_stage: bool
    next_stage_credential_source: str
    account_seq_allowed: bool
    real_order_related_call_allowed: bool
    stock_warnings_included: bool
    stock_warnings_deferred: bool
    expected_oauth_token_endpoint_calls: int
    expected_business_api_calls: int
    expected_total_network_calls: int
    allowed_business_endpoints: tuple[PlannedBusinessEndpoint, ...]
    denied_endpoints: tuple[str, ...]
    required_ignore_patterns: tuple[str, ...]
    append_upsert_policy: SnapshotAppendUpsertPolicy


@dataclass(frozen=True, slots=True)
class LiveSnapshotLocalDbPreflightResult:
    """Safe result derived only from caller-supplied observations."""

    planned_path_is_expected: bool
    planned_path_is_repo_relative: bool
    existing_db_state_allowed: bool
    db_write_disabled_this_stage: bool
    db_file_unmodified_this_stage: bool
    git_tracking_policy_satisfied: bool
    git_ignore_policy_satisfied: bool
    missing_ignore_patterns: tuple[str, ...]
    external_actions_disabled_this_stage: bool
    next_stage_call_scope_valid: bool
    append_upsert_policy_valid: bool
    preflight_contract_valid: bool
    ready_for_separately_approved_next_stage: bool
    observed_db_file_exists: bool
    safe_message: str


_ALLOWED_BUSINESS_ENDPOINTS = (
    PlannedBusinessEndpoint(
        method="GET",
        path="/api/v1/stocks",
        endpoint_category="stock_info",
        query=(("symbols", STOCK_SYMBOL),),
    ),
    PlannedBusinessEndpoint(
        method="GET",
        path="/api/v1/prices",
        endpoint_category="market_data",
        query=(("symbols", STOCK_SYMBOL),),
    ),
    PlannedBusinessEndpoint(
        method="GET",
        path="/api/v1/candles",
        endpoint_category="market_data",
        query=(
            ("symbol", STOCK_SYMBOL),
            ("interval", CANDLE_INTERVAL),
            ("count", str(CANDLE_COUNT)),
            ("adjusted", "true"),
        ),
    ),
    PlannedBusinessEndpoint(
        method="GET",
        path="/api/v1/exchange-rate",
        endpoint_category="market_info",
        query=(("baseCurrency", "USD"), ("quoteCurrency", "KRW")),
    ),
)

_DENIED_ENDPOINTS = (
    "GET /api/v1/stocks/{symbol}/warnings",
    "POST /api/v1/orders",
    "GET /api/v1/orders",
    "GET /api/v1/accounts",
    "GET /api/v1/assets",
    "GET /api/v1/balance",
    "GET /api/v1/fills",
    "PATCH /api/v1/prices",
)

_APPEND_UPSERT_POLICY = SnapshotAppendUpsertPolicy(
    schema_initialization_idempotent_required=True,
    existing_db_delete_allowed=False,
    existing_db_overwrite_allowed=False,
    stock_info_write_mode="upsert",
    price_snapshot_write_mode="insert",
    candle_write_mode="insert",
    exchange_rate_write_mode="insert",
    post_write_verification="repository_count_delta_or_minimum_presence_and_timestamp",
    raw_response_body_storage_allowed=False,
    credential_storage_allowed=False,
    access_token_storage_allowed=False,
    authorization_header_storage_allowed=False,
    db_content_dump_allowed=False,
)


def build_live_snapshot_local_db_preflight() -> LiveSnapshotLocalDbPreflightPlan:
    """Build the fixed MS-06.08 plan without external or storage I/O."""

    return LiveSnapshotLocalDbPreflightPlan(
        stage=STAGE,
        planned_db_relative_path=PLANNED_DB_RELATIVE_PATH,
        db_file_write_allowed_this_stage=False,
        actual_db_file_modified_this_stage=False,
        existing_db_file_allowed=True,
        db_file_git_tracked_allowed=False,
        data_directory_git_tracked_allowed=False,
        api_call_allowed_this_stage=False,
        oauth_token_endpoint_allowed_this_stage=False,
        live_smoke_execution_allowed_this_stage=False,
        env_file_read_allowed_this_stage=False,
        credential_required_this_stage=False,
        next_stage_credential_source=NEXT_STAGE_CREDENTIAL_SOURCE,
        account_seq_allowed=False,
        real_order_related_call_allowed=False,
        stock_warnings_included=False,
        stock_warnings_deferred=True,
        expected_oauth_token_endpoint_calls=1,
        expected_business_api_calls=len(_ALLOWED_BUSINESS_ENDPOINTS),
        expected_total_network_calls=1 + len(_ALLOWED_BUSINESS_ENDPOINTS),
        allowed_business_endpoints=_ALLOWED_BUSINESS_ENDPOINTS,
        denied_endpoints=_DENIED_ENDPOINTS,
        required_ignore_patterns=REQUIRED_IGNORE_PATTERNS,
        append_upsert_policy=_APPEND_UPSERT_POLICY,
    )


def validate_live_snapshot_local_db_preflight(
    plan: LiveSnapshotLocalDbPreflightPlan,
    *,
    observed_ignore_patterns: Iterable[str],
    observed_db_file_exists: bool,
    observed_db_file_modified_this_stage: bool,
    observed_db_file_git_tracked: bool,
    observed_data_directory_git_tracked: bool,
) -> LiveSnapshotLocalDbPreflightResult:
    """Validate policy using explicit observations without performing I/O."""

    normalized_path = plan.planned_db_relative_path.replace("\\", "/")
    planned_path = PurePosixPath(normalized_path)
    planned_path_is_expected = normalized_path == PLANNED_DB_RELATIVE_PATH
    planned_path_is_repo_relative = (
        not planned_path.is_absolute()
        and ".." not in planned_path.parts
        and planned_path.parts[:2] == ("data", "local")
    )
    existing_db_state_allowed = (
        plan.existing_db_file_allowed or not observed_db_file_exists
    )
    db_write_disabled_this_stage = plan.db_file_write_allowed_this_stage is False
    db_file_unmodified_this_stage = all(
        value is False
        for value in (
            plan.actual_db_file_modified_this_stage,
            observed_db_file_modified_this_stage,
        )
    )
    git_tracking_policy_satisfied = all(
        value is False
        for value in (
            plan.db_file_git_tracked_allowed,
            plan.data_directory_git_tracked_allowed,
            observed_db_file_git_tracked,
            observed_data_directory_git_tracked,
        )
    )

    observed_patterns = {
        pattern.strip()
        for pattern in observed_ignore_patterns
        if pattern and pattern.strip()
    }
    missing_ignore_patterns = tuple(
        pattern
        for pattern in plan.required_ignore_patterns
        if pattern not in observed_patterns
    )
    git_ignore_policy_satisfied = (
        plan.required_ignore_patterns == REQUIRED_IGNORE_PATTERNS
        and not missing_ignore_patterns
    )
    external_actions_disabled_this_stage = all(
        value is False
        for value in (
            plan.api_call_allowed_this_stage,
            plan.oauth_token_endpoint_allowed_this_stage,
            plan.live_smoke_execution_allowed_this_stage,
            plan.env_file_read_allowed_this_stage,
            plan.credential_required_this_stage,
            plan.account_seq_allowed,
            plan.real_order_related_call_allowed,
            plan.stock_warnings_included,
        )
    ) and plan.stock_warnings_deferred
    next_stage_call_scope_valid = _next_stage_call_scope_is_valid(plan)
    append_upsert_policy_valid = plan.append_upsert_policy == _APPEND_UPSERT_POLICY

    preflight_contract_valid = all(
        (
            plan.stage == STAGE,
            planned_path_is_expected,
            planned_path_is_repo_relative,
            existing_db_state_allowed,
            db_write_disabled_this_stage,
            db_file_unmodified_this_stage,
            git_tracking_policy_satisfied,
            git_ignore_policy_satisfied,
            external_actions_disabled_this_stage,
            plan.next_stage_credential_source == NEXT_STAGE_CREDENTIAL_SOURCE,
            next_stage_call_scope_valid,
            append_upsert_policy_valid,
        )
    )
    safe_message = (
        "Live snapshot file DB preflight is valid; this stage remains no-I/O."
        if preflight_contract_valid
        else "Live snapshot file DB preflight failed; next-stage execution is blocked."
    )

    return LiveSnapshotLocalDbPreflightResult(
        planned_path_is_expected=planned_path_is_expected,
        planned_path_is_repo_relative=planned_path_is_repo_relative,
        existing_db_state_allowed=existing_db_state_allowed,
        db_write_disabled_this_stage=db_write_disabled_this_stage,
        db_file_unmodified_this_stage=db_file_unmodified_this_stage,
        git_tracking_policy_satisfied=git_tracking_policy_satisfied,
        git_ignore_policy_satisfied=git_ignore_policy_satisfied,
        missing_ignore_patterns=missing_ignore_patterns,
        external_actions_disabled_this_stage=external_actions_disabled_this_stage,
        next_stage_call_scope_valid=next_stage_call_scope_valid,
        append_upsert_policy_valid=append_upsert_policy_valid,
        preflight_contract_valid=preflight_contract_valid,
        ready_for_separately_approved_next_stage=preflight_contract_valid,
        observed_db_file_exists=observed_db_file_exists,
        safe_message=safe_message,
    )


def _next_stage_call_scope_is_valid(
    plan: LiveSnapshotLocalDbPreflightPlan,
) -> bool:
    return all(
        (
            plan.expected_oauth_token_endpoint_calls == 1,
            plan.expected_business_api_calls == 4,
            plan.expected_total_network_calls == 5,
            plan.allowed_business_endpoints == _ALLOWED_BUSINESS_ENDPOINTS,
            plan.denied_endpoints == _DENIED_ENDPOINTS,
            all(
                endpoint.method == "GET"
                and endpoint.requires_auth
                and not endpoint.requires_account_seq
                and endpoint.is_read_only
                for endpoint in plan.allowed_business_endpoints
            ),
        )
    )
