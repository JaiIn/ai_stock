"""Disabled read-only Toss API live smoke skeleton.

This module exposes a local pure-function entry point that proves a future
read-only live smoke is still disabled. It reuses the MS-14 and MS-15.00
preflight layers and never loads runtime config or calls services.
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
from ai_stock.clients.toss_api_live_smoke_plan import (
    TossApiReadOnlyLiveSmokePlan,
    TossApiReadOnlyLiveSmokePlanningValidationResult,
    build_toss_api_readonly_live_smoke_plan,
    run_toss_api_readonly_live_smoke_planning_preflight_checks,
)


TOSS_API_READONLY_LIVE_SMOKE_DISABLED_VERSION = "MS-15.01"
TOSS_API_READONLY_LIVE_SMOKE_DISABLED_SCOPE = (
    "pure_no_io_readonly_live_smoke_disabled_skeleton"
)
DEFAULT_DISABLED_REQUEST_ID = "symbolic_disabled_readonly_smoke_request"
DEFAULT_DISABLED_TARGET_ID = "symbolic_market_data_readonly_smoke"
DEFAULT_NEXT_STAGE = "MS-15.02 read-only live smoke explicit approval gate"


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokeDisabledPolicy:
    """Policy proving the skeleton is callable but execution remains disabled."""

    skeleton_version: str
    skeleton_scope: str
    disabled_skeleton_only: bool
    planning_gate_required: bool
    uses_ms_15_00_plan: bool
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
    disabled_execution_result_only: bool
    explicit_user_approval_required_for_live_stage: bool


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokeDisabledRequest:
    """Symbolic request shape for the disabled skeleton."""

    symbolic_request_id: str
    target_id: str
    request_scope: str
    readonly: bool
    planning_only: bool
    disabled: bool
    live_call_attempted: bool
    credential_attached: bool
    token_attached: bool
    account_seq_attached: bool
    raw_payload_attached: bool


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokeDisabledDecision:
    """Decision returned by the disabled skeleton gate."""

    skeleton_invocation_allowed: bool
    planning_gate_passed: bool
    live_execution_allowed_now: bool
    credential_request_allowed_now: bool
    oauth_allowed_now: bool
    token_issuance_allowed_now: bool
    account_seq_allowed_now: bool
    order_allowed_now: bool
    account_data_allowed_now: bool
    balance_allowed_now: bool
    fills_allowed_now: bool
    openai_key_allowed_now: bool
    llm_allowed_now: bool
    disabled_reason: str
    next_stage: str
    explicit_approval_required: bool


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokeDisabledResult:
    """Safe result from invoking the disabled skeleton."""

    result_id: str
    passed: bool
    disabled: bool
    decision: TossApiReadOnlyLiveSmokeDisabledDecision
    safe_message: str
    safe_diagnostics: tuple[str, ...]
    next_stage: str


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokeDisabledValidationResult:
    """Validation result for the disabled skeleton output."""

    passed: bool
    failures: tuple[str, ...]
    checked_policy_flags: tuple[str, ...]
    checked_request_flags: tuple[str, ...]
    checked_decision_flags: tuple[str, ...]
    checked_result_flags: tuple[str, ...]
    diagnostics: tuple[str, ...]


def build_toss_api_readonly_live_smoke_disabled_policy() -> (
    TossApiReadOnlyLiveSmokeDisabledPolicy
):
    """Build the closed MS-15.01 disabled skeleton policy."""

    return TossApiReadOnlyLiveSmokeDisabledPolicy(
        skeleton_version=TOSS_API_READONLY_LIVE_SMOKE_DISABLED_VERSION,
        skeleton_scope=TOSS_API_READONLY_LIVE_SMOKE_DISABLED_SCOPE,
        disabled_skeleton_only=True,
        planning_gate_required=True,
        uses_ms_15_00_plan=True,
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
        disabled_execution_result_only=True,
        explicit_user_approval_required_for_live_stage=True,
    )


def build_toss_api_readonly_live_smoke_disabled_request(
    *,
    symbolic_request_id: str = DEFAULT_DISABLED_REQUEST_ID,
    target_id: str = DEFAULT_DISABLED_TARGET_ID,
) -> TossApiReadOnlyLiveSmokeDisabledRequest:
    """Build a symbolic disabled skeleton request."""

    return TossApiReadOnlyLiveSmokeDisabledRequest(
        symbolic_request_id=symbolic_request_id,
        target_id=target_id,
        request_scope="symbolic_disabled_readonly_smoke_entrypoint",
        readonly=True,
        planning_only=True,
        disabled=True,
        live_call_attempted=False,
        credential_attached=False,
        token_attached=False,
        account_seq_attached=False,
        raw_payload_attached=False,
    )


def evaluate_toss_api_readonly_live_smoke_disabled_decision(
    plan: TossApiReadOnlyLiveSmokePlan | None = None,
    planning_preflight: TossApiReadOnlyLiveSmokePlanningValidationResult | None = None,
) -> TossApiReadOnlyLiveSmokeDisabledDecision:
    """Evaluate the closed decision using the MS-15.00 planning gate."""

    active_plan = plan or build_toss_api_readonly_live_smoke_plan()
    active_preflight = (
        planning_preflight
        or run_toss_api_readonly_live_smoke_planning_preflight_checks()
    )
    planning_gate_passed = (
        active_plan.execution_gate.planning_passed and active_preflight.passed
    )

    return TossApiReadOnlyLiveSmokeDisabledDecision(
        skeleton_invocation_allowed=True,
        planning_gate_passed=planning_gate_passed,
        live_execution_allowed_now=False,
        credential_request_allowed_now=False,
        oauth_allowed_now=False,
        token_issuance_allowed_now=False,
        account_seq_allowed_now=False,
        order_allowed_now=False,
        account_data_allowed_now=False,
        balance_allowed_now=False,
        fills_allowed_now=False,
        openai_key_allowed_now=False,
        llm_allowed_now=False,
        disabled_reason="explicit_future_live_stage_required",
        next_stage=DEFAULT_NEXT_STAGE,
        explicit_approval_required=True,
    )


def run_toss_api_readonly_live_smoke_disabled_skeleton(
    request: TossApiReadOnlyLiveSmokeDisabledRequest | None = None,
) -> TossApiReadOnlyLiveSmokeDisabledResult:
    """Invoke the local disabled skeleton without runtime access."""

    active_request = request or build_toss_api_readonly_live_smoke_disabled_request()
    plan = build_toss_api_readonly_live_smoke_plan()
    planning_preflight = run_toss_api_readonly_live_smoke_planning_preflight_checks()
    decision = evaluate_toss_api_readonly_live_smoke_disabled_decision(
        plan=plan,
        planning_preflight=planning_preflight,
    )
    policy = build_toss_api_readonly_live_smoke_disabled_policy()
    failures: list[str] = []
    failures.extend(_validate_disabled_policy(policy))
    failures.extend(_validate_disabled_request(active_request, plan))
    failures.extend(_validate_disabled_decision(decision))

    redacted_probe = redact_mapping(
        {"access_token": "dummy-sensitive-value"},
        build_toss_api_redaction_policy(),
    )
    if (
        redacted_probe["access_token"]
        != build_toss_api_redaction_policy().redaction_placeholder
    ):
        failures.append("redaction_probe_must_mask_sensitive_value")

    safe_message = "Disabled skeleton only; future explicit approval required."
    safe_diagnostics = (
        "pure_no_io_disabled_skeleton",
        "planning_gate_reused",
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

    return TossApiReadOnlyLiveSmokeDisabledResult(
        result_id="symbolic_disabled_readonly_smoke_result",
        passed=not failures and decision.planning_gate_passed,
        disabled=True,
        decision=decision,
        safe_message=safe_message,
        safe_diagnostics=safe_diagnostics,
        next_stage=DEFAULT_NEXT_STAGE,
    )


def validate_toss_api_readonly_live_smoke_disabled_result(
    result: TossApiReadOnlyLiveSmokeDisabledResult | None = None,
) -> TossApiReadOnlyLiveSmokeDisabledValidationResult:
    """Validate disabled skeleton output."""

    active_result = result or run_toss_api_readonly_live_smoke_disabled_skeleton()
    failures: list[str] = []
    failures.extend(_validate_disabled_decision(active_result.decision))
    if not active_result.passed:
        failures.append("disabled_result_must_pass")
    if not active_result.disabled:
        failures.append("disabled_result_must_stay_disabled")
    if active_result.next_stage != DEFAULT_NEXT_STAGE:
        failures.append("next_stage_must_match_contract")
    sensitive_validation = validate_no_sensitive_output(
        {
            "safe_message": active_result.safe_message,
            "safe_diagnostics": active_result.safe_diagnostics,
            "safe_next_stage": active_result.next_stage,
        },
        build_toss_api_redaction_policy(),
    )
    failures.extend(sensitive_validation.failures)

    return TossApiReadOnlyLiveSmokeDisabledValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=_disabled_policy_flag_names(),
        checked_request_flags=_disabled_request_flag_names(),
        checked_decision_flags=_disabled_decision_flag_names(),
        checked_result_flags=_disabled_result_flag_names(),
        diagnostics=(
            "pure_no_io_readonly_live_smoke_disabled_skeleton",
            "symbolic_disabled_skeleton_only",
            "live_execution_blocked_now",
            "redacted_output_only",
        ),
    )


def run_toss_api_readonly_live_smoke_disabled_preflight_checks() -> (
    TossApiReadOnlyLiveSmokeDisabledValidationResult
):
    """Run deterministic MS-15.01 disabled skeleton checks."""

    for result in (
        run_toss_api_client_contract_preflight_checks(),
        run_toss_api_fake_transport_preflight_checks(),
        run_toss_api_config_guardrail_preflight_checks(),
        run_toss_api_live_readiness_preflight_checks(),
    ):
        if result.failures:
            disabled_result = run_toss_api_readonly_live_smoke_disabled_skeleton()
            return TossApiReadOnlyLiveSmokeDisabledValidationResult(
                passed=False,
                failures=result.failures,
                checked_policy_flags=_disabled_policy_flag_names(),
                checked_request_flags=_disabled_request_flag_names(),
                checked_decision_flags=_disabled_decision_flag_names(),
                checked_result_flags=_disabled_result_flag_names(),
                diagnostics=disabled_result.safe_diagnostics,
            )
    no_secret_result = run_toss_api_no_secret_dry_run()
    if not no_secret_result.passed:
        return TossApiReadOnlyLiveSmokeDisabledValidationResult(
            passed=False,
            failures=no_secret_result.failures,
            checked_policy_flags=_disabled_policy_flag_names(),
            checked_request_flags=_disabled_request_flag_names(),
            checked_decision_flags=_disabled_decision_flag_names(),
            checked_result_flags=_disabled_result_flag_names(),
            diagnostics=("no_secret_dry_run_must_pass",),
        )
    planning_preflight = run_toss_api_readonly_live_smoke_planning_preflight_checks()
    if not planning_preflight.passed:
        return TossApiReadOnlyLiveSmokeDisabledValidationResult(
            passed=False,
            failures=planning_preflight.failures,
            checked_policy_flags=_disabled_policy_flag_names(),
            checked_request_flags=_disabled_request_flag_names(),
            checked_decision_flags=_disabled_decision_flag_names(),
            checked_result_flags=_disabled_result_flag_names(),
            diagnostics=planning_preflight.diagnostics,
        )
    return validate_toss_api_readonly_live_smoke_disabled_result(
        run_toss_api_readonly_live_smoke_disabled_skeleton()
    )


def _validate_disabled_policy(
    policy: TossApiReadOnlyLiveSmokeDisabledPolicy,
) -> tuple[str, ...]:
    failures = [
        f"{flag}_must_be_true"
        for flag in _disabled_policy_true_flag_names()
        if not getattr(policy, flag)
    ]
    failures.extend(
        f"{flag}_must_be_false"
        for flag in _disabled_policy_false_flag_names()
        if getattr(policy, flag)
    )
    return tuple(failures)


def _validate_disabled_request(
    request: TossApiReadOnlyLiveSmokeDisabledRequest,
    plan: TossApiReadOnlyLiveSmokePlan,
) -> tuple[str, ...]:
    failures: list[str] = []
    target_ids = {target.target_id for target in plan.targets}
    if request.target_id not in target_ids:
        failures.append("disabled_request_target_must_match_planning_target")
    for flag in ("readonly", "planning_only", "disabled"):
        if not getattr(request, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in (
        "live_call_attempted",
        "credential_attached",
        "token_attached",
        "account_seq_attached",
        "raw_payload_attached",
    ):
        if getattr(request, flag):
            failures.append(f"{flag}_must_be_false")
    return tuple(failures)


def _validate_disabled_decision(
    decision: TossApiReadOnlyLiveSmokeDisabledDecision,
) -> tuple[str, ...]:
    failures: list[str] = []
    if not decision.skeleton_invocation_allowed:
        failures.append("skeleton_invocation_allowed_must_be_true")
    if not decision.planning_gate_passed:
        failures.append("planning_gate_passed_must_be_true")
    if not decision.explicit_approval_required:
        failures.append("explicit_approval_required_must_be_true")
    if decision.next_stage != DEFAULT_NEXT_STAGE:
        failures.append("next_stage_must_match_contract")
    for flag in (
        "live_execution_allowed_now",
        "credential_request_allowed_now",
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


def _disabled_policy_true_flag_names() -> tuple[str, ...]:
    return (
        "disabled_skeleton_only",
        "planning_gate_required",
        "uses_ms_15_00_plan",
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
        "explicit_user_approval_required_for_live_stage",
    )


def _disabled_policy_false_flag_names() -> tuple[str, ...]:
    return (
        "credential_required_now",
        "toss_key_required_now",
        "toss_secret_required_now",
        "openai_key_required_now",
        "access_token_required_now",
        "safe_to_request_user_secret_now",
        "live_execution_allowed_now",
    )


def _disabled_policy_flag_names() -> tuple[str, ...]:
    return (*_disabled_policy_true_flag_names(), *_disabled_policy_false_flag_names())


def _disabled_request_flag_names() -> tuple[str, ...]:
    return (
        "readonly",
        "planning_only",
        "disabled",
        "live_call_attempted",
        "credential_attached",
        "token_attached",
        "account_seq_attached",
        "raw_payload_attached",
    )


def _disabled_decision_flag_names() -> tuple[str, ...]:
    return (
        "skeleton_invocation_allowed",
        "planning_gate_passed",
        "live_execution_allowed_now",
        "credential_request_allowed_now",
        "oauth_allowed_now",
        "token_issuance_allowed_now",
        "account_seq_allowed_now",
        "order_allowed_now",
        "account_data_allowed_now",
        "balance_allowed_now",
        "fills_allowed_now",
        "openai_key_allowed_now",
        "llm_allowed_now",
        "explicit_approval_required",
    )


def _disabled_result_flag_names() -> tuple[str, ...]:
    return ("passed", "disabled")
