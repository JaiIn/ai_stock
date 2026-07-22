"""Credential request timing policy for a future read-only Toss API smoke.

This module is pure no-I/O. It does not request, read, load, or use credential
values. MS-15.03 only records when a later stage may ask for Toss credentials
after explicit approval, while keeping the current stage closed.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai_stock.clients.toss_api_client_contract import (
    build_toss_api_redaction_policy,
    redact_mapping,
    run_toss_api_client_contract_preflight_checks,
    validate_no_sensitive_output,
)
from ai_stock.clients.toss_api_config_guardrail import (
    run_toss_api_config_guardrail_preflight_checks,
)
from ai_stock.clients.toss_api_fake_transport import (
    run_toss_api_fake_transport_preflight_checks,
)
from ai_stock.clients.toss_api_live_readiness import (
    run_toss_api_live_readiness_preflight_checks,
    run_toss_api_no_secret_dry_run,
)
from ai_stock.clients.toss_api_live_smoke_approval import (
    TossApiReadOnlyLiveSmokeApprovalGateResult,
    TossApiReadOnlyLiveSmokeApprovalValidationResult,
    run_toss_api_readonly_live_smoke_approval_gate,
    run_toss_api_readonly_live_smoke_approval_preflight_checks,
)
from ai_stock.clients.toss_api_live_smoke_disabled import (
    run_toss_api_readonly_live_smoke_disabled_preflight_checks,
)
from ai_stock.clients.toss_api_live_smoke_plan import (
    run_toss_api_readonly_live_smoke_planning_preflight_checks,
)


TOSS_API_CREDENTIAL_REQUEST_TIMING_VERSION = "MS-15.03"
TOSS_API_CREDENTIAL_REQUEST_TIMING_SCOPE = (
    "pure_no_io_credential_request_timing_policy"
)
DEFAULT_CANDIDATE_STAGE_LABEL = "MS-16.00 first read-only Toss API live smoke"
DEFAULT_CANDIDATE_STAGE_ID = "ms_16_00_first_readonly_toss_api_live_smoke"
DEFAULT_NEXT_STAGE = DEFAULT_CANDIDATE_STAGE_LABEL
TIMING_REQUIREMENT_IDS = (
    "explicit_user_approval_for_ms_16_00_required",
    "toss_key_secret_request_must_be_separate_step",
    "credential_entry_must_not_be_committed",
    "env_file_read_must_be_separately_approved",
    "oauth_token_issuance_must_be_separately_approved",
    "live_http_call_must_be_separately_approved",
    "raw_response_output_must_be_blocked",
    "authorization_header_output_must_be_blocked",
    "token_output_must_be_blocked",
    "account_seq_must_remain_blocked",
    "account_order_balance_fills_scope_must_remain_blocked",
    "db_write_must_remain_blocked",
    "streamlit_ui_must_remain_unchanged",
    "openai_key_must_not_be_requested",
    "llm_call_must_remain_blocked",
    "rollback_path_required",
    "redacted_diagnostics_only_required",
)
SAFE_TIMING_REQUIREMENT_IDS = tuple(
    f"safe_timing_requirement_{index:02d}"
    for index, _ in enumerate(TIMING_REQUIREMENT_IDS, start=1)
)


@dataclass(frozen=True)
class TossApiCredentialRequestTimingPolicy:
    """Policy defining when credentials may be requested in a later stage."""

    timing_version: str
    timing_scope: str
    credential_timing_policy_only: bool
    current_stage_requests_credentials: bool
    current_stage_reads_credentials: bool
    current_stage_uses_credentials: bool
    next_live_stage_candidate: str
    explicit_user_approval_required_before_request: bool
    separate_secret_entry_required: bool
    separate_env_read_approval_required: bool
    separate_oauth_approval_required: bool
    separate_live_http_approval_required: bool
    account_seq_must_remain_blocked: bool
    order_scope_must_remain_blocked: bool
    account_balance_fills_scope_must_remain_blocked: bool
    raw_payload_output_must_remain_blocked: bool
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
    no_live_http_now: bool
    credential_required_now: bool
    toss_key_required_now: bool
    toss_secret_required_now: bool
    openai_key_required_now: bool
    access_token_required_now: bool
    safe_to_request_user_secret_now: bool
    live_execution_allowed_now: bool
    credential_request_allowed_now: bool


@dataclass(frozen=True)
class TossApiCredentialRequestCandidateStage:
    """Symbolic later stage where a Toss credential request may be considered."""

    stage_label: str
    stage_scope: str
    readonly_market_data_only: bool
    may_request_toss_credentials_later: bool
    may_request_openai_key_later: bool
    may_request_account_seq_later: bool
    may_request_order_scope_later: bool
    requires_explicit_user_approval: bool
    requires_redaction_policy: bool
    requires_no_raw_payload_output: bool
    requires_no_db_write: bool
    requires_no_account_balance_fills: bool
    requires_readonly_scope: bool
    live_execution_allowed_in_current_stage: bool
    credential_request_allowed_in_current_stage: bool


@dataclass(frozen=True)
class TossApiCredentialRequestRequirement:
    """One timing requirement for requesting credentials in a later stage."""

    requirement_id: str
    safe_requirement_id: str
    category: str
    required: bool
    satisfied_now: bool
    required_before_candidate_stage: bool
    evidence_label: str


@dataclass(frozen=True)
class TossApiCredentialRequestTimingDecision:
    """Closed current-stage decision plus future candidate signal."""

    timing_policy_invocation_allowed: bool
    approval_gate_passed: bool
    current_stage_credential_request_allowed: bool
    current_stage_env_read_allowed: bool
    current_stage_oauth_allowed: bool
    current_stage_token_issuance_allowed: bool
    current_stage_live_http_allowed: bool
    current_stage_live_execution_allowed: bool
    current_stage_account_seq_allowed: bool
    current_stage_order_allowed: bool
    current_stage_account_data_allowed: bool
    current_stage_balance_allowed: bool
    current_stage_fills_allowed: bool
    current_stage_openai_key_allowed: bool
    current_stage_llm_allowed: bool
    ms_16_00_can_request_toss_credentials_after_explicit_approval: bool
    ms_16_00_can_request_openai_key: bool
    ms_16_00_can_use_account_seq: bool
    ms_16_00_can_use_order_scope: bool
    next_stage: str
    blocking_reasons: tuple[str, ...]
    safe_summary: tuple[str, ...]


@dataclass(frozen=True)
class TossApiCredentialRequestTimingResult:
    """Safe timing result with no secrets or runtime data."""

    result_id: str
    passed: bool
    policy_closed_for_current_stage: bool
    candidate_stage_label: str
    decision: TossApiCredentialRequestTimingDecision
    requirement_ids: tuple[str, ...]
    safe_message: str
    safe_diagnostics: tuple[str, ...]
    next_stage: str


@dataclass(frozen=True)
class TossApiCredentialRequestTimingValidationResult:
    """Validation result for MS-15.03 credential request timing."""

    passed: bool
    failures: tuple[str, ...]
    checked_policy_flags: tuple[str, ...]
    checked_candidate_stage_flags: tuple[str, ...]
    checked_requirement_ids: tuple[str, ...]
    checked_decision_flags: tuple[str, ...]
    checked_result_flags: tuple[str, ...]
    diagnostics: tuple[str, ...]


def build_toss_api_credential_request_timing_policy() -> (
    TossApiCredentialRequestTimingPolicy
):
    """Build the closed current-stage credential timing policy."""

    return TossApiCredentialRequestTimingPolicy(
        timing_version=TOSS_API_CREDENTIAL_REQUEST_TIMING_VERSION,
        timing_scope=TOSS_API_CREDENTIAL_REQUEST_TIMING_SCOPE,
        credential_timing_policy_only=True,
        current_stage_requests_credentials=False,
        current_stage_reads_credentials=False,
        current_stage_uses_credentials=False,
        next_live_stage_candidate=DEFAULT_CANDIDATE_STAGE_LABEL,
        explicit_user_approval_required_before_request=True,
        separate_secret_entry_required=True,
        separate_env_read_approval_required=True,
        separate_oauth_approval_required=True,
        separate_live_http_approval_required=True,
        account_seq_must_remain_blocked=True,
        order_scope_must_remain_blocked=True,
        account_balance_fills_scope_must_remain_blocked=True,
        raw_payload_output_must_remain_blocked=True,
        no_network=True,
        no_oauth=True,
        no_credentials_now=True,
        no_env_read=True,
        no_file_read=True,
        no_file_write=True,
        no_account_seq=True,
        no_orders=True,
        no_account_assets=True,
        no_balance=True,
        no_fills=True,
        no_db=True,
        no_streamlit=True,
        no_llm=True,
        no_recommendation=True,
        no_ranking=True,
        no_live_http_now=True,
        credential_required_now=False,
        toss_key_required_now=False,
        toss_secret_required_now=False,
        openai_key_required_now=False,
        access_token_required_now=False,
        safe_to_request_user_secret_now=False,
        live_execution_allowed_now=False,
        credential_request_allowed_now=False,
    )


def build_toss_api_credential_request_candidate_stages() -> (
    tuple[TossApiCredentialRequestCandidateStage, ...]
):
    """Build symbolic candidate stages for later credential request review."""

    return (
        TossApiCredentialRequestCandidateStage(
            stage_label=DEFAULT_CANDIDATE_STAGE_ID,
            stage_scope="symbolic_readonly_market_data_live_smoke_candidate",
            readonly_market_data_only=True,
            may_request_toss_credentials_later=True,
            may_request_openai_key_later=False,
            may_request_account_seq_later=False,
            may_request_order_scope_later=False,
            requires_explicit_user_approval=True,
            requires_redaction_policy=True,
            requires_no_raw_payload_output=True,
            requires_no_db_write=True,
            requires_no_account_balance_fills=True,
            requires_readonly_scope=True,
            live_execution_allowed_in_current_stage=False,
            credential_request_allowed_in_current_stage=False,
        ),
    )


def build_toss_api_credential_request_requirements() -> (
    tuple[TossApiCredentialRequestRequirement, ...]
):
    """Build timing requirements using safe IDs for result output."""

    return tuple(
        TossApiCredentialRequestRequirement(
            requirement_id=requirement_id,
            safe_requirement_id=safe_requirement_id,
            category="credential_request_timing",
            required=True,
            satisfied_now=False,
            required_before_candidate_stage=True,
            evidence_label="future_stage_separate_approval_required",
        )
        for requirement_id, safe_requirement_id in zip(
            TIMING_REQUIREMENT_IDS,
            SAFE_TIMING_REQUIREMENT_IDS,
            strict=True,
        )
    )


def evaluate_toss_api_credential_request_timing_decision(
    approval_result: TossApiReadOnlyLiveSmokeApprovalGateResult | None = None,
    approval_preflight: TossApiReadOnlyLiveSmokeApprovalValidationResult | None = None,
) -> TossApiCredentialRequestTimingDecision:
    """Evaluate credential timing while keeping MS-15.03 closed."""

    active_approval_result = (
        approval_result or run_toss_api_readonly_live_smoke_approval_gate()
    )
    active_approval_preflight = (
        approval_preflight
        or run_toss_api_readonly_live_smoke_approval_preflight_checks()
    )
    approval_gate_passed = (
        active_approval_result.passed
        and active_approval_result.gate_closed
        and active_approval_preflight.passed
    )

    return TossApiCredentialRequestTimingDecision(
        timing_policy_invocation_allowed=True,
        approval_gate_passed=approval_gate_passed,
        current_stage_credential_request_allowed=False,
        current_stage_env_read_allowed=False,
        current_stage_oauth_allowed=False,
        current_stage_token_issuance_allowed=False,
        current_stage_live_http_allowed=False,
        current_stage_live_execution_allowed=False,
        current_stage_account_seq_allowed=False,
        current_stage_order_allowed=False,
        current_stage_account_data_allowed=False,
        current_stage_balance_allowed=False,
        current_stage_fills_allowed=False,
        current_stage_openai_key_allowed=False,
        current_stage_llm_allowed=False,
        ms_16_00_can_request_toss_credentials_after_explicit_approval=True,
        ms_16_00_can_request_openai_key=False,
        ms_16_00_can_use_account_seq=False,
        ms_16_00_can_use_order_scope=False,
        next_stage=DEFAULT_NEXT_STAGE,
        blocking_reasons=(
            "current_stage_closed",
            "future_stage_approval_required",
            "runtime_access_closed",
        ),
        safe_summary=(
            "timing_policy_only",
            "future_candidate_recorded",
            "redacted_summary_only",
        ),
    )


def run_toss_api_credential_request_timing_policy() -> (
    TossApiCredentialRequestTimingResult
):
    """Run the local no-I/O credential request timing policy."""

    policy = build_toss_api_credential_request_timing_policy()
    candidate_stages = build_toss_api_credential_request_candidate_stages()
    requirements = build_toss_api_credential_request_requirements()
    approval_result = run_toss_api_readonly_live_smoke_approval_gate()
    approval_preflight = run_toss_api_readonly_live_smoke_approval_preflight_checks()
    decision = evaluate_toss_api_credential_request_timing_decision(
        approval_result=approval_result,
        approval_preflight=approval_preflight,
    )
    failures: list[str] = []
    failures.extend(_validate_timing_policy(policy))
    failures.extend(_validate_candidate_stages(candidate_stages))
    failures.extend(_validate_timing_requirements(requirements))
    failures.extend(_validate_timing_decision(decision))

    redacted_probe = redact_mapping(
        {"access_token": "dummy-sensitive-value"},
        build_toss_api_redaction_policy(),
    )
    if (
        redacted_probe["access_token"]
        != build_toss_api_redaction_policy().redaction_placeholder
    ):
        failures.append("redaction_probe_must_mask_sensitive_value")

    safe_message = "Credential timing policy closed for current stage."
    safe_diagnostics = (
        "pure_no_io_timing_policy",
        "approval_gate_reused",
        "future_candidate_recorded",
        "current_stage_closed",
        "redacted_summary_only",
    )
    sensitive_validation = validate_no_sensitive_output(
        {
            "safe_message": safe_message,
            "safe_diagnostics": safe_diagnostics,
            "safe_next_stage": DEFAULT_NEXT_STAGE,
        },
        build_toss_api_redaction_policy(),
    )
    failures.extend(sensitive_validation.failures)

    return TossApiCredentialRequestTimingResult(
        result_id="symbolic_credential_request_timing_result",
        passed=not failures and decision.approval_gate_passed,
        policy_closed_for_current_stage=True,
        candidate_stage_label=DEFAULT_CANDIDATE_STAGE_ID,
        decision=decision,
        requirement_ids=tuple(item.safe_requirement_id for item in requirements),
        safe_message=safe_message,
        safe_diagnostics=safe_diagnostics,
        next_stage=DEFAULT_NEXT_STAGE,
    )


def validate_toss_api_credential_request_timing_result(
    result: TossApiCredentialRequestTimingResult | None = None,
) -> TossApiCredentialRequestTimingValidationResult:
    """Validate the credential timing result."""

    active_result = result or run_toss_api_credential_request_timing_policy()
    failures: list[str] = []
    failures.extend(_validate_timing_decision(active_result.decision))
    if not active_result.passed:
        failures.append("timing_result_must_pass")
    if not active_result.policy_closed_for_current_stage:
        failures.append("policy_must_be_closed_for_current_stage")
    if active_result.requirement_ids != SAFE_TIMING_REQUIREMENT_IDS:
        failures.append("safe_timing_requirement_ids_must_match_contract")
    sensitive_validation = validate_no_sensitive_output(
        {
            "safe_message": active_result.safe_message,
            "safe_diagnostics": active_result.safe_diagnostics,
            "safe_next_stage": active_result.next_stage,
        },
        build_toss_api_redaction_policy(),
    )
    failures.extend(sensitive_validation.failures)

    return TossApiCredentialRequestTimingValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=_timing_policy_flag_names(),
        checked_candidate_stage_flags=_candidate_stage_flag_names(),
        checked_requirement_ids=TIMING_REQUIREMENT_IDS,
        checked_decision_flags=_timing_decision_flag_names(),
        checked_result_flags=_timing_result_flag_names(),
        diagnostics=(
            "pure_no_io_credential_request_timing_policy",
            "symbolic_credential_timing_policy_only",
            "current_stage_request_blocked",
            "future_candidate_requires_explicit_approval",
            "redacted_output_only",
        ),
    )


def run_toss_api_credential_request_timing_preflight_checks() -> (
    TossApiCredentialRequestTimingValidationResult
):
    """Run deterministic MS-15.03 credential timing checks."""

    for result in (
        run_toss_api_client_contract_preflight_checks(),
        run_toss_api_fake_transport_preflight_checks(),
        run_toss_api_config_guardrail_preflight_checks(),
        run_toss_api_live_readiness_preflight_checks(),
    ):
        if result.failures:
            return _failed_timing_validation(result.failures)
    no_secret_result = run_toss_api_no_secret_dry_run()
    if not no_secret_result.passed:
        return _failed_timing_validation(no_secret_result.failures)
    planning_preflight = run_toss_api_readonly_live_smoke_planning_preflight_checks()
    if not planning_preflight.passed:
        return _failed_timing_validation(planning_preflight.failures)
    disabled_preflight = run_toss_api_readonly_live_smoke_disabled_preflight_checks()
    if not disabled_preflight.passed:
        return _failed_timing_validation(disabled_preflight.failures)
    approval_preflight = run_toss_api_readonly_live_smoke_approval_preflight_checks()
    if not approval_preflight.passed:
        return _failed_timing_validation(approval_preflight.failures)
    return validate_toss_api_credential_request_timing_result(
        run_toss_api_credential_request_timing_policy()
    )


def _failed_timing_validation(
    failures: tuple[str, ...],
) -> TossApiCredentialRequestTimingValidationResult:
    return TossApiCredentialRequestTimingValidationResult(
        passed=False,
        failures=failures,
        checked_policy_flags=_timing_policy_flag_names(),
        checked_candidate_stage_flags=_candidate_stage_flag_names(),
        checked_requirement_ids=TIMING_REQUIREMENT_IDS,
        checked_decision_flags=_timing_decision_flag_names(),
        checked_result_flags=_timing_result_flag_names(),
        diagnostics=("timing_policy_dependency_failed",),
    )


def _validate_timing_policy(
    policy: TossApiCredentialRequestTimingPolicy,
) -> tuple[str, ...]:
    failures = [
        f"{flag}_must_be_true"
        for flag in _timing_policy_true_flag_names()
        if not getattr(policy, flag)
    ]
    failures.extend(
        f"{flag}_must_be_false"
        for flag in _timing_policy_false_flag_names()
        if getattr(policy, flag)
    )
    return tuple(failures)


def _validate_candidate_stages(
    candidate_stages: tuple[TossApiCredentialRequestCandidateStage, ...],
) -> tuple[str, ...]:
    failures: list[str] = []
    if len(candidate_stages) != 1:
        failures.append("one_candidate_stage_must_be_defined")
        return tuple(failures)
    candidate = candidate_stages[0]
    if candidate.stage_label != DEFAULT_CANDIDATE_STAGE_ID:
        failures.append("candidate_stage_must_point_to_ms_16_00")
    for flag in (
        "readonly_market_data_only",
        "may_request_toss_credentials_later",
        "requires_explicit_user_approval",
        "requires_redaction_policy",
        "requires_no_raw_payload_output",
        "requires_no_db_write",
        "requires_no_account_balance_fills",
        "requires_readonly_scope",
    ):
        if not getattr(candidate, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in (
        "may_request_openai_key_later",
        "may_request_account_seq_later",
        "may_request_order_scope_later",
        "live_execution_allowed_in_current_stage",
        "credential_request_allowed_in_current_stage",
    ):
        if getattr(candidate, flag):
            failures.append(f"{flag}_must_be_false")
    return tuple(failures)


def _validate_timing_requirements(
    requirements: tuple[TossApiCredentialRequestRequirement, ...],
) -> tuple[str, ...]:
    failures: list[str] = []
    if tuple(item.requirement_id for item in requirements) != TIMING_REQUIREMENT_IDS:
        failures.append("timing_requirement_ids_must_match_contract")
    if tuple(item.safe_requirement_id for item in requirements) != SAFE_TIMING_REQUIREMENT_IDS:
        failures.append("safe_timing_requirement_ids_must_match_contract")
    for item in requirements:
        if not item.required:
            failures.append(f"timing_requirement_must_be_required:{item.requirement_id}")
        if item.satisfied_now:
            failures.append(f"timing_requirement_must_not_be_satisfied_now:{item.requirement_id}")
        if not item.required_before_candidate_stage:
            failures.append(
                f"timing_requirement_must_precede_candidate:{item.requirement_id}"
            )
    return tuple(failures)


def _validate_timing_decision(
    decision: TossApiCredentialRequestTimingDecision,
) -> tuple[str, ...]:
    failures: list[str] = []
    for flag in (
        "timing_policy_invocation_allowed",
        "approval_gate_passed",
        "ms_16_00_can_request_toss_credentials_after_explicit_approval",
    ):
        if not getattr(decision, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in (
        "current_stage_credential_request_allowed",
        "current_stage_env_read_allowed",
        "current_stage_oauth_allowed",
        "current_stage_token_issuance_allowed",
        "current_stage_live_http_allowed",
        "current_stage_live_execution_allowed",
        "current_stage_account_seq_allowed",
        "current_stage_order_allowed",
        "current_stage_account_data_allowed",
        "current_stage_balance_allowed",
        "current_stage_fills_allowed",
        "current_stage_openai_key_allowed",
        "current_stage_llm_allowed",
        "ms_16_00_can_request_openai_key",
        "ms_16_00_can_use_account_seq",
        "ms_16_00_can_use_order_scope",
    ):
        if getattr(decision, flag):
            failures.append(f"{flag}_must_be_false")
    return tuple(failures)


def _timing_policy_true_flag_names() -> tuple[str, ...]:
    return (
        "credential_timing_policy_only",
        "explicit_user_approval_required_before_request",
        "separate_secret_entry_required",
        "separate_env_read_approval_required",
        "separate_oauth_approval_required",
        "separate_live_http_approval_required",
        "account_seq_must_remain_blocked",
        "order_scope_must_remain_blocked",
        "account_balance_fills_scope_must_remain_blocked",
        "raw_payload_output_must_remain_blocked",
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
        "no_live_http_now",
    )


def _timing_policy_false_flag_names() -> tuple[str, ...]:
    return (
        "current_stage_requests_credentials",
        "current_stage_reads_credentials",
        "current_stage_uses_credentials",
        "credential_required_now",
        "toss_key_required_now",
        "toss_secret_required_now",
        "openai_key_required_now",
        "access_token_required_now",
        "safe_to_request_user_secret_now",
        "live_execution_allowed_now",
        "credential_request_allowed_now",
    )


def _timing_policy_flag_names() -> tuple[str, ...]:
    return (*_timing_policy_true_flag_names(), *_timing_policy_false_flag_names())


def _candidate_stage_flag_names() -> tuple[str, ...]:
    return (
        "readonly_market_data_only",
        "may_request_toss_credentials_later",
        "may_request_openai_key_later",
        "may_request_account_seq_later",
        "may_request_order_scope_later",
        "requires_explicit_user_approval",
        "requires_redaction_policy",
        "requires_no_raw_payload_output",
        "requires_no_db_write",
        "requires_no_account_balance_fills",
        "requires_readonly_scope",
        "live_execution_allowed_in_current_stage",
        "credential_request_allowed_in_current_stage",
    )


def _timing_decision_flag_names() -> tuple[str, ...]:
    return (
        "timing_policy_invocation_allowed",
        "approval_gate_passed",
        "current_stage_credential_request_allowed",
        "current_stage_env_read_allowed",
        "current_stage_oauth_allowed",
        "current_stage_token_issuance_allowed",
        "current_stage_live_http_allowed",
        "current_stage_live_execution_allowed",
        "current_stage_account_seq_allowed",
        "current_stage_order_allowed",
        "current_stage_account_data_allowed",
        "current_stage_balance_allowed",
        "current_stage_fills_allowed",
        "current_stage_openai_key_allowed",
        "current_stage_llm_allowed",
        "ms_16_00_can_request_toss_credentials_after_explicit_approval",
        "ms_16_00_can_request_openai_key",
        "ms_16_00_can_use_account_seq",
        "ms_16_00_can_use_order_scope",
    )


def _timing_result_flag_names() -> tuple[str, ...]:
    return ("passed", "policy_closed_for_current_stage")
