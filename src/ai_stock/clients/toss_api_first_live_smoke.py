"""First read-only Toss API live smoke gate with redacted diagnostics.

MS-16.00 allows checking local process credential presence for approved names
and models a tightly gated read-only market-data smoke. The default path is a
blocked dry run. No credential value, raw request, raw response, account scope,
order scope, DB access, Streamlit, OpenAI/LLM, or recommendation output is
returned.
"""

from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
import json
import os
import time
import urllib.error
import urllib.request

from ai_stock.clients.toss_api_client_contract import (
    build_toss_api_redaction_policy,
    redact_mapping,
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


TOSS_API_FIRST_LIVE_SMOKE_VERSION = "MS-16.00"
TOSS_API_FIRST_LIVE_SMOKE_SCOPE = "first_readonly_toss_api_live_smoke"
TOSS_API_KEY_ENV_NAME = "AI_STOCK_TOSS_API_KEY"
TOSS_API_SECRET_ENV_NAME = "AI_STOCK_TOSS_API_SECRET"
REQUIRED_TOSS_API_ENV_NAMES = (TOSS_API_KEY_ENV_NAME, TOSS_API_SECRET_ENV_NAME)
DEFAULT_ENDPOINT_ID = "symbolic_market_data_readonly_existing_candidate"
DEFAULT_ENDPOINT_SCOPE = "readonly_market_data_public_candidate"
DEFAULT_NEXT_STAGE = "MS-16.01 read-only live smoke result hardening"
BLOCKED_HTTP_RESULT = "safe_http_result_blocked"
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
class TossApiFirstLiveSmokePolicy:
    """Policy for the tightly gated first read-only live smoke."""

    smoke_version: str
    smoke_scope: str
    first_live_smoke_only: bool
    readonly_market_data_only: bool
    credential_request_allowed_in_this_stage: bool
    credential_value_output_allowed: bool
    credential_commit_allowed: bool
    env_file_read_allowed: bool
    process_env_read_allowed_for_allowed_names_only: bool
    oauth_token_issuance_allowed: bool
    access_token_required: bool
    authorization_bearer_output_allowed: bool
    account_seq_allowed: bool
    order_scope_allowed: bool
    account_data_allowed: bool
    balance_allowed: bool
    fills_allowed: bool
    db_read_allowed: bool
    db_write_allowed: bool
    streamlit_allowed: bool
    openai_key_allowed: bool
    llm_allowed: bool
    recommendation_allowed: bool
    ranking_allowed: bool
    buy_sell_hold_allowed: bool
    raw_request_output_allowed: bool
    raw_response_output_allowed: bool
    redacted_diagnostics_only: bool
    live_http_allowed_only_when_runtime_approved: bool
    default_runtime_approved: bool


@dataclass(frozen=True)
class TossApiFirstLiveSmokeCredentialPresence:
    """Credential presence booleans without any value material."""

    required_env_names: tuple[str, ...]
    api_key_present: bool
    api_secret_present: bool
    all_required_credentials_present: bool
    credential_values_loaded_but_never_exposed: bool
    missing_env_names_redacted: tuple[str, ...]


@dataclass(frozen=True)
class TossApiFirstLiveSmokeEndpointCandidate:
    """Read-only market-data endpoint candidate metadata."""

    endpoint_id: str
    endpoint_scope: str
    readonly: bool
    market_data_only: bool
    requires_account_seq: bool
    requires_order_scope: bool
    requires_account_balance_fills: bool
    allows_raw_payload_output: bool
    endpoint_confirmed: bool
    live_http_executable_without_oauth: bool


@dataclass(frozen=True)
class TossApiFirstLiveSmokeRuntimeApproval:
    """Explicit runtime approvals required before any live HTTP attempt."""

    explicit_user_approved_ms_16_00: bool
    runtime_live_http_approved: bool
    credential_request_approved: bool
    readonly_scope_confirmed: bool
    raw_output_block_confirmed: bool
    no_account_scope_confirmed: bool
    no_order_scope_confirmed: bool


@dataclass(frozen=True)
class TossApiFirstLiveSmokeRequestPlan:
    """Redacted request plan without URL, headers, or request payload."""

    method: str
    endpoint_id: str
    endpoint_scope: str
    readonly: bool
    market_data_only: bool
    credential_attached: bool
    headers_redacted: bool
    body_redacted: bool
    raw_request_output_allowed: bool


@dataclass(frozen=True)
class TossApiFirstLiveSmokeHttpResult:
    """Safe HTTP result summary with no raw payload."""

    attempted: bool
    status_code: int | None
    success: bool
    error_category: str | None
    response_shape_summary: tuple[str, ...]
    elapsed_ms: int | None
    redacted_diagnostics: tuple[str, ...]


@dataclass(frozen=True)
class TossApiFirstLiveSmokeDecision:
    """Decision proving whether live HTTP was attempted or safely blocked."""

    live_http_attempted: bool
    blocked: bool
    blocking_reasons: tuple[str, ...]
    safe_message: str
    next_stage: str
    readonly_scope_confirmed: bool
    account_seq_used: bool
    order_scope_used: bool
    account_balance_fills_scope_used: bool
    raw_request_output: bool
    raw_response_output: bool
    credentials_redacted: bool
    result_safe_to_report: bool
    openai_key_used: bool
    llm_used: bool
    db_written: bool
    streamlit_used: bool
    recommendation_generated: bool
    ranking_generated: bool
    buy_sell_hold_generated: bool


@dataclass(frozen=True)
class TossApiFirstLiveSmokeResult:
    """Top-level safe result for MS-16.00."""

    result_id: str
    passed: bool
    blocked: bool
    credential_presence: TossApiFirstLiveSmokeCredentialPresence
    endpoint_candidate: TossApiFirstLiveSmokeEndpointCandidate
    runtime_approval: TossApiFirstLiveSmokeRuntimeApproval
    request_plan: TossApiFirstLiveSmokeRequestPlan
    http_result: TossApiFirstLiveSmokeHttpResult
    decision: TossApiFirstLiveSmokeDecision
    safe_diagnostics: tuple[str, ...]
    next_stage: str


@dataclass(frozen=True)
class TossApiFirstLiveSmokeValidationResult:
    """Validation result for first live smoke safety output."""

    passed: bool
    failures: tuple[str, ...]
    checked_policy_flags: tuple[str, ...]
    checked_credential_presence_flags: tuple[str, ...]
    checked_endpoint_candidate_flags: tuple[str, ...]
    checked_runtime_approval_flags: tuple[str, ...]
    checked_request_plan_flags: tuple[str, ...]
    checked_http_result_fields: tuple[str, ...]
    checked_decision_flags: tuple[str, ...]
    diagnostics: tuple[str, ...]


FirstLiveSmokeExecutor = Callable[
    [TossApiFirstLiveSmokeRequestPlan],
    TossApiFirstLiveSmokeHttpResult,
]


def build_toss_api_first_live_smoke_policy() -> TossApiFirstLiveSmokePolicy:
    """Build MS-16.00 first live smoke policy."""

    return TossApiFirstLiveSmokePolicy(
        smoke_version=TOSS_API_FIRST_LIVE_SMOKE_VERSION,
        smoke_scope=TOSS_API_FIRST_LIVE_SMOKE_SCOPE,
        first_live_smoke_only=True,
        readonly_market_data_only=True,
        credential_request_allowed_in_this_stage=True,
        credential_value_output_allowed=False,
        credential_commit_allowed=False,
        env_file_read_allowed=False,
        process_env_read_allowed_for_allowed_names_only=True,
        oauth_token_issuance_allowed=False,
        access_token_required=False,
        authorization_bearer_output_allowed=False,
        account_seq_allowed=False,
        order_scope_allowed=False,
        account_data_allowed=False,
        balance_allowed=False,
        fills_allowed=False,
        db_read_allowed=False,
        db_write_allowed=False,
        streamlit_allowed=False,
        openai_key_allowed=False,
        llm_allowed=False,
        recommendation_allowed=False,
        ranking_allowed=False,
        buy_sell_hold_allowed=False,
        raw_request_output_allowed=False,
        raw_response_output_allowed=False,
        redacted_diagnostics_only=True,
        live_http_allowed_only_when_runtime_approved=True,
        default_runtime_approved=False,
    )


def read_toss_api_first_live_smoke_credential_presence(
    environ: Mapping[str, str] | None = None,
) -> TossApiFirstLiveSmokeCredentialPresence:
    """Read allowed process environment names and expose only booleans."""

    active_environ = environ
    api_key_present = _env_value_present(TOSS_API_KEY_ENV_NAME, active_environ)
    api_secret_present = _env_value_present(TOSS_API_SECRET_ENV_NAME, active_environ)
    missing_names = tuple(
        env_name
        for env_name, present in (
            (TOSS_API_KEY_ENV_NAME, api_key_present),
            (TOSS_API_SECRET_ENV_NAME, api_secret_present),
        )
        if not present
    )
    return TossApiFirstLiveSmokeCredentialPresence(
        required_env_names=REQUIRED_TOSS_API_ENV_NAMES,
        api_key_present=api_key_present,
        api_secret_present=api_secret_present,
        all_required_credentials_present=api_key_present and api_secret_present,
        credential_values_loaded_but_never_exposed=api_key_present
        or api_secret_present,
        missing_env_names_redacted=tuple(
            "missing_required_name_redacted" for _ in missing_names
        ),
    )


def build_toss_api_first_live_smoke_endpoint_candidates() -> (
    tuple[TossApiFirstLiveSmokeEndpointCandidate, ...]
):
    """Build read-only endpoint candidates, defaulting to non-executable."""

    return (
        TossApiFirstLiveSmokeEndpointCandidate(
            endpoint_id=DEFAULT_ENDPOINT_ID,
            endpoint_scope=DEFAULT_ENDPOINT_SCOPE,
            readonly=True,
            market_data_only=True,
            requires_account_seq=False,
            requires_order_scope=False,
            requires_account_balance_fills=False,
            allows_raw_payload_output=False,
            endpoint_confirmed=False,
            live_http_executable_without_oauth=False,
        ),
    )


def build_toss_api_first_live_smoke_runtime_approval(
    *,
    explicit_user_approved_ms_16_00: bool = False,
    runtime_live_http_approved: bool = False,
    credential_request_approved: bool = False,
    readonly_scope_confirmed: bool = False,
    raw_output_block_confirmed: bool = False,
    no_account_scope_confirmed: bool = False,
    no_order_scope_confirmed: bool = False,
) -> TossApiFirstLiveSmokeRuntimeApproval:
    """Build runtime approval flags. Defaults keep live HTTP blocked."""

    return TossApiFirstLiveSmokeRuntimeApproval(
        explicit_user_approved_ms_16_00=explicit_user_approved_ms_16_00,
        runtime_live_http_approved=runtime_live_http_approved,
        credential_request_approved=credential_request_approved,
        readonly_scope_confirmed=readonly_scope_confirmed,
        raw_output_block_confirmed=raw_output_block_confirmed,
        no_account_scope_confirmed=no_account_scope_confirmed,
        no_order_scope_confirmed=no_order_scope_confirmed,
    )


def build_toss_api_first_live_smoke_request_plan(
    credential_presence: TossApiFirstLiveSmokeCredentialPresence | None = None,
    endpoint_candidate: TossApiFirstLiveSmokeEndpointCandidate | None = None,
) -> TossApiFirstLiveSmokeRequestPlan:
    """Build a redacted request plan with no concrete URL or headers."""

    active_credential_presence = (
        credential_presence or read_toss_api_first_live_smoke_credential_presence()
    )
    active_endpoint_candidate = (
        endpoint_candidate or build_toss_api_first_live_smoke_endpoint_candidates()[0]
    )
    return TossApiFirstLiveSmokeRequestPlan(
        method="GET",
        endpoint_id=active_endpoint_candidate.endpoint_id,
        endpoint_scope=active_endpoint_candidate.endpoint_scope,
        readonly=True,
        market_data_only=True,
        credential_attached=active_credential_presence.all_required_credentials_present,
        headers_redacted=True,
        body_redacted=True,
        raw_request_output_allowed=False,
    )


def execute_toss_api_first_live_smoke_http(
    request_plan: TossApiFirstLiveSmokeRequestPlan,
    *,
    executor: FirstLiveSmokeExecutor | None = None,
) -> TossApiFirstLiveSmokeHttpResult:
    """Execute an injected live smoke executor and sanitize its result."""

    if executor is None:
        return _blocked_http_result("runtime_executor_unavailable")
    started = time.perf_counter()
    try:
        result = executor(request_plan)
    except (OSError, RuntimeError, ValueError, urllib.error.URLError):
        elapsed_ms = int((time.perf_counter() - started) * 1000)
        return TossApiFirstLiveSmokeHttpResult(
            attempted=True,
            status_code=None,
            success=False,
            error_category="safe_executor_failure",
            response_shape_summary=(),
            elapsed_ms=elapsed_ms,
            redacted_diagnostics=("executor_failed_safely",),
        )
    elapsed_ms = result.elapsed_ms
    if elapsed_ms is None:
        elapsed_ms = int((time.perf_counter() - started) * 1000)
    return TossApiFirstLiveSmokeHttpResult(
        attempted=True,
        status_code=result.status_code,
        success=result.success,
        error_category=_safe_error_category(result.error_category),
        response_shape_summary=tuple(
            _safe_shape_item(item) for item in result.response_shape_summary
        ),
        elapsed_ms=elapsed_ms,
        redacted_diagnostics=tuple(
            _safe_shape_item(item) for item in result.redacted_diagnostics
        ),
    )


def evaluate_toss_api_first_live_smoke_decision(
    credential_presence: TossApiFirstLiveSmokeCredentialPresence,
    endpoint_candidate: TossApiFirstLiveSmokeEndpointCandidate,
    runtime_approval: TossApiFirstLiveSmokeRuntimeApproval,
    http_result: TossApiFirstLiveSmokeHttpResult,
) -> TossApiFirstLiveSmokeDecision:
    """Evaluate blocked or attempted first live smoke decision."""

    blocking_reasons = _blocking_reasons(
        credential_presence,
        endpoint_candidate,
        runtime_approval,
    )
    live_http_attempted = http_result.attempted and not blocking_reasons
    blocked = bool(blocking_reasons) or not live_http_attempted
    safe_message = (
        "Read-only live smoke attempted with redacted diagnostics."
        if live_http_attempted
        else "Read-only live smoke blocked safely."
    )
    return TossApiFirstLiveSmokeDecision(
        live_http_attempted=live_http_attempted,
        blocked=blocked,
        blocking_reasons=blocking_reasons,
        safe_message=safe_message,
        next_stage=DEFAULT_NEXT_STAGE,
        readonly_scope_confirmed=runtime_approval.readonly_scope_confirmed
        and endpoint_candidate.readonly
        and endpoint_candidate.market_data_only,
        account_seq_used=False,
        order_scope_used=False,
        account_balance_fills_scope_used=False,
        raw_request_output=False,
        raw_response_output=False,
        credentials_redacted=True,
        result_safe_to_report=True,
        openai_key_used=False,
        llm_used=False,
        db_written=False,
        streamlit_used=False,
        recommendation_generated=False,
        ranking_generated=False,
        buy_sell_hold_generated=False,
    )


def run_toss_api_first_live_smoke(
    *,
    credential_presence: TossApiFirstLiveSmokeCredentialPresence | None = None,
    endpoint_candidate: TossApiFirstLiveSmokeEndpointCandidate | None = None,
    runtime_approval: TossApiFirstLiveSmokeRuntimeApproval | None = None,
    executor: FirstLiveSmokeExecutor | None = None,
) -> TossApiFirstLiveSmokeResult:
    """Run default blocked dry run or a fully approved injected smoke."""

    active_credential_presence = (
        credential_presence or read_toss_api_first_live_smoke_credential_presence()
    )
    active_endpoint_candidate = (
        endpoint_candidate or build_toss_api_first_live_smoke_endpoint_candidates()[0]
    )
    active_runtime_approval = (
        runtime_approval or build_toss_api_first_live_smoke_runtime_approval()
    )
    request_plan = build_toss_api_first_live_smoke_request_plan(
        active_credential_presence,
        active_endpoint_candidate,
    )
    blocking_reasons = _blocking_reasons(
        active_credential_presence,
        active_endpoint_candidate,
        active_runtime_approval,
    )
    http_result = (
        _blocked_http_result("gate_blocked")
        if blocking_reasons
        else execute_toss_api_first_live_smoke_http(request_plan, executor=executor)
    )
    decision = evaluate_toss_api_first_live_smoke_decision(
        active_credential_presence,
        active_endpoint_candidate,
        active_runtime_approval,
        http_result,
    )
    safe_diagnostics = (
        "first_readonly_smoke",
        "redacted_diagnostics_only",
        "live_http_attempted" if decision.live_http_attempted else "live_http_blocked",
    )
    result = TossApiFirstLiveSmokeResult(
        result_id="safe_first_readonly_live_smoke_result",
        passed=not validate_toss_api_first_live_smoke_result_failures(
            decision=decision,
            http_result=http_result,
            safe_diagnostics=safe_diagnostics,
        ),
        blocked=decision.blocked,
        credential_presence=active_credential_presence,
        endpoint_candidate=active_endpoint_candidate,
        runtime_approval=active_runtime_approval,
        request_plan=request_plan,
        http_result=http_result,
        decision=decision,
        safe_diagnostics=safe_diagnostics,
        next_stage=DEFAULT_NEXT_STAGE,
    )
    return result


def validate_toss_api_first_live_smoke_result(
    result: TossApiFirstLiveSmokeResult | None = None,
) -> TossApiFirstLiveSmokeValidationResult:
    """Validate first live smoke result for redacted safe reporting."""

    active_result = result or run_toss_api_first_live_smoke()
    failures = validate_toss_api_first_live_smoke_result_failures(
        decision=active_result.decision,
        http_result=active_result.http_result,
        safe_diagnostics=active_result.safe_diagnostics,
    )
    failures.extend(_validate_policy(build_toss_api_first_live_smoke_policy()))
    failures.extend(_validate_credential_presence(active_result.credential_presence))
    failures.extend(_validate_endpoint_candidate(active_result.endpoint_candidate))
    failures.extend(_validate_runtime_approval(active_result.runtime_approval))
    failures.extend(_validate_request_plan(active_result.request_plan))

    sensitive_validation = validate_no_sensitive_output(
        {
            "safe_message": active_result.decision.safe_message,
            "safe_diagnostics": active_result.safe_diagnostics,
            "safe_next_stage": active_result.next_stage,
        },
        build_toss_api_redaction_policy(),
    )
    failures.extend(sensitive_validation.failures)

    return TossApiFirstLiveSmokeValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=_policy_flag_names(),
        checked_credential_presence_flags=_credential_presence_flag_names(),
        checked_endpoint_candidate_flags=_endpoint_candidate_flag_names(),
        checked_runtime_approval_flags=_runtime_approval_flag_names(),
        checked_request_plan_flags=_request_plan_flag_names(),
        checked_http_result_fields=_http_result_field_names(),
        checked_decision_flags=_decision_flag_names(),
        diagnostics=(
            "first_readonly_live_smoke_validation",
            "default_blocked_dry_run",
            "redacted_diagnostics_only",
        ),
    )


