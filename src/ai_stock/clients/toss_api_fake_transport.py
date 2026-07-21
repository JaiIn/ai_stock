"""Pure fake transport fixtures for the Toss API client contract.

This module is deterministic and in-memory only. It reuses the MS-14.00
contract shapes without creating live HTTP, credential, account, or storage
capability.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ai_stock.clients.toss_api_client_contract import (
    TossApiClientContractPolicy,
    TossApiExternalCapabilityFlags,
    TossApiRedactionPolicy,
    build_symbolic_toss_api_endpoint_contracts,
    build_toss_api_client_contract_policy,
    build_toss_api_external_capability_flags,
    build_toss_api_redaction_policy,
    redact_mapping,
    run_toss_api_client_contract_preflight_checks,
    validate_no_sensitive_output,
)


TOSS_API_FAKE_TRANSPORT_VERSION = "MS-14.01"
TOSS_API_FAKE_TRANSPORT_SCOPE = (
    "pure_no_io_toss_api_fake_transport_response_fixtures"
)

FAKE_FIXTURE_NAMES = (
    "market_data_ok_placeholder",
    "market_data_empty_placeholder",
    "market_data_error_placeholder",
    "rate_limited_placeholder",
    "redaction_required_placeholder",
    "endpoint_not_allowed_placeholder",
)


@dataclass(frozen=True)
class TossApiFakeTransportPolicy:
    """Policy proving that fake transport is in-memory and no-I/O only."""

    fake_transport_version: str
    fake_transport_scope: str
    uses_contract_policy: bool
    contract_policy: TossApiClientContractPolicy
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
    fake_transport_ready: bool
    live_http_ready: bool
    oauth_ready: bool
    credential_required_now: bool
    account_seq_required_now: bool
    order_required_now: bool
    streamlit_required: bool
    http_smoke_required: bool
    raw_payload_allowed: bool
    redaction_required: bool
    observation_only_notes: tuple[str, ...]


@dataclass(frozen=True)
class TossApiFakeRequest:
    """Symbolic request shape that cannot perform live network work."""

    request_id: str
    endpoint_kind: str
    symbolic_method: str
    query_shape: tuple[str, ...]
    body_shape: tuple[str, ...]
    header_shape: tuple[str, ...]
    dry_run_only: bool
    live_call_allowed: bool
    redaction_required: bool


@dataclass(frozen=True)
class TossApiFakeResponse:
    """Contract-safe fake response preview with no raw payload."""

    fixture_name: str
    endpoint_kind: str
    normalized_status: str
    response_kind: str
    status_code_shape: str
    redacted_body_preview: Mapping[str, object]
    diagnostics: tuple[str, ...]
    raw_payload_allowed: bool
    sensitive_output_present: bool


@dataclass(frozen=True)
class TossApiFakeFixture:
    """In-memory fixture joining symbolic fake input and safe output."""

    fixture_name: str
    description: str
    fake_request: TossApiFakeRequest
    fake_response: TossApiFakeResponse
    expected_passed: bool
    expected_failures: tuple[str, ...]
    expected_diagnostics: tuple[str, ...]


@dataclass(frozen=True)
class TossApiFakeTransportResult:
    """Result returned by the fake transport runner."""

    passed: bool
    fixture_name: str
    endpoint_kind: str
    normalized_status: str
    response_kind: str
    redacted_body_preview: Mapping[str, object]
    diagnostics: tuple[str, ...]
    failures: tuple[str, ...]
    capability_flags: TossApiExternalCapabilityFlags


@dataclass(frozen=True)
class TossApiFakeTransportValidationResult:
    """Validation result for fake transport policy and fixtures."""

    passed: bool
    failures: tuple[str, ...]
    checked_fixture_names: tuple[str, ...]
    checked_endpoint_kinds: tuple[str, ...]
    checked_policy_flags: tuple[str, ...]
    checked_response_kinds: tuple[str, ...]
    checked_redaction_fields: tuple[str, ...]
    diagnostics: tuple[str, ...]


def build_toss_api_fake_transport_policy(
    contract_policy: TossApiClientContractPolicy | None = None,
) -> TossApiFakeTransportPolicy:
    """Return the MS-14.01 fake transport policy."""

    active_contract_policy = contract_policy or build_toss_api_client_contract_policy()
    return TossApiFakeTransportPolicy(
        fake_transport_version=TOSS_API_FAKE_TRANSPORT_VERSION,
        fake_transport_scope=TOSS_API_FAKE_TRANSPORT_SCOPE,
        uses_contract_policy=True,
        contract_policy=active_contract_policy,
        no_network=active_contract_policy.no_network,
        no_oauth=active_contract_policy.no_oauth,
        no_credentials=active_contract_policy.no_credentials,
        no_account_seq=active_contract_policy.no_account_seq,
        no_orders=active_contract_policy.no_orders,
        no_account_assets=active_contract_policy.no_account_assets,
        no_balance=active_contract_policy.no_balance,
        no_fills=active_contract_policy.no_fills,
        no_db=active_contract_policy.no_db,
        no_file_io=active_contract_policy.no_file_io,
        no_streamlit=active_contract_policy.no_streamlit,
        no_llm=active_contract_policy.no_llm,
        no_recommendation=active_contract_policy.no_recommendation,
        no_ranking=active_contract_policy.no_ranking,
        fake_transport_ready=True,
        live_http_ready=False,
        oauth_ready=False,
        credential_required_now=False,
        account_seq_required_now=False,
        order_required_now=False,
        streamlit_required=False,
        http_smoke_required=False,
        raw_payload_allowed=False,
        redaction_required=True,
        observation_only_notes=(
            "fake_transport_in_memory_only",
            "contract_safe_preview_only",
            "no_live_http",
            "no_credential_or_account_input",
            "no_trading_or_asset_capability",
        ),
    )


def build_toss_api_fake_request(
    endpoint_kind: str = "read_only_market_data_placeholder",
    request_id: str = "fake_market_data_request",
) -> TossApiFakeRequest:
    """Build a symbolic dry-run fake request shape."""

    return TossApiFakeRequest(
        request_id=request_id,
        endpoint_kind=endpoint_kind,
        symbolic_method="SYMBOLIC_METHOD",
        query_shape=("symbolic_market_query",),
        body_shape=("empty_symbolic_body",),
        header_shape=("redacted_header_names_only",),
        dry_run_only=True,
        live_call_allowed=False,
        redaction_required=True,
    )


def build_toss_api_fake_fixtures() -> tuple[TossApiFakeFixture, ...]:
    """Return deterministic in-memory fake response fixtures."""

    redaction_policy = build_toss_api_redaction_policy()
    redacted_preview_value = redact_mapping(
        {"access_token": "synthetic-sensitive-value"},
        redaction_policy,
    )["access_token"]
    return (
        _build_toss_api_fake_fixture(
            fixture_name="market_data_ok_placeholder",
            description="Symbolic market data preview with usable placeholder values",
            normalized_status="ok_placeholder",
            response_kind="safe_market_data_preview",
            preview={
                "preview_state": "ok",
                "symbol_shape": "ticker_symbol_placeholder",
                "value_shape": "decimal_string_placeholder",
            },
            diagnostics=("safe_preview_ready",),
            expected_passed=True,
        ),
        _build_toss_api_fake_fixture(
            fixture_name="market_data_empty_placeholder",
            description="Symbolic market data preview with no rows",
            normalized_status="empty_placeholder",
            response_kind="safe_empty_preview",
            preview={
                "preview_state": "empty",
                "row_shape": "empty_tuple_placeholder",
            },
            diagnostics=("safe_empty_preview",),
            expected_passed=True,
        ),
        _build_toss_api_fake_fixture(
            fixture_name="market_data_error_placeholder",
            description="Symbolic market data preview with a safe error state",
            normalized_status="error_placeholder",
            response_kind="safe_error_preview",
            preview={
                "preview_state": "error",
                "error_shape": "symbolic_error_placeholder",
            },
            diagnostics=("safe_error_preview",),
            expected_passed=True,
        ),
        _build_toss_api_fake_fixture(
            fixture_name="rate_limited_placeholder",
            description="Symbolic throttling state without external retry behavior",
            normalized_status="rate_limited_safe_error",
            response_kind="safe_error_preview",
            preview={
                "preview_state": "rate_limited",
                "retry_shape": "symbolic_wait_hint",
            },
            diagnostics=("safe_rate_limit_preview",),
            expected_passed=True,
        ),
        _build_toss_api_fake_fixture(
            fixture_name="redaction_required_placeholder",
            description="Symbolic fixture proving sensitive values are masked",
            normalized_status="redaction_checked",
            response_kind="safe_redacted_preview",
            preview={
                "preview_state": "redaction_checked",
                "redacted_preview": redacted_preview_value,
            },
            diagnostics=("safe_redaction_preview",),
            expected_passed=True,
        ),
        _build_toss_api_fake_fixture(
            fixture_name="endpoint_not_allowed_placeholder",
            description="Symbolic denied endpoint returns a safe failure",
            endpoint_kind="blocked_endpoint_placeholder",
            normalized_status="safe_contract_failure",
            response_kind="safe_failure_preview",
            preview={
                "preview_state": "blocked",
                "failure_shape": "symbolic_denied_endpoint",
            },
            diagnostics=("safe_failure_preview",),
            expected_passed=False,
            expected_failures=("endpoint_not_allowed",),
        ),
    )


def run_toss_api_fake_transport(
    fixture_name: str,
    fixtures: tuple[TossApiFakeFixture, ...] | None = None,
) -> TossApiFakeTransportResult:
    """Return a contract-safe fake transport result for a named fixture."""

    selected_fixtures = fixtures or build_toss_api_fake_fixtures()
    fixture = next(
        (candidate for candidate in selected_fixtures if candidate.fixture_name == fixture_name),
        None,
    )
    if fixture is None:
        return TossApiFakeTransportResult(
            passed=False,
            fixture_name=fixture_name,
            endpoint_kind="unknown_symbolic_endpoint",
            normalized_status="safe_contract_failure",
            response_kind="safe_failure_preview",
            redacted_body_preview={"preview_state": "unknown_fixture"},
            diagnostics=("safe_unknown_fixture",),
            failures=("fixture_not_found",),
            capability_flags=build_toss_api_external_capability_flags(),
        )

    validation = validate_toss_api_fake_fixture(fixture)
    failures = (*fixture.expected_failures, *validation.failures)
    passed = fixture.expected_passed and not validation.failures
    return TossApiFakeTransportResult(
        passed=passed,
        fixture_name=fixture.fixture_name,
        endpoint_kind=fixture.fake_response.endpoint_kind,
        normalized_status=fixture.fake_response.normalized_status,
        response_kind=fixture.fake_response.response_kind,
        redacted_body_preview=fixture.fake_response.redacted_body_preview,
        diagnostics=(
            *fixture.fake_response.diagnostics,
            *fixture.expected_diagnostics,
        ),
        failures=failures,
        capability_flags=build_toss_api_external_capability_flags(),
    )


def validate_toss_api_fake_transport_policy(
    policy: TossApiFakeTransportPolicy | None = None,
) -> TossApiFakeTransportValidationResult:
    """Validate the no-I/O fake transport policy."""

    active_policy = policy or build_toss_api_fake_transport_policy()
    required_true_flags = (
        "uses_contract_policy",
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
        "fake_transport_ready",
        "redaction_required",
    )
    required_false_flags = (
        "live_http_ready",
        "oauth_ready",
        "credential_required_now",
        "account_seq_required_now",
        "order_required_now",
        "streamlit_required",
        "http_smoke_required",
        "raw_payload_allowed",
    )
    failures = [
        f"{flag}_must_be_true"
        for flag in required_true_flags
        if not getattr(active_policy, flag)
    ]
    failures.extend(
        f"{flag}_must_be_false"
        for flag in required_false_flags
        if getattr(active_policy, flag)
    )

    return TossApiFakeTransportValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_fixture_names=(),
        checked_endpoint_kinds=active_policy.contract_policy.allowed_endpoint_kinds,
        checked_policy_flags=(*required_true_flags, *required_false_flags),
        checked_response_kinds=(),
        checked_redaction_fields=active_policy.contract_policy.sensitive_field_names,
        diagnostics=("fake_transport_policy_validation",),
    )


def validate_toss_api_fake_fixture(
    fixture: TossApiFakeFixture,
    policy: TossApiFakeTransportPolicy | None = None,
) -> TossApiFakeTransportValidationResult:
    """Validate one in-memory fake fixture."""

    active_policy = policy or build_toss_api_fake_transport_policy()
    redaction_policy = build_toss_api_redaction_policy()
    allowed_endpoint_kinds = active_policy.contract_policy.allowed_endpoint_kinds
    failures: list[str] = []

    if fixture.fixture_name not in FAKE_FIXTURE_NAMES:
        failures.append("fixture_name_not_registered")
    if (
        fixture.fake_request.endpoint_kind not in allowed_endpoint_kinds
        and fixture.fixture_name != "endpoint_not_allowed_placeholder"
    ):
        failures.append("fixture_endpoint_not_allowed")
    if fixture.fake_request.live_call_allowed:
        failures.append("live_call_allowed_must_be_false")
    if not fixture.fake_request.dry_run_only:
        failures.append("dry_run_only_must_be_true")
    if not fixture.fake_request.redaction_required:
        failures.append("redaction_required_must_be_true")
    if fixture.fake_response.raw_payload_allowed:
        failures.append("raw_payload_allowed_must_be_false")
    if fixture.fake_response.sensitive_output_present:
        failures.append("sensitive_output_present_must_be_false")

    sensitive_result = validate_no_sensitive_output(
        fixture.fake_response.redacted_body_preview,
        redaction_policy,
    )
    failures.extend(sensitive_result.failures)

    if _contains_unredacted_sensitive_text(
        fixture.fake_response.redacted_body_preview,
        redaction_policy,
    ):
        failures.append("sensitive_preview_text_must_be_redacted")

    return TossApiFakeTransportValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_fixture_names=(fixture.fixture_name,),
        checked_endpoint_kinds=(fixture.fake_request.endpoint_kind,),
        checked_policy_flags=(
            "dry_run_only",
            "live_call_allowed",
            "redaction_required",
            "raw_payload_allowed",
        ),
        checked_response_kinds=(fixture.fake_response.response_kind,),
        checked_redaction_fields=redaction_policy.sensitive_field_names,
        diagnostics=("fake_fixture_validation",),
    )


def run_toss_api_fake_transport_preflight_checks() -> (
    TossApiFakeTransportValidationResult
):
    """Run deterministic fake transport checks without I/O."""

    policy = build_toss_api_fake_transport_policy()
    policy_result = validate_toss_api_fake_transport_policy(policy)
    contract_result = run_toss_api_client_contract_preflight_checks()
    endpoints = build_symbolic_toss_api_endpoint_contracts()
    fixtures = build_toss_api_fake_fixtures()
    fixture_results = tuple(
        validate_toss_api_fake_fixture(fixture, policy) for fixture in fixtures
    )
    transport_results = tuple(
        run_toss_api_fake_transport(fixture.fixture_name, fixtures)
        for fixture in fixtures
    )

    failures: list[str] = [*policy_result.failures, *contract_result.failures]
    for result in fixture_results:
        failures.extend(result.failures)
    for transport_result in transport_results:
        unexpected_failures = tuple(
            failure
            for failure in transport_result.failures
            if transport_result.fixture_name != "endpoint_not_allowed_placeholder"
            or failure != "endpoint_not_allowed"
        )
        failures.extend(unexpected_failures)

    if tuple(fixture.fixture_name for fixture in fixtures) != FAKE_FIXTURE_NAMES:
        failures.append("fixture_matrix_must_be_complete")

    checked_endpoint_kinds = tuple(
        dict.fromkeys(
            (
                *(endpoint.endpoint_kind for endpoint in endpoints),
                *(fixture.fake_request.endpoint_kind for fixture in fixtures),
            )
        )
    )
    return TossApiFakeTransportValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_fixture_names=tuple(fixture.fixture_name for fixture in fixtures),
        checked_endpoint_kinds=checked_endpoint_kinds,
        checked_policy_flags=policy_result.checked_policy_flags,
        checked_response_kinds=tuple(
            fixture.fake_response.response_kind for fixture in fixtures
        ),
        checked_redaction_fields=policy.contract_policy.sensitive_field_names,
        diagnostics=(
            "pure_no_io_fake_transport_preflight",
            "symbolic_endpoint_contract_reused",
            "in_memory_fixture_matrix",
            "redacted_preview_only",
        ),
    )


def _build_toss_api_fake_fixture(
    *,
    fixture_name: str,
    description: str,
    normalized_status: str,
    response_kind: str,
    preview: Mapping[str, object],
    diagnostics: tuple[str, ...],
    expected_passed: bool,
    endpoint_kind: str = "read_only_market_data_placeholder",
    expected_failures: tuple[str, ...] = (),
) -> TossApiFakeFixture:
    fake_request = build_toss_api_fake_request(
        endpoint_kind=endpoint_kind,
        request_id=f"{fixture_name}_request_shape",
    )
    fake_response = TossApiFakeResponse(
        fixture_name=fixture_name,
        endpoint_kind=endpoint_kind,
        normalized_status=normalized_status,
        response_kind=response_kind,
        status_code_shape="symbolic_status_code",
        redacted_body_preview=dict(preview),
        diagnostics=diagnostics,
        raw_payload_allowed=False,
        sensitive_output_present=False,
    )
    return TossApiFakeFixture(
        fixture_name=fixture_name,
        description=description,
        fake_request=fake_request,
        fake_response=fake_response,
        expected_passed=expected_passed,
        expected_failures=expected_failures,
        expected_diagnostics=("contract_safe_fixture",),
    )


def _contains_unredacted_sensitive_text(
    values: Mapping[str, object],
    policy: TossApiRedactionPolicy,
) -> bool:
    placeholder = policy.redaction_placeholder
    rendered_values = " ".join(str(value).casefold() for value in values.values())
    return any(
        sensitive.casefold() in rendered_values
        for sensitive in policy.sensitive_field_names
        if sensitive != placeholder
    )
