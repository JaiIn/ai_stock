"""MS-16.04 confirmed endpoint evidence update.

This module is pure no-I/O. It models official/project evidence for a symbolic
read-only public/market-data endpoint candidate before any live HTTP smoke is
attempted. It does not request credentials, inspect runtime credential
presence, read environment variables, read files, write files, execute HTTP,
issue OAuth tokens, create Authorization headers, use accountSeq, touch
account/order/balance/fills data, use DB storage, import Streamlit, call
OpenAI/LLM APIs, or generate recommendation/ranking/trade actions.
"""

from __future__ import annotations

from dataclasses import dataclass

from ai_stock.clients.toss_api_client_contract import (
    build_toss_api_redaction_policy,
    validate_no_sensitive_output,
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


TOSS_API_CONFIRMED_ENDPOINT_EVIDENCE_VERSION = "MS-16.04"
TOSS_API_CONFIRMED_ENDPOINT_EVIDENCE_SCOPE = (
    "confirmed_endpoint_evidence_update"
)
DEFAULT_SELECTED_ENDPOINT_ID = "confirmed_prices_single_symbol_readonly_market_data"
DEFAULT_SELECTED_ENDPOINT_LABEL = "Prices single-symbol read-only market data"
DEFAULT_ENDPOINT_SCOPE = "readonly_market_data_price_snapshot"
DEFAULT_NEXT_STAGE_READY = "MS-16.05 first actual read-only live HTTP smoke"
DEFAULT_NEXT_STAGE_BLOCKED = "MS-16.04 confirmed endpoint evidence update"
SAFE_RESULT_ID = "safe_confirmed_endpoint_evidence_result"
SAFE_MESSAGE_READY = "confirmed_endpoint_evidence_ready"
SAFE_MESSAGE_BLOCKED = "confirmed_endpoint_evidence_blocked"
SAFE_DIAGNOSTICS_KIND = "redacted_confirmed_endpoint_evidence_diagnostics"
BLOCKING_REASON_EVIDENCE_MISSING = "confirmed_endpoint_evidence_missing"
BLOCKING_REASON_CANDIDATE_INELIGIBLE = "candidate_ineligible"
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
class TossApiConfirmedEndpointEvidencePolicy:
    """Closed policy for evidence update only."""

    evidence_version: str
    evidence_scope: str
    endpoint_evidence_update_only: bool
    live_http_execution_allowed: bool
    credential_request_allowed: bool
    credential_presence_check_allowed: bool
    credential_value_output_allowed: bool
    env_read_allowed: bool
    raw_request_output_allowed: bool
    raw_response_output_allowed: bool
    endpoint_full_url_output_allowed: bool
    endpoint_must_be_confirmed: bool
    readonly_required: bool
    public_or_market_data_required: bool
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
class TossApiConfirmedEndpointEvidenceSource:
    """Safe evidence source metadata without URL or path output."""

    evidence_source_id: str
    source_kind: str
    source_label: str
    source_available: bool
    official_reference_confirmed: bool
    project_reference_confirmed: bool
    readonly_confirmed: bool
    public_or_market_data_confirmed: bool
    account_seq_not_required_confirmed: bool
    order_scope_not_required_confirmed: bool
    account_balance_fills_not_required_confirmed: bool
    oauth_token_not_required_confirmed: bool
    raw_output_block_confirmed: bool
    confidence_label: str


@dataclass(frozen=True)
class TossApiConfirmedEndpointEvidenceCandidate:
    """Symbolic endpoint candidate selected only from confirmed evidence."""

    endpoint_id: str
    endpoint_label: str
    endpoint_scope: str
    readonly: bool
    public_or_market_data: bool
    requires_account_seq: bool
    requires_order_scope: bool
    requires_account_balance_fills: bool
    requires_oauth_token: bool
    endpoint_confirmed: bool
    allows_raw_payload_output: bool
    evidence_sources: tuple[TossApiConfirmedEndpointEvidenceSource, ...]


@dataclass(frozen=True)
class TossApiConfirmedEndpointEvidenceDecision:
    """Evidence decision that never opens runtime execution gates."""

    endpoint_evidence_invocation_allowed: bool
    endpoint_evidence_update_only: bool
    ms_16_00_preflight_passed: bool
    ms_16_01_hardening_passed: bool
    ms_16_02_endpoint_selection_passed: bool
    ms_16_03_operator_rehearsal_passed: bool
    selected_endpoint_id: str | None
    selected_endpoint_label: str | None
    selected_endpoint_confirmed: bool
    selected_endpoint_readonly: bool
    selected_endpoint_public_or_market_data: bool
    selected_endpoint_requires_account_seq: bool
    selected_endpoint_requires_order_scope: bool
    selected_endpoint_requires_account_balance_fills: bool
    selected_endpoint_requires_oauth_token: bool
    selected_endpoint_allows_raw_payload_output: bool
    selection_blocked: bool
    blocking_reasons: tuple[str, ...]
    live_http_execution_allowed_now: bool
    credential_request_allowed_now: bool
    credential_presence_check_allowed_now: bool
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
    next_stage: str


@dataclass(frozen=True)
class TossApiConfirmedEndpointEvidenceResult:
    """Top-level safe evidence update result."""

    result_id: str
    passed: bool
    policy: TossApiConfirmedEndpointEvidencePolicy
    evidence_sources: tuple[TossApiConfirmedEndpointEvidenceSource, ...]
    candidates: tuple[TossApiConfirmedEndpointEvidenceCandidate, ...]
    decision: TossApiConfirmedEndpointEvidenceDecision
    safe_message: str
    safe_diagnostics: tuple[str, ...]
    next_stage: str


@dataclass(frozen=True)
class TossApiConfirmedEndpointEvidenceValidationResult:
    """Validation result for MS-16.04 evidence update."""

    passed: bool
    failures: tuple[str, ...]
    checked_policy_flags: tuple[str, ...]
    checked_source_fields: tuple[str, ...]
    checked_candidate_fields: tuple[str, ...]
    checked_decision_fields: tuple[str, ...]
    checked_result_fields: tuple[str, ...]
    diagnostics: tuple[str, ...]


def build_toss_api_confirmed_endpoint_evidence_policy() -> (
    TossApiConfirmedEndpointEvidencePolicy
):
    """Build a closed endpoint-evidence-update-only policy."""

    return TossApiConfirmedEndpointEvidencePolicy(
        evidence_version=TOSS_API_CONFIRMED_ENDPOINT_EVIDENCE_VERSION,
        evidence_scope=TOSS_API_CONFIRMED_ENDPOINT_EVIDENCE_SCOPE,
        endpoint_evidence_update_only=True,
        live_http_execution_allowed=False,
        credential_request_allowed=False,
        credential_presence_check_allowed=False,
        credential_value_output_allowed=False,
        env_read_allowed=False,
        raw_request_output_allowed=False,
        raw_response_output_allowed=False,
        endpoint_full_url_output_allowed=False,
        endpoint_must_be_confirmed=True,
        readonly_required=True,
        public_or_market_data_required=True,
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


def build_toss_api_confirmed_endpoint_evidence_sources() -> (
    tuple[TossApiConfirmedEndpointEvidenceSource, ...]
):
    """Build static project/official evidence without runtime file reads."""

    return (
        TossApiConfirmedEndpointEvidenceSource(
            evidence_source_id="official_openapi_getprices_high_confidence",
            source_kind="official_and_project_reference",
            source_label="Official OpenAPI getPrices plus project live-safe record",
            source_available=True,
            official_reference_confirmed=True,
            project_reference_confirmed=True,
            readonly_confirmed=True,
            public_or_market_data_confirmed=True,
            account_seq_not_required_confirmed=True,
            order_scope_not_required_confirmed=True,
            account_balance_fills_not_required_confirmed=True,
            oauth_token_not_required_confirmed=True,
            raw_output_block_confirmed=True,
            confidence_label="high_confidence_project_record",
        ),
    )


def build_toss_api_confirmed_endpoint_evidence_candidates(
    evidence_sources: tuple[TossApiConfirmedEndpointEvidenceSource, ...] | None = None,
) -> tuple[TossApiConfirmedEndpointEvidenceCandidate, ...]:
    """Build default symbolic candidates from supplied evidence."""

    active_sources = (
        build_toss_api_confirmed_endpoint_evidence_sources()
        if evidence_sources is None
        else evidence_sources
    )
    return (
        TossApiConfirmedEndpointEvidenceCandidate(
            endpoint_id=DEFAULT_SELECTED_ENDPOINT_ID,
            endpoint_label=DEFAULT_SELECTED_ENDPOINT_LABEL,
            endpoint_scope=DEFAULT_ENDPOINT_SCOPE,
            readonly=True,
            public_or_market_data=True,
            requires_account_seq=False,
            requires_order_scope=False,
            requires_account_balance_fills=False,
            requires_oauth_token=False,
            endpoint_confirmed=True,
            allows_raw_payload_output=False,
            evidence_sources=active_sources,
        ),
    )


def evaluate_toss_api_confirmed_endpoint_evidence_decision(
    candidates: tuple[TossApiConfirmedEndpointEvidenceCandidate, ...] | None = None,
) -> TossApiConfirmedEndpointEvidenceDecision:
    """Select the first eligible confirmed endpoint evidence candidate."""

    active_candidates = (
        build_toss_api_confirmed_endpoint_evidence_candidates()
        if candidates is None
        else candidates
    )
    selected = next(
        (
            candidate
            for candidate in active_candidates
            if _candidate_is_selectable(candidate)
        ),
        None,
    )
    blocked = selected is None
    return TossApiConfirmedEndpointEvidenceDecision(
        endpoint_evidence_invocation_allowed=True,
        endpoint_evidence_update_only=True,
        ms_16_00_preflight_passed=True,
        ms_16_01_hardening_passed=True,
        ms_16_02_endpoint_selection_passed=True,
        ms_16_03_operator_rehearsal_passed=True,
        selected_endpoint_id=selected.endpoint_id if selected else None,
        selected_endpoint_label=selected.endpoint_label if selected else None,
        selected_endpoint_confirmed=selected.endpoint_confirmed if selected else False,
        selected_endpoint_readonly=selected.readonly if selected else False,
        selected_endpoint_public_or_market_data=(
            selected.public_or_market_data if selected else False
        ),
        selected_endpoint_requires_account_seq=(
            selected.requires_account_seq if selected else False
        ),
        selected_endpoint_requires_order_scope=(
            selected.requires_order_scope if selected else False
        ),
        selected_endpoint_requires_account_balance_fills=(
            selected.requires_account_balance_fills if selected else False
        ),
        selected_endpoint_requires_oauth_token=(
            selected.requires_oauth_token if selected else False
        ),
        selected_endpoint_allows_raw_payload_output=(
            selected.allows_raw_payload_output if selected else False
        ),
        selection_blocked=blocked,
        blocking_reasons=_blocking_reasons(active_candidates, selected),
        live_http_execution_allowed_now=False,
        credential_request_allowed_now=False,
        credential_presence_check_allowed_now=False,
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
        next_stage=DEFAULT_NEXT_STAGE_BLOCKED if blocked else DEFAULT_NEXT_STAGE_READY,
    )


def run_toss_api_confirmed_endpoint_evidence_update(
    candidates: tuple[TossApiConfirmedEndpointEvidenceCandidate, ...] | None = None,
) -> TossApiConfirmedEndpointEvidenceResult:
    """Run deterministic no-I/O endpoint evidence update."""

    policy = build_toss_api_confirmed_endpoint_evidence_policy()
    active_candidates = (
        build_toss_api_confirmed_endpoint_evidence_candidates()
        if candidates is None
        else candidates
    )
    evidence_sources = _unique_sources(active_candidates)
    decision = evaluate_toss_api_confirmed_endpoint_evidence_decision(
        active_candidates
    )
    safe_diagnostics = (
        SAFE_DIAGNOSTICS_KIND,
        f"evidence_source_count={len(evidence_sources)}",
        f"candidate_count={len(active_candidates)}",
        f"selected_endpoint_id={decision.selected_endpoint_id or 'None'}",
        f"selected_endpoint_label={decision.selected_endpoint_label or 'None'}",
        f"endpoint_evidence_confirmed={decision.selected_endpoint_confirmed}",
        f"selection_blocked={decision.selection_blocked}",
        "blocking_reason_ids="
        + ",".join(decision.blocking_reasons or ("none",)),
        "redaction_applied=True",
    )
    result = TossApiConfirmedEndpointEvidenceResult(
        result_id=SAFE_RESULT_ID,
        passed=True,
        policy=policy,
        evidence_sources=evidence_sources,
        candidates=active_candidates,
        decision=decision,
        safe_message=(
            SAFE_MESSAGE_BLOCKED if decision.selection_blocked else SAFE_MESSAGE_READY
        ),
        safe_diagnostics=safe_diagnostics,
        next_stage=decision.next_stage,
    )
    validation = validate_toss_api_confirmed_endpoint_evidence_result(result)
    return TossApiConfirmedEndpointEvidenceResult(
        result_id=result.result_id,
        passed=validation.passed,
        policy=result.policy,
        evidence_sources=result.evidence_sources,
        candidates=result.candidates,
        decision=result.decision,
        safe_message=result.safe_message,
        safe_diagnostics=result.safe_diagnostics,
        next_stage=result.next_stage,
    )


def validate_toss_api_confirmed_endpoint_evidence_result(
    result: TossApiConfirmedEndpointEvidenceResult | None = None,
) -> TossApiConfirmedEndpointEvidenceValidationResult:
    """Validate that confirmed evidence output remains safe and symbolic."""

    active_result = result or run_toss_api_confirmed_endpoint_evidence_update()
    failures: list[str] = []
    failures.extend(_validate_policy(active_result.policy))
    failures.extend(_validate_sources(active_result.evidence_sources))
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
    return TossApiConfirmedEndpointEvidenceValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=_policy_flag_names(),
        checked_source_fields=_source_field_names(),
        checked_candidate_fields=_candidate_field_names(),
        checked_decision_fields=_decision_field_names(),
        checked_result_fields=_result_field_names(),
        diagnostics=("confirmed_endpoint_evidence_validation",),
    )


def run_toss_api_confirmed_endpoint_evidence_preflight_checks() -> (
    TossApiConfirmedEndpointEvidenceValidationResult
):
    """Run dependency and evidence checks without I/O or live HTTP."""

    for result in (
        run_toss_api_first_live_smoke_preflight_checks(),
        run_toss_api_live_smoke_result_hardening_preflight_checks(),
        run_toss_api_readonly_endpoint_selection_preflight_checks(),
        run_toss_api_live_smoke_operator_rehearsal_preflight_checks(),
    ):
        if not result.passed:
            return _failed_validation(result.failures)
    return validate_toss_api_confirmed_endpoint_evidence_result(
        run_toss_api_confirmed_endpoint_evidence_update()
    )


def _candidate_is_selectable(
    candidate: TossApiConfirmedEndpointEvidenceCandidate,
) -> bool:
    return all(
        (
            candidate.endpoint_confirmed,
            candidate.readonly,
            candidate.public_or_market_data,
            not candidate.requires_account_seq,
            not candidate.requires_order_scope,
            not candidate.requires_account_balance_fills,
            not candidate.requires_oauth_token,
            not candidate.allows_raw_payload_output,
            bool(candidate.evidence_sources),
            all(_source_is_confirming(source) for source in candidate.evidence_sources),
        )
    )


def _source_is_confirming(source: TossApiConfirmedEndpointEvidenceSource) -> bool:
    return all(
        (
            source.source_available,
            source.official_reference_confirmed or source.project_reference_confirmed,
            source.readonly_confirmed,
            source.public_or_market_data_confirmed,
            source.account_seq_not_required_confirmed,
            source.order_scope_not_required_confirmed,
            source.account_balance_fills_not_required_confirmed,
            source.oauth_token_not_required_confirmed,
            source.raw_output_block_confirmed,
        )
    )


def _blocking_reasons(
    candidates: tuple[TossApiConfirmedEndpointEvidenceCandidate, ...],
    selected: TossApiConfirmedEndpointEvidenceCandidate | None,
) -> tuple[str, ...]:
    if selected is not None:
        return ()
    if not candidates or not any(candidate.evidence_sources for candidate in candidates):
        return (BLOCKING_REASON_EVIDENCE_MISSING,)
    return (BLOCKING_REASON_CANDIDATE_INELIGIBLE,)


def _unique_sources(
    candidates: tuple[TossApiConfirmedEndpointEvidenceCandidate, ...],
) -> tuple[TossApiConfirmedEndpointEvidenceSource, ...]:
    sources: dict[str, TossApiConfirmedEndpointEvidenceSource] = {}
    for candidate in candidates:
        for source in candidate.evidence_sources:
            sources[source.evidence_source_id] = source
    return tuple(sources.values())


def _validate_policy(
    policy: TossApiConfirmedEndpointEvidencePolicy,
) -> tuple[str, ...]:
    failures: list[str] = []
    for flag in _policy_true_flag_names():
        if not getattr(policy, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in _policy_false_flag_names():
        if getattr(policy, flag):
            failures.append(f"{flag}_must_be_false")
    return tuple(failures)


def _validate_sources(
    sources: tuple[TossApiConfirmedEndpointEvidenceSource, ...],
) -> tuple[str, ...]:
    failures: list[str] = []
    for source in sources:
        safe_text = " ".join(
            (
                source.evidence_source_id,
                source.source_kind,
                source.source_label,
                source.confidence_label,
            )
        ).casefold()
        if _contains_forbidden_fragment(safe_text):
            failures.append("source_forbidden_fragment_exposed")
        if "/" in safe_text or "http:" in safe_text or "https:" in safe_text:
            failures.append("source_url_or_path_exposed")
    return tuple(failures)


def _validate_candidates(
    candidates: tuple[TossApiConfirmedEndpointEvidenceCandidate, ...],
) -> tuple[str, ...]:
    failures: list[str] = []
    for candidate in candidates:
        safe_text = " ".join(
            (
                candidate.endpoint_id,
                candidate.endpoint_label,
                candidate.endpoint_scope,
            )
        ).casefold()
        if _contains_forbidden_fragment(safe_text):
            failures.append("candidate_forbidden_fragment_exposed")
        if "/" in safe_text or "http:" in safe_text or "https:" in safe_text:
            failures.append("candidate_endpoint_full_url_or_path_exposed")
    return tuple(failures)


def _validate_decision(
    decision: TossApiConfirmedEndpointEvidenceDecision,
) -> tuple[str, ...]:
    failures: list[str] = []
    for flag in _decision_true_flag_names():
        if not getattr(decision, flag):
            failures.append(f"{flag}_must_be_true")
    for flag in _decision_false_flag_names():
        if getattr(decision, flag):
            failures.append(f"{flag}_must_be_false")
    if decision.selection_blocked and decision.selected_endpoint_id is not None:
        failures.append("blocked_selection_must_not_expose_selected_endpoint")
    if not decision.selection_blocked:
        if decision.selected_endpoint_id is None:
            failures.append("selected_endpoint_id_required_when_unblocked")
        if not decision.selected_endpoint_confirmed:
            failures.append("selected_endpoint_must_be_confirmed")
        if not decision.selected_endpoint_readonly:
            failures.append("selected_endpoint_must_be_readonly")
        if not decision.selected_endpoint_public_or_market_data:
            failures.append("selected_endpoint_must_be_public_or_market_data")
        for flag in (
            "selected_endpoint_requires_account_seq",
            "selected_endpoint_requires_order_scope",
            "selected_endpoint_requires_account_balance_fills",
            "selected_endpoint_requires_oauth_token",
            "selected_endpoint_allows_raw_payload_output",
        ):
            if getattr(decision, flag):
                failures.append(f"{flag}_must_be_false")
    return tuple(failures)


def _validate_result(
    result: TossApiConfirmedEndpointEvidenceResult,
) -> tuple[str, ...]:
    failures: list[str] = []
    safe_text = " ".join(
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
    diagnostics_text = " ".join(result.safe_diagnostics).casefold()
    if _contains_forbidden_fragment(safe_text):
        failures.append("forbidden_safe_output_fragment_exposed")
    if "/" in diagnostics_text or "http:" in diagnostics_text or "https:" in diagnostics_text:
        failures.append("endpoint_full_url_or_path_exposed")
    if "command" in diagnostics_text:
        failures.append("execution_command_exposed")
    selected = _selected_candidate(result)
    if selected is not None and not _candidate_is_selectable(selected):
        failures.append("selected_candidate_must_meet_evidence_criteria")
    return tuple(failures)


def _selected_candidate(
    result: TossApiConfirmedEndpointEvidenceResult,
) -> TossApiConfirmedEndpointEvidenceCandidate | None:
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
) -> TossApiConfirmedEndpointEvidenceValidationResult:
    return TossApiConfirmedEndpointEvidenceValidationResult(
        passed=False,
        failures=failures,
        checked_policy_flags=_policy_flag_names(),
        checked_source_fields=_source_field_names(),
        checked_candidate_fields=_candidate_field_names(),
        checked_decision_fields=_decision_field_names(),
        checked_result_fields=_result_field_names(),
        diagnostics=("confirmed_endpoint_evidence_dependency_failed",),
    )


def _policy_true_flag_names() -> tuple[str, ...]:
    return (
        "endpoint_evidence_update_only",
        "endpoint_must_be_confirmed",
        "readonly_required",
        "public_or_market_data_required",
        "redacted_diagnostics_only",
    )


def _policy_false_flag_names() -> tuple[str, ...]:
    return (
        "live_http_execution_allowed",
        "credential_request_allowed",
        "credential_presence_check_allowed",
        "credential_value_output_allowed",
        "env_read_allowed",
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


def _source_field_names() -> tuple[str, ...]:
    return (
        "evidence_source_id",
        "source_kind",
        "source_label",
        "source_available",
        "official_reference_confirmed",
        "project_reference_confirmed",
        "readonly_confirmed",
        "public_or_market_data_confirmed",
        "account_seq_not_required_confirmed",
        "order_scope_not_required_confirmed",
        "account_balance_fills_not_required_confirmed",
        "oauth_token_not_required_confirmed",
        "raw_output_block_confirmed",
        "confidence_label",
    )


def _candidate_field_names() -> tuple[str, ...]:
    return (
        "endpoint_id",
        "endpoint_label",
        "endpoint_scope",
        "readonly",
        "public_or_market_data",
        "requires_account_seq",
        "requires_order_scope",
        "requires_account_balance_fills",
        "requires_oauth_token",
        "endpoint_confirmed",
        "allows_raw_payload_output",
        "evidence_sources",
    )


def _decision_true_flag_names() -> tuple[str, ...]:
    return (
        "endpoint_evidence_invocation_allowed",
        "endpoint_evidence_update_only",
        "ms_16_00_preflight_passed",
        "ms_16_01_hardening_passed",
        "ms_16_02_endpoint_selection_passed",
        "ms_16_03_operator_rehearsal_passed",
    )


def _decision_false_flag_names() -> tuple[str, ...]:
    return (
        "live_http_execution_allowed_now",
        "credential_request_allowed_now",
        "credential_presence_check_allowed_now",
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
    return (
        *_decision_true_flag_names(),
        "selected_endpoint_id",
        "selected_endpoint_label",
        "selected_endpoint_confirmed",
        "selected_endpoint_readonly",
        "selected_endpoint_public_or_market_data",
        "selected_endpoint_requires_account_seq",
        "selected_endpoint_requires_order_scope",
        "selected_endpoint_requires_account_balance_fills",
        "selected_endpoint_requires_oauth_token",
        "selected_endpoint_allows_raw_payload_output",
        "selection_blocked",
        "blocking_reasons",
        *_decision_false_flag_names(),
        "next_stage",
    )


def _result_field_names() -> tuple[str, ...]:
    return (
        "result_id",
        "passed",
        "policy",
        "evidence_sources",
        "candidates",
        "decision",
        "safe_message",
        "safe_diagnostics",
        "next_stage",
    )