def run_toss_api_first_live_smoke_preflight_checks() -> (
    TossApiFirstLiveSmokeValidationResult
):
    """Run deterministic checks without attempting live HTTP."""

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
    ):
        if not result.passed:
            return _failed_validation(result.failures)
    return validate_toss_api_first_live_smoke_result(run_toss_api_first_live_smoke())


def validate_toss_api_first_live_smoke_result_failures(
    *,
    decision: TossApiFirstLiveSmokeDecision,
    http_result: TossApiFirstLiveSmokeHttpResult,
    safe_diagnostics: tuple[str, ...],
) -> list[str]:
    """Return validation failures for a result subset."""

    failures: list[str] = []
    if decision.account_seq_used:
        failures.append("account_seq_used_must_be_false")
    if decision.order_scope_used:
        failures.append("order_scope_used_must_be_false")
    if decision.account_balance_fills_scope_used:
        failures.append("account_balance_fills_scope_used_must_be_false")
    for flag in (
        "raw_request_output",
        "raw_response_output",
        "openai_key_used",
        "llm_used",
        "db_written",
        "streamlit_used",
        "recommendation_generated",
        "ranking_generated",
        "buy_sell_hold_generated",
    ):
        if getattr(decision, flag):
            failures.append(f"{flag}_must_be_false")
    if not decision.credentials_redacted:
        failures.append("credentials_must_be_redacted")
    if not decision.result_safe_to_report:
        failures.append("result_must_be_safe_to_report")
    if not http_result.redacted_diagnostics:
        failures.append("http_result_must_include_safe_diagnostics")
    sensitive_validation = validate_no_sensitive_output(
        {
            "safe_diagnostics": safe_diagnostics,
            "http_diagnostics": http_result.redacted_diagnostics,
        },
        build_toss_api_redaction_policy(),
    )
    failures.extend(sensitive_validation.failures)
    redacted_probe = redact_mapping(
        {"access_token": "dummy-sensitive-value"},
        build_toss_api_redaction_policy(),
    )
    if (
        redacted_probe["access_token"]
        != build_toss_api_redaction_policy().redaction_placeholder
    ):
        failures.append("redaction_probe_must_mask_sensitive_value")
    safe_text = " ".join(
        (
            decision.safe_message,
            *safe_diagnostics,
            *http_result.redacted_diagnostics,
            *http_result.response_shape_summary,
        )
    ).casefold()
    for fragment in FORBIDDEN_SAFE_OUTPUT_FRAGMENTS:
        if fragment in safe_text:
            failures.append("forbidden_safe_output_fragment_exposed")
            break
    return failures


