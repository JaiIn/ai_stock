"""MS-16.01 read-only live smoke result hardening.

This module is pure no-I/O. It does not execute live HTTP, request credentials,
read environment variables, read files, write files, use DB storage, import
Streamlit, call OpenAI/LLM APIs, or generate recommendation/ranking/trade
actions. It hardens the safe reporting shape around MS-16.00 blocked dry-run and
injected executor result paths.
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
from ai_stock.clients.toss_api_credential_timing import (
    run_toss_api_credential_request_timing_preflight_checks,
)
from ai_stock.clients.toss_api_fake_transport import (
    run_toss_api_fake_transport_preflight_checks,
)
from ai_stock.clients.toss_api_first_live_smoke import (
    TossApiFirstLiveSmokeCredentialPresence,
    TossApiFirstLiveSmokeResult,
    build_toss_api_first_live_smoke_endpoint_candidates,
    build_toss_api_first_live_smoke_runtime_approval,
    run_toss_api_first_live_smoke,
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


TOSS_API_LIVE_SMOKE_RESULT_HARDENING_VERSION = "MS-16.01"
TOSS_API_LIVE_SMOKE_RESULT_HARDENING_SCOPE = (
    "readonly_live_smoke_result_hardening"
)
DEFAULT_NEXT_STAGE = "MS-16.02 confirmed read-only endpoint selection"
SAFE_DIAGNOSTICS_KIND = "redacted_result_diagnostics"
SAFE_ERROR_CODE = "safe_blocked_or_summarized_error"
SAFE_OPERATOR_ACTION = "review_redacted_summary_only"
SAFE_REDACTED_MESSAGE = "sensitive_detail_redacted"
SAFE_PROBE_PREFIX = "safe_probe_label_"
SYNTHETIC_FORBIDDEN_PROBE_INPUTS = (
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
    ".env",
    "buy",
    "sell",
    "hold",
    "strong_buy",
    "recommendation",
    "action",
    "rank",
    "ranking",
    "ranking_position",
    "priority",
    "order",
    "target_price",
    "expected_return",
    "profit_probability",
    "must_buy",
    "must_sell",
)
FORBIDDEN_SAFE_OUTPUT_FRAGMENTS = tuple(
    token.casefold() for token in SYNTHETIC_FORBIDDEN_PROBE_INPUTS
)


@dataclass(frozen=True)
class TossApiLiveSmokeResultHardeningPolicy:
    """Policy for MS-16.01 result hardening only."""

    hardening_version: str
    hardening_scope: str
    result_hardening_only: bool
    live_http_execution_allowed: bool
    credential_request_allowed: bool
    credential_value_output_allowed: bool
    raw_request_output_allowed: bool
    raw_response_output_allowed: bool
    authorization_header_output_allowed: bool
    token_output_allowed: bool
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
    redacted_diagnostics_only: bool
    status_code_allowed: bool
    elapsed_ms_allowed: bool
    response_shape_summary_allowed: bool
    error_category_allowed: bool


@dataclass(frozen=True)
class TossApiLiveSmokeSafeHttpSummary:
    """Safe HTTP summary shape with no request/response payload."""

    attempted: bool
    status_code: int | None
    success: bool
    error_category: str | None
    response_shape_summary: tuple[str, ...]
    elapsed_ms: int | None
    diagnostics_kind: str
    redaction_applied: bool


@dataclass(frozen=True)
class TossApiLiveSmokeSafeErrorSummary:
    """Safe error summary without exception text or traceback."""

    error_category: str | None
    safe_error_code: str
    retryable: bool
    operator_action: str
    redacted_message: str


@dataclass(frozen=True)
class TossApiLiveSmokeRedactionProbe:
    """Synthetic redaction probe metadata without raw probe values."""

    probe_id: str
    synthetic_input_count: int
    sanitized_probe_labels: tuple[str, ...]
    redaction_placeholder: str
    synthetic_values_returned: bool
    validation_failure_expected_for_raw_probe: bool
    validation_failure_observed_for_raw_probe: bool


@dataclass(frozen=True)
class TossApiLiveSmokeResultHardeningDecision:
    """Decision proving result hardening remains closed to live execution."""

    hardening_invocation_allowed: bool
    ms_16_00_preflight_passed: bool
    live_http_execution_allowed: bool
    credential_request_allowed: bool
    raw_request_output_allowed: bool
    raw_response_output_allowed: bool
    credentials_redacted: bool
    safe_http_summary_allowed: bool
    safe_error_summary_allowed: bool
    redaction_probe_passed: bool
    account_seq_used: bool
    order_scope_used: bool
    account_balance_fills_scope_used: bool
    openai_key_used: bool
    llm_used: bool
    db_written: bool
    streamlit_used: bool
    recommendation_generated: bool
    ranking_generated: bool
    buy_sell_hold_generated: bool
    next_stage: str


@dataclass(frozen=True)
class TossApiLiveSmokeResultHardeningResult:
    """Top-level safe hardening result."""

    result_id: str
    passed: bool
    policy: TossApiLiveSmokeResultHardeningPolicy
    safe_http_summary: TossApiLiveSmokeSafeHttpSummary
    safe_error_summary: TossApiLiveSmokeSafeErrorSummary
    redaction_probe: TossApiLiveSmokeRedactionProbe
    decision: TossApiLiveSmokeResultHardeningDecision
    safe_diagnostics: tuple[str, ...]
    next_stage: str


@dataclass(frozen=True)
class TossApiLiveSmokeResultHardeningValidationResult:
    """Validation result for MS-16.01 hardening."""

    passed: bool
    failures: tuple[str, ...]
    checked_policy_flags: tuple[str, ...]
    checked_safe_http_summary_fields: tuple[str, ...]
    checked_safe_error_summary_fields: tuple[str, ...]
    checked_redaction_probe_fields: tuple[str, ...]
    checked_decision_flags: tuple[str, ...]
    checked_result_fields: tuple[str, ...]
    diagnostics: tuple[str, ...]


def build_toss_api_live_smoke_result_hardening_policy() -> (
    TossApiLiveSmokeResultHardeningPolicy
):
    """Build a closed result-hardening-only policy."""

    return TossApiLiveSmokeResultHardeningPolicy(
        hardening_version=TOSS_API_LIVE_SMOKE_RESULT_HARDENING_VERSION,
        hardening_scope=TOSS_API_LIVE_SMOKE_RESULT_HARDENING_SCOPE,
        result_hardening_only=True,
        live_http_execution_allowed=False,
        credential_request_allowed=False,
        credential_value_output_allowed=False,
        raw_request_output_allowed=False,
        raw_response_output_allowed=False,
        authorization_header_output_allowed=False,
        token_output_allowed=False,
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
        redacted_diagnostics_only=True,
        status_code_allowed=True,
        elapsed_ms_allowed=True,
        response_shape_summary_allowed=True,
        error_category_allowed=True,
    )


def build_toss_api_live_smoke_safe_http_summary(
    first_live_smoke_result: TossApiFirstLiveSmokeResult | None = None,
) -> TossApiLiveSmokeSafeHttpSummary:
    """Build a safe HTTP summary from MS-16.00 result output."""

    active_result = first_live_smoke_result or _build_default_first_live_smoke_result()
    http_result = active_result.http_result
    return TossApiLiveSmokeSafeHttpSummary(
        attempted=http_result.attempted,
        status_code=http_result.status_code,
        success=http_result.success,
        error_category=_safe_category(http_result.error_category),
        response_shape_summary=tuple(
            _safe_label(item) for item in http_result.response_shape_summary
        ),
        elapsed_ms=http_result.elapsed_ms,
        diagnostics_kind=SAFE_DIAGNOSTICS_KIND,
        redaction_applied=True,
    )


def build_toss_api_live_smoke_safe_error_summary(
    first_live_smoke_result: TossApiFirstLiveSmokeResult | None = None,
) -> TossApiLiveSmokeSafeErrorSummary:
    """Build a safe error summary without exception text."""

    active_result = first_live_smoke_result or _build_default_first_live_smoke_result()
    return TossApiLiveSmokeSafeErrorSummary(
        error_category=_safe_category(active_result.http_result.error_category),
        safe_error_code=SAFE_ERROR_CODE,
        retryable=False,
        operator_action=SAFE_OPERATOR_ACTION,
        redacted_message=SAFE_REDACTED_MESSAGE,
    )


def build_toss_api_live_smoke_redaction_probe() -> TossApiLiveSmokeRedactionProbe:
    """Build synthetic redaction probe metadata without returning raw inputs."""

    policy = build_toss_api_redaction_policy()
    raw_probe = {token: "synthetic-sensitive-value" for token in _probe_mapping_keys()}
    redacted_probe = redact_mapping(raw_probe, policy)
    raw_validation = validate_no_sensitive_output(raw_probe, policy)
    contract_redaction_observed = any(
        value == policy.redaction_placeholder for value in redacted_probe.values()
    )
    custom_fragment_failure_observed = _contains_forbidden_fragment(
        " ".join(SYNTHETIC_FORBIDDEN_PROBE_INPUTS)
    )
    return TossApiLiveSmokeRedactionProbe(
        probe_id="safe_probe",
        synthetic_input_count=len(SYNTHETIC_FORBIDDEN_PROBE_INPUTS),
        sanitized_probe_labels=tuple(
            f"{SAFE_PROBE_PREFIX}{index:02d}"
            for index, _ in enumerate(SYNTHETIC_FORBIDDEN_PROBE_INPUTS, start=1)
        ),
        redaction_placeholder=policy.redaction_placeholder,
        synthetic_values_returned=False,
        validation_failure_expected_for_raw_probe=True,
        validation_failure_observed_for_raw_probe=(
            contract_redaction_observed
            and not raw_validation.passed
            and custom_fragment_failure_observed
        ),
    )


def evaluate_toss_api_live_smoke_result_hardening_decision(
    *,
    ms_16_00_preflight_passed: bool = True,
    redaction_probe: TossApiLiveSmokeRedactionProbe | None = None,
) -> TossApiLiveSmokeResultHardeningDecision:
    """Evaluate the closed result hardening decision."""

    active_probe = redaction_probe or build_toss_api_live_smoke_redaction_probe()
    return TossApiLiveSmokeResultHardeningDecision(
        hardening_invocation_allowed=True,
        ms_16_00_preflight_passed=ms_16_00_preflight_passed,
        live_http_execution_allowed=False,
        credential_request_allowed=False,
        raw_request_output_allowed=False,
        raw_response_output_allowed=False,
        credentials_redacted=True,
        safe_http_summary_allowed=True,
        safe_error_summary_allowed=True,
        redaction_probe_passed=(
            active_probe.validation_failure_expected_for_raw_probe
            and active_probe.validation_failure_observed_for_raw_probe
            and not active_probe.synthetic_values_returned
        ),
        account_seq_used=False,
        order_scope_used=False,
        account_balance_fills_scope_used=False,
        openai_key_used=False,
        llm_used=False,
        db_written=False,
        streamlit_used=False,
        recommendation_generated=False,
        ranking_generated=False,
        buy_sell_hold_generated=False,
        next_stage=DEFAULT_NEXT_STAGE,
    )


def run_toss_api_live_smoke_result_hardening(
    first_live_smoke_result: TossApiFirstLiveSmokeResult | None = None,
) -> TossApiLiveSmokeResultHardeningResult:
    """Run deterministic result hardening without live HTTP."""

    active_first_result = first_live_smoke_result or _build_default_first_live_smoke_result()
    policy = build_toss_api_live_smoke_result_hardening_policy()
    safe_http_summary = build_toss_api_live_smoke_safe_http_summary(active_first_result)
    safe_error_summary = build_toss_api_live_smoke_safe_error_summary(active_first_result)
    redaction_probe = build_toss_api_live_smoke_redaction_probe()
    ms16_validation = validate_toss_api_first_live_smoke_result(active_first_result)
    decision = evaluate_toss_api_live_smoke_result_hardening_decision(
        ms_16_00_preflight_passed=ms16_validation.passed,
        redaction_probe=redaction_probe,
    )
    safe_diagnostics = (
        "result_hardening",
        "redacted_summary_only",
        "live_execution_closed",
    )
    result = TossApiLiveSmokeResultHardeningResult(
        result_id="safe_live_smoke_result_hardening_result",
        passed=False,
        policy=policy,
        safe_http_summary=safe_http_summary,
        safe_error_summary=safe_error_summary,
        redaction_probe=redaction_probe,
        decision=decision,
        safe_diagnostics=safe_diagnostics,
        next_stage=DEFAULT_NEXT_STAGE,
    )
    validation = validate_toss_api_live_smoke_result_hardening_result(result)
    return TossApiLiveSmokeResultHardeningResult(
        result_id=result.result_id,
        passed=validation.passed,
        policy=policy,
        safe_http_summary=safe_http_summary,
        safe_error_summary=safe_error_summary,
        redaction_probe=redaction_probe,
        decision=decision,
        safe_diagnostics=safe_diagnostics,
        next_stage=DEFAULT_NEXT_STAGE,
    )


def validate_toss_api_live_smoke_result_hardening_result(
    result: TossApiLiveSmokeResultHardeningResult | None = None,
) -> TossApiLiveSmokeResultHardeningValidationResult:
    """Validate that hardening output stays redacted and closed."""

    active_result = result or run_toss_api_live_smoke_result_hardening()
    failures: list[str] = []
    failures.extend(_validate_policy(active_result.policy))
    failures.extend(_validate_safe_http_summary(active_result.safe_http_summary))
    failures.extend(_validate_safe_error_summary(active_result.safe_error_summary))
    failures.extend(_validate_redaction_probe(active_result.redaction_probe))
    failures.extend(_validate_decision(active_result.decision))
    failures.extend(_validate_safe_output_text(active_result))
    sensitive_validation = validate_no_sensitive_output(
        {
            "safe_diagnostics": active_result.safe_diagnostics,
            "safe_message": active_result.safe_error_summary.redacted_message,
            "safe_next_stage": active_result.next_stage,
        },
        build_toss_api_redaction_policy(),
    )
    failures.extend(sensitive_validation.failures)
    return TossApiLiveSmokeResultHardeningValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=_policy_flag_names(),
        checked_safe_http_summary_fields=_safe_http_summary_field_names(),
        checked_safe_error_summary_fields=_safe_error_summary_field_names(),
        checked_redaction_probe_fields=_redaction_probe_field_names(),
        checked_decision_flags=_decision_flag_names(),
        checked_result_fields=_result_field_names(),
        diagnostics=(
            "live_smoke_result_hardening_validation",
            "redacted_diagnostics_only",
        ),
    )


def run_toss_api_live_smoke_result_hardening_preflight_checks() -> (
    TossApiLiveSmokeResultHardeningValidationResult
):
    """Run dependency and hardening checks without live HTTP."""

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
    ):
        if not result.passed:
            return _failed_validation(result.failures)
    return validate_toss_api_live_smoke_result_hardening_result(
        run_toss_api_live_smoke_result_hardening()
    )


def _build_default_first_live_smoke_result() -> TossApiFirstLiveSmokeResult:
    credential_presence = TossApiFirstLiveSmokeCredentialPresence(
        required_env_names=("AI_STOCK_TOSS_API_KEY", "AI_STOCK_TOSS_API_SECRET"),
        api_key_present=False,
        api_secret_present=False,
        all_required_credentials_present=False,
        credential_values_loaded_but_never_exposed=False,
        missing_env_names_redacted=(
            "missing_required_name_redacted",
            "missing_required_name_redacted",
        ),
    )
    return run_toss_api_first_live_smoke(
        credential_presence=credential_presence,
        endpoint_candidate=build_toss_api_first_live_smoke_endpoint_candidates()[0],
        runtime_approval=build_toss_api_first_live_smoke_runtime_approval(),
        executor=None,
    )


def _probe_mapping_keys() -> tuple[str, ...]:
    return tuple(
        token.replace(".", "_").replace("Seq", "_seq")
        for token in SYNTHETIC_FORBIDDEN_PROBE_INPUTS
    )


def _safe_label(value: str) -> str:
    normalized = "".join(
        character
        for character in value.casefold()
        if character.isalnum() or character in {"_", "-"}
    )
    return normalized[:64] or "safe_summary"


def _safe_category(value: str | None) -> str | None:
    if value is None:
        return None
    return _safe_label(value)


def _validate_policy(
    policy: TossApiLiveSmokeResultHardeningPolicy,
) -> tuple[str, ...]:
    failures: list[str] = []
    for flag in _policy_true_flag_names():
        if not getattr(policy, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in _policy_false_flag_names():
        if getattr(policy, flag):
            failures.append(f"{flag}_must_be_false")
    return tuple(failures)


def _validate_safe_http_summary(
    summary: TossApiLiveSmokeSafeHttpSummary,
) -> tuple[str, ...]:
    failures: list[str] = []
    if not summary.redaction_applied:
        failures.append("http_summary_redaction_applied_must_be_true")
    if summary.diagnostics_kind != SAFE_DIAGNOSTICS_KIND:
        failures.append("http_summary_diagnostics_kind_must_be_safe")
    return tuple(failures)


def _validate_safe_error_summary(
    summary: TossApiLiveSmokeSafeErrorSummary,
) -> tuple[str, ...]:
    failures: list[str] = []
    if summary.safe_error_code != SAFE_ERROR_CODE:
        failures.append("safe_error_code_must_be_symbolic")
    if summary.operator_action != SAFE_OPERATOR_ACTION:
        failures.append("operator_action_must_be_symbolic")
    if summary.redacted_message != SAFE_REDACTED_MESSAGE:
        failures.append("redacted_message_must_be_safe")
    return tuple(failures)


def _validate_redaction_probe(
    probe: TossApiLiveSmokeRedactionProbe,
) -> tuple[str, ...]:
    failures: list[str] = []
    if probe.synthetic_input_count != len(SYNTHETIC_FORBIDDEN_PROBE_INPUTS):
        failures.append("redaction_probe_count_must_match_forbidden_inputs")
    if len(probe.sanitized_probe_labels) != probe.synthetic_input_count:
        failures.append("redaction_probe_labels_must_match_count")
    if probe.synthetic_values_returned:
        failures.append("redaction_probe_must_not_return_raw_values")
    if not probe.validation_failure_expected_for_raw_probe:
        failures.append("redaction_probe_must_expect_raw_failure")
    if not probe.validation_failure_observed_for_raw_probe:
        failures.append("redaction_probe_must_observe_raw_failure")
    return tuple(failures)


def _validate_decision(
    decision: TossApiLiveSmokeResultHardeningDecision,
) -> tuple[str, ...]:
    failures: list[str] = []
    for flag in _decision_true_flag_names():
        if not getattr(decision, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in _decision_false_flag_names():
        if getattr(decision, flag):
            failures.append(f"{flag}_must_be_false")
    return tuple(failures)


def _validate_safe_output_text(
    result: TossApiLiveSmokeResultHardeningResult,
) -> tuple[str, ...]:
    safe_text = " ".join(
        (
            result.result_id,
            *result.safe_diagnostics,
            result.safe_http_summary.diagnostics_kind,
            *(result.safe_http_summary.response_shape_summary),
            result.safe_http_summary.error_category or "",
            result.safe_error_summary.error_category or "",
            result.safe_error_summary.safe_error_code,
            result.safe_error_summary.operator_action,
            result.safe_error_summary.redacted_message,
            result.redaction_probe.probe_id,
            *(result.redaction_probe.sanitized_probe_labels),
            result.next_stage,
        )
    ).casefold()
    if _contains_forbidden_fragment(safe_text):
        return ("forbidden_safe_output_fragment_exposed",)
    return ()


def _contains_forbidden_fragment(value: str) -> bool:
    lowered = value.casefold()
    return any(fragment in lowered for fragment in FORBIDDEN_SAFE_OUTPUT_FRAGMENTS)


def _failed_validation(
    failures: tuple[str, ...],
) -> TossApiLiveSmokeResultHardeningValidationResult:
    return TossApiLiveSmokeResultHardeningValidationResult(
        passed=False,
        failures=failures,
        checked_policy_flags=_policy_flag_names(),
        checked_safe_http_summary_fields=_safe_http_summary_field_names(),
        checked_safe_error_summary_fields=_safe_error_summary_field_names(),
        checked_redaction_probe_fields=_redaction_probe_field_names(),
        checked_decision_flags=_decision_flag_names(),
        checked_result_fields=_result_field_names(),
        diagnostics=("live_smoke_result_hardening_dependency_failed",),
    )


def _policy_true_flag_names() -> tuple[str, ...]:
    return (
        "result_hardening_only",
        "redacted_diagnostics_only",
        "status_code_allowed",
        "elapsed_ms_allowed",
        "response_shape_summary_allowed",
        "error_category_allowed",
    )


def _policy_false_flag_names() -> tuple[str, ...]:
    return (
        "live_http_execution_allowed",
        "credential_request_allowed",
        "credential_value_output_allowed",
        "raw_request_output_allowed",
        "raw_response_output_allowed",
        "authorization_header_output_allowed",
        "token_output_allowed",
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
    )


def _policy_flag_names() -> tuple[str, ...]:
    return (*_policy_true_flag_names(), *_policy_false_flag_names())


def _safe_http_summary_field_names() -> tuple[str, ...]:
    return (
        "attempted",
        "status_code",
        "success",
        "error_category",
        "response_shape_summary",
        "elapsed_ms",
        "diagnostics_kind",
        "redaction_applied",
    )


def _safe_error_summary_field_names() -> tuple[str, ...]:
    return (
        "error_category",
        "safe_error_code",
        "retryable",
        "operator_action",
        "redacted_message",
    )


def _redaction_probe_field_names() -> tuple[str, ...]:
    return (
        "probe_id",
        "synthetic_input_count",
        "sanitized_probe_labels",
        "redaction_placeholder",
        "synthetic_values_returned",
        "validation_failure_expected_for_raw_probe",
        "validation_failure_observed_for_raw_probe",
    )


def _decision_true_flag_names() -> tuple[str, ...]:
    return (
        "hardening_invocation_allowed",
        "ms_16_00_preflight_passed",
        "credentials_redacted",
        "safe_http_summary_allowed",
        "safe_error_summary_allowed",
        "redaction_probe_passed",
    )


def _decision_false_flag_names() -> tuple[str, ...]:
    return (
        "live_http_execution_allowed",
        "credential_request_allowed",
        "raw_request_output_allowed",
        "raw_response_output_allowed",
        "account_seq_used",
        "order_scope_used",
        "account_balance_fills_scope_used",
        "openai_key_used",
        "llm_used",
        "db_written",
        "streamlit_used",
        "recommendation_generated",
        "ranking_generated",
        "buy_sell_hold_generated",
    )


def _decision_flag_names() -> tuple[str, ...]:
    return (*_decision_true_flag_names(), *_decision_false_flag_names())


def _result_field_names() -> tuple[str, ...]:
    return (
        "result_id",
        "passed",
        "policy",
        "safe_http_summary",
        "safe_error_summary",
        "redaction_probe",
        "decision",
        "safe_diagnostics",
        "next_stage",
    )
