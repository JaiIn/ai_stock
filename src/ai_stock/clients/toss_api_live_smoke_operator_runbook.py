"""MS-16.03 live smoke operator runbook rehearsal.

This module is pure no-I/O. It models operator prerequisites, runtime approval
checklist items, stop conditions, and runbook steps before any live HTTP smoke
can be attempted. It does not request credentials, read environment variables,
read files, write files, execute HTTP, issue OAuth tokens, create Authorization
headers, use accountSeq, touch account/order/balance/fills data, use DB storage,
import Streamlit, call OpenAI/LLM APIs, or generate recommendation/ranking/trade
actions.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai_stock.clients.toss_api_client_contract import (
    build_toss_api_redaction_policy,
    run_toss_api_client_contract_preflight_checks,
    validate_no_sensitive_output,
)
from ai_stock.clients.toss_api_config_guardrail import (
    run_toss_api_config_guardrail_preflight_checks,
)
from ai_stock.clients.toss_api_credential_timing import (
    run_toss_api_credential_request_timing_preflight_checks,
)
from ai_stock.clients.toss_api_fake_transport import (
    run_toss_api_fake_transport_preflight_checks,
)
from ai_stock.clients.toss_api_first_live_smoke import (
    run_toss_api_first_live_smoke_preflight_checks,
    validate_toss_api_first_live_smoke_result,
)
from ai_stock.clients.toss_api_live_readiness import (
    run_toss_api_live_readiness_preflight_checks,
    run_toss_api_no_secret_dry_run,
)
from ai_stock.clients.toss_api_live_smoke_approval import (
    run_toss_api_readonly_live_smoke_approval_preflight_checks,
)
from ai_stock.clients.toss_api_live_smoke_disabled import (
    run_toss_api_readonly_live_smoke_disabled_preflight_checks,
)
from ai_stock.clients.toss_api_live_smoke_plan import (
    run_toss_api_readonly_live_smoke_planning_preflight_checks,
)
from ai_stock.clients.toss_api_live_smoke_result_hardening import (
    run_toss_api_live_smoke_result_hardening_preflight_checks,
    validate_toss_api_live_smoke_result_hardening_result,
)
from ai_stock.clients.toss_api_readonly_endpoint_selection import (
    TossApiReadOnlyEndpointSelectionResult,
    run_toss_api_readonly_endpoint_selection,
    run_toss_api_readonly_endpoint_selection_preflight_checks,
    validate_toss_api_readonly_endpoint_selection_result,
)


TOSS_API_LIVE_SMOKE_OPERATOR_RUNBOOK_VERSION = "MS-16.03"
TOSS_API_LIVE_SMOKE_OPERATOR_RUNBOOK_SCOPE = (
    "live_smoke_operator_runbook_runtime_approval_rehearsal"
)
DEFAULT_NEXT_STAGE = (
    "MS-16.04 confirmed endpoint evidence update "
    "or MS-16.04 live smoke dry-run command contract"
)
SAFE_RESULT_ID = "safe_live_smoke_operator_rehearsal_result"
SAFE_MESSAGE_BLOCKED = "live_smoke_operator_rehearsal_blocked"
SAFE_DIAGNOSTICS_KIND = "redacted_operator_rehearsal_diagnostics"
SELECTED_ENDPOINT_MISSING = "selected_endpoint_missing"
ENDPOINT_SELECTION_BLOCKED = "endpoint_selection_blocked"
SAFE_LOCAL_CREDENTIAL_INSTRUCTION = (
    "Use only symbolic local session variable names "
    "AI_STOCK_TOSS_API_KEY and AI_STOCK_TOSS_API_SECRET later; never record "
    "values, partial values, length, hash, or fingerprint."
)
FORBIDDEN_SAFE_OUTPUT_FRAGMENTS = (
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
    "accountseq",
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
    ".env",
    "strong_buy",
    "recommendation",
    "ranking_position",
    "target_price",
    "expected_return",
    "profit_probability",
    "must_buy",
    "must_sell",
)


@dataclass(frozen=True)
class TossApiLiveSmokeOperatorRunbookPolicy:
    """Closed policy for operator runbook rehearsal only."""

    runbook_version: str
    runbook_scope: str
    operator_runbook_only: bool
    runtime_approval_rehearsal_only: bool
    live_http_execution_allowed: bool
    credential_request_allowed: bool
    credential_value_output_allowed: bool
    env_read_allowed: bool
    raw_request_output_allowed: bool
    raw_response_output_allowed: bool
    endpoint_full_url_output_allowed: bool
    endpoint_must_be_selected_before_live: bool
    selected_endpoint_required_for_live: bool
    current_selected_endpoint_available: bool
    current_endpoint_selection_blocked: bool
    account_seq_allowed: bool
    order_scope_allowed: bool
    account_data_allowed: bool
    balance_allowed: bool
    fills_allowed: bool
    oauth_token_issuance_allowed: bool
    access_token_required_now: bool
    db_read_allowed: bool
    db_write_allowed: bool
    streamlit_allowed: bool
    openai_key_allowed: bool
    llm_allowed: bool
    recommendation_allowed: bool
    ranking_allowed: bool
    buy_sell_hold_allowed: bool
    redacted_diagnostics_only: bool


@dataclass(frozen=True)
class TossApiLiveSmokeOperatorPrerequisite:
    """Symbolic prerequisite row without runtime inspection."""

    prerequisite_id: str
    prerequisite_label: str
    required_for_live: bool
    satisfied_now: bool
    blocking_if_unsatisfied: bool
    safe_operator_instruction: str


@dataclass(frozen=True)
class TossApiLiveSmokeRuntimeApprovalChecklist:
    """Runtime approval checklist rehearsal values."""

    checklist_id: str
    explicit_ms_16_live_http_approval_present: bool
    confirmed_readonly_endpoint_selected: bool
    confirmed_no_account_scope: bool
    confirmed_no_order_scope: bool
    confirmed_no_balance_scope: bool
    confirmed_no_fills_scope: bool
    confirmed_no_account_seq: bool
    confirmed_no_oauth_token_issuance: bool
    confirmed_raw_output_block: bool
    confirmed_redacted_diagnostics_only: bool
    confirmed_local_session_credentials_only: bool
    confirmed_no_env_files: bool
    confirmed_no_openai_key: bool
    confirmed_no_llm: bool
    approval_rehearsal_passed: bool


@dataclass(frozen=True)
class TossApiLiveSmokeStopCondition:
    """Stop condition that prevents live smoke progression."""

    stop_condition_id: str
    stop_condition_label: str
    triggered_now: bool
    severity: str
    safe_operator_action: str


@dataclass(frozen=True)
class TossApiLiveSmokeOperatorRunbookStep:
    """Symbolic runbook step with no executable command."""

    step_id: str
    step_label: str
    step_kind: str
    allowed_now: bool
    required_before_live: bool
    safe_instruction: str


@dataclass(frozen=True)
class TossApiLiveSmokeOperatorRehearsalDecision:
    """Closed rehearsal decision before live smoke can run."""

    operator_runbook_invocation_allowed: bool
    runtime_approval_rehearsal_only: bool
    ms_16_00_preflight_passed: bool
    ms_16_01_hardening_passed: bool
    ms_16_02_endpoint_selection_passed: bool
    selected_endpoint_available: bool
    endpoint_selection_blocked: bool
    live_http_execution_allowed_now: bool
    credential_request_allowed_now: bool
    env_read_allowed_now: bool
    oauth_allowed_now: bool
    token_issuance_allowed_now: bool
    account_seq_allowed_now: bool
    order_allowed_now: bool
    account_data_allowed_now: bool
    balance_allowed_now: bool
    fills_allowed_now: bool
    openai_key_allowed_now: bool
    llm_allowed_now: bool
    db_write_allowed_now: bool
    streamlit_allowed_now: bool
    recommendation_allowed_now: bool
    ranking_allowed_now: bool
    buy_sell_hold_allowed_now: bool
    raw_request_output_allowed: bool
    raw_response_output_allowed: bool
    endpoint_full_url_output_allowed: bool
    rehearsal_blocked: bool
    blocking_reasons: tuple[str, ...]
    next_stage: str


@dataclass(frozen=True)
class TossApiLiveSmokeOperatorRehearsalResult:
    """Top-level safe operator rehearsal result."""

    result_id: str
    passed: bool
    policy: TossApiLiveSmokeOperatorRunbookPolicy
    prerequisites: tuple[TossApiLiveSmokeOperatorPrerequisite, ...]
    approval_checklist: TossApiLiveSmokeRuntimeApprovalChecklist
    stop_conditions: tuple[TossApiLiveSmokeStopCondition, ...]
    runbook_steps: tuple[TossApiLiveSmokeOperatorRunbookStep, ...]
    decision: TossApiLiveSmokeOperatorRehearsalDecision
    safe_message: str
    safe_diagnostics: tuple[str, ...]
    next_stage: str


@dataclass(frozen=True)
class TossApiLiveSmokeOperatorRehearsalValidationResult:
    """Validation result for MS-16.03 operator rehearsal."""

    passed: bool
    failures: tuple[str, ...]
    checked_policy_flags: tuple[str, ...]
    checked_prerequisite_fields: tuple[str, ...]
    checked_approval_checklist_fields: tuple[str, ...]
    checked_stop_condition_fields: tuple[str, ...]
    checked_runbook_step_fields: tuple[str, ...]
    checked_decision_fields: tuple[str, ...]
    checked_result_fields: tuple[str, ...]
    diagnostics: tuple[str, ...]


def build_toss_api_live_smoke_operator_runbook_policy() -> (
    TossApiLiveSmokeOperatorRunbookPolicy
):
    """Build the closed operator runbook rehearsal policy."""

    return TossApiLiveSmokeOperatorRunbookPolicy(
        runbook_version=TOSS_API_LIVE_SMOKE_OPERATOR_RUNBOOK_VERSION,
        runbook_scope=TOSS_API_LIVE_SMOKE_OPERATOR_RUNBOOK_SCOPE,
        operator_runbook_only=True,
        runtime_approval_rehearsal_only=True,
        live_http_execution_allowed=False,
        credential_request_allowed=False,
        credential_value_output_allowed=False,
        env_read_allowed=False,
        raw_request_output_allowed=False,
        raw_response_output_allowed=False,
        endpoint_full_url_output_allowed=False,
        endpoint_must_be_selected_before_live=True,
        selected_endpoint_required_for_live=True,
        current_selected_endpoint_available=False,
        current_endpoint_selection_blocked=True,
        account_seq_allowed=False,
        order_scope_allowed=False,
        account_data_allowed=False,
        balance_allowed=False,
        fills_allowed=False,
        oauth_token_issuance_allowed=False,
        access_token_required_now=False,
        db_read_allowed=False,
        db_write_allowed=False,
        streamlit_allowed=False,
        openai_key_allowed=False,
        llm_allowed=False,
        recommendation_allowed=False,
        ranking_allowed=False,
        buy_sell_hold_allowed=False,
        redacted_diagnostics_only=True,
    )


def build_toss_api_live_smoke_operator_prerequisites(
    selection_result: TossApiReadOnlyEndpointSelectionResult | None = None,
) -> tuple[TossApiLiveSmokeOperatorPrerequisite, ...]:
    """Build symbolic prerequisites without checking runtime state."""

    active_selection = selection_result or run_toss_api_readonly_endpoint_selection()
    selected_available = active_selection.decision.selected_endpoint_id is not None
    return (
        _prerequisite(
            "confirmed_readonly_endpoint_selected",
            "confirmed readonly endpoint selected",
            selected_available,
            "Stop until a symbolic confirmed read-only public candidate is selected.",
        ),
        _prerequisite(
            "ms_16_00_first_live_smoke_framework_available",
            "MS-16.00 first live smoke framework available",
            True,
            "Review the MS-16.00 blocked dry-run framework only.",
        ),
        _prerequisite(
            "ms_16_01_result_hardening_available",
            "MS-16.01 result hardening available",
            True,
            "Review redacted summary and validation controls only.",
        ),
        _prerequisite(
            "ms_16_02_endpoint_selection_available",
            "MS-16.02 endpoint selection available",
            active_selection.passed,
            "Require endpoint selection validation before any later run.",
        ),
        _prerequisite(
            "runtime_live_http_approval_required",
            "runtime live HTTP approval required",
            False,
            "Rehearse approval wording only; do not collect approval in this stage.",
        ),
        _prerequisite(
            "credential_local_session_only",
            "credential local session only",
            False,
            SAFE_LOCAL_CREDENTIAL_INSTRUCTION,
        ),
        _prerequisite(
            "raw_output_block_required",
            "raw output block required",
            True,
            "Keep request and response payload output blocked.",
        ),
        _prerequisite(
            "account_scope_block_required",
            "account scope block required",
            True,
            "Keep account scope unavailable.",
        ),
        _prerequisite(
            "order_scope_block_required",
            "order scope block required",
            True,
            "Keep order scope unavailable.",
        ),
        _prerequisite(
            "oauth_token_scope_block_required",
            "OAuth token scope block required",
            True,
            "Keep OAuth token issuance unavailable.",
        ),
        _prerequisite(
            "env_file_usage_block_required",
            "environment file usage block required",
            True,
            "Do not use environment files in this rehearsal.",
        ),
        _prerequisite(
            "no_llm_no_openai_required",
            "no LLM or OpenAI scope required",
            True,
            "Keep OpenAI and LLM scope unavailable.",
        ),
    )


def build_toss_api_live_smoke_runtime_approval_checklist(
    selection_result: TossApiReadOnlyEndpointSelectionResult | None = None,
) -> TossApiLiveSmokeRuntimeApprovalChecklist:
    """Build default runtime approval checklist values."""

    active_selection = selection_result or run_toss_api_readonly_endpoint_selection()
    selected_available = active_selection.decision.selected_endpoint_id is not None
    return TossApiLiveSmokeRuntimeApprovalChecklist(
        checklist_id="ms_16_03_runtime_approval_rehearsal_checklist",
        explicit_ms_16_live_http_approval_present=False,
        confirmed_readonly_endpoint_selected=selected_available,
        confirmed_no_account_scope=True,
        confirmed_no_order_scope=True,
        confirmed_no_balance_scope=True,
        confirmed_no_fills_scope=True,
        confirmed_no_account_seq=True,
        confirmed_no_oauth_token_issuance=True,
        confirmed_raw_output_block=True,
        confirmed_redacted_diagnostics_only=True,
        confirmed_local_session_credentials_only=False,
        confirmed_no_env_files=True,
        confirmed_no_openai_key=True,
        confirmed_no_llm=True,
        approval_rehearsal_passed=False,
    )


def build_toss_api_live_smoke_stop_conditions(
    selection_result: TossApiReadOnlyEndpointSelectionResult | None = None,
) -> tuple[TossApiLiveSmokeStopCondition, ...]:
    """Build stop conditions; default selection stop conditions are triggered."""

    active_selection = selection_result or run_toss_api_readonly_endpoint_selection()
    selected_missing = active_selection.decision.selected_endpoint_id is None
    selection_blocked = active_selection.decision.selection_blocked
    return (
        _stop_condition(SELECTED_ENDPOINT_MISSING, selected_missing),
        _stop_condition(ENDPOINT_SELECTION_BLOCKED, selection_blocked),
        _stop_condition("endpoint_requires_account_seq", False),
        _stop_condition("endpoint_requires_order_scope", False),
        _stop_condition("endpoint_requires_oauth_token", False),
        _stop_condition("raw_response_would_be_exposed", False),
        _stop_condition("credential_value_would_be_exposed", False),
        _stop_condition("env_file_required", False),
        _stop_condition("account_balance_fills_scope_detected", False),
        _stop_condition("openai_or_llm_scope_detected", False),
        _stop_condition("recommendation_or_trading_action_detected", False),
    )


def build_toss_api_live_smoke_operator_runbook_steps() -> (
    tuple[TossApiLiveSmokeOperatorRunbookStep, ...]
):
    """Build symbolic runbook steps without commands."""

    return (
        _runbook_step("verify_main_commit", "verify main commit", True),
        _runbook_step("verify_ms_16_00_preflight", "verify MS-16.00 preflight", True),
        _runbook_step("verify_ms_16_01_hardening", "verify MS-16.01 hardening", True),
        _runbook_step(
            "verify_ms_16_02_endpoint_selection",
            "verify MS-16.02 endpoint selection",
            True,
        ),
        _runbook_step("verify_selected_endpoint", "verify selected endpoint", False),
        _runbook_step("collect_runtime_approval", "rehearse runtime approval", False),
        _runbook_step(
            "require_local_session_credentials",
            "rehearse local session credential rule",
            False,
        ),
        _runbook_step("block_env_files", "verify environment file block", True),
        _runbook_step("block_raw_output", "verify raw output block", True),
        _runbook_step("block_account_scope", "verify account scope block", True),
        _runbook_step("block_order_scope", "verify order scope block", True),
        _runbook_step("block_oauth_token_scope", "verify OAuth token scope block", True),
        _runbook_step("execute_live_http_smoke", "live HTTP smoke remains blocked", False),
    )


def evaluate_toss_api_live_smoke_operator_rehearsal_decision(
    selection_result: TossApiReadOnlyEndpointSelectionResult | None = None,
) -> TossApiLiveSmokeOperatorRehearsalDecision:
    """Evaluate the closed operator rehearsal decision."""

    active_selection = selection_result or run_toss_api_readonly_endpoint_selection()
    selected_available = active_selection.decision.selected_endpoint_id is not None
    endpoint_blocked = active_selection.decision.selection_blocked
    reasons = _blocking_reasons(selected_available, endpoint_blocked)
    return TossApiLiveSmokeOperatorRehearsalDecision(
        operator_runbook_invocation_allowed=True,
        runtime_approval_rehearsal_only=True,
        ms_16_00_preflight_passed=True,
        ms_16_01_hardening_passed=True,
        ms_16_02_endpoint_selection_passed=active_selection.passed,
        selected_endpoint_available=selected_available,
        endpoint_selection_blocked=endpoint_blocked,
        live_http_execution_allowed_now=False,
        credential_request_allowed_now=False,
        env_read_allowed_now=False,
        oauth_allowed_now=False,
        token_issuance_allowed_now=False,
        account_seq_allowed_now=False,
        order_allowed_now=False,
        account_data_allowed_now=False,
        balance_allowed_now=False,
        fills_allowed_now=False,
        openai_key_allowed_now=False,
        llm_allowed_now=False,
        db_write_allowed_now=False,
        streamlit_allowed_now=False,
        recommendation_allowed_now=False,
        ranking_allowed_now=False,
        buy_sell_hold_allowed_now=False,
        raw_request_output_allowed=False,
        raw_response_output_allowed=False,
        endpoint_full_url_output_allowed=False,
        rehearsal_blocked=bool(reasons),
        blocking_reasons=reasons,
        next_stage=DEFAULT_NEXT_STAGE,
    )


def run_toss_api_live_smoke_operator_rehearsal(
    selection_result: TossApiReadOnlyEndpointSelectionResult | None = None,
) -> TossApiLiveSmokeOperatorRehearsalResult:
    """Run deterministic no-I/O operator rehearsal."""

    active_selection = selection_result or run_toss_api_readonly_endpoint_selection()
    policy = build_toss_api_live_smoke_operator_runbook_policy()
    prerequisites = build_toss_api_live_smoke_operator_prerequisites(active_selection)
    approval_checklist = build_toss_api_live_smoke_runtime_approval_checklist(
        active_selection
    )
    stop_conditions = build_toss_api_live_smoke_stop_conditions(active_selection)
    runbook_steps = build_toss_api_live_smoke_operator_runbook_steps()
    decision = evaluate_toss_api_live_smoke_operator_rehearsal_decision(
        active_selection
    )
    triggered_ids = tuple(
        condition.stop_condition_id
        for condition in stop_conditions
        if condition.triggered_now
    )
    safe_diagnostics = (
        SAFE_DIAGNOSTICS_KIND,
        f"prerequisite_count={len(prerequisites)}",
        f"stop_condition_count={len(stop_conditions)}",
        "triggered_stop_condition_ids=" + ",".join(triggered_ids or ("none",)),
        f"runbook_step_count={len(runbook_steps)}",
        f"selected_endpoint_id={active_selection.decision.selected_endpoint_id or 'None'}",
        "selected_endpoint_label="
        + f"{active_selection.decision.selected_endpoint_label or 'None'}",
        f"rehearsal_blocked={decision.rehearsal_blocked}",
        "blocking_reason_ids=" + ",".join(decision.blocking_reasons or ("none",)),
        "redaction_applied=True",
    )
    result = TossApiLiveSmokeOperatorRehearsalResult(
        result_id=SAFE_RESULT_ID,
        passed=False,
        policy=policy,
        prerequisites=prerequisites,
        approval_checklist=approval_checklist,
        stop_conditions=stop_conditions,
        runbook_steps=runbook_steps,
        decision=decision,
        safe_message=SAFE_MESSAGE_BLOCKED,
        safe_diagnostics=safe_diagnostics,
        next_stage=DEFAULT_NEXT_STAGE,
    )
    validation = validate_toss_api_live_smoke_operator_rehearsal_result(result)
    return TossApiLiveSmokeOperatorRehearsalResult(
        result_id=result.result_id,
        passed=validation.passed,
        policy=result.policy,
        prerequisites=result.prerequisites,
        approval_checklist=result.approval_checklist,
        stop_conditions=result.stop_conditions,
        runbook_steps=result.runbook_steps,
        decision=result.decision,
        safe_message=result.safe_message,
        safe_diagnostics=result.safe_diagnostics,
        next_stage=result.next_stage,
    )


def validate_toss_api_live_smoke_operator_rehearsal_result(
    result: TossApiLiveSmokeOperatorRehearsalResult | None = None,
) -> TossApiLiveSmokeOperatorRehearsalValidationResult:
    """Validate that operator rehearsal remains safe and blocked."""

    active_result = result or run_toss_api_live_smoke_operator_rehearsal()
    failures: list[str] = []
    failures.extend(_validate_policy(active_result.policy))
    failures.extend(_validate_prerequisites(active_result.prerequisites))
    failures.extend(_validate_approval_checklist(active_result.approval_checklist))
    failures.extend(_validate_stop_conditions(active_result.stop_conditions))
    failures.extend(_validate_runbook_steps(active_result.runbook_steps))
    failures.extend(_validate_decision(active_result.decision))
    failures.extend(_validate_result(active_result))
    sensitive_validation = validate_no_sensitive_output(
        {
            "safe_message": active_result.safe_message,
            "safe_diagnostics": active_result.safe_diagnostics,
            "next_stage": active_result.next_stage,
        },
        build_toss_api_redaction_policy(),
    )
    failures.extend(sensitive_validation.failures)
    return TossApiLiveSmokeOperatorRehearsalValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=_policy_flag_names(),
        checked_prerequisite_fields=_prerequisite_field_names(),
        checked_approval_checklist_fields=_approval_checklist_field_names(),
        checked_stop_condition_fields=_stop_condition_field_names(),
        checked_runbook_step_fields=_runbook_step_field_names(),
        checked_decision_fields=_decision_field_names(),
        checked_result_fields=_result_field_names(),
        diagnostics=("operator_runbook_rehearsal_validation",),
    )


def run_toss_api_live_smoke_operator_rehearsal_preflight_checks() -> (
    TossApiLiveSmokeOperatorRehearsalValidationResult
):
    """Run dependency and rehearsal checks without I/O or live HTTP."""

    for result in (
        run_toss_api_client_contract_preflight_checks(),
        run_toss_api_fake_transport_preflight_checks(),
        run_toss_api_config_guardrail_preflight_checks(),
        run_toss_api_live_readiness_preflight_checks(),
    ):
        if result.failures:
            return _failed_validation(result.failures)
    no_secret_result = run_toss_api_no_secret_dry_run()
    if not no_secret_result.passed:
        return _failed_validation(no_secret_result.failures)
    for result in (
        run_toss_api_readonly_live_smoke_planning_preflight_checks(),
        run_toss_api_readonly_live_smoke_disabled_preflight_checks(),
        run_toss_api_readonly_live_smoke_approval_preflight_checks(),
        run_toss_api_credential_request_timing_preflight_checks(),
        run_toss_api_first_live_smoke_preflight_checks(),
        run_toss_api_live_smoke_result_hardening_preflight_checks(),
        run_toss_api_readonly_endpoint_selection_preflight_checks(),
    ):
        if not result.passed:
            return _failed_validation(result.failures)
    first_validation = validate_toss_api_first_live_smoke_result()
    if not first_validation.passed:
        return _failed_validation(first_validation.failures)
    hardening_validation = validate_toss_api_live_smoke_result_hardening_result()
    if not hardening_validation.passed:
        return _failed_validation(hardening_validation.failures)
    selection_validation = validate_toss_api_readonly_endpoint_selection_result()
    if not selection_validation.passed:
        return _failed_validation(selection_validation.failures)
    return validate_toss_api_live_smoke_operator_rehearsal_result(
        run_toss_api_live_smoke_operator_rehearsal()
    )


def _prerequisite(
    prerequisite_id: str,
    label: str,
    satisfied_now: bool,
    instruction: str,
) -> TossApiLiveSmokeOperatorPrerequisite:
    return TossApiLiveSmokeOperatorPrerequisite(
        prerequisite_id=prerequisite_id,
        prerequisite_label=label,
        required_for_live=True,
        satisfied_now=satisfied_now,
        blocking_if_unsatisfied=True,
        safe_operator_instruction=instruction,
    )


def _stop_condition(
    stop_condition_id: str,
    triggered_now: bool,
) -> TossApiLiveSmokeStopCondition:
    return TossApiLiveSmokeStopCondition(
        stop_condition_id=stop_condition_id,
        stop_condition_label=stop_condition_id,
        triggered_now=triggered_now,
        severity="blocker" if triggered_now else "guard",
        safe_operator_action="stop_and_keep_rehearsal_closed"
        if triggered_now
        else "keep_guard_active",
    )


def _runbook_step(
    step_id: str,
    label: str,
    allowed_now: bool,
) -> TossApiLiveSmokeOperatorRunbookStep:
    return TossApiLiveSmokeOperatorRunbookStep(
        step_id=step_id,
        step_label=label,
        step_kind="symbolic_rehearsal_step",
        allowed_now=allowed_now,
        required_before_live=True,
        safe_instruction="symbolic checklist item only; no executable command",
    )


def _blocking_reasons(
    selected_available: bool,
    endpoint_selection_blocked: bool,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not selected_available:
        reasons.append(SELECTED_ENDPOINT_MISSING)
    if endpoint_selection_blocked:
        reasons.append(ENDPOINT_SELECTION_BLOCKED)
    return tuple(reasons)


def _validate_policy(
    policy: TossApiLiveSmokeOperatorRunbookPolicy,
) -> tuple[str, ...]:
    failures: list[str] = []
    for flag in _policy_true_flag_names():
        if not getattr(policy, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in _policy_false_flag_names():
        if getattr(policy, flag):
            failures.append(f"{flag}_must_be_false")
    return tuple(failures)


def _validate_prerequisites(
    prerequisites: tuple[TossApiLiveSmokeOperatorPrerequisite, ...],
) -> tuple[str, ...]:
    failures: list[str] = []
    ids = {item.prerequisite_id for item in prerequisites}
    if "credential_local_session_only" not in ids:
        failures.append("credential_local_session_only_prerequisite_missing")
    for item in prerequisites:
        instruction = item.safe_operator_instruction.casefold()
        if ".env" in instruction:
            failures.append("prerequisite_must_not_refer_to_env_file")
    return tuple(failures)


def _validate_approval_checklist(
    checklist: TossApiLiveSmokeRuntimeApprovalChecklist,
) -> tuple[str, ...]:
    failures: list[str] = []
    if checklist.explicit_ms_16_live_http_approval_present:
        failures.append("approval_must_not_be_present_in_rehearsal")
    if checklist.confirmed_readonly_endpoint_selected:
        failures.append("default_selected_endpoint_must_be_false")
    if checklist.approval_rehearsal_passed:
        failures.append("approval_rehearsal_must_be_false")
    return tuple(failures)


def _validate_stop_conditions(
    stop_conditions: tuple[TossApiLiveSmokeStopCondition, ...],
) -> tuple[str, ...]:
    triggered = {
        condition.stop_condition_id
        for condition in stop_conditions
        if condition.triggered_now
    }
    failures: list[str] = []
    if SELECTED_ENDPOINT_MISSING not in triggered:
        failures.append("selected_endpoint_missing_stop_condition_must_trigger")
    if ENDPOINT_SELECTION_BLOCKED not in triggered:
        failures.append("endpoint_selection_blocked_stop_condition_must_trigger")
    return tuple(failures)


def _validate_runbook_steps(
    steps: tuple[TossApiLiveSmokeOperatorRunbookStep, ...],
) -> tuple[str, ...]:
    failures: list[str] = []
    execute_steps = [step for step in steps if step.step_id == "execute_live_http_smoke"]
    if len(execute_steps) != 1:
        failures.append("execute_live_http_smoke_step_missing")
    elif execute_steps[0].allowed_now:
        failures.append("execute_live_http_smoke_must_be_disallowed")
    for step in steps:
        if ".env" in step.safe_instruction.casefold():
            failures.append("runbook_step_must_not_refer_to_env_file")
    return tuple(failures)


def _validate_decision(
    decision: TossApiLiveSmokeOperatorRehearsalDecision,
) -> tuple[str, ...]:
    failures: list[str] = []
    for flag in _decision_true_flag_names():
        if not getattr(decision, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in _decision_false_flag_names():
        if getattr(decision, flag):
            failures.append(f"{flag}_must_be_false")
    for required_reason in (SELECTED_ENDPOINT_MISSING, ENDPOINT_SELECTION_BLOCKED):
        if required_reason not in decision.blocking_reasons:
            failures.append(f"{required_reason}_blocking_reason_missing")
    return tuple(failures)


def _validate_result(
    result: TossApiLiveSmokeOperatorRehearsalResult,
) -> tuple[str, ...]:
    failures: list[str] = []
    diagnostics_text = " ".join(result.safe_diagnostics).casefold()
    safe_text = " ".join(
        (
            result.result_id,
            result.safe_message,
            *result.safe_diagnostics,
            *result.decision.blocking_reasons,
            result.next_stage,
        )
    ).casefold()
    if _contains_forbidden_fragment(safe_text):
        failures.append("forbidden_safe_output_fragment_exposed")
    if "/" in diagnostics_text or "http:" in diagnostics_text or "https:" in diagnostics_text:
        failures.append("endpoint_full_url_or_path_exposed")
    if "command" in diagnostics_text:
        failures.append("execution_command_exposed")
    return tuple(failures)


def _contains_forbidden_fragment(value: str) -> bool:
    lowered = value.casefold()
    return any(fragment in lowered for fragment in FORBIDDEN_SAFE_OUTPUT_FRAGMENTS)


def _failed_validation(
    failures: tuple[str, ...],
) -> TossApiLiveSmokeOperatorRehearsalValidationResult:
    return TossApiLiveSmokeOperatorRehearsalValidationResult(
        passed=False,
        failures=failures,
        checked_policy_flags=_policy_flag_names(),
        checked_prerequisite_fields=_prerequisite_field_names(),
        checked_approval_checklist_fields=_approval_checklist_field_names(),
        checked_stop_condition_fields=_stop_condition_field_names(),
        checked_runbook_step_fields=_runbook_step_field_names(),
        checked_decision_fields=_decision_field_names(),
        checked_result_fields=_result_field_names(),
        diagnostics=("operator_rehearsal_dependency_failed",),
    )


def _policy_true_flag_names() -> tuple[str, ...]:
    return (
        "operator_runbook_only",
        "runtime_approval_rehearsal_only",
        "endpoint_must_be_selected_before_live",
        "selected_endpoint_required_for_live",
        "current_endpoint_selection_blocked",
        "redacted_diagnostics_only",
    )


def _policy_false_flag_names() -> tuple[str, ...]:
    return (
        "live_http_execution_allowed",
        "credential_request_allowed",
        "credential_value_output_allowed",
        "env_read_allowed",
        "raw_request_output_allowed",
        "raw_response_output_allowed",
        "endpoint_full_url_output_allowed",
        "current_selected_endpoint_available",
        "account_seq_allowed",
        "order_scope_allowed",
        "account_data_allowed",
        "balance_allowed",
        "fills_allowed",
        "oauth_token_issuance_allowed",
        "access_token_required_now",
        "db_read_allowed",
        "db_write_allowed",
        "streamlit_allowed",
        "openai_key_allowed",
        "llm_allowed",
        "recommendation_allowed",
        "ranking_allowed",
        "buy_sell_hold_allowed",
    )


def _policy_flag_names() -> tuple[str, ...]:
    return (*_policy_true_flag_names(), *_policy_false_flag_names())


def _prerequisite_field_names() -> tuple[str, ...]:
    return (
        "prerequisite_id",
        "prerequisite_label",
        "required_for_live",
        "satisfied_now",
        "blocking_if_unsatisfied",
        "safe_operator_instruction",
    )


def _approval_checklist_field_names() -> tuple[str, ...]:
    return (
        "checklist_id",
        "explicit_ms_16_live_http_approval_present",
        "confirmed_readonly_endpoint_selected",
        "confirmed_no_account_scope",
        "confirmed_no_order_scope",
        "confirmed_no_balance_scope",
        "confirmed_no_fills_scope",
        "confirmed_no_account_seq",
        "confirmed_no_oauth_token_issuance",
        "confirmed_raw_output_block",
        "confirmed_redacted_diagnostics_only",
        "confirmed_local_session_credentials_only",
        "confirmed_no_env_files",
        "confirmed_no_openai_key",
        "confirmed_no_llm",
        "approval_rehearsal_passed",
    )


def _stop_condition_field_names() -> tuple[str, ...]:
    return (
        "stop_condition_id",
        "stop_condition_label",
        "triggered_now",
        "severity",
        "safe_operator_action",
    )


def _runbook_step_field_names() -> tuple[str, ...]:
    return (
        "step_id",
        "step_label",
        "step_kind",
        "allowed_now",
        "required_before_live",
        "safe_instruction",
    )


def _decision_true_flag_names() -> tuple[str, ...]:
    return (
        "operator_runbook_invocation_allowed",
        "runtime_approval_rehearsal_only",
        "ms_16_00_preflight_passed",
        "ms_16_01_hardening_passed",
        "ms_16_02_endpoint_selection_passed",
        "endpoint_selection_blocked",
        "rehearsal_blocked",
    )


def _decision_false_flag_names() -> tuple[str, ...]:
    return (
        "selected_endpoint_available",
        "live_http_execution_allowed_now",
        "credential_request_allowed_now",
        "env_read_allowed_now",
        "oauth_allowed_now",
        "token_issuance_allowed_now",
        "account_seq_allowed_now",
        "order_allowed_now",
        "account_data_allowed_now",
        "balance_allowed_now",
        "fills_allowed_now",
        "openai_key_allowed_now",
        "llm_allowed_now",
        "db_write_allowed_now",
        "streamlit_allowed_now",
        "recommendation_allowed_now",
        "ranking_allowed_now",
        "buy_sell_hold_allowed_now",
        "raw_request_output_allowed",
        "raw_response_output_allowed",
        "endpoint_full_url_output_allowed",
    )


def _decision_field_names() -> tuple[str, ...]:
    return (*_decision_true_flag_names(), *_decision_false_flag_names())


def _result_field_names() -> tuple[str, ...]:
    return (
        "result_id",
        "passed",
        "policy",
        "prerequisites",
        "approval_checklist",
        "stop_conditions",
        "runbook_steps",
        "decision",
        "safe_message",
        "safe_diagnostics",
        "next_stage",
    )