def _env_value_present(env_name: str, environ: Mapping[str, str] | None) -> bool:
    if env_name not in REQUIRED_TOSS_API_ENV_NAMES:
        return False
    value = os.environ.get(env_name) if environ is None else environ.get(env_name)
    return bool(value)


def _blocking_reasons(
    credential_presence: TossApiFirstLiveSmokeCredentialPresence,
    endpoint_candidate: TossApiFirstLiveSmokeEndpointCandidate,
    runtime_approval: TossApiFirstLiveSmokeRuntimeApproval,
) -> tuple[str, ...]:
    reasons: list[str] = []
    if not runtime_approval.explicit_user_approved_ms_16_00:
        reasons.append("runtime_approval_missing")
    if not runtime_approval.runtime_live_http_approved:
        reasons.append("live_http_approval_missing")
    if not runtime_approval.credential_request_approved:
        reasons.append("credential_request_approval_missing")
    if not runtime_approval.readonly_scope_confirmed:
        reasons.append("readonly_scope_not_confirmed")
    if not runtime_approval.raw_output_block_confirmed:
        reasons.append("raw_output_block_not_confirmed")
    if not runtime_approval.no_account_scope_confirmed:
        reasons.append("account_scope_block_not_confirmed")
    if not runtime_approval.no_order_scope_confirmed:
        reasons.append("order_scope_block_not_confirmed")
    if not credential_presence.all_required_credentials_present:
        reasons.append("required_credential_presence_missing")
    if not endpoint_candidate.endpoint_confirmed:
        reasons.append("endpoint_not_confirmed")
    if not endpoint_candidate.live_http_executable_without_oauth:
        reasons.append("oauth_free_endpoint_not_confirmed")
    if endpoint_candidate.requires_account_seq:
        reasons.append("account_seq_required_endpoint_blocked")
    if endpoint_candidate.requires_order_scope:
        reasons.append("order_scope_endpoint_blocked")
    if endpoint_candidate.requires_account_balance_fills:
        reasons.append("account_data_endpoint_blocked")
    if endpoint_candidate.allows_raw_payload_output:
        reasons.append("raw_payload_endpoint_blocked")
    return tuple(reasons)


