"""Pure contract preflight for future Toss API client work.

This module intentionally defines shapes, flags, and redaction helpers only.
It does not create a live client, read credentials, build URLs, or perform I/O.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping


TOSS_API_CLIENT_CONTRACT_VERSION = "MS-14.00"
TOSS_API_CLIENT_CONTRACT_SCOPE = "pure_no_io_toss_api_client_contract_preflight"

ALLOWED_ENDPOINT_KINDS = (
    "read_only_market_data_placeholder",
    "contract_only_endpoint_id",
)
FORBIDDEN_ENDPOINT_KINDS = (
    "oauth_token",
    "account",
    "account_assets",
    "balance",
    "fills",
    "order",
    "live_http",
    "llm",
    "recommendation",
    "ranking",
)
ALLOWED_REQUEST_FIELDS = (
    "method",
    "endpoint_kind",
    "query_shape",
    "body_shape",
    "header_shape",
    "timeout_policy",
    "retry_policy",
    "idempotency_policy",
    "redaction_required",
    "dry_run_only",
    "live_call_allowed",
)
FORBIDDEN_REQUEST_FIELDS = (
    "url",
    "base_url",
    "oauth_url",
    "token_endpoint",
    "authorization",
    "bearer",
    "access_token",
    "accountSeq",
    "account_seq",
    "order_id",
    "account_balance",
    "holdings",
    "fills",
    "raw_request",
)
ALLOWED_RESPONSE_FIELDS = (
    "normalized_status",
    "status_code_shape",
    "response_kind",
    "normalized_body_shape",
    "error_shape",
    "redacted_body_preview",
    "diagnostics",
    "raw_payload_allowed",
)
FORBIDDEN_RESPONSE_FIELDS = (
    "raw_response",
    "raw_request",
    "db_row",
    "authorization",
    "bearer",
    "access_token",
    "accountSeq",
    "account_seq",
    "account_balance",
    "holdings",
    "fills",
    "order_id",
)
SENSITIVE_FIELD_NAMES = (
    "access_token",
    "refresh_token",
    "authorization",
    "bearer",
    "api_key",
    "secret_key",
    "client_secret",
    "app_key",
    "app_secret",
    "token",
    "accountSeq",
    "account_seq",
    "account_number",
    "account_balance",
    "holdings",
    "fills",
    "order_id",
    "raw_response",
    "raw_request",
    "db_row",
    "file_path",
    "env_path",
    ".env.local",
)
ERROR_KINDS = (
    "configuration_missing",
    "credential_unavailable",
    "oauth_not_allowed",
    "network_not_allowed",
    "endpoint_not_allowed",
    "account_seq_not_allowed",
    "order_not_allowed",
    "account_asset_not_allowed",
    "raw_payload_blocked",
    "redaction_failed",
    "unknown_contract_error",
)


@dataclass(frozen=True)
class TossApiExternalCapabilityFlags:
    """Flags proving that MS-14.00 has no external runtime capability."""

    live_http_ready: bool
    fake_transport_ready: bool
    oauth_ready: bool
    credential_required_now: bool
    account_seq_required_now: bool
    order_required_now: bool
    db_required_now: bool
    streamlit_required: bool
    http_smoke_required: bool
    llm_required: bool
    recommendation_required: bool
    ranking_required: bool


@dataclass(frozen=True)
class TossApiCredentialNamePolicy:
    """Symbolic credential field-name policy without credential values."""

    credential_field_names: tuple[str, ...]
    required_now: bool
    read_from_env_now: bool
    read_from_file_now: bool
    print_allowed: bool
    raw_value_allowed: bool
    mask_required: bool


@dataclass(frozen=True)
class TossApiEndpointContract:
    """Symbolic endpoint contract with no concrete URL or path."""

    endpoint_id: str
    endpoint_kind: str
    description: str
    symbolic_only: bool
    allowed: bool
    live_http_ready: bool
    fake_transport_ready: bool
    oauth_ready: bool
    account_seq_required_now: bool
    order_required_now: bool


@dataclass(frozen=True)
class TossApiRequestContract:
    """Request shape contract that cannot execute a live request."""

    method: str
    endpoint_kind: str
    query_shape: tuple[str, ...]
    body_shape: tuple[str, ...]
    header_shape: tuple[str, ...]
    timeout_policy: str
    retry_policy: str
    idempotency_policy: str
    redaction_required: bool
    dry_run_only: bool
    live_call_allowed: bool


@dataclass(frozen=True)
class TossApiResponseContract:
    """Response normalization contract that blocks raw payload output."""

    normalized_status: str
    status_code_shape: str
    response_kind: str
    normalized_body_shape: tuple[str, ...]
    error_shape: tuple[str, ...]
    redacted_body_preview: Mapping[str, object]
    diagnostics: tuple[str, ...]
    raw_payload_allowed: bool


@dataclass(frozen=True)
class TossApiErrorContract:
    """Symbolic error shape contract."""

    error_kind: str
    message: str
    retryable: bool
    safe_to_display: bool
    raw_payload_allowed: bool


@dataclass(frozen=True)
class TossApiRedactionPolicy:
    """Sensitive field policy for deterministic masking."""

    sensitive_field_names: tuple[str, ...]
    redaction_placeholder: str
    raw_payload_policy: str
    block_raw_payload_fields: bool
    preserve_unknown_fields: bool


@dataclass(frozen=True)
class TossApiRedactionResult:
    """Result of redacting a single value or mapping."""

    value: object
    redacted: bool
    blocked: bool
    field_name: str


@dataclass(frozen=True)
class TossApiClientContractPolicy:
    """Top-level Toss API client contract policy."""

    contract_version: str
    contract_scope: str
    no_network: bool
    no_oauth: bool
    no_credentials: bool
    no_account_seq: bool
    no_orders: bool
    no_account_assets: bool
    no_balance: bool
    no_fills: bool
    no_db: bool
    no_file_io: bool
    no_streamlit: bool
    no_llm: bool
    no_recommendation: bool
    no_ranking: bool
    allowed_endpoint_kinds: tuple[str, ...]
    forbidden_endpoint_kinds: tuple[str, ...]
    allowed_request_fields: tuple[str, ...]
    forbidden_request_fields: tuple[str, ...]
    allowed_response_fields: tuple[str, ...]
    forbidden_response_fields: tuple[str, ...]
    sensitive_field_names: tuple[str, ...]
    redaction_placeholder: str
    raw_payload_policy: str
    observation_only_notes: tuple[str, ...]


@dataclass(frozen=True)
class TossApiContractValidationResult:
    """Validation result for the contract preflight."""

    passed: bool
    failures: tuple[str, ...]
    checked_policy_flags: tuple[str, ...]
    checked_endpoint_kinds: tuple[str, ...]
    checked_request_fields: tuple[str, ...]
    checked_response_fields: tuple[str, ...]
    checked_error_kinds: tuple[str, ...]
    checked_redaction_fields: tuple[str, ...]
    diagnostics: tuple[str, ...]


def build_toss_api_external_capability_flags() -> TossApiExternalCapabilityFlags:
    """Return the false external-capability contract for MS-14.00."""

    return TossApiExternalCapabilityFlags(
        live_http_ready=False,
        fake_transport_ready=False,
        oauth_ready=False,
        credential_required_now=False,
        account_seq_required_now=False,
        order_required_now=False,
        db_required_now=False,
        streamlit_required=False,
        http_smoke_required=False,
        llm_required=False,
        recommendation_required=False,
        ranking_required=False,
    )


def build_toss_api_credential_name_policy() -> TossApiCredentialNamePolicy:
    """Return symbolic credential names without values or loaders."""

    return TossApiCredentialNamePolicy(
        credential_field_names=(
            "app_key_name",
            "app_secret_name",
            "access_token_name",
            "refresh_token_name",
        ),
        required_now=False,
        read_from_env_now=False,
        read_from_file_now=False,
        print_allowed=False,
        raw_value_allowed=False,
        mask_required=True,
    )


def build_toss_api_redaction_policy() -> TossApiRedactionPolicy:
    """Return deterministic redaction policy."""

    return TossApiRedactionPolicy(
        sensitive_field_names=SENSITIVE_FIELD_NAMES,
        redaction_placeholder="[REDACTED]",
        raw_payload_policy="blocked_without_storage_or_output",
        block_raw_payload_fields=True,
        preserve_unknown_fields=True,
    )


def build_toss_api_client_contract_policy() -> TossApiClientContractPolicy:
    """Return the top-level no-I/O client contract policy."""

    return TossApiClientContractPolicy(
        contract_version=TOSS_API_CLIENT_CONTRACT_VERSION,
        contract_scope=TOSS_API_CLIENT_CONTRACT_SCOPE,
        no_network=True,
        no_oauth=True,
        no_credentials=True,
        no_account_seq=True,
        no_orders=True,
        no_account_assets=True,
        no_balance=True,
        no_fills=True,
        no_db=True,
        no_file_io=True,
        no_streamlit=True,
        no_llm=True,
        no_recommendation=True,
        no_ranking=True,
        allowed_endpoint_kinds=ALLOWED_ENDPOINT_KINDS,
        forbidden_endpoint_kinds=FORBIDDEN_ENDPOINT_KINDS,
        allowed_request_fields=ALLOWED_REQUEST_FIELDS,
        forbidden_request_fields=FORBIDDEN_REQUEST_FIELDS,
        allowed_response_fields=ALLOWED_RESPONSE_FIELDS,
        forbidden_response_fields=FORBIDDEN_RESPONSE_FIELDS,
        sensitive_field_names=SENSITIVE_FIELD_NAMES,
        redaction_placeholder="[REDACTED]",
        raw_payload_policy="blocked_without_storage_or_output",
        observation_only_notes=(
            "contract_shapes_only",
            "no_live_http",
            "no_oauth_token_issuance",
            "no_credentials_loaded",
            "no_account_seq",
            "no_order_account_balance_or_fill_access",
        ),
    )


def build_symbolic_toss_api_endpoint_contracts() -> tuple[TossApiEndpointContract, ...]:
    """Return symbolic endpoint contracts without concrete URL/path values."""

    return (
        TossApiEndpointContract(
            endpoint_id="market_data_contract_only",
            endpoint_kind="read_only_market_data_placeholder",
            description="Symbolic read-only market data contract placeholder",
            symbolic_only=True,
            allowed=True,
            live_http_ready=False,
            fake_transport_ready=False,
            oauth_ready=False,
            account_seq_required_now=False,
            order_required_now=False,
        ),
        TossApiEndpointContract(
            endpoint_id="generic_contract_only",
            endpoint_kind="contract_only_endpoint_id",
            description="Generic symbolic endpoint id for future contract tests",
            symbolic_only=True,
            allowed=True,
            live_http_ready=False,
            fake_transport_ready=False,
            oauth_ready=False,
            account_seq_required_now=False,
            order_required_now=False,
        ),
    )


def build_toss_api_request_contract(
    endpoint_kind: str = "read_only_market_data_placeholder",
) -> TossApiRequestContract:
    """Return a dry-run-only request contract shape."""

    return TossApiRequestContract(
        method="SYMBOLIC_METHOD",
        endpoint_kind=endpoint_kind,
        query_shape=("symbolic_query_fields_only",),
        body_shape=(),
        header_shape=("redacted_header_names_only",),
        timeout_policy="shape_only_no_runtime_timeout",
        retry_policy="shape_only_no_retry_execution",
        idempotency_policy="shape_only_no_operation_execution",
        redaction_required=True,
        dry_run_only=True,
        live_call_allowed=False,
    )


def build_toss_api_response_contract() -> TossApiResponseContract:
    """Return a normalized response contract with raw payload blocked."""

    return TossApiResponseContract(
        normalized_status="contract_shape_only",
        status_code_shape="symbolic_status_code",
        response_kind="normalized_contract_response",
        normalized_body_shape=("redacted_body_preview",),
        error_shape=("error_kind", "safe_message"),
        redacted_body_preview={"status": "contract_only"},
        diagnostics=("raw_payload_blocked", "no_token_or_account_output"),
        raw_payload_allowed=False,
    )


def build_toss_api_error_contracts() -> tuple[TossApiErrorContract, ...]:
    """Return symbolic error contracts."""

    retryable = {"network_not_allowed", "unknown_contract_error"}
    return tuple(
        TossApiErrorContract(
            error_kind=error_kind,
            message=f"{error_kind}_contract_shape",
            retryable=error_kind in retryable,
            safe_to_display=True,
            raw_payload_allowed=False,
        )
        for error_kind in ERROR_KINDS
    )


def redact_sensitive_value(
    field_name: str,
    value: object,
    policy: TossApiRedactionPolicy | None = None,
) -> TossApiRedactionResult:
    """Redact a value when its field name is sensitive."""

    active_policy = policy or build_toss_api_redaction_policy()
    field_is_sensitive = _is_sensitive_field_name(field_name, active_policy)
    if field_is_sensitive:
        return TossApiRedactionResult(
            value=active_policy.redaction_placeholder,
            redacted=True,
            blocked=_is_raw_payload_field(field_name),
            field_name=field_name,
        )
    return TossApiRedactionResult(
        value=value,
        redacted=False,
        blocked=False,
        field_name=field_name,
    )


def redact_mapping(
    values: Mapping[str, object],
    policy: TossApiRedactionPolicy | None = None,
) -> Mapping[str, object]:
    """Return a redacted copy of a mapping."""

    active_policy = policy or build_toss_api_redaction_policy()
    return {
        key: redact_sensitive_value(key, value, active_policy).value
        for key, value in values.items()
    }


def validate_no_sensitive_output(
    values: Mapping[str, object],
    policy: TossApiRedactionPolicy | None = None,
) -> TossApiContractValidationResult:
    """Validate that a mapping does not expose sensitive values."""

    active_policy = policy or build_toss_api_redaction_policy()
    failures = tuple(
        f"sensitive_field_exposed:{key}"
        for key in values
        if _is_sensitive_field_name(key, active_policy)
        and values[key] != active_policy.redaction_placeholder
    )
    return TossApiContractValidationResult(
        passed=not failures,
        failures=failures,
        checked_policy_flags=(),
        checked_endpoint_kinds=(),
        checked_request_fields=(),
        checked_response_fields=tuple(values),
        checked_error_kinds=(),
        checked_redaction_fields=active_policy.sensitive_field_names,
        diagnostics=("sensitive_output_validation",),
    )


def validate_toss_api_endpoint_contract(
    endpoint: TossApiEndpointContract,
    policy: TossApiClientContractPolicy | None = None,
) -> TossApiContractValidationResult:
    """Validate one symbolic endpoint contract."""

    active_policy = policy or build_toss_api_client_contract_policy()
    failures: list[str] = []
    if endpoint.endpoint_kind not in active_policy.allowed_endpoint_kinds:
        failures.append(f"endpoint_kind_not_allowed:{endpoint.endpoint_kind}")
    if endpoint.endpoint_kind in active_policy.forbidden_endpoint_kinds:
        failures.append(f"endpoint_kind_forbidden:{endpoint.endpoint_kind}")
    if not endpoint.symbolic_only:
        failures.append("endpoint_must_be_symbolic_only")
    if endpoint.live_http_ready:
        failures.append("live_http_ready_must_be_false")
    if endpoint.oauth_ready:
        failures.append("oauth_ready_must_be_false")
    if endpoint.account_seq_required_now:
        failures.append("account_seq_required_now_must_be_false")
    if endpoint.order_required_now:
        failures.append("order_required_now_must_be_false")

    return TossApiContractValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=("no_network", "no_oauth", "no_account_seq"),
        checked_endpoint_kinds=(endpoint.endpoint_kind,),
        checked_request_fields=(),
        checked_response_fields=(),
        checked_error_kinds=(),
        checked_redaction_fields=active_policy.sensitive_field_names,
        diagnostics=("symbolic_endpoint_contract_validation",),
    )


def validate_toss_api_request_contract(
    request_contract: TossApiRequestContract,
    policy: TossApiClientContractPolicy | None = None,
) -> TossApiContractValidationResult:
    """Validate one dry-run request contract."""

    active_policy = policy or build_toss_api_client_contract_policy()
    failures: list[str] = []
    if request_contract.endpoint_kind not in active_policy.allowed_endpoint_kinds:
        failures.append(
            f"request_endpoint_kind_not_allowed:{request_contract.endpoint_kind}"
        )
    if not request_contract.redaction_required:
        failures.append("redaction_required_must_be_true")
    if not request_contract.dry_run_only:
        failures.append("dry_run_only_must_be_true")
    if request_contract.live_call_allowed:
        failures.append("live_call_allowed_must_be_false")
    for field_name in (
        *request_contract.query_shape,
        *request_contract.body_shape,
        *request_contract.header_shape,
    ):
        if field_name in active_policy.forbidden_request_fields:
            failures.append(f"forbidden_request_field:{field_name}")

    return TossApiContractValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=("redaction_required", "dry_run_only"),
        checked_endpoint_kinds=(request_contract.endpoint_kind,),
        checked_request_fields=active_policy.allowed_request_fields,
        checked_response_fields=(),
        checked_error_kinds=(),
        checked_redaction_fields=active_policy.sensitive_field_names,
        diagnostics=("dry_run_request_contract_validation",),
    )


def validate_toss_api_response_contract(
    response_contract: TossApiResponseContract,
    policy: TossApiClientContractPolicy | None = None,
) -> TossApiContractValidationResult:
    """Validate one normalized response contract."""

    active_policy = policy or build_toss_api_client_contract_policy()
    failures: list[str] = []
    if response_contract.raw_payload_allowed:
        failures.append("raw_payload_allowed_must_be_false")
    sensitive_result = validate_no_sensitive_output(
        response_contract.redacted_body_preview,
        build_toss_api_redaction_policy(),
    )
    failures.extend(sensitive_result.failures)

    return TossApiContractValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=("raw_payload_allowed", "redaction_required"),
        checked_endpoint_kinds=(),
        checked_request_fields=(),
        checked_response_fields=active_policy.allowed_response_fields,
        checked_error_kinds=(),
        checked_redaction_fields=active_policy.sensitive_field_names,
        diagnostics=("normalized_response_contract_validation",),
    )


def validate_toss_api_client_contract_policy(
    policy: TossApiClientContractPolicy | None = None,
) -> TossApiContractValidationResult:
    """Validate the top-level client contract policy."""

    active_policy = policy or build_toss_api_client_contract_policy()
    required_true_flags = (
        "no_network",
        "no_oauth",
        "no_credentials",
        "no_account_seq",
        "no_orders",
        "no_account_assets",
        "no_balance",
        "no_fills",
        "no_db",
        "no_file_io",
        "no_streamlit",
        "no_llm",
        "no_recommendation",
        "no_ranking",
    )
    failures = tuple(
        f"{flag}_must_be_true"
        for flag in required_true_flags
        if not getattr(active_policy, flag)
    )

    return TossApiContractValidationResult(
        passed=not failures,
        failures=failures,
        checked_policy_flags=required_true_flags,
        checked_endpoint_kinds=active_policy.allowed_endpoint_kinds,
        checked_request_fields=active_policy.allowed_request_fields,
        checked_response_fields=active_policy.allowed_response_fields,
        checked_error_kinds=ERROR_KINDS,
        checked_redaction_fields=active_policy.sensitive_field_names,
        diagnostics=("client_contract_policy_validation",),
    )


def run_toss_api_client_contract_preflight_checks() -> (
    TossApiContractValidationResult
):
    """Run the deterministic no-I/O contract preflight checks."""

    policy = build_toss_api_client_contract_policy()
    capability_flags = build_toss_api_external_capability_flags()
    credential_policy = build_toss_api_credential_name_policy()
    endpoint_results = tuple(
        validate_toss_api_endpoint_contract(endpoint, policy)
        for endpoint in build_symbolic_toss_api_endpoint_contracts()
    )
    request_result = validate_toss_api_request_contract(
        build_toss_api_request_contract(), policy
    )
    response_result = validate_toss_api_response_contract(
        build_toss_api_response_contract(), policy
    )
    policy_result = validate_toss_api_client_contract_policy(policy)

    failures: list[str] = []
    for result in (*endpoint_results, request_result, response_result, policy_result):
        failures.extend(result.failures)

    false_flag_names = tuple(
        name for name, value in capability_flags.__dict__.items() if value is False
    )
    expected_false_flags = tuple(capability_flags.__dict__)
    if false_flag_names != expected_false_flags:
        failures.append("external_capability_flags_must_all_be_false")
    if credential_policy.required_now:
        failures.append("credential_required_now_must_be_false")
    if not credential_policy.mask_required:
        failures.append("credential_mask_required_must_be_true")
    if credential_policy.raw_value_allowed:
        failures.append("credential_raw_value_allowed_must_be_false")

    return TossApiContractValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=(
            *policy_result.checked_policy_flags,
            *expected_false_flags,
            "credential_required_now",
            "mask_required",
            "raw_value_allowed",
        ),
        checked_endpoint_kinds=policy.allowed_endpoint_kinds,
        checked_request_fields=policy.allowed_request_fields,
        checked_response_fields=policy.allowed_response_fields,
        checked_error_kinds=ERROR_KINDS,
        checked_redaction_fields=policy.sensitive_field_names,
        diagnostics=(
            "pure_no_io_contract_preflight",
            "symbolic_endpoint_contract_only",
            "raw_payload_blocked",
            "sensitive_fields_redacted",
        ),
    )


def _is_sensitive_field_name(
    field_name: str,
    policy: TossApiRedactionPolicy,
) -> bool:
    normalized = field_name.casefold()
    return any(
        normalized == sensitive.casefold()
        for sensitive in policy.sensitive_field_names
    )


def _is_raw_payload_field(field_name: str) -> bool:
    return field_name in {"raw_response", "raw_request", "db_row"}
