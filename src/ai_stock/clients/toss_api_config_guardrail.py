"""Pure credential/config redaction guardrail for future Toss API work.

This module defines validation-only policy and redaction helpers. It does not
read environment variables, read files, create credentials, or call services.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ai_stock.clients.toss_api_client_contract import (
    TossApiClientContractPolicy,
    TossApiCredentialNamePolicy,
    TossApiExternalCapabilityFlags,
    TossApiRedactionPolicy,
    build_toss_api_client_contract_policy,
    build_toss_api_credential_name_policy,
    build_toss_api_external_capability_flags,
    build_toss_api_redaction_policy,
    redact_mapping,
    redact_sensitive_value,
    run_toss_api_client_contract_preflight_checks,
    validate_no_sensitive_output,
)


TOSS_API_CONFIG_GUARDRAIL_VERSION = "MS-14.02"
TOSS_API_CONFIG_GUARDRAIL_SCOPE = (
    "pure_no_io_credential_config_redaction_guardrail"
)

SYMBOLIC_CONFIG_SOURCE_KINDS = (
    "symbolic_env_later",
    "symbolic_local_secret_file_later",
    "symbolic_runtime_injection_later",
)
FORBIDDEN_NOW_SOURCE_KINDS = (
    "live_environment_read",
    "local_secret_file_read",
    "local_config_loader_now",
    "runtime_secret_prompt",
)


@dataclass(frozen=True)
class TossApiConfigGuardrailPolicy:
    """Top-level no-I/O guardrail policy for future credential config."""

    guardrail_version: str
    guardrail_scope: str
    uses_contract_policy: bool
    contract_policy: TossApiClientContractPolicy
    credential_name_policy: TossApiCredentialNamePolicy
    no_network: bool
    no_oauth: bool
    no_credentials_now: bool
    no_env_read: bool
    no_file_read: bool
    no_file_write: bool
    no_account_seq: bool
    no_orders: bool
    no_account_assets: bool
    no_balance: bool
    no_fills: bool
    no_db: bool
    no_streamlit: bool
    no_llm: bool
    no_recommendation: bool
    no_ranking: bool
    credential_required_now: bool
    credential_names_defined: bool
    credential_values_allowed: bool
    env_read_allowed: bool
    file_read_allowed: bool
    live_http_ready: bool
    oauth_ready: bool
    account_seq_required_now: bool
    order_required_now: bool
    streamlit_required: bool
    http_smoke_required: bool
    raw_payload_allowed: bool
    redaction_required: bool
    mask_required: bool
    fail_closed_on_sensitive_output: bool
    observation_only_notes: tuple[str, ...]


@dataclass(frozen=True)
class TossApiConfigSourcePolicy:
    """Symbolic source policy without current read/write capability."""

    source_kind: str
    allowed_later_sources: tuple[str, ...]
    forbidden_now_sources: tuple[str, ...]
    read_now: bool
    write_now: bool
    required_now: bool
    validation_only: bool


@dataclass(frozen=True)
class TossApiConfigFieldPolicy:
    """Name-only credential field policy without values."""

    symbolic_field_name: str
    purpose_label: str
    required_now: bool
    required_for_future_live_smoke: bool
    value_allowed: bool
    raw_output_allowed: bool
    mask_required: bool
    print_allowed: bool
    log_allowed: bool
    persist_allowed: bool


@dataclass(frozen=True)
class TossApiConfigRedactionResult:
    """Safe redaction output that never returns raw sensitive values."""

    passed: bool
    safe_config_preview: Mapping[str, object]
    failures: tuple[str, ...]
    redacted_field_labels: tuple[str, ...]
    blocked_field_labels: tuple[str, ...]
    diagnostics: tuple[str, ...]


@dataclass(frozen=True)
class TossApiConfigValidationResult:
    """Validation result for config guardrail policies and mappings."""

    passed: bool
    failures: tuple[str, ...]
    checked_policy_flags: tuple[str, ...]
    checked_source_kinds: tuple[str, ...]
    checked_field_policy_names: tuple[str, ...]
    checked_redaction_labels: tuple[str, ...]
    diagnostics: tuple[str, ...]


@dataclass(frozen=True)
class TossApiCredentialReadinessDecision:
    """Decision proving secrets must not be requested in this stage."""

    credential_required_now: bool
    toss_key_required_now: bool
    toss_secret_required_now: bool
    openai_key_required_now: bool
    access_token_required_now: bool
    account_seq_required_now: bool
    live_http_allowed_now: bool
    oauth_allowed_now: bool
    safe_to_request_user_secret_now: bool
    next_possible_secret_stage_label: str
    blocking_reason_until_live_smoke: str


@dataclass(frozen=True)
class TossApiConfigGuardrailPreflightResult:
    """Aggregate preflight result for the config guardrail stage."""

    passed: bool
    failures: tuple[str, ...]
    policy_result: TossApiConfigValidationResult
    source_result: TossApiConfigValidationResult
    field_result: TossApiConfigValidationResult
    readiness_result: TossApiConfigValidationResult
    redaction_result: TossApiConfigRedactionResult
    capability_flags: TossApiExternalCapabilityFlags
    diagnostics: tuple[str, ...]


def build_toss_api_config_guardrail_policy(
    contract_policy: TossApiClientContractPolicy | None = None,
    credential_name_policy: TossApiCredentialNamePolicy | None = None,
) -> TossApiConfigGuardrailPolicy:
    """Return the top-level pure config guardrail policy."""

    active_contract_policy = contract_policy or build_toss_api_client_contract_policy()
    active_credential_policy = (
        credential_name_policy or build_toss_api_credential_name_policy()
    )
    return TossApiConfigGuardrailPolicy(
        guardrail_version=TOSS_API_CONFIG_GUARDRAIL_VERSION,
        guardrail_scope=TOSS_API_CONFIG_GUARDRAIL_SCOPE,
        uses_contract_policy=True,
        contract_policy=active_contract_policy,
        credential_name_policy=active_credential_policy,
        no_network=active_contract_policy.no_network,
        no_oauth=active_contract_policy.no_oauth,
        no_credentials_now=True,
        no_env_read=True,
        no_file_read=True,
        no_file_write=True,
        no_account_seq=active_contract_policy.no_account_seq,
        no_orders=active_contract_policy.no_orders,
        no_account_assets=active_contract_policy.no_account_assets,
        no_balance=active_contract_policy.no_balance,
        no_fills=active_contract_policy.no_fills,
        no_db=active_contract_policy.no_db,
        no_streamlit=active_contract_policy.no_streamlit,
        no_llm=active_contract_policy.no_llm,
        no_recommendation=active_contract_policy.no_recommendation,
        no_ranking=active_contract_policy.no_ranking,
        credential_required_now=False,
        credential_names_defined=True,
        credential_values_allowed=False,
        env_read_allowed=False,
        file_read_allowed=False,
        live_http_ready=False,
        oauth_ready=False,
        account_seq_required_now=False,
        order_required_now=False,
        streamlit_required=False,
        http_smoke_required=False,
        raw_payload_allowed=False,
        redaction_required=True,
        mask_required=True,
        fail_closed_on_sensitive_output=True,
        observation_only_notes=(
            "config_guardrail_only",
            "name_policy_without_values",
            "no_secret_prompt_now",
            "no_runtime_source_read",
            "live_smoke_gate_not_reached",
        ),
    )


def build_toss_api_config_source_policy(
    source_kind: str = "symbolic_runtime_injection_later",
) -> TossApiConfigSourcePolicy:
    """Return a validation-only symbolic config source policy."""

    return TossApiConfigSourcePolicy(
        source_kind=source_kind,
        allowed_later_sources=SYMBOLIC_CONFIG_SOURCE_KINDS,
        forbidden_now_sources=FORBIDDEN_NOW_SOURCE_KINDS,
        read_now=False,
        write_now=False,
        required_now=False,
        validation_only=True,
    )


def build_toss_api_config_field_policies() -> tuple[TossApiConfigFieldPolicy, ...]:
    """Return symbolic credential field policies without values."""

    return (
        TossApiConfigFieldPolicy(
            symbolic_field_name="symbolic_toss_app_key",
            purpose_label="future_toss_key_name_only",
            required_now=False,
            required_for_future_live_smoke=True,
            value_allowed=False,
            raw_output_allowed=False,
            mask_required=True,
            print_allowed=False,
            log_allowed=False,
            persist_allowed=False,
        ),
        TossApiConfigFieldPolicy(
            symbolic_field_name="symbolic_toss_app_secret",
            purpose_label="future_toss_secret_name_only",
            required_now=False,
            required_for_future_live_smoke=True,
            value_allowed=False,
            raw_output_allowed=False,
            mask_required=True,
            print_allowed=False,
            log_allowed=False,
            persist_allowed=False,
        ),
        TossApiConfigFieldPolicy(
            symbolic_field_name="symbolic_toss_access_token_later",
            purpose_label="future_toss_token_name_only",
            required_now=False,
            required_for_future_live_smoke=False,
            value_allowed=False,
            raw_output_allowed=False,
            mask_required=True,
            print_allowed=False,
            log_allowed=False,
            persist_allowed=False,
        ),
        TossApiConfigFieldPolicy(
            symbolic_field_name="symbolic_toss_refresh_token_later",
            purpose_label="future_toss_refresh_name_only",
            required_now=False,
            required_for_future_live_smoke=False,
            value_allowed=False,
            raw_output_allowed=False,
            mask_required=True,
            print_allowed=False,
            log_allowed=False,
            persist_allowed=False,
        ),
        TossApiConfigFieldPolicy(
            symbolic_field_name="symbolic_openai_api_key_later",
            purpose_label="future_llm_key_name_only",
            required_now=False,
            required_for_future_live_smoke=False,
            value_allowed=False,
            raw_output_allowed=False,
            mask_required=True,
            print_allowed=False,
            log_allowed=False,
            persist_allowed=False,
        ),
        TossApiConfigFieldPolicy(
            symbolic_field_name="symbolic_account_seq_later",
            purpose_label="future_account_identifier_name_only",
            required_now=False,
            required_for_future_live_smoke=False,
            value_allowed=False,
            raw_output_allowed=False,
            mask_required=True,
            print_allowed=False,
            log_allowed=False,
            persist_allowed=False,
        ),
    )


def build_toss_api_credential_readiness_decision() -> (
    TossApiCredentialReadinessDecision
):
    """Return the stage decision that secrets must not be requested now."""

    return TossApiCredentialReadinessDecision(
        credential_required_now=False,
        toss_key_required_now=False,
        toss_secret_required_now=False,
        openai_key_required_now=False,
        access_token_required_now=False,
        account_seq_required_now=False,
        live_http_allowed_now=False,
        oauth_allowed_now=False,
        safe_to_request_user_secret_now=False,
        next_possible_secret_stage_label="MS-14.03 no-secret dry run gate",
        blocking_reason_until_live_smoke="credential_request_blocked_until_explicit_gate",
    )


def redact_toss_api_config_mapping(
    values: Mapping[str, object],
    redaction_policy: TossApiRedactionPolicy | None = None,
) -> TossApiConfigRedactionResult:
    """Redact a config mapping and expose only safe preview keys."""

    active_redaction_policy = redaction_policy or build_toss_api_redaction_policy()
    redacted_values = redact_mapping(values, active_redaction_policy)
    safe_preview: dict[str, object] = {}
    redacted_labels: list[str] = []
    blocked_labels: list[str] = []
    failures: list[str] = []

    for index, (field_name, original_value) in enumerate(values.items(), start=1):
        redaction_result = redact_sensitive_value(
            field_name,
            original_value,
            active_redaction_policy,
        )
        safe_key = f"safe_config_entry_{index}"
        if redaction_result.redacted:
            safe_preview[safe_key] = active_redaction_policy.redaction_placeholder
            redacted_labels.append(safe_key)
            if redaction_result.blocked:
                blocked_labels.append(safe_key)
        else:
            safe_preview[safe_key] = redacted_values[field_name]

    sensitive_validation = validate_no_sensitive_output(
        redacted_values,
        active_redaction_policy,
    )
    failures.extend(sensitive_validation.failures)
    if _preview_contains_unredacted_sensitive_value(values, safe_preview):
        failures.append("safe_preview_must_not_expose_sensitive_value")

    return TossApiConfigRedactionResult(
        passed=not failures,
        safe_config_preview=safe_preview,
        failures=tuple(failures),
        redacted_field_labels=tuple(redacted_labels),
        blocked_field_labels=tuple(blocked_labels),
        diagnostics=("config_values_masked", "safe_preview_only"),
    )


def validate_toss_api_config_mapping(
    values: Mapping[str, object],
    policy: TossApiConfigGuardrailPolicy | None = None,
) -> TossApiConfigValidationResult:
    """Validate a caller-supplied in-memory config mapping."""

    active_policy = policy or build_toss_api_config_guardrail_policy()
    redaction_result = redact_toss_api_config_mapping(values)
    failures = list(redaction_result.failures)
    if active_policy.credential_values_allowed:
        failures.append("credential_values_allowed_must_be_false")
    if not active_policy.fail_closed_on_sensitive_output:
        failures.append("fail_closed_on_sensitive_output_must_be_true")

    return TossApiConfigValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=(
            "credential_values_allowed",
            "fail_closed_on_sensitive_output",
        ),
        checked_source_kinds=(),
        checked_field_policy_names=(),
        checked_redaction_labels=redaction_result.redacted_field_labels,
        diagnostics=("config_mapping_redaction_validation",),
    )


def validate_toss_api_config_guardrail_policy(
    policy: TossApiConfigGuardrailPolicy | None = None,
) -> TossApiConfigValidationResult:
    """Validate top-level config guardrail flags."""

    active_policy = policy or build_toss_api_config_guardrail_policy()
    required_true_flags = (
        "uses_contract_policy",
        "no_network",
        "no_oauth",
        "no_credentials_now",
        "no_env_read",
        "no_file_read",
        "no_file_write",
        "no_account_seq",
        "no_orders",
        "no_account_assets",
        "no_balance",
        "no_fills",
        "no_db",
        "no_streamlit",
        "no_llm",
        "no_recommendation",
        "no_ranking",
        "credential_names_defined",
        "redaction_required",
        "mask_required",
        "fail_closed_on_sensitive_output",
    )
    required_false_flags = (
        "credential_required_now",
        "credential_values_allowed",
        "env_read_allowed",
        "file_read_allowed",
        "live_http_ready",
        "oauth_ready",
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
    if active_policy.contract_policy.contract_version != "MS-14.00":
        failures.append("contract_policy_version_must_be_ms_14_00")
    if active_policy.credential_name_policy.required_now:
        failures.append("credential_name_policy_required_now_must_be_false")

    return TossApiConfigValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=(*required_true_flags, *required_false_flags),
        checked_source_kinds=(),
        checked_field_policy_names=active_policy.credential_name_policy.credential_field_names,
        checked_redaction_labels=(),
        diagnostics=("config_guardrail_policy_validation",),
    )


def validate_toss_api_config_source_policy(
    source_policy: TossApiConfigSourcePolicy | None = None,
) -> TossApiConfigValidationResult:
    """Validate symbolic source policy with no current reads or writes."""

    active_source_policy = source_policy or build_toss_api_config_source_policy()
    failures: list[str] = []
    if active_source_policy.source_kind not in active_source_policy.allowed_later_sources:
        failures.append("source_kind_must_be_symbolic_later_source")
    if active_source_policy.read_now:
        failures.append("source_read_now_must_be_false")
    if active_source_policy.write_now:
        failures.append("source_write_now_must_be_false")
    if active_source_policy.required_now:
        failures.append("source_required_now_must_be_false")
    if not active_source_policy.validation_only:
        failures.append("source_policy_must_be_validation_only")

    return TossApiConfigValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=(
            "read_now",
            "write_now",
            "required_now",
            "validation_only",
        ),
        checked_source_kinds=(
            active_source_policy.source_kind,
            *active_source_policy.allowed_later_sources,
        ),
        checked_field_policy_names=(),
        checked_redaction_labels=(),
        diagnostics=("symbolic_source_policy_validation",),
    )


def validate_toss_api_config_field_policies(
    field_policies: tuple[TossApiConfigFieldPolicy, ...] | None = None,
) -> TossApiConfigValidationResult:
    """Validate symbolic credential field policies."""

    active_field_policies = field_policies or build_toss_api_config_field_policies()
    failures: list[str] = []
    for field_policy in active_field_policies:
        if not field_policy.symbolic_field_name.startswith("symbolic_"):
            failures.append("field_policy_name_must_be_symbolic")
        if field_policy.required_now:
            failures.append("field_policy_required_now_must_be_false")
        if field_policy.value_allowed:
            failures.append("field_policy_value_allowed_must_be_false")
        if field_policy.raw_output_allowed:
            failures.append("field_policy_raw_output_allowed_must_be_false")
        if not field_policy.mask_required:
            failures.append("field_policy_mask_required_must_be_true")
        if field_policy.print_allowed:
            failures.append("field_policy_print_allowed_must_be_false")
        if field_policy.log_allowed:
            failures.append("field_policy_log_allowed_must_be_false")
        if field_policy.persist_allowed:
            failures.append("field_policy_persist_allowed_must_be_false")

    return TossApiConfigValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=(
            "required_now",
            "value_allowed",
            "raw_output_allowed",
            "mask_required",
            "print_allowed",
            "log_allowed",
            "persist_allowed",
        ),
        checked_source_kinds=(),
        checked_field_policy_names=tuple(
            field_policy.symbolic_field_name for field_policy in active_field_policies
        ),
        checked_redaction_labels=(),
        diagnostics=("symbolic_field_policy_validation",),
    )


def validate_toss_api_credential_readiness_decision(
    decision: TossApiCredentialReadinessDecision | None = None,
) -> TossApiConfigValidationResult:
    """Validate that secrets are not requested in MS-14.02."""

    active_decision = decision or build_toss_api_credential_readiness_decision()
    required_false_flags = (
        "credential_required_now",
        "toss_key_required_now",
        "toss_secret_required_now",
        "openai_key_required_now",
        "access_token_required_now",
        "account_seq_required_now",
        "live_http_allowed_now",
        "oauth_allowed_now",
        "safe_to_request_user_secret_now",
    )
    failures = tuple(
        f"{flag}_must_be_false"
        for flag in required_false_flags
        if getattr(active_decision, flag)
    )

    return TossApiConfigValidationResult(
        passed=not failures,
        failures=failures,
        checked_policy_flags=required_false_flags,
        checked_source_kinds=(),
        checked_field_policy_names=(),
        checked_redaction_labels=(),
        diagnostics=("credential_readiness_decision_validation",),
    )


def run_toss_api_config_guardrail_preflight_checks() -> (
    TossApiConfigGuardrailPreflightResult
):
    """Run deterministic config guardrail checks without I/O."""

    policy = build_toss_api_config_guardrail_policy()
    source_policy = build_toss_api_config_source_policy()
    field_policies = build_toss_api_config_field_policies()
    readiness_decision = build_toss_api_credential_readiness_decision()
    redaction_result = redact_toss_api_config_mapping(
        {
            "access_token": "dummy-sensitive-value",
            "api_key": "dummy-key-value",
        }
    )
    policy_result = validate_toss_api_config_guardrail_policy(policy)
    source_result = validate_toss_api_config_source_policy(source_policy)
    field_result = validate_toss_api_config_field_policies(field_policies)
    readiness_result = validate_toss_api_credential_readiness_decision(
        readiness_decision
    )
    mapping_result = validate_toss_api_config_mapping(
        {
            "access_token": "dummy-sensitive-value",
            "api_key": "dummy-key-value",
        },
        policy,
    )
    contract_result = run_toss_api_client_contract_preflight_checks()
    capability_flags = build_toss_api_external_capability_flags()

    failures: list[str] = []
    for result in (
        policy_result,
        source_result,
        field_result,
        readiness_result,
        mapping_result,
    ):
        failures.extend(result.failures)
    failures.extend(redaction_result.failures)
    failures.extend(contract_result.failures)

    expected_false_flags = tuple(capability_flags.__dict__)
    if tuple(name for name, value in capability_flags.__dict__.items() if not value) != (
        expected_false_flags
    ):
        failures.append("external_capability_flags_must_all_be_false")

    return TossApiConfigGuardrailPreflightResult(
        passed=not failures,
        failures=tuple(failures),
        policy_result=policy_result,
        source_result=source_result,
        field_result=field_result,
        readiness_result=readiness_result,
        redaction_result=redaction_result,
        capability_flags=capability_flags,
        diagnostics=(
            "pure_no_io_config_guardrail_preflight",
            "symbolic_config_only",
            "user_prompt_blocked_now",
            "redacted_output_only",
        ),
    )


def _preview_contains_unredacted_sensitive_value(
    original_values: Mapping[str, object],
    safe_preview: Mapping[str, object],
) -> bool:
    preview_values = {str(value) for value in safe_preview.values()}
    redaction_policy = build_toss_api_redaction_policy()
    return any(
        str(value) in preview_values
        for key, value in original_values.items()
        if redact_sensitive_value(key, value, redaction_policy).redacted
    )