def _blocked_http_result(error_category: str) -> TossApiFirstLiveSmokeHttpResult:
    return TossApiFirstLiveSmokeHttpResult(
        attempted=False,
        status_code=None,
        success=False,
        error_category=error_category,
        response_shape_summary=(),
        elapsed_ms=None,
        redacted_diagnostics=(BLOCKED_HTTP_RESULT,),
    )


def _safe_error_category(error_category: str | None) -> str | None:
    if error_category is None:
        return None
    normalized = "".join(
        character
        for character in error_category.casefold()
        if character.isalnum() or character in {"_", "-"}
    )
    return normalized[:64] or "safe_error"


def _safe_shape_item(item: str) -> str:
    normalized = "".join(
        character
        for character in item.casefold()
        if character.isalnum() or character in {"_", "-"}
    )
    return normalized[:64] or "safe_shape"


def _safe_response_shape_from_json_bytes(body: bytes) -> tuple[str, ...]:
    try:
        parsed = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return ("non_json_body",)
    if isinstance(parsed, Mapping):
        return tuple(sorted(_safe_shape_item(str(key)) for key in parsed)[:8])
    if isinstance(parsed, list):
        return ("array_body", f"array_size_{len(parsed)}")
    return (type(parsed).__name__,)


def _unused_stdlib_probe_marker() -> str:
    """Keep urllib.request import intentional without performing I/O."""

    return urllib.request.__name__


