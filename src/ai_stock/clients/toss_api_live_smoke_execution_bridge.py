"""MS-16.05a live smoke auth/execution bridge realignment.

This module is pure no-I/O. It supersedes the MS-16.04 OAuth-free assumption
for the selected Prices read-only market-data endpoint while preserving the
symbolic endpoint selection. It does not read credentials or environment
variables, issue tokens, create headers, execute HTTP, write files, touch DB
storage, import Streamlit, call OpenAI/LLM APIs, or produce recommendation or
trading actions.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai_stock.clients.toss_api_client_contract import (
    build_toss_api_redaction_policy,
    validate_no_sensitive_output,
)
from ai_stock.clients.toss_api_confirmed_endpoint_evidence import (
    run_toss_api_confirmed_endpoint_evidence_update,
    validate_toss_api_confirmed_endpoint_evidence_result,
)
from ai_stock.clients.toss_api_first_live_smoke import (
    run_toss_api_first_live_smoke_preflight_checks,
)
from ai_stock.clients.toss_api_live_smoke_operator_runbook import (
    run_toss_api_live_smoke_operator_rehearsal_preflight_checks,
)
from ai_stock.clients.toss_api_live_smoke_result_hardening import (
    run_toss_api_live_smoke_result_hardening_preflight_checks,
)
from ai_stock.clients.toss_api_readonly_endpoint_selection import (
    run_toss_api_readonly_endpoint_selection_preflight_checks,
)


TOSS_API_LIVE_SMOKE_EXECUTION_BRIDGE_VERSION = "MS-16.05a"
TOSS_API_LIVE_SMOKE_EXECUTION_BRIDGE_SCOPE = (
    "live_smoke_auth_execution_bridge_realignment"
)
SELECTED_ENDPOINT_ID = "confirmed_prices_single_symbol_readonly_market_data"
SELECTED_ENDPOINT_LABEL = "Prices single-symbol read-only market data"
OPERATION_KIND = "getPrices"
NEXT_STAGE = "MS-16.05b first actual read-only live HTTP smoke"
SAFE_RESULT_ID = "safe_live_smoke_execution_bridge_result"
SAFE_MESSAGE = "live_smoke_auth_execution_bridge_ready"
SAFE_DIAGNOSTICS_KIND = "redacted_live_smoke_execution_bridge_diagnostics"
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
class TossApiLiveSmokeExecutionBridgePolicy:
    """Closed policy for bridge realignment only."""

    bridge_version: str
    bridge_scope: str
    execution_bridge_only: bool
    auth_realignment_only: bool
    actual_live_http_allowed: bool
    oauth_token_request_allowed_now: bool
    readonly_business_request_allowed_now: bool
    credential_request_allowed: bool
    credential_presence_check_allowed: bool
    env_read_allowed: bool
    credential_value_output_allowed: bool
    access_token_output_allowed: bool
    authorization_bearer_output_allowed: bool
    raw_request_output_allowed: bool
    raw_response_output_allowed: bool
    endpoint_full_url_output_allowed: bool
    account_seq_allowed: bool
    order_scope_allowed: bool
    account_data_allowed: bool
    balance_allowed: bool
    fills_allowed: bool
    retry_loop_allowed: bool
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
class TossApiLiveSmokeAuthRealignment:
    """Superseding record for the selected endpoint auth requirement."""

    realignment_id: str
    selected_endpoint_id: str
    selected_endpoint_label: str
    previous_oauth_required_assumption: bool
    corrected_oauth_required: bool
    corrected_access_token_required: bool
    corrected_authorization_bearer_required: bool
    account_seq_required: bool
    order_scope_required: bool
    account_balance_fills_required: bool
    correction_reason: str
    supersedes_ms_16_04_oauth_assumption: bool


@dataclass(frozen=True)
class TossApiLiveSmokeExecutionPlan:
    """Future MS-16.05b execution plan without executable request material."""

    plan_id: str
    selected_endpoint_id: str
    selected_endpoint_label: str
    operation_kind: str
    planned_network_call_count: int
    planned_oauth_call_count: int
    planned_readonly_business_call_count: int
    planned_retry_count: int
    credential_source_policy: str
    token_storage_policy: str
    authorization_header_output_allowed: bool
    access_token_output_allowed: bool
    raw_request_output_allowed: bool
    raw_response_output_allowed: bool
    endpoint_full_url_output_allowed: bool
    account_seq_used: bool
    order_scope_used: bool
    account_balance_fills_scope_used: bool
    ready_for_ms_16_05b: bool


@dataclass(frozen=True)
class TossApiLiveSmokeExecutionGuard:
    """Guard flags required before the future live smoke stage."""

    confirmed_endpoint_selected: bool
    oauth_requirement_realigned: bool
    access_token_output_blocked: bool
    authorization_header_output_blocked: bool
    raw_request_output_blocked: bool
    raw_response_output_blocked: bool
    endpoint_full_url_output_blocked: bool
    account_seq_blocked: bool
    order_scope_blocked: bool
    account_balance_fills_scope_blocked: bool
    retry_loop_blocked: bool
    credential_values_blocked: bool
    env_files_blocked: bool
    no_db_write: bool
    no_streamlit: bool
    no_openai_llm: bool
    no_recommendation_or_trading_action: bool


@dataclass(frozen=True)
class TossApiLiveSmokeExecutionBridgeDecision:
    """Decision proving this stage plans but does not execute live HTTP."""

    execution_bridge_invocation_allowed: bool
    execution_bridge_only: bool
    actual_live_http_attempted: bool
    oauth_token_request_attempted: bool
    readonly_business_request_attempted: bool
    credential_request_performed: bool
    credential_presence_check_performed: bool
    env_read_performed: bool
    selected_endpoint_id: str
    selected_endpoint_ready: bool
    oauth_requirement_realigned: bool
    future_ms_16_05b_network_call_count: int
    future_ms_16_05b_oauth_call_count: int
    future_ms_16_05b_readonly_business_call_count: int
    future_ms_16_05b_retry_count: int
    ready_for_ms_16_05b: bool
    live_http_execution_allowed_now: bool
    credential_request_allowed_now: bool
    credential_presence_check_allowed_now: bool
    env_read_allowed_now: bool
    oauth_token_issuance_allowed_now: bool
    access_token_output_allowed: bool
    authorization_bearer_output_allowed: bool
    raw_request_output_allowed: bool
    raw_response_output_allowed: bool
    endpoint_full_url_output_allowed: bool
    account_seq_allowed_now: bool
    order_allowed_now: bool
    account_data_allowed_now: bool
    balance_allowed_now: bool
    fills_allowed_now: bool
    db_write_allowed_now: bool
    streamlit_allowed_now: bool
    openai_key_allowed_now: bool
    llm_allowed_now: bool
    recommendation_allowed_now: bool
    ranking_allowed_now: bool
    buy_sell_hold_allowed_now: bool
    next_stage: str


@dataclass(frozen=True)
class TossApiLiveSmokeExecutionBridgeResult:
    """Top-level bridge result with safe diagnostics only."""

    result_id: str
    passed: bool
    policy: TossApiLiveSmokeExecutionBridgePolicy
    auth_realignment: TossApiLiveSmokeAuthRealignment
    execution_plan: TossApiLiveSmokeExecutionPlan
    execution_guard: TossApiLiveSmokeExecutionGuard
    decision: TossApiLiveSmokeExecutionBridgeDecision
    safe_message: str
    safe_diagnostics: tuple[str, ...]
    next_stage: str


@dataclass(frozen=True)
class TossApiLiveSmokeExecutionBridgeValidationResult:
    """Validation result for bridge safety output."""

    passed: bool
    failures: tuple[str, ...]
    checked_policy_flags: tuple[str, ...]
    checked_realignment_fields: tuple[str, ...]
    checked_plan_fields: tuple[str, ...]
    checked_guard_flags: tuple[str, ...]
    checked_decision_flags: tuple[str, ...]
    checked_result_fields: tuple[str, ...]
    diagnostics: tuple[str, ...]


def build_toss_api_live_smoke_execution_bridge_policy() -> (
    TossApiLiveSmokeExecutionBridgePolicy
):
    """Build the closed MS-16.05a execution bridge policy."""

    return TossApiLiveSmokeExecutionBridgePolicy(
        bridge_version=TOSS_API_LIVE_SMOKE_EXECUTION_BRIDGE_VERSION,
        bridge_scope=TOSS_API_LIVE_SMOKE_EXECUTION_BRIDGE_SCOPE,
        execution_bridge_only=True,
        auth_realignment_only=True,
        actual_live_http_allowed=False,
        oauth_token_request_allowed_now=False,
        readonly_business_request_allowed_now=False,
        credential_request_allowed=False,
        credential_presence_check_allowed=False,
        env_read_allowed=False,
        credential_value_output_allowed=False,
        access_token_output_allowed=False,
        authorization_bearer_output_allowed=False,
        raw_request_output_allowed=False,
        raw_response_output_allowed=False,
        endpoint_full_url_output_allowed=False,
        account_seq_allowed=False,
        order_scope_allowed=False,
        account_data_allowed=False,
        balance_allowed=False,
        fills_allowed=False,
        retry_loop_allowed=False,
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


def build_toss_api_live_smoke_auth_realignment() -> (
    TossApiLiveSmokeAuthRealignment
):
    """Build the MS-16.04 OAuth assumption correction record."""

    return TossApiLiveSmokeAuthRealignment(
        realignment_id="ms_16_05a_getprices_oauth_requirement_realignment",
        selected_endpoint_id=SELECTED_ENDPOINT_ID,
        selected_endpoint_label=SELECTED_ENDPOINT_LABEL,
        previous_oauth_required_assumption=False,
        corrected_oauth_required=True,
        corrected_access_token_required=True,
        corrected_authorization_bearer_required=True,
        account_seq_required=False,
        order_scope_required=False,
        account_balance_fills_required=False,
        correction_reason="getprices_readonly_market_data_requires_oauth_client_credentials",
        supersedes_ms_16_04_oauth_assumption=True,
    )


def build_toss_api_live_smoke_execution_plan() -> TossApiLiveSmokeExecutionPlan:
    """Build the future MS-16.05b plan without executable request material."""

    return TossApiLiveSmokeExecutionPlan(
        plan_id="ms_16_05b_first_actual_readonly_smoke_plan",
        selected_endpoint_id=SELECTED_ENDPOINT_ID,
        selected_endpoint_label=SELECTED_ENDPOINT_LABEL,
        operation_kind=OPERATION_KIND,
        planned_network_call_count=2,
        planned_oauth_call_count=1,
        planned_readonly_business_call_count=1,
        planned_retry_count=0,
        credential_source_policy="local_session_env_only_for_future_stage",
        token_storage_policy="memory_only_no_raw_output_for_future_stage",
        authorization_header_output_allowed=False,
        access_token_output_allowed=False,
        raw_request_output_allowed=False,
        raw_response_output_allowed=False,
        endpoint_full_url_output_allowed=False,
        account_seq_used=False,
        order_scope_used=False,
        account_balance_fills_scope_used=False,
        ready_for_ms_16_05b=True,
    )


def build_toss_api_live_smoke_execution_guard() -> TossApiLiveSmokeExecutionGuard:
    """Build guard flags for the future live smoke stage."""

    return TossApiLiveSmokeExecutionGuard(
        confirmed_endpoint_selected=True,
        oauth_requirement_realigned=True,
        access_token_output_blocked=True,
        authorization_header_output_blocked=True,
        raw_request_output_blocked=True,
        raw_response_output_blocked=True,
        endpoint_full_url_output_blocked=True,
        account_seq_blocked=True,
        order_scope_blocked=True,
        account_balance_fills_scope_blocked=True,
        retry_loop_blocked=True,
        credential_values_blocked=True,
        env_files_blocked=True,
        no_db_write=True,
        no_streamlit=True,
        no_openai_llm=True,
        no_recommendation_or_trading_action=True,
    )


def evaluate_toss_api_live_smoke_execution_bridge_decision(
    realignment: TossApiLiveSmokeAuthRealignment | None = None,
    execution_plan: TossApiLiveSmokeExecutionPlan | None = None,
    execution_guard: TossApiLiveSmokeExecutionGuard | None = None,
) -> TossApiLiveSmokeExecutionBridgeDecision:
    """Evaluate the bridge decision without attempting live HTTP."""

    active_realignment = realignment or build_toss_api_live_smoke_auth_realignment()
    active_plan = execution_plan or build_toss_api_live_smoke_execution_plan()
    active_guard = execution_guard or build_toss_api_live_smoke_execution_guard()
    ready = _ready_for_ms_16_05b(active_realignment, active_plan, active_guard)
    return TossApiLiveSmokeExecutionBridgeDecision(
        execution_bridge_invocation_allowed=True,
        execution_bridge_only=True,
        actual_live_http_attempted=False,
        oauth_token_request_attempted=False,
        readonly_business_request_attempted=False,
        credential_request_performed=False,
        credential_presence_check_performed=False,
        env_read_performed=False,
        selected_endpoint_id=active_plan.selected_endpoint_id,
        selected_endpoint_ready=active_guard.confirmed_endpoint_selected,
        oauth_requirement_realigned=active_realignment.corrected_oauth_required
        and active_guard.oauth_requirement_realigned,
        future_ms_16_05b_network_call_count=active_plan.planned_network_call_count,
        future_ms_16_05b_oauth_call_count=active_plan.planned_oauth_call_count,
        future_ms_16_05b_readonly_business_call_count=(
            active_plan.planned_readonly_business_call_count
        ),
        future_ms_16_05b_retry_count=active_plan.planned_retry_count,
        ready_for_ms_16_05b=ready,
        live_http_execution_allowed_now=False,
        credential_request_allowed_now=False,
        credential_presence_check_allowed_now=False,
        env_read_allowed_now=False,
        oauth_token_issuance_allowed_now=False,
        access_token_output_allowed=False,
        authorization_bearer_output_allowed=False,
        raw_request_output_allowed=False,
        raw_response_output_allowed=False,
        endpoint_full_url_output_allowed=False,
        account_seq_allowed_now=False,
        order_allowed_now=False,
        account_data_allowed_now=False,
        balance_allowed_now=False,
        fills_allowed_now=False,
        db_write_allowed_now=False,
        streamlit_allowed_now=False,
        openai_key_allowed_now=False,
        llm_allowed_now=False,
        recommendation_allowed_now=False,
        ranking_allowed_now=False,
        buy_sell_hold_allowed_now=False,
        next_stage=NEXT_STAGE,
    )


def run_toss_api_live_smoke_execution_bridge() -> (
    TossApiLiveSmokeExecutionBridgeResult
):
    """Run deterministic bridge realignment without I/O or live HTTP."""

    policy = build_toss_api_live_smoke_execution_bridge_policy()
    realignment = build_toss_api_live_smoke_auth_realignment()
    execution_plan = build_toss_api_live_smoke_execution_plan()
    execution_guard = build_toss_api_live_smoke_execution_guard()
    decision = evaluate_toss_api_live_smoke_execution_bridge_decision(
        realignment,
        execution_plan,
        execution_guard,
    )
    safe_diagnostics = (
        SAFE_DIAGNOSTICS_KIND,
        f"selected_endpoint_id={decision.selected_endpoint_id}",
        f"selected_endpoint_label={SELECTED_ENDPOINT_LABEL}",
        f"oauth_required={realignment.corrected_oauth_required}",
        f"access_required={realignment.corrected_access_token_required}",
        f"planned_network_call_count={decision.future_ms_16_05b_network_call_count}",
        f"planned_oauth_call_count={decision.future_ms_16_05b_oauth_call_count}",
        "planned_readonly_business_call_count="
        + str(decision.future_ms_16_05b_readonly_business_call_count),
        f"retry_count={decision.future_ms_16_05b_retry_count}",
        f"ready_for_ms_16_05b={decision.ready_for_ms_16_05b}",
        "redaction_applied=True",
    )
    result = TossApiLiveSmokeExecutionBridgeResult(
        result_id=SAFE_RESULT_ID,
        passed=True,
        policy=policy,
        auth_realignment=realignment,
        execution_plan=execution_plan,
        execution_guard=execution_guard,
        decision=decision,
        safe_message=SAFE_MESSAGE,
        safe_diagnostics=safe_diagnostics,
        next_stage=NEXT_STAGE,
    )
    validation = validate_toss_api_live_smoke_execution_bridge_result(result)
    return TossApiLiveSmokeExecutionBridgeResult(
        result_id=result.result_id,
        passed=validation.passed,
        policy=result.policy,
        auth_realignment=result.auth_realignment,
        execution_plan=result.execution_plan,
        execution_guard=result.execution_guard,
        decision=result.decision,
        safe_message=result.safe_message,
        safe_diagnostics=result.safe_diagnostics,
        next_stage=result.next_stage,
    )


def validate_toss_api_live_smoke_execution_bridge_result(
    result: TossApiLiveSmokeExecutionBridgeResult | None = None,
) -> TossApiLiveSmokeExecutionBridgeValidationResult:
    """Validate bridge output for closed gates and redacted diagnostics."""

    active_result = result or run_toss_api_live_smoke_execution_bridge()
    failures: list[str] = []
    failures.extend(_validate_policy(active_result.policy))
    failures.extend(_validate_realignment(active_result.auth_realignment))
    failures.extend(_validate_execution_plan(active_result.execution_plan))
    failures.extend(_validate_execution_guard(active_result.execution_guard))
    failures.extend(_validate_decision(active_result.decision))
    failures.extend(_validate_result(active_result))
    sensitive_validation = validate_no_sensitive_output(
        {
            "safe_message": active_result.safe_message,
            "safe_diagnostics": active_result.safe_diagnostics,
        },
        build_toss_api_redaction_policy(),
    )
    failures.extend(sensitive_validation.failures)
    return TossApiLiveSmokeExecutionBridgeValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=_policy_flag_names(),
        checked_realignment_fields=_realignment_field_names(),
        checked_plan_fields=_plan_field_names(),
        checked_guard_flags=_guard_flag_names(),
        checked_decision_flags=_decision_flag_names(),
        checked_result_fields=_result_field_names(),
        diagnostics=("live_smoke_execution_bridge_validation",),
    )


def run_toss_api_live_smoke_execution_bridge_preflight_checks() -> (
    TossApiLiveSmokeExecutionBridgeValidationResult
):
    """Run dependency checks and bridge validation without I/O."""

    for result in (
        run_toss_api_first_live_smoke_preflight_checks(),
        run_toss_api_live_smoke_result_hardening_preflight_checks(),
        run_toss_api_readonly_endpoint_selection_preflight_checks(),
        run_toss_api_live_smoke_operator_rehearsal_preflight_checks(),
    ):
        if not result.passed:
            return _failed_validation(result.failures)
    evidence_result = run_toss_api_confirmed_endpoint_evidence_update()
    evidence_validation = validate_toss_api_confirmed_endpoint_evidence_result(
        evidence_result
    )
    if not evidence_validation.passed:
        return _failed_validation(evidence_validation.failures)
    if (
        evidence_result.decision.selected_endpoint_id != SELECTED_ENDPOINT_ID
        or evidence_result.decision.selection_blocked
    ):
        return _failed_validation(("ms_16_04_selected_endpoint_not_ready",))
    return validate_toss_api_live_smoke_execution_bridge_result(
        run_toss_api_live_smoke_execution_bridge()
    )


def _ready_for_ms_16_05b(
    realignment: TossApiLiveSmokeAuthRealignment,
    plan: TossApiLiveSmokeExecutionPlan,
    guard: TossApiLiveSmokeExecutionGuard,
) -> bool:
    return all(
        (
            realignment.supersedes_ms_16_04_oauth_assumption,
            realignment.corrected_oauth_required,
            realignment.corrected_access_token_required,
            realignment.corrected_authorization_bearer_required,
            not realignment.account_seq_required,
            not realignment.order_scope_required,
            not realignment.account_balance_fills_required,
            plan.selected_endpoint_id == SELECTED_ENDPOINT_ID,
            plan.operation_kind == OPERATION_KIND,
            plan.planned_network_call_count == 2,
            plan.planned_oauth_call_count == 1,
            plan.planned_readonly_business_call_count == 1,
            plan.planned_retry_count == 0,
            plan.ready_for_ms_16_05b,
            all(getattr(guard, flag) for flag in _guard_flag_names()),
        )
    )


def _validate_policy(
    policy: TossApiLiveSmokeExecutionBridgePolicy,
) -> tuple[str, ...]:
    failures: list[str] = []
    for flag in _policy_true_flag_names():
        if not getattr(policy, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in _policy_false_flag_names():
        if getattr(policy, flag):
            failures.append(f"{flag}_must_be_false")
    return tuple(failures)


def _validate_realignment(
    realignment: TossApiLiveSmokeAuthRealignment,
) -> tuple[str, ...]:
    failures: list[str] = []
    expected_true = (
        "corrected_oauth_required",
        "corrected_access_token_required",
        "corrected_authorization_bearer_required",
        "supersedes_ms_16_04_oauth_assumption",
    )
    for flag in expected_true:
        if not getattr(realignment, flag):
            failures.append(f"{flag}_must_be_true")
    expected_false = (
        "previous_oauth_required_assumption",
        "account_seq_required",
        "order_scope_required",
        "account_balance_fills_required",
    )
    for flag in expected_false:
        if getattr(realignment, flag):
            failures.append(f"{flag}_must_be_false")
    if realignment.selected_endpoint_id != SELECTED_ENDPOINT_ID:
        failures.append("selected_endpoint_id_must_be_preserved")
    return tuple(failures)


def _validate_execution_plan(
    plan: TossApiLiveSmokeExecutionPlan,
) -> tuple[str, ...]:
    failures: list[str] = []
    expected_counts = {
        "planned_network_call_count": 2,
        "planned_oauth_call_count": 1,
        "planned_readonly_business_call_count": 1,
        "planned_retry_count": 0,
    }
    for field_name, expected in expected_counts.items():
        if getattr(plan, field_name) != expected:
            failures.append(f"{field_name}_must_equal_{expected}")
    for flag in (
        "authorization_header_output_allowed",
        "access_token_output_allowed",
        "raw_request_output_allowed",
        "raw_response_output_allowed",
        "endpoint_full_url_output_allowed",
        "account_seq_used",
        "order_scope_used",
        "account_balance_fills_scope_used",
    ):
        if getattr(plan, flag):
            failures.append(f"{flag}_must_be_false")
    if not plan.ready_for_ms_16_05b:
        failures.append("ready_for_ms_16_05b_must_be_true")
    return tuple(failures)


def _validate_execution_guard(
    guard: TossApiLiveSmokeExecutionGuard,
) -> tuple[str, ...]:
    return tuple(
        f"{flag}_must_be_true"
        for flag in _guard_flag_names()
        if not getattr(guard, flag)
    )


def _validate_decision(
    decision: TossApiLiveSmokeExecutionBridgeDecision,
) -> tuple[str, ...]:
    failures: list[str] = []
    for flag in (
        "execution_bridge_invocation_allowed",
        "execution_bridge_only",
        "selected_endpoint_ready",
        "oauth_requirement_realigned",
        "ready_for_ms_16_05b",
    ):
        if not getattr(decision, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in _decision_false_flag_names():
        if getattr(decision, flag):
            failures.append(f"{flag}_must_be_false")
    if decision.selected_endpoint_id != SELECTED_ENDPOINT_ID:
        failures.append("selected_endpoint_id_must_be_preserved")
    if decision.future_ms_16_05b_network_call_count != 2:
        failures.append("future_network_call_count_must_be_two")
    if decision.future_ms_16_05b_oauth_call_count != 1:
        failures.append("future_oauth_call_count_must_be_one")
    if decision.future_ms_16_05b_readonly_business_call_count != 1:
        failures.append("future_readonly_business_call_count_must_be_one")
    if decision.future_ms_16_05b_retry_count != 0:
        failures.append("future_retry_count_must_be_zero")
    return tuple(failures)


def _validate_result(
    result: TossApiLiveSmokeExecutionBridgeResult,
) -> tuple[str, ...]:
    failures: list[str] = []
    safe_text = " ".join((result.safe_message, *result.safe_diagnostics)).casefold()
    for fragment in FORBIDDEN_SAFE_OUTPUT_FRAGMENTS:
        if fragment in safe_text:
            failures.append("forbidden_safe_output_fragment_exposed")
            break
    if "/" in safe_text or "http:" in safe_text or "https:" in safe_text:
        failures.append("endpoint_full_url_or_path_exposed")
    if result.next_stage != NEXT_STAGE:
        failures.append("next_stage_must_be_ms_16_05b")
    return tuple(failures)


def _failed_validation(
    failures: tuple[str, ...],
) -> TossApiLiveSmokeExecutionBridgeValidationResult:
    return TossApiLiveSmokeExecutionBridgeValidationResult(
        passed=False,
        failures=failures,
        checked_policy_flags=_policy_flag_names(),
        checked_realignment_fields=_realignment_field_names(),
        checked_plan_fields=_plan_field_names(),
        checked_guard_flags=_guard_flag_names(),
        checked_decision_flags=_decision_flag_names(),
        checked_result_fields=_result_field_names(),
        diagnostics=("live_smoke_execution_bridge_dependency_failed",),
    )


def _policy_true_flag_names() -> tuple[str, ...]:
    return (
        "execution_bridge_only",
        "auth_realignment_only",
        "redacted_diagnostics_only",
    )


def _policy_false_flag_names() -> tuple[str, ...]:
    return (
        "actual_live_http_allowed",
        "oauth_token_request_allowed_now",
        "readonly_business_request_allowed_now",
        "credential_request_allowed",
        "credential_presence_check_allowed",
        "env_read_allowed",
        "credential_value_output_allowed",
        "access_token_output_allowed",
        "authorization_bearer_output_allowed",
        "raw_request_output_allowed",
        "raw_response_output_allowed",
        "endpoint_full_url_output_allowed",
        "account_seq_allowed",
        "order_scope_allowed",
        "account_data_allowed",
        "balance_allowed",
        "fills_allowed",
        "retry_loop_allowed",
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


def _realignment_field_names() -> tuple[str, ...]:
    return (
        "previous_oauth_required_assumption",
        "corrected_oauth_required",
        "corrected_access_token_required",
        "corrected_authorization_bearer_required",
        "account_seq_required",
        "order_scope_required",
        "account_balance_fills_required",
        "supersedes_ms_16_04_oauth_assumption",
    )


def _plan_field_names() -> tuple[str, ...]:
    return (
        "planned_network_call_count",
        "planned_oauth_call_count",
        "planned_readonly_business_call_count",
        "planned_retry_count",
        "credential_source_policy",
        "token_storage_policy",
        "authorization_header_output_allowed",
        "access_token_output_allowed",
        "raw_request_output_allowed",
        "raw_response_output_allowed",
        "endpoint_full_url_output_allowed",
        "ready_for_ms_16_05b",
    )


def _guard_flag_names() -> tuple[str, ...]:
    return (
        "confirmed_endpoint_selected",
        "oauth_requirement_realigned",
        "access_token_output_blocked",
        "authorization_header_output_blocked",
        "raw_request_output_blocked",
        "raw_response_output_blocked",
        "endpoint_full_url_output_blocked",
        "account_seq_blocked",
        "order_scope_blocked",
        "account_balance_fills_scope_blocked",
        "retry_loop_blocked",
        "credential_values_blocked",
        "env_files_blocked",
        "no_db_write",
        "no_streamlit",
        "no_openai_llm",
        "no_recommendation_or_trading_action",
    )


def _decision_false_flag_names() -> tuple[str, ...]:
    return (
        "actual_live_http_attempted",
        "oauth_token_request_attempted",
        "readonly_business_request_attempted",
        "credential_request_performed",
        "credential_presence_check_performed",
        "env_read_performed",
        "live_http_execution_allowed_now",
        "credential_request_allowed_now",
        "credential_presence_check_allowed_now",
        "env_read_allowed_now",
        "oauth_token_issuance_allowed_now",
        "access_token_output_allowed",
        "authorization_bearer_output_allowed",
        "raw_request_output_allowed",
        "raw_response_output_allowed",
        "endpoint_full_url_output_allowed",
        "account_seq_allowed_now",
        "order_allowed_now",
        "account_data_allowed_now",
        "balance_allowed_now",
        "fills_allowed_now",
        "db_write_allowed_now",
        "streamlit_allowed_now",
        "openai_key_allowed_now",
        "llm_allowed_now",
        "recommendation_allowed_now",
        "ranking_allowed_now",
        "buy_sell_hold_allowed_now",
    )


def _decision_flag_names() -> tuple[str, ...]:
    return (
        "execution_bridge_invocation_allowed",
        "execution_bridge_only",
        "selected_endpoint_ready",
        "oauth_requirement_realigned",
        "ready_for_ms_16_05b",
        *_decision_false_flag_names(),
    )


def _result_field_names() -> tuple[str, ...]:
    return (
        "result_id",
        "passed",
        "safe_message",
        "safe_diagnostics",
        "next_stage",
    )
