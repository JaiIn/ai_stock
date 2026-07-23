"""MS-16.02 confirmed read-only endpoint selection.

This module is pure no-I/O. It does not execute live HTTP, request or read
credentials, read environment variables, read files, write files, use DB
storage, import Streamlit, call OpenAI/LLM APIs, or generate recommendation,
ranking, or trade actions. It selects only symbolic endpoint candidates whose
read-only/public evidence is already supplied by project-local contracts.
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


TOSS_API_READONLY_ENDPOINT_SELECTION_VERSION = "MS-16.02"
TOSS_API_READONLY_ENDPOINT_SELECTION_SCOPE = "confirmed_readonly_endpoint_selection"
DEFAULT_NEXT_STAGE = (
    "MS-16.03 live smoke operator runbook / runtime approval rehearsal"
)
DEFAULT_EVIDENCE_ID = "ms_16_02_unconfirmed_project_reference_evidence"
DEFAULT_ENDPOINT_ID = "symbolic_unconfirmed_readonly_endpoint_candidate"
DEFAULT_ENDPOINT_LABEL = "unconfirmed_project_candidate"
DEFAULT_ENDPOINT_SCOPE = "readonly_or_public_candidate_unconfirmed"
NO_SELECTED_ENDPOINT = None
SAFE_RESULT_ID = "safe_readonly_endpoint_selection_result"
SAFE_MESSAGE_BLOCKED = "readonly_endpoint_selection_blocked"
SAFE_MESSAGE_SELECTED = "readonly_endpoint_selection_ready"
SAFE_DIAGNOSTICS_KIND = "redacted_endpoint_selection_diagnostics"
BLOCKING_REASON_NO_SELECTED = "no_confirmed_candidate"
BLOCKING_REASON_CANDIDATE_REJECTED = "candidate_ineligible"
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
class TossApiReadOnlyEndpointSelectionPolicy:
    """Policy for selecting a confirmed read-only endpoint only."""

    selection_version: str
    selection_scope: str
    endpoint_selection_only: bool
    live_http_execution_allowed: bool
    credential_request_allowed: bool
    credential_value_output_allowed: bool
    raw_request_output_allowed: bool
    raw_response_output_allowed: bool
    endpoint_full_url_output_allowed: bool
    endpoint_must_be_confirmed: bool
    readonly_required: bool
    market_data_or_public_required: bool
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
class TossApiReadOnlyEndpointEvidence:
    """Evidence that a candidate is safe for read-only public smoke."""

    evidence_id: str
    source_kind: str
    source_label: str
    source_available: bool
    readonly_confirmed: bool
    market_data_or_public_confirmed: bool
    account_seq_not_required_confirmed: bool
    order_scope_not_required_confirmed: bool
    account_balance_fills_not_required_confirmed: bool
    oauth_not_required_for_smoke_confirmed: bool
    raw_output_block_confirmed: bool
    confidence_label: str


@dataclass(frozen=True)
class TossApiReadOnlyEndpointCandidate:
    """Symbolic endpoint candidate without a URL or concrete path."""

    endpoint_id: str
    endpoint_label: str
    endpoint_scope: str
    readonly: bool
    market_data_only: bool
    public_or_market_data: bool
    requires_account_seq: bool
    requires_order_scope: bool
    requires_account_balance_fills: bool
    requires_oauth_token: bool
    live_http_executable_without_oauth: bool
    endpoint_confirmed: bool
    allows_raw_payload_output: bool
    evidence: TossApiReadOnlyEndpointEvidence


@dataclass(frozen=True)
class TossApiReadOnlyEndpointSelectionDecision:
    """Selection decision that never opens live runtime gates."""

    endpoint_selection_invocation_allowed: bool
    ms_16_00_preflight_passed: bool
    ms_16_01_hardening_passed: bool
    selected_endpoint_id: str | None
    selected_endpoint_label: str | None
    selected_endpoint_confirmed: bool
    selection_blocked: bool
    blocking_reasons: tuple[str, ...]
    live_http_execution_allowed_now: bool
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
    db_write_allowed_now: bool
    streamlit_allowed_now: bool
    recommendation_allowed_now: bool
    ranking_allowed_now: bool
    buy_sell_hold_allowed_now: bool
    raw_request_output_allowed: bool
    raw_response_output_allowed: bool
    endpoint_full_url_output_allowed: bool
    next_stage: str


@dataclass(frozen=True)
class TossApiReadOnlyEndpointSelectionResult:
    """Top-level safe endpoint selection result."""

    result_id: str
    passed: bool
    policy: TossApiReadOnlyEndpointSelectionPolicy
    candidates: tuple[TossApiReadOnlyEndpointCandidate, ...]
    decision: TossApiReadOnlyEndpointSelectionDecision
    safe_message: str
    safe_diagnostics: tuple[str, ...]
    next_stage: str


@dataclass(frozen=True)
class TossApiReadOnlyEndpointSelectionValidationResult:
    """Validation result for MS-16.02 endpoint selection."""

    passed: bool
    failures: tuple[str, ...]
    checked_policy_flags: tuple[str, ...]
    checked_evidence_fields: tuple[str, ...]
    checked_candidate_fields: tuple[str, ...]
    checked_decision_fields: tuple[str, ...]
    checked_result_fields: tuple[str, ...]
    diagnostics: tuple[str, ...]


def build_toss_api_readonly_endpoint_selection_policy() -> (
    TossApiReadOnlyEndpointSelectionPolicy
):
    """Build a closed endpoint-selection-only policy."""

    return TossApiReadOnlyEndpointSelectionPolicy(
        selection_version=TOSS_API_READONLY_ENDPOINT_SELECTION_VERSION,
        selection_scope=TOSS_API_READONLY_ENDPOINT_SELECTION_SCOPE,
        endpoint_selection_only=True,
        live_http_execution_allowed=False,
        credential_request_allowed=False,
        credential_value_output_allowed=False,
        raw_request_output_allowed=False,
        raw_response_output_allowed=False,
        endpoint_full_url_output_allowed=False,
        endpoint_must_be_confirmed=True,
        readonly_required=True,
        market_data_or_public_required=True,
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


def build_toss_api_readonly_endpoint_evidence(
    *,
    evidence_id: str = DEFAULT_EVIDENCE_ID,
    source_kind: str = "project_reference",
    source_label: str = "endpoint_matrix_symbolic_candidate",
    source_available: bool = True,
    readonly_confirmed: bool = False,
    market_data_or_public_confirmed: bool = False,
    account_seq_not_required_confirmed: bool = False,
    order_scope_not_required_confirmed: bool = False,
    account_balance_fills_not_required_confirmed: bool = False,
    oauth_not_required_for_smoke_confirmed: bool = False,
    raw_output_block_confirmed: bool = True,
    confidence_label: str = "insufficient_confirmation",
) -> TossApiReadOnlyEndpointEvidence:
    """Build symbolic evidence without reading any project file at runtime."""

    return TossApiReadOnlyEndpointEvidence(
        evidence_id=evidence_id,
        source_kind=source_kind,
        source_label=source_label,
        source_available=source_available,
        readonly_confirmed=readonly_confirmed,
        market_data_or_public_confirmed=market_data_or_public_confirmed,
        account_seq_not_required_confirmed=account_seq_not_required_confirmed,
        order_scope_not_required_confirmed=order_scope_not_required_confirmed,
        account_balance_fills_not_required_confirmed=(
            account_balance_fills_not_required_confirmed
        ),
        oauth_not_required_for_smoke_confirmed=(
            oauth_not_required_for_smoke_confirmed
        ),
        raw_output_block_confirmed=raw_output_block_confirmed,
        confidence_label=confidence_label,
    )


def build_toss_api_readonly_endpoint_candidates(
    evidence: TossApiReadOnlyEndpointEvidence | None = None,
) -> tuple[TossApiReadOnlyEndpointCandidate, ...]:
    """Build default candidates; default remains unconfirmed and blocked."""

    active_evidence = evidence or build_toss_api_readonly_endpoint_evidence()
    return (
        TossApiReadOnlyEndpointCandidate(
            endpoint_id=DEFAULT_ENDPOINT_ID,
            endpoint_label=DEFAULT_ENDPOINT_LABEL,
            endpoint_scope=DEFAULT_ENDPOINT_SCOPE,
            readonly=True,
            market_data_only=True,
            public_or_market_data=True,
            requires_account_seq=False,
            requires_order_scope=False,
            requires_account_balance_fills=False,
            requires_oauth_token=False,
            live_http_executable_without_oauth=False,
            endpoint_confirmed=False,
            allows_raw_payload_output=False,
            evidence=active_evidence,
        ),
    )


def evaluate_toss_api_readonly_endpoint_selection_decision(
    candidates: tuple[TossApiReadOnlyEndpointCandidate, ...] | None = None,
) -> TossApiReadOnlyEndpointSelectionDecision:
    """Select the first eligible confirmed candidate, otherwise stay blocked."""

    active_candidates = candidates or build_toss_api_readonly_endpoint_candidates()
    selected = next(
        (candidate for candidate in active_candidates if _candidate_is_selectable(candidate)),
        None,
    )
    blocked = selected is None
    return TossApiReadOnlyEndpointSelectionDecision(
        endpoint_selection_invocation_allowed=True,
        ms_16_00_preflight_passed=True,
        ms_16_01_hardening_passed=True,
        selected_endpoint_id=selected.endpoint_id if selected else NO_SELECTED_ENDPOINT,
        selected_endpoint_label=(
            selected.endpoint_label if selected else NO_SELECTED_ENDPOINT
        ),
        selected_endpoint_confirmed=selected.endpoint_confirmed if selected else False,
        selection_blocked=blocked,
        blocking_reasons=_blocking_reasons(active_candidates, selected),
        live_http_execution_allowed_now=False,
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
        db_write_allowed_now=False,
        streamlit_allowed_now=False,
        recommendation_allowed_now=False,
        ranking_allowed_now=False,
        buy_sell_hold_allowed_now=False,
        raw_request_output_allowed=False,
        raw_response_output_allowed=False,
        endpoint_full_url_output_allowed=False,
        next_stage=DEFAULT_NEXT_STAGE,
    )


def run_toss_api_readonly_endpoint_selection(
    candidates: tuple[TossApiReadOnlyEndpointCandidate, ...] | None = None,
) -> TossApiReadOnlyEndpointSelectionResult:
    """Run deterministic no-I/O endpoint selection."""

    policy = build_toss_api_readonly_endpoint_selection_policy()
    active_candidates = candidates or build_toss_api_readonly_endpoint_candidates()
    decision = evaluate_toss_api_readonly_endpoint_selection_decision(
        active_candidates
    )
    safe_diagnostics = (
        SAFE_DIAGNOSTICS_KIND,
        f"candidate_count={len(active_candidates)}",
        f"selected_endpoint_id={decision.selected_endpoint_id or 'None'}",
        f"selected_endpoint_label={decision.selected_endpoint_label or 'None'}",
        f"selection_blocked={decision.selection_blocked}",
        "blocking_reason_ids="
        + ",".join(decision.blocking_reasons or ("none",)),
        "redaction_applied=True",
    )
    result = TossApiReadOnlyEndpointSelectionResult(
        result_id=SAFE_RESULT_ID,
        passed=True,
        policy=policy,
        candidates=active_candidates,
        decision=decision,
        safe_message=SAFE_MESSAGE_BLOCKED if decision.selection_blocked else SAFE_MESSAGE_SELECTED,
        safe_diagnostics=safe_diagnostics,
        next_stage=DEFAULT_NEXT_STAGE,
    )
    validation = validate_toss_api_readonly_endpoint_selection_result(result)
    return TossApiReadOnlyEndpointSelectionResult(
        result_id=result.result_id,
        passed=validation.passed,
        policy=result.policy,
        candidates=result.candidates,
        decision=result.decision,
        safe_message=result.safe_message,
        safe_diagnostics=result.safe_diagnostics,
        next_stage=result.next_stage,
    )


def validate_toss_api_readonly_endpoint_selection_result(
    result: TossApiReadOnlyEndpointSelectionResult | None = None,
) -> TossApiReadOnlyEndpointSelectionValidationResult:
    """Validate that endpoint selection remains safe and symbolic."""

    active_result = result or run_toss_api_readonly_endpoint_selection()
    failures: list[str] = []
    failures.extend(_validate_policy(active_result.policy))
    failures.extend(_validate_candidates(active_result.candidates))
    failures.extend(_validate_decision(active_result.decision))
    failures.extend(_validate_result(active_result))
    sensitive_validation = validate_no_sensitive_output(
        {
            "safe_message": active_result.safe_message,
            "safe_diagnostics": active_result.safe_diagnostics,
            "selected_endpoint_id": active_result.decision.selected_endpoint_id,
            "selected_endpoint_label": active_result.decision.selected_endpoint_label,
        },
        build_toss_api_redaction_policy(),
    )
    failures.extend(sensitive_validation.failures)
    return TossApiReadOnlyEndpointSelectionValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=_policy_flag_names(),
        checked_evidence_fields=_evidence_field_names(),
        checked_candidate_fields=_candidate_field_names(),
        checked_decision_fields=_decision_field_names(),
        checked_result_fields=_result_field_names(),
        diagnostics=(
            "readonly_endpoint_selection_validation",
            "redacted_diagnostics_only",
        ),
    )


def run_toss_api_readonly_endpoint_selection_preflight_checks() -> (
    TossApiReadOnlyEndpointSelectionValidationResult
):
    """Run dependency and endpoint selection checks without live HTTP."""

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
    ):
        if not result.passed:
            return _failed_validation(result.failures)
    first_validation = validate_toss_api_first_live_smoke_result()
    if not first_validation.passed:
        return _failed_validation(first_validation.failures)
    hardening_validation = validate_toss_api_live_smoke_result_hardening_result()
    if not hardening_validation.passed:
        return _failed_validation(hardening_validation.failures)
    return validate_toss_api_readonly_endpoint_selection_result(
        run_toss_api_readonly_endpoint_selection()
    )


def _candidate_is_selectable(candidate: TossApiReadOnlyEndpointCandidate) -> bool:
    evidence = candidate.evidence
    return all(
        (
            candidate.endpoint_confirmed,
            candidate.readonly,
            candidate.market_data_only or candidate.public_or_market_data,
            not candidate.requires_account_seq,
            not candidate.requires_order_scope,
            not candidate.requires_account_balance_fills,
            not candidate.requires_oauth_token,
            candidate.live_http_executable_without_oauth,
            not candidate.allows_raw_payload_output,
            evidence.readonly_confirmed,
            evidence.account_seq_not_required_confirmed,
            evidence.order_scope_not_required_confirmed,
            evidence.account_balance_fills_not_required_confirmed,
            evidence.oauth_not_required_for_smoke_confirmed,
            evidence.raw_output_block_confirmed,
        )
    )


def _blocking_reasons(
    candidates: tuple[TossApiReadOnlyEndpointCandidate, ...],
    selected: TossApiReadOnlyEndpointCandidate | None,
) -> tuple[str, ...]:
    if selected is not None:
        return ()
    if not candidates:
        return (BLOCKING_REASON_NO_SELECTED,)
    return (BLOCKING_REASON_CANDIDATE_REJECTED,)


def _validate_policy(
    policy: TossApiReadOnlyEndpointSelectionPolicy,
) -> tuple[str, ...]:
    failures: list[str] = []
    for flag in _policy_true_flag_names():
        if not getattr(policy, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in _policy_false_flag_names():
        if getattr(policy, flag):
            failures.append(f"{flag}_must_be_false")
    return tuple(failures)


def _validate_candidates(
    candidates: tuple[TossApiReadOnlyEndpointCandidate, ...],
) -> tuple[str, ...]:
    failures: list[str] = []
    for candidate in candidates:
        failures.extend(_validate_evidence(candidate.evidence))
        safe_text = " ".join(
            (
                candidate.endpoint_id,
                candidate.endpoint_label,
                candidate.endpoint_scope,
                candidate.evidence.evidence_id,
                candidate.evidence.source_kind,
                candidate.evidence.source_label,
                candidate.evidence.confidence_label,
            )
        ).casefold()
        if _contains_forbidden_fragment(safe_text):
            failures.append("candidate_forbidden_fragment_exposed")
        if "/" in safe_text or "http:" in safe_text or "https:" in safe_text:
            failures.append("candidate_endpoint_full_url_or_path_exposed")
    return tuple(failures)


def _validate_evidence(
    evidence: TossApiReadOnlyEndpointEvidence,
) -> tuple[str, ...]:
    return ()


def _validate_decision(
    decision: TossApiReadOnlyEndpointSelectionDecision,
) -> tuple[str, ...]:
    failures: list[str] = []
    for flag in _decision_true_flag_names():
        if not getattr(decision, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in _decision_false_flag_names():
        if getattr(decision, flag):
            failures.append(f"{flag}_must_be_false")
    if decision.selection_blocked and decision.selected_endpoint_confirmed:
        failures.append("blocked_selection_must_not_confirm_endpoint")
    if not decision.selection_blocked and not decision.selected_endpoint_confirmed:
        failures.append("selected_endpoint_must_be_confirmed")
    return tuple(failures)


def _validate_result(
    result: TossApiReadOnlyEndpointSelectionResult,
) -> tuple[str, ...]:
    failures: list[str] = []
    safe_output_text = " ".join(
        (
            result.result_id,
            result.safe_message,
            *result.safe_diagnostics,
            result.decision.selected_endpoint_id or "",
            result.decision.selected_endpoint_label or "",
            *result.decision.blocking_reasons,
            result.next_stage,
        )
    ).casefold()
    endpoint_output_text = " ".join(
        (
            *result.safe_diagnostics,
            result.decision.selected_endpoint_id or "",
            result.decision.selected_endpoint_label or "",
        )
    ).casefold()
    if _contains_forbidden_fragment(safe_output_text):
        failures.append("forbidden_safe_output_fragment_exposed")
    if (
        "/" in endpoint_output_text
        or "http:" in endpoint_output_text
        or "https:" in endpoint_output_text
    ):
        failures.append("endpoint_full_url_or_path_exposed")
    selected = _selected_candidate(result)
    if selected is not None and not _candidate_is_selectable(selected):
        failures.append("selected_candidate_must_meet_readonly_criteria")
    return tuple(failures)


def _selected_candidate(
    result: TossApiReadOnlyEndpointSelectionResult,
) -> TossApiReadOnlyEndpointCandidate | None:
    selected_id = result.decision.selected_endpoint_id
    if selected_id is None:
        return None
    for candidate in result.candidates:
        if candidate.endpoint_id == selected_id:
            return candidate
    return None


def _contains_forbidden_fragment(value: str) -> bool:
    lowered = value.casefold()
    return any(fragment in lowered for fragment in FORBIDDEN_SAFE_OUTPUT_FRAGMENTS)


def _failed_validation(
    failures: tuple[str, ...],
) -> TossApiReadOnlyEndpointSelectionValidationResult:
    return TossApiReadOnlyEndpointSelectionValidationResult(
        passed=False,
        failures=failures,
        checked_policy_flags=_policy_flag_names(),
        checked_evidence_fields=_evidence_field_names(),
        checked_candidate_fields=_candidate_field_names(),
        checked_decision_fields=_decision_field_names(),
        checked_result_fields=_result_field_names(),
        diagnostics=("readonly_endpoint_selection_dependency_failed",),
    )


def _policy_true_flag_names() -> tuple[str, ...]:
    return (
        "endpoint_selection_only",
        "endpoint_must_be_confirmed",
        "readonly_required",
        "market_data_or_public_required",
        "redacted_diagnostics_only",
    )


def _policy_false_flag_names() -> tuple[str, ...]:
    return (
        "live_http_execution_allowed",
        "credential_request_allowed",
        "credential_value_output_allowed",
        "raw_request_output_allowed",
        "raw_response_output_allowed",
        "endpoint_full_url_output_allowed",
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


def _evidence_field_names() -> tuple[str, ...]:
    return (
        "evidence_id",
        "source_kind",
        "source_label",
        "source_available",
        "readonly_confirmed",
        "market_data_or_public_confirmed",
        "account_seq_not_required_confirmed",
        "order_scope_not_required_confirmed",
        "account_balance_fills_not_required_confirmed",
        "oauth_not_required_for_smoke_confirmed",
        "raw_output_block_confirmed",
        "confidence_label",
    )


def _candidate_field_names() -> tuple[str, ...]:
    return (
        "endpoint_id",
        "endpoint_label",
        "endpoint_scope",
        "readonly",
        "market_data_only",
        "public_or_market_data",
        "requires_account_seq",
        "requires_order_scope",
        "requires_account_balance_fills",
        "requires_oauth_token",
        "live_http_executable_without_oauth",
        "endpoint_confirmed",
        "allows_raw_payload_output",
        "evidence",
    )


def _decision_field_names() -> tuple[str, ...]:
    return (
        "endpoint_selection_invocation_allowed",
        "ms_16_00_preflight_passed",
        "ms_16_01_hardening_passed",
        "selected_endpoint_id",
        "selected_endpoint_label",
        "selected_endpoint_confirmed",
        "selection_blocked",
        "blocking_reasons",
        "live_http_execution_allowed_now",
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
        "db_write_allowed_now",
        "streamlit_allowed_now",
        "recommendation_allowed_now",
        "ranking_allowed_now",
        "buy_sell_hold_allowed_now",
        "raw_request_output_allowed",
        "raw_response_output_allowed",
        "endpoint_full_url_output_allowed",
        "next_stage",
    )


def _result_field_names() -> tuple[str, ...]:
    return (
        "result_id",
        "passed",
        "policy",
        "candidates",
        "decision",
        "safe_message",
        "safe_diagnostics",
        "next_stage",
    )


def _decision_true_flag_names() -> tuple[str, ...]:
    return (
        "endpoint_selection_invocation_allowed",
        "ms_16_00_preflight_passed",
        "ms_16_01_hardening_passed",
    )


def _decision_false_flag_names() -> tuple[str, ...]:
    return (
        "live_http_execution_allowed_now",
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
        "db_write_allowed_now",
        "streamlit_allowed_now",
        "recommendation_allowed_now",
        "ranking_allowed_now",
        "buy_sell_hold_allowed_now",
        "raw_request_output_allowed",
        "raw_response_output_allowed",
        "endpoint_full_url_output_allowed",
    )