def _failed_validation(
    failures: tuple[str, ...],
) -> TossApiFirstLiveSmokeValidationResult:
    return TossApiFirstLiveSmokeValidationResult(
        passed=False,
        failures=failures,
        checked_policy_flags=_policy_flag_names(),
        checked_credential_presence_flags=_credential_presence_flag_names(),
        checked_endpoint_candidate_flags=_endpoint_candidate_flag_names(),
        checked_runtime_approval_flags=_runtime_approval_flag_names(),
        checked_request_plan_flags=_request_plan_flag_names(),
        checked_http_result_fields=_http_result_field_names(),
        checked_decision_flags=_decision_flag_names(),
        diagnostics=("first_live_smoke_dependency_failed",),
    )


def _validate_policy(policy: TossApiFirstLiveSmokePolicy) -> tuple[str, ...]:
    failures = [
        f"{flag}_must_be_true"
        for flag in _policy_true_flag_names()
        if not getattr(policy, flag)
    ]
    failures.extend(
        f"{flag}_must_be_false"
        for flag in _policy_false_flag_names()
        if getattr(policy, flag)
    )
    return tuple(failures)


def _validate_credential_presence(
    presence: TossApiFirstLiveSmokeCredentialPresence,
) -> tuple[str, ...]:
    failures: list[str] = []
    if presence.required_env_names != REQUIRED_TOSS_API_ENV_NAMES:
        failures.append("required_env_names_must_match_allowed_names")
    if presence.all_required_credentials_present != (
        presence.api_key_present and presence.api_secret_present
    ):
        failures.append("credential_presence_summary_must_match_parts")
    if any(
        name in REQUIRED_TOSS_API_ENV_NAMES
        for name in presence.missing_env_names_redacted
    ):
        failures.append("missing_env_names_must_be_redacted")
    return tuple(failures)


