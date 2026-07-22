"""Explicit approval gate for a future read-only Toss API live smoke.

This module models the approval gate as pure no-I/O data and deterministic
helpers. It records that no explicit approval is present in MS-15.02 and keeps
runtime execution, credential requests, OAuth, and live HTTP blocked.
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
from ai_stock.clients.toss_api_live_smoke_disabled import (
    TossApiReadOnlyLiveSmokeDisabledResult,
    TossApiReadOnlyLiveSmokeDisabledValidationResult,
    run_toss_api_readonly_live_smoke_disabled_preflight_checks,
    run_toss_api_readonly_live_smoke_disabled_skeleton,
)
from ai_stock.clients.toss_api_live_smoke_plan import (
    TossApiReadOnlyLiveSmokePlan,
    TossApiReadOnlyLiveSmokePlanningValidationResult,
    build_toss_api_readonly_live_smoke_plan,
    run_toss_api_readonly_live_smoke_planning_preflight_checks,
)


TOSS_API_READONLY_LIVE_SMOKE_APPROVAL_VERSION = "MS-15.02"
TOSS_API_READONLY_LIVE_SMOKE_APPROVAL_SCOPE = (
    "pure_no_io_readonly_live_smoke_explicit_approval_gate"
)
DEFAULT_APPROVAL_INTENT_ID = "symbolic_readonly_smoke_approval_intent"
DEFAULT_REQUESTED_STAGE_LABEL = "symbolic_readonly_live_smoke_future_stage"
DEFAULT_NEXT_STAGE = "MS-15.03 credential request timing policy"
APPROVAL_REQUIREMENT_IDS = (
    "explicit_user_message_required",
    "branch_stage_must_be_live_smoke_stage",
    "read_only_scope_required",
    "credential_request_must_be_separately_approved",
    "env_read_must_be_separately_approved",
    "oauth_token_must_be_separately_approved",
    "live_http_must_be_separately_approved",
    "account_seq_must_remain_blocked",
    "order_scope_must_remain_blocked",
    "account_balance_fills_scope_must_remain_blocked",
    "raw_payload_output_must_remain_blocked",
    "rollback_path_required",
    "redacted_diagnostics_only_required",
)
SAFE_REQUIREMENT_IDS = tuple(
    f"safe_requirement_{index:02d}"
    for index, _ in enumerate(APPROVAL_REQUIREMENT_IDS, start=1)
)


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokeApprovalPolicy:
    """Policy proving approval is modeled but not granted in MS-15.02."""

    approval_version: str
    approval_scope: str
    approval_gate_only: bool
    explicit_user_approval_required: bool
    disabled_skeleton_required: bool
    planning_gate_required: bool
    uses_ms_15_00_plan: bool
    uses_ms_15_01_disabled_skeleton: bool
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
    disabled_execution_result_only: bool


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokeApprovalIntent:
    """Symbolic intent that does not record actual approval."""

    symbolic_intent_id: str
    requested_stage_label: str
    requested_scope: str
    readonly: bool
    planning_only: bool
    approval_recorded: bool
    live_call_requested: bool
    live_call_approved: bool
    credential_request_approved: bool
    oauth_approved: bool
    token_issuance_approved: bool
    account_seq_approved: bool
    order_approved: bool
    account_data_approved: bool
    raw_payload_approved: bool


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokeApprovalRequirement:
    """One symbolic approval requirement for a future live stage."""

    requirement_id: str
    safe_requirement_id: str
    category: str
    required: bool
    satisfied_now: bool
    evidence_label: str


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokeApprovalDecision:
    """Closed approval gate decision for MS-15.02."""

    approval_gate_invocation_allowed: bool
    planning_gate_passed: bool
    disabled_skeleton_passed: bool
    explicit_approval_present: bool
    live_execution_allowed_now: bool
    credential_request_allowed_now: bool
    env_read_allowed_now: bool
    file_read_allowed_now: bool
    oauth_allowed_now: bool
    token_issuance_allowed_now: bool
    account_seq_allowed_now: bool
    order_allowed_now: bool
    account_data_allowed_now: bool
    balance_allowed_now: bool
    fills_allowed_now: bool
    openai_key_allowed_now: bool
    llm_allowed_now: bool
    next_stage: str
    blocking_reasons: tuple[str, ...]
    safe_summary: tuple[str, ...]


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokeApprovalGateResult:
    """Safe result from evaluating the approval gate."""

    result_id: str
    passed: bool
    gate_closed: bool
    decision: TossApiReadOnlyLiveSmokeApprovalDecision
    requirement_ids: tuple[str, ...]
    safe_message: str
    safe_diagnostics: tuple[str, ...]
    next_stage: str


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokeApprovalValidationResult:
    """Validation result for the explicit approval gate."""

    passed: bool
    failures: tuple[str, ...]
    checked_policy_flags: tuple[str, ...]
    checked_intent_flags: tuple[str, ...]
    checked_requirement_ids: tuple[str, ...]
    checked_decision_flags: tuple[str, ...]
    checked_result_flags: tuple[str, ...]
    diagnostics: tuple[str, ...]


def build_toss_api_readonly_live_smoke_approval_policy() -> (
    TossApiReadOnlyLiveSmokeApprovalPolicy
):
    """Build the closed MS-15.02 approval policy."""

    return TossApiReadOnlyLiveSmokeApprovalPolicy(
        approval_version=TOSS_API_READONLY_LIVE_SMOKE_APPROVAL_VERSION,
        approval_scope=TOSS_API_READONLY_LIVE_SMOKE_APPROVAL_SCOPE,
        approval_gate_only=True,
        explicit_user_approval_required=True,
        disabled_skeleton_required=True,
        planning_gate_required=True,
        uses_ms_15_00_plan=True,
        uses_ms_15_01_disabled_skeleton=True,
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
        disabled_execution_result_only=True,
    )


def build_toss_api_readonly_live_smoke_approval_intent(
    *,
    symbolic_intent_id: str = DEFAULT_APPROVAL_INTENT_ID,
    requested_stage_label: str = DEFAULT_REQUESTED_STAGE_LABEL,
) -> TossApiReadOnlyLiveSmokeApprovalIntent:
    """Build a symbolic no-approval intent."""

    return TossApiReadOnlyLiveSmokeApprovalIntent(
        symbolic_intent_id=symbolic_intent_id,
        requested_stage_label=requested_stage_label,
        requested_scope="symbolic_explicit_approval_gate_entrypoint",
        readonly=True,
        planning_only=True,
        approval_recorded=False,
        live_call_requested=False,
        live_call_approved=False,
        credential_request_approved=False,
        oauth_approved=False,
        token_issuance_approved=False,
        account_seq_approved=False,
        order_approved=False,
        account_data_approved=False,
        raw_payload_approved=False,
    )


def build_toss_api_readonly_live_smoke_approval_requirements() -> (
    tuple[TossApiReadOnlyLiveSmokeApprovalRequirement, ...]
):
    """Build symbolic requirements for a future explicit approval stage."""

    return tuple(
        TossApiReadOnlyLiveSmokeApprovalRequirement(
            requirement_id=requirement_id,
            safe_requirement_id=safe_requirement_id,
            category="explicit_approval_gate",
            required=True,
            satisfied_now=False,
            evidence_label="future_explicit_stage_required",
        )
        for requirement_id, safe_requirement_id in zip(
            APPROVAL_REQUIREMENT_IDS,
            SAFE_REQUIREMENT_IDS,
            strict=True,
        )
    )


def evaluate_toss_api_readonly_live_smoke_approval_decision(
    plan: TossApiReadOnlyLiveSmokePlan | None = None,
    planning_preflight: TossApiReadOnlyLiveSmokePlanningValidationResult | None = None,
    disabled_result: TossApiReadOnlyLiveSmokeDisabledResult | None = None,
    disabled_preflight: TossApiReadOnlyLiveSmokeDisabledValidationResult | None = None,
) -> TossApiReadOnlyLiveSmokeApprovalDecision:
    """Evaluate the approval decision while keeping the gate closed."""

    active_plan = plan or build_toss_api_readonly_live_smoke_plan()
    active_planning_preflight = (
        planning_preflight
        or run_toss_api_readonly_live_smoke_planning_preflight_checks()
    )
    active_disabled_result = (
        disabled_result or run_toss_api_readonly_live_smoke_disabled_skeleton()
    )
    active_disabled_preflight = (
        disabled_preflight
        or run_toss_api_readonly_live_smoke_disabled_preflight_checks()
    )
    planning_gate_passed = (
        active_plan.execution_gate.planning_passed
        and active_planning_preflight.passed
    )
    disabled_skeleton_passed = (
        active_disabled_result.passed
        and active_disabled_result.disabled
        and active_disabled_preflight.passed
    )

    return TossApiReadOnlyLiveSmokeApprovalDecision(
        approval_gate_invocation_allowed=True,
        planning_gate_passed=planning_gate_passed,
        disabled_skeleton_passed=disabled_skeleton_passed,
        explicit_approval_present=False,
        live_execution_allowed_now=False,
        credential_request_allowed_now=False,
        env_read_allowed_now=False,
        file_read_allowed_now=False,
        oauth_allowed_now=False,
        token_issuance_allowed_now=False,
        account_seq_allowed_now=False,
        order_allowed_now=False,
        account_data_allowed_now=False,
        balance_allowed_now=False,
        fills_allowed_now=False,
        openai_key_allowed_now=False,
        llm_allowed_now=False,
        next_stage=DEFAULT_NEXT_STAGE,
        blocking_reasons=(
            "future_explicit_approval_absent",
            "runtime_access_closed",
            "secret_prompt_closed",
        ),
        safe_summary=(
            "gate_closed",
            "approval_absent",
            "redacted_summary_only",
        ),
    )


def run_toss_api_readonly_live_smoke_approval_gate(
    intent: TossApiReadOnlyLiveSmokeApprovalIntent | None = None,
) -> TossApiReadOnlyLiveSmokeApprovalGateResult:
    """Run the local no-I/O explicit approval gate."""

    active_intent = intent or build_toss_api_readonly_live_smoke_approval_intent()
    plan = build_toss_api_readonly_live_smoke_plan()
    planning_preflight = run_toss_api_readonly_live_smoke_planning_preflight_checks()
    disabled_result = run_toss_api_readonly_live_smoke_disabled_skeleton()
    disabled_preflight = run_toss_api_readonly_live_smoke_disabled_preflight_checks()
    requirements = build_toss_api_readonly_live_smoke_approval_requirements()
    decision = evaluate_toss_api_readonly_live_smoke_approval_decision(
        plan=plan,
        planning_preflight=planning_preflight,
        disabled_result=disabled_result,
        disabled_preflight=disabled_preflight,
    )
    failures: list[str] = []
    failures.extend(_validate_approval_policy(build_toss_api_readonly_live_smoke_approval_policy()))
    failures.extend(_validate_approval_intent(active_intent))
    failures.extend(_validate_approval_requirements(requirements))
    failures.extend(_validate_approval_decision(decision))

    redacted_probe = redact_mapping(
        {"access_token": "dummy-sensitive-value"},
        build_toss_api_redaction_policy(),
    )
    if (
        redacted_probe["access_token"]
        != build_toss_api_redaction_policy().redaction_placeholder
    ):
        failures.append("redaction_probe_must_mask_sensitive_value")

    safe_message = "Approval gate closed; future explicit approval required."
    safe_diagnostics = (
        "pure_no_io_approval_gate",
        "planning_gate_reused",
        "disabled_skeleton_reused",
        "runtime_execution_closed",
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

    return TossApiReadOnlyLiveSmokeApprovalGateResult(
        result_id="symbolic_readonly_live_smoke_approval_gate_result",
        passed=not failures
        and decision.planning_gate_passed
        and decision.disabled_skeleton_passed,
        gate_closed=True,
        decision=decision,
        requirement_ids=tuple(item.safe_requirement_id for item in requirements),
        safe_message=safe_message,
        safe_diagnostics=safe_diagnostics,
        next_stage=DEFAULT_NEXT_STAGE,
    )


def validate_toss_api_readonly_live_smoke_approval_gate_result(
    result: TossApiReadOnlyLiveSmokeApprovalGateResult | None = None,
) -> TossApiReadOnlyLiveSmokeApprovalValidationResult:
    """Validate approval gate output."""

    active_result = result or run_toss_api_readonly_live_smoke_approval_gate()
    failures: list[str] = []
    failures.extend(_validate_approval_decision(active_result.decision))
    if not active_result.passed:
        failures.append("approval_gate_result_must_pass")
    if not active_result.gate_closed:
        failures.append("approval_gate_must_remain_closed")
    if active_result.requirement_ids != SAFE_REQUIREMENT_IDS:
        failures.append("safe_requirement_ids_must_match_contract")
    sensitive_validation = validate_no_sensitive_output(
        {
            "safe_message": active_result.safe_message,
            "safe_diagnostics": active_result.safe_diagnostics,
            "safe_next_stage": active_result.next_stage,
        },
        build_toss_api_redaction_policy(),
    )
    failures.extend(sensitive_validation.failures)

    return TossApiReadOnlyLiveSmokeApprovalValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=_approval_policy_flag_names(),
        checked_intent_flags=_approval_intent_flag_names(),
        checked_requirement_ids=APPROVAL_REQUIREMENT_IDS,
        checked_decision_flags=_approval_decision_flag_names(),
        checked_result_flags=_approval_result_flag_names(),
        diagnostics=(
            "pure_no_io_readonly_live_smoke_explicit_approval_gate",
            "symbolic_explicit_approval_gate_only",
            "explicit_approval_absent",
            "live_execution_blocked_now",
            "redacted_output_only",
        ),
    )


def run_toss_api_readonly_live_smoke_approval_preflight_checks() -> (
    TossApiReadOnlyLiveSmokeApprovalValidationResult
):
    """Run deterministic MS-15.02 approval gate checks."""

    for result in (
        run_toss_api_client_contract_preflight_checks(),
        run_toss_api_fake_transport_preflight_checks(),
        run_toss_api_config_guardrail_preflight_checks(),
        run_toss_api_live_readiness_preflight_checks(),
    ):
        if result.failures:
            return _failed_approval_validation(result.failures)
    no_secret_result = run_toss_api_no_secret_dry_run()
    if not no_secret_result.passed:
        return _failed_approval_validation(no_secret_result.failures)
    planning_preflight = run_toss_api_readonly_live_smoke_planning_preflight_checks()
    if not planning_preflight.passed:
        return _failed_approval_validation(planning_preflight.failures)
    disabled_preflight = run_toss_api_readonly_live_smoke_disabled_preflight_checks()
    if not disabled_preflight.passed:
        return _failed_approval_validation(disabled_preflight.failures)
    return validate_toss_api_readonly_live_smoke_approval_gate_result(
        run_toss_api_readonly_live_smoke_approval_gate()
    )


def _failed_approval_validation(
    failures: tuple[str, ...],
) -> TossApiReadOnlyLiveSmokeApprovalValidationResult:
    return TossApiReadOnlyLiveSmokeApprovalValidationResult(
        passed=False,
        failures=failures,
        checked_policy_flags=_approval_policy_flag_names(),
        checked_intent_flags=_approval_intent_flag_names(),
        checked_requirement_ids=APPROVAL_REQUIREMENT_IDS,
        checked_decision_flags=_approval_decision_flag_names(),
        checked_result_flags=_approval_result_flag_names(),
        diagnostics=("approval_gate_dependency_failed",),
    )


def _validate_approval_policy(
    policy: TossApiReadOnlyLiveSmokeApprovalPolicy,
) -> tuple[str, ...]:
    failures = [
        f"{flag}_must_be_true"
        for flag in _approval_policy_true_flag_names()
        if not getattr(policy, flag)
    ]
    failures.extend(
        f"{flag}_must_be_false"
        for flag in _approval_policy_false_flag_names()
        if getattr(policy, flag)
    )
    return tuple(failures)


def _validate_approval_intent(
    intent: TossApiReadOnlyLiveSmokeApprovalIntent,
) -> tuple[str, ...]:
    failures: list[str] = []
    for flag in ("readonly", "planning_only"):
        if not getattr(intent, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in (
        "approval_recorded",
        "live_call_requested",
        "live_call_approved",
        "credential_request_approved",
        "oauth_approved",
        "token_issuance_approved",
        "account_seq_approved",
        "order_approved",
        "account_data_approved",
        "raw_payload_approved",
    ):
        if getattr(intent, flag):
            failures.append(f"{flag}_must_be_false")
    return tuple(failures)


def _validate_approval_requirements(
    requirements: tuple[TossApiReadOnlyLiveSmokeApprovalRequirement, ...],
) -> tuple[str, ...]:
    failures: list[str] = []
    if tuple(item.requirement_id for item in requirements) != APPROVAL_REQUIREMENT_IDS:
        failures.append("approval_requirement_ids_must_match_contract")
    if tuple(item.safe_requirement_id for item in requirements) != SAFE_REQUIREMENT_IDS:
        failures.append("safe_requirement_ids_must_match_contract")
    for item in requirements:
        if not item.required:
            failures.append(f"approval_requirement_must_be_required:{item.requirement_id}")
        if item.satisfied_now:
            failures.append(f"approval_requirement_must_not_be_satisfied_now:{item.requirement_id}")
    return tuple(failures)


def _validate_approval_decision(
    decision: TossApiReadOnlyLiveSmokeApprovalDecision,
) -> tuple[str, ...]:
    failures: list[str] = []
    for flag in (
        "approval_gate_invocation_allowed",
        "planning_gate_passed",
        "disabled_skeleton_passed",
    ):
        if not getattr(decision, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in (
        "explicit_approval_present",
        "live_execution_allowed_now",
        "credential_request_allowed_now",
        "env_read_allowed_now",
        "file_read_allowed_now",
        "oauth_allowed_now",
        "token_issuance_allowed_now",
        "account_seq_allowed_now",
        "order_allowed_now",
        "account_data_allowed_now",
        "balance_allowed_now",
        "fills_allowed_now",
        "openai_key_allowed_now",
        "llm_allowed_now",
    ):
        if getattr(decision, flag):
            failures.append(f"{flag}_must_be_false")
    return tuple(failures)


def _approval_policy_true_flag_names() -> tuple[str, ...]:
    return (
        "approval_gate_only",
        "explicit_user_approval_required",
        "disabled_skeleton_required",
        "planning_gate_required",
        "uses_ms_15_00_plan",
        "uses_ms_15_01_disabled_skeleton",
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
        "disabled_execution_result_only",
    )


def _approval_policy_false_flag_names() -> tuple[str, ...]:
    return (
        "credential_required_now",
        "toss_key_required_now",
        "toss_secret_required_now",
        "openai_key_required_now",
        "access_token_required_now",
        "safe_to_request_user_secret_now",
        "live_execution_allowed_now",
        "credential_request_allowed_now",
    )


def _approval_policy_flag_names() -> tuple[str, ...]:
    return (*_approval_policy_true_flag_names(), *_approval_policy_false_flag_names())


def _approval_intent_flag_names() -> tuple[str, ...]:
    return (
        "readonly",
        "planning_only",
        "approval_recorded",
        "live_call_requested",
        "live_call_approved",
        "credential_request_approved",
        "oauth_approved",
        "token_issuance_approved",
        "account_seq_approved",
        "order_approved",
        "account_data_approved",
        "raw_payload_approved",
    )


def _approval_decision_flag_names() -> tuple[str, ...]:
    return (
        "approval_gate_invocation_allowed",
        "planning_gate_passed",
        "disabled_skeleton_passed",
        "explicit_approval_present",
        "live_execution_allowed_now",
        "credential_request_allowed_now",
        "env_read_allowed_now",
        "file_read_allowed_now",
        "oauth_allowed_now",
        "token_issuance_allowed_now",
        "account_seq_allowed_now",
        "order_allowed_now",
        "account_data_allowed_now",
        "balance_allowed_now",
        "fills_allowed_now",
        "openai_key_allowed_now",
        "llm_allowed_now",
    )


def _approval_result_flag_names() -> tuple[str, ...]:
    return ("passed", "gate_closed")
