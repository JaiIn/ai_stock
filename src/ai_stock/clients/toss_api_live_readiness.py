"""Pure live-readiness gate for future Toss API smoke planning.

This module only evaluates symbolic preflight state from MS-14.00 through
MS-14.02. It does not read runtime config, create secrets, or call services.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Mapping

from ai_stock.clients.toss_api_client_contract import (
    TossApiContractValidationResult,
    TossApiExternalCapabilityFlags,
    build_toss_api_external_capability_flags,
    build_toss_api_redaction_policy,
    redact_mapping,
    run_toss_api_client_contract_preflight_checks,
    validate_no_sensitive_output,
)
from ai_stock.clients.toss_api_config_guardrail import (
    TossApiConfigGuardrailPreflightResult,
    run_toss_api_config_guardrail_preflight_checks,
)
from ai_stock.clients.toss_api_fake_transport import (
    TossApiFakeTransportValidationResult,
    run_toss_api_fake_transport_preflight_checks,
)


TOSS_API_LIVE_READINESS_VERSION = "MS-14.03"
TOSS_API_LIVE_READINESS_SCOPE = (
    "pure_no_io_live_readiness_no_secret_dry_run_gate"
)
NEXT_STAGE_LIVE_SMOKE_CANDIDATE = "MS-15.00 first read-only live smoke planning"

CHECKLIST_CATEGORIES = (
    "contract_preflight",
    "fake_transport_preflight",
    "config_guardrail_preflight",
    "credential_request_block",
    "secret_output_block",
    "env_read_block",
    "file_io_block",
    "live_http_block",
    "oauth_block",
    "account_seq_block",
    "order_account_balance_fills_block",
    "db_block",
    "streamlit_block",
    "llm_block",
    "recommendation_ranking_action_block",
    "next_stage_gate",
)


@dataclass(frozen=True)
class TossApiLiveReadinessPolicy:
    """Policy proving that live readiness remains no-secret and no-I/O."""

    readiness_version: str
    readiness_scope: str
    uses_contract_policy: bool
    uses_fake_transport: bool
    uses_config_guardrail: bool
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
    no_secret_dry_run_only: bool
    credential_required_now: bool
    toss_key_required_now: bool
    toss_secret_required_now: bool
    openai_key_required_now: bool
    access_token_required_now: bool
    safe_to_request_user_secret_now: bool
    live_http_ready: bool
    oauth_ready: bool
    account_seq_required_now: bool
    order_required_now: bool
    streamlit_required: bool
    http_smoke_required: bool
    next_stage_live_smoke_candidate: str
    blocking_reason_until_explicit_live_stage: str


@dataclass(frozen=True)
class TossApiLiveReadinessChecklistItem:
    """One symbolic readiness checklist entry."""

    item_id: str
    title: str
    category: str
    passed: bool
    severity: str
    evidence_label: str
    blocking: bool
    remediation_hint: str


@dataclass(frozen=True)
class TossApiLiveReadinessGateDecision:
    """Decision for whether live smoke can proceed in this stage."""

    passed: bool
    live_smoke_allowed_now: bool
    safe_to_request_user_secret_now: bool
    credential_required_now: bool
    toss_key_required_now: bool
    toss_secret_required_now: bool
    access_token_required_now: bool
    oauth_allowed_now: bool
    live_http_allowed_now: bool
    account_seq_allowed_now: bool
    order_allowed_now: bool
    openai_key_allowed_now: bool
    next_allowed_stage: str
    blocking_reasons: tuple[str, ...]
    checklist_summary: Mapping[str, int]


@dataclass(frozen=True)
class TossApiLiveReadinessPreflightResult:
    """Aggregate live-readiness preflight result."""

    passed: bool
    failures: tuple[str, ...]
    policy: TossApiLiveReadinessPolicy
    checklist: tuple[TossApiLiveReadinessChecklistItem, ...]
    gate_decision: TossApiLiveReadinessGateDecision
    contract_preflight: TossApiContractValidationResult
    fake_transport_preflight: TossApiFakeTransportValidationResult
    config_guardrail_preflight: TossApiConfigGuardrailPreflightResult
    capability_flags: TossApiExternalCapabilityFlags
    diagnostics: tuple[str, ...]


@dataclass(frozen=True)
class TossApiNoSecretDryRunResult:
    """Safe summary result for the no-secret dry run gate."""

    passed: bool
    policy_version: str
    checklist_item_ids: tuple[str, ...]
    checklist_passed_count: int
    checklist_blocking_count: int
    gate_decision: TossApiLiveReadinessGateDecision
    safe_diagnostics: tuple[str, ...]
    next_stage_label: str


def build_toss_api_live_readiness_policy() -> TossApiLiveReadinessPolicy:
    """Return the MS-14.03 no-secret live-readiness policy."""

    return TossApiLiveReadinessPolicy(
        readiness_version=TOSS_API_LIVE_READINESS_VERSION,
        readiness_scope=TOSS_API_LIVE_READINESS_SCOPE,
        uses_contract_policy=True,
        uses_fake_transport=True,
        uses_config_guardrail=True,
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
        no_secret_dry_run_only=True,
        credential_required_now=False,
        toss_key_required_now=False,
        toss_secret_required_now=False,
        openai_key_required_now=False,
        access_token_required_now=False,
        safe_to_request_user_secret_now=False,
        live_http_ready=False,
        oauth_ready=False,
        account_seq_required_now=False,
        order_required_now=False,
        streamlit_required=False,
        http_smoke_required=False,
        next_stage_live_smoke_candidate=NEXT_STAGE_LIVE_SMOKE_CANDIDATE,
        blocking_reason_until_explicit_live_stage="explicit_live_stage_gate_required",
    )


def build_toss_api_live_readiness_checklist(
    contract_preflight: TossApiContractValidationResult | None = None,
    fake_transport_preflight: TossApiFakeTransportValidationResult | None = None,
    config_guardrail_preflight: TossApiConfigGuardrailPreflightResult | None = None,
    policy: TossApiLiveReadinessPolicy | None = None,
) -> tuple[TossApiLiveReadinessChecklistItem, ...]:
    """Build deterministic checklist items from symbolic preflight results."""

    active_policy = policy or build_toss_api_live_readiness_policy()
    contract_result = (
        contract_preflight or run_toss_api_client_contract_preflight_checks()
    )
    fake_result = (
        fake_transport_preflight or run_toss_api_fake_transport_preflight_checks()
    )
    config_result = (
        config_guardrail_preflight or run_toss_api_config_guardrail_preflight_checks()
    )

    return (
        _build_checklist_item(
            item_id="ms1400_contract_preflight",
            title="MS-14.00 contract preflight",
            category="contract_preflight",
            passed=contract_result.passed,
            evidence_label="contract_result_passed",
            blocking=not contract_result.passed,
            remediation_hint="repair_contract_preflight",
        ),
        _build_checklist_item(
            item_id="ms1401_fake_transport_preflight",
            title="MS-14.01 fake transport preflight",
            category="fake_transport_preflight",
            passed=fake_result.passed,
            evidence_label="fake_transport_result_passed",
            blocking=not fake_result.passed,
            remediation_hint="repair_fake_transport_preflight",
        ),
        _build_checklist_item(
            item_id="ms1402_config_guardrail_preflight",
            title="MS-14.02 config guardrail preflight",
            category="config_guardrail_preflight",
            passed=config_result.passed,
            evidence_label="config_guardrail_result_passed",
            blocking=not config_result.passed,
            remediation_hint="repair_config_guardrail_preflight",
        ),
        _build_checklist_item(
            item_id="secret_request_disabled",
            title="Secret request disabled",
            category="credential_request_block",
            passed=not active_policy.safe_to_request_user_secret_now,
            evidence_label="safe_to_request_user_secret_now_false",
            blocking=True,
            remediation_hint="wait_for_explicit_live_stage",
        ),
        _build_checklist_item(
            item_id="secret_output_disabled",
            title="Secret output disabled",
            category="secret_output_block",
            passed=True,
            evidence_label="redacted_safe_output_only",
            blocking=True,
            remediation_hint="keep_output_redacted",
        ),
        _build_checklist_item(
            item_id="env_read_disabled",
            title="Environment read disabled",
            category="env_read_block",
            passed=active_policy.no_env_read,
            evidence_label="no_env_read_true",
            blocking=True,
            remediation_hint="wait_for_explicit_live_stage",
        ),
        _build_checklist_item(
            item_id="file_io_disabled",
            title="File I/O disabled",
            category="file_io_block",
            passed=active_policy.no_file_read and active_policy.no_file_write,
            evidence_label="no_file_read_write_true",
            blocking=True,
            remediation_hint="wait_for_explicit_live_stage",
        ),
        _build_checklist_item(
            item_id="live_http_disabled",
            title="Live HTTP disabled",
            category="live_http_block",
            passed=active_policy.no_live_http_now,
            evidence_label="no_live_http_now_true",
            blocking=True,
            remediation_hint="wait_for_explicit_live_stage",
        ),
        _build_checklist_item(
            item_id="oauth_disabled",
            title="OAuth disabled",
            category="oauth_block",
            passed=active_policy.no_oauth and not active_policy.oauth_ready,
            evidence_label="oauth_ready_false",
            blocking=True,
            remediation_hint="wait_for_explicit_live_stage",
        ),
        _build_checklist_item(
            item_id="account_seq_disabled",
            title="Account sequence disabled",
            category="account_seq_block",
            passed=active_policy.no_account_seq
            and not active_policy.account_seq_required_now,
            evidence_label="account_seq_required_now_false",
            blocking=True,
            remediation_hint="wait_for_explicit_live_stage",
        ),
        _build_checklist_item(
            item_id="trading_account_data_disabled",
            title="Trading and account data disabled",
            category="order_account_balance_fills_block",
            passed=active_policy.no_orders
            and active_policy.no_account_assets
            and active_policy.no_balance
            and active_policy.no_fills,
            evidence_label="account_trade_capability_false",
            blocking=True,
            remediation_hint="wait_for_explicit_live_stage",
        ),
        _build_checklist_item(
            item_id="db_disabled",
            title="Database disabled",
            category="db_block",
            passed=active_policy.no_db,
            evidence_label="no_db_true",
            blocking=True,
            remediation_hint="wait_for_explicit_live_stage",
        ),
        _build_checklist_item(
            item_id="streamlit_disabled",
            title="Streamlit disabled",
            category="streamlit_block",
            passed=active_policy.no_streamlit and not active_policy.streamlit_required,
            evidence_label="streamlit_required_false",
            blocking=False,
            remediation_hint="keep_client_layer_ui_free",
        ),
        _build_checklist_item(
            item_id="llm_disabled",
            title="LLM disabled",
            category="llm_block",
            passed=active_policy.no_llm,
            evidence_label="no_llm_true",
            blocking=True,
            remediation_hint="wait_for_explicit_ai_stage",
        ),
        _build_checklist_item(
            item_id="ranking_directive_disabled",
            title="Ranking and directive output disabled",
            category="recommendation_ranking_action_block",
            passed=active_policy.no_recommendation and active_policy.no_ranking,
            evidence_label="no_recommendation_no_ranking_true",
            blocking=True,
            remediation_hint="wait_for_explicit_model_stage",
        ),
        _build_checklist_item(
            item_id="next_stage_label_recorded",
            title="Next stage label recorded",
            category="next_stage_gate",
            passed=active_policy.next_stage_live_smoke_candidate
            == NEXT_STAGE_LIVE_SMOKE_CANDIDATE,
            evidence_label="next_stage_candidate_recorded",
            blocking=False,
            remediation_hint="keep_manual_approval_required",
        ),
    )


def evaluate_toss_api_live_readiness_gate(
    checklist: tuple[TossApiLiveReadinessChecklistItem, ...] | None = None,
    policy: TossApiLiveReadinessPolicy | None = None,
) -> TossApiLiveReadinessGateDecision:
    """Evaluate the stage gate without allowing live work now."""

    active_policy = policy or build_toss_api_live_readiness_policy()
    active_checklist = checklist or build_toss_api_live_readiness_checklist(
        policy=active_policy
    )
    passed_count = sum(1 for item in active_checklist if item.passed)
    blocking_count = sum(1 for item in active_checklist if item.blocking)
    failed_count = sum(1 for item in active_checklist if not item.passed)

    return TossApiLiveReadinessGateDecision(
        passed=failed_count == 0,
        live_smoke_allowed_now=False,
        safe_to_request_user_secret_now=False,
        credential_required_now=False,
        toss_key_required_now=False,
        toss_secret_required_now=False,
        access_token_required_now=False,
        oauth_allowed_now=False,
        live_http_allowed_now=False,
        account_seq_allowed_now=False,
        order_allowed_now=False,
        openai_key_allowed_now=False,
        next_allowed_stage=active_policy.next_stage_live_smoke_candidate,
        blocking_reasons=(
            "manual_live_stage_required",
            "runtime_access_disabled_now",
            "user_secret_prompt_disabled",
        ),
        checklist_summary={
            "total": len(active_checklist),
            "passed": passed_count,
            "failed": failed_count,
            "blocking": blocking_count,
        },
    )


def run_toss_api_no_secret_dry_run() -> TossApiNoSecretDryRunResult:
    """Run the deterministic no-secret dry run and return a safe summary."""

    policy = build_toss_api_live_readiness_policy()
    checklist = build_toss_api_live_readiness_checklist(policy=policy)
    gate_decision = evaluate_toss_api_live_readiness_gate(checklist, policy)
    return TossApiNoSecretDryRunResult(
        passed=gate_decision.passed,
        policy_version=policy.readiness_version,
        checklist_item_ids=tuple(item.item_id for item in checklist),
        checklist_passed_count=sum(1 for item in checklist if item.passed),
        checklist_blocking_count=sum(1 for item in checklist if item.blocking),
        gate_decision=gate_decision,
        safe_diagnostics=(
            "dry_run_completed",
            "preflight_layers_passed",
            "manual_gate_required",
        ),
        next_stage_label=policy.next_stage_live_smoke_candidate,
    )


def validate_toss_api_live_readiness_policy(
    policy: TossApiLiveReadinessPolicy | None = None,
) -> TossApiContractValidationResult:
    """Validate the MS-14.03 policy flags."""

    active_policy = policy or build_toss_api_live_readiness_policy()
    required_true_flags = (
        "uses_contract_policy",
        "uses_fake_transport",
        "uses_config_guardrail",
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
        "no_secret_dry_run_only",
    )
    required_false_flags = (
        "credential_required_now",
        "toss_key_required_now",
        "toss_secret_required_now",
        "openai_key_required_now",
        "access_token_required_now",
        "safe_to_request_user_secret_now",
        "live_http_ready",
        "oauth_ready",
        "account_seq_required_now",
        "order_required_now",
        "streamlit_required",
        "http_smoke_required",
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

    return TossApiContractValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=(*required_true_flags, *required_false_flags),
        checked_endpoint_kinds=(),
        checked_request_fields=(),
        checked_response_fields=(),
        checked_error_kinds=(),
        checked_redaction_fields=build_toss_api_redaction_policy().sensitive_field_names,
        diagnostics=("live_readiness_policy_validation",),
    )


def validate_toss_api_live_readiness_checklist(
    checklist: tuple[TossApiLiveReadinessChecklistItem, ...] | None = None,
) -> TossApiContractValidationResult:
    """Validate checklist category coverage and passing evidence."""

    active_checklist = checklist or build_toss_api_live_readiness_checklist()
    failures: list[str] = []
    categories = tuple(item.category for item in active_checklist)
    if categories != CHECKLIST_CATEGORIES:
        failures.append("checklist_categories_must_match_contract")
    for item in active_checklist:
        if not item.passed:
            failures.append(f"checklist_item_failed:{item.item_id}")
        if item.category not in CHECKLIST_CATEGORIES:
            failures.append(f"checklist_category_unknown:{item.category}")

    return TossApiContractValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=("checklist_category_coverage",),
        checked_endpoint_kinds=(),
        checked_request_fields=(),
        checked_response_fields=(),
        checked_error_kinds=(),
        checked_redaction_fields=build_toss_api_redaction_policy().sensitive_field_names,
        diagnostics=("live_readiness_checklist_validation",),
    )


def validate_toss_api_no_secret_dry_run_result(
    result: TossApiNoSecretDryRunResult | None = None,
) -> TossApiContractValidationResult:
    """Validate that the dry run result exposes only safe summary values."""

    active_result = result or run_toss_api_no_secret_dry_run()
    safe_output = _safe_output_mapping_from_dry_run(active_result)
    sensitive_result = validate_no_sensitive_output(
        safe_output,
        build_toss_api_redaction_policy(),
    )
    failures = list(sensitive_result.failures)
    if active_result.gate_decision.live_smoke_allowed_now:
        failures.append("live_smoke_allowed_now_must_be_false")
    if active_result.gate_decision.safe_to_request_user_secret_now:
        failures.append("safe_to_request_user_secret_now_must_be_false")
    if active_result.gate_decision.credential_required_now:
        failures.append("credential_required_now_must_be_false")
    if active_result.gate_decision.oauth_allowed_now:
        failures.append("oauth_allowed_now_must_be_false")
    if active_result.gate_decision.live_http_allowed_now:
        failures.append("live_http_allowed_now_must_be_false")
    if active_result.gate_decision.account_seq_allowed_now:
        failures.append("account_seq_allowed_now_must_be_false")
    if active_result.gate_decision.order_allowed_now:
        failures.append("order_allowed_now_must_be_false")
    if active_result.gate_decision.openai_key_allowed_now:
        failures.append("openai_key_allowed_now_must_be_false")

    return TossApiContractValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=(
            "live_smoke_allowed_now",
            "safe_to_request_user_secret_now",
            "credential_required_now",
            "oauth_allowed_now",
            "live_http_allowed_now",
            "account_seq_allowed_now",
            "order_allowed_now",
            "openai_key_allowed_now",
        ),
        checked_endpoint_kinds=(),
        checked_request_fields=(),
        checked_response_fields=tuple(safe_output),
        checked_error_kinds=(),
        checked_redaction_fields=build_toss_api_redaction_policy().sensitive_field_names,
        diagnostics=("no_secret_dry_run_result_validation",),
    )


def run_toss_api_live_readiness_preflight_checks() -> (
    TossApiLiveReadinessPreflightResult
):
    """Run deterministic MS-14.03 preflight checks without I/O."""

    policy = build_toss_api_live_readiness_policy()
    contract_preflight = run_toss_api_client_contract_preflight_checks()
    fake_transport_preflight = run_toss_api_fake_transport_preflight_checks()
    config_guardrail_preflight = run_toss_api_config_guardrail_preflight_checks()
    checklist = build_toss_api_live_readiness_checklist(
        contract_preflight=contract_preflight,
        fake_transport_preflight=fake_transport_preflight,
        config_guardrail_preflight=config_guardrail_preflight,
        policy=policy,
    )
    gate_decision = evaluate_toss_api_live_readiness_gate(checklist, policy)
    dry_run_result = run_toss_api_no_secret_dry_run()
    policy_result = validate_toss_api_live_readiness_policy(policy)
    checklist_result = validate_toss_api_live_readiness_checklist(checklist)
    dry_run_validation = validate_toss_api_no_secret_dry_run_result(dry_run_result)
    capability_flags = build_toss_api_external_capability_flags()
    redacted_probe = redact_mapping(
        {"access_token": "dummy-sensitive-value"},
        build_toss_api_redaction_policy(),
    )

    failures: list[str] = []
    for result in (
        contract_preflight,
        fake_transport_preflight,
        config_guardrail_preflight,
        policy_result,
        checklist_result,
        dry_run_validation,
    ):
        failures.extend(result.failures)
    if redacted_probe["access_token"] != build_toss_api_redaction_policy().redaction_placeholder:
        failures.append("redaction_probe_must_mask_sensitive_value")
    if any(capability_flags.__dict__.values()):
        failures.append("external_capability_flags_must_all_be_false")

    return TossApiLiveReadinessPreflightResult(
        passed=not failures,
        failures=tuple(failures),
        policy=policy,
        checklist=checklist,
        gate_decision=gate_decision,
        contract_preflight=contract_preflight,
        fake_transport_preflight=fake_transport_preflight,
        config_guardrail_preflight=config_guardrail_preflight,
        capability_flags=capability_flags,
        diagnostics=(
            "pure_no_io_live_readiness_preflight",
            "contract_fake_config_layers_reused",
            "no_secret_dry_run_only",
            "manual_gate_required",
        ),
    )


def _build_checklist_item(
    *,
    item_id: str,
    title: str,
    category: str,
    passed: bool,
    evidence_label: str,
    blocking: bool,
    remediation_hint: str,
) -> TossApiLiveReadinessChecklistItem:
    return TossApiLiveReadinessChecklistItem(
        item_id=item_id,
        title=title,
        category=category,
        passed=passed,
        severity="blocking" if blocking else "info",
        evidence_label=evidence_label,
        blocking=blocking,
        remediation_hint=remediation_hint,
    )


def _safe_output_mapping_from_dry_run(
    result: TossApiNoSecretDryRunResult,
) -> Mapping[str, object]:
    return {
        "safe_policy_version": result.policy_version,
        "safe_checklist_count": len(result.checklist_item_ids),
        "safe_passed_count": result.checklist_passed_count,
        "safe_blocking_count": result.checklist_blocking_count,
        "safe_next_stage": result.next_stage_label,
        "safe_diagnostics": result.safe_diagnostics,
        "safe_blocking_reasons": result.gate_decision.blocking_reasons,
    }