def _validate_endpoint_candidate(
    candidate: TossApiFirstLiveSmokeEndpointCandidate,
) -> tuple[str, ...]:
    failures: list[str] = []
    for flag in ("readonly", "market_data_only"):
        if not getattr(candidate, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in (
        "requires_account_seq",
        "requires_order_scope",
        "requires_account_balance_fills",
        "allows_raw_payload_output",
    ):
        if getattr(candidate, flag):
            failures.append(f"{flag}_must_be_false")
    return tuple(failures)


def _validate_runtime_approval(
    approval: TossApiFirstLiveSmokeRuntimeApproval,
) -> tuple[str, ...]:
    failures: list[str] = []
    if approval == build_toss_api_first_live_smoke_runtime_approval():
        return tuple(failures)
    for flag in _runtime_approval_flag_names():
        if not getattr(approval, flag):
            failures.append(f"{flag}_must_be_true_when_attempting")
    return tuple(failures)


def _validate_request_plan(
    plan: TossApiFirstLiveSmokeRequestPlan,
) -> tuple[str, ...]:
    failures: list[str] = []
    for flag in ("readonly", "market_data_only", "headers_redacted", "body_redacted"):
        if not getattr(plan, flag):
            failures.append(f"{flag}_must_be_true")
    if plan.raw_request_output_allowed:
        failures.append("raw_request_output_allowed_must_be_false")
    return tuple(failures)


def _policy_true_flag_names() -> tuple[str, ...]:
    return (
        "first_live_smoke_only",
        "readonly_market_data_only",
        "credential_request_allowed_in_this_stage",
        "process_env_read_allowed_for_allowed_names_only",
        "redacted_diagnostics_only",
        "live_http_allowed_only_when_runtime_approved",
    )


def _policy_false_flag_names() -> tuple[str, ...]:
    return (
        "credential_value_output_allowed",
        "credential_commit_allowed",
        "env_file_read_allowed",
        "oauth_token_issuance_allowed",
        "access_token_required",
        "authorization_bearer_output_allowed",
        "account_seq_allowed",
        "order_scope_allowed",
        "account_data_allowed",
        "balance_allowed",
        "fills_allowed",
        "db_read_allowed",
        "db_write_allowed",
        "streamlit_allowed",
        "openai_key_allowed",
        "llm_allowed",
        "recommendation_allowed",
        "ranking_allowed",
        "buy_sell_hold_allowed",
        "raw_request_output_allowed",
        "raw_response_output_allowed",
        "default_runtime_approved",
    )


def _policy_flag_names() -> tuple[str, ...]:
    return (*_policy_true_flag_names(), *_policy_false_flag_names())


def _credential_presence_flag_names() -> tuple[str, ...]:
    return (
        "api_key_present",
        "api_secret_present",
        "all_required_credentials_present",
        "credential_values_loaded_but_never_exposed",
        "missing_env_names_redacted",
    )


def _endpoint_candidate_flag_names() -> tuple[str, ...]:
    return (
        "readonly",
        "market_data_only",
        "requires_account_seq",
        "requires_order_scope",
        "requires_account_balance_fills",
        "allows_raw_payload_output",
        "endpoint_confirmed",
        "live_http_executable_without_oauth",
    )


def _runtime_approval_flag_names() -> tuple[str, ...]:
    return (
        "explicit_user_approved_ms_16_00",
        "runtime_live_http_approved",
        "credential_request_approved",
        "readonly_scope_confirmed",
        "raw_output_block_confirmed",
        "no_account_scope_confirmed",
        "no_order_scope_confirmed",
    )


def _request_plan_flag_names() -> tuple[str, ...]:
    return (
        "readonly",
        "market_data_only",
        "credential_attached",
        "headers_redacted",
        "body_redacted",
        "raw_request_output_allowed",
    )


def _http_result_field_names() -> tuple[str, ...]:
    return (
        "attempted",
        "status_code",
        "success",
        "error_category",
        "response_shape_summary",
        "elapsed_ms",
        "redacted_diagnostics",
    )


def _decision_flag_names() -> tuple[str, ...]:
    return (
        "live_http_attempted",
        "blocked",
        "readonly_scope_confirmed",
        "account_seq_used",
        "order_scope_used",
        "account_balance_fills_scope_used",
        "raw_request_output",
        "raw_response_output",
        "credentials_redacted",
        "result_safe_to_report",
        "openai_key_used",
        "llm_used",
        "db_written",
        "streamlit_used",
        "recommendation_generated",
        "ranking_generated",
        "buy_sell_hold_generated",
    )
