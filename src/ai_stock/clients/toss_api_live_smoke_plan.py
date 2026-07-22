"""Pure planning gate for a future read-only Toss API live smoke.

This module defines symbolic planning shapes only. It reuses MS-14 preflight
layers and does not load runtime config, create credentials, or call services.
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
from ai_stock.clients.toss_api_live_readiness import (
    TossApiLiveReadinessPreflightResult,
    TossApiNoSecretDryRunResult,
    run_toss_api_live_readiness_preflight_checks,
    run_toss_api_no_secret_dry_run,
)


TOSS_API_READONLY_LIVE_SMOKE_PLAN_VERSION = "MS-15.00"
TOSS_API_READONLY_LIVE_SMOKE_PLAN_SCOPE = (
    "pure_no_io_first_readonly_live_smoke_planning"
)

READONLY_LIVE_SMOKE_TARGET_IDS = (
    "symbolic_market_data_readonly_smoke",
    "symbolic_rate_limit_handling_smoke",
    "symbolic_redaction_probe_smoke",
)
ALLOWLIST_ITEMS = (
    "symbolic_readonly_market_data_target",
    "planning_documentation_only",
    "safe_redacted_summary_only",
    "explicit_future_approval_required",
)
BLOCKLIST_ITEMS = (
    "live_execution_now",
    "secret_request_now",
    "oauth_now",
    "token_issuance_now",
    "account_seq_now",
    "order_or_account_data_now",
    "db_or_file_io_now",
    "streamlit_or_llm_now",
    "recommendation_or_ranking_now",
)
PREREQUISITE_IDS = (
    "ms1400_contract_preflight_passed",
    "ms1401_fake_transport_preflight_passed",
    "ms1402_config_guardrail_preflight_passed",
    "ms1403_live_readiness_preflight_passed",
    "ms1403_no_secret_dry_run_passed",
    "explicit_live_stage_approval_not_present",
)


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokePlanningPolicy:
    """Policy proving MS-15.00 remains planning-only and no-I/O."""

    planning_version: str
    planning_scope: str
    planning_only: bool
    uses_contract_preflight: bool
    uses_fake_transport_preflight: bool
    uses_config_guardrail_preflight: bool
    uses_live_readiness_preflight: bool
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
    explicit_user_approval_required_for_live_stage: bool


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokeTarget:
    """Symbolic future read-only smoke target without endpoint details."""

    target_id: str
    target_kind: str
    description: str
    readonly: bool
    market_data_only: bool
    account_data_allowed: bool
    order_data_allowed: bool
    balance_data_allowed: bool
    fills_data_allowed: bool
    actual_url_defined: bool
    actual_endpoint_path_defined: bool
    live_call_allowed_now: bool
    planning_only: bool


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokeAllowlist:
    """Allowed symbolic planning items for the future smoke stage."""

    allowed_items: tuple[str, ...]
    allowed_target_ids: tuple[str, ...]
    readonly_only: bool
    market_data_only: bool
    planning_only: bool
    redacted_output_only: bool


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokeBlocklist:
    """Blocked capabilities for MS-15.00 planning."""

    blocked_items: tuple[str, ...]
    block_live_execution_now: bool
    block_credential_request_now: bool
    block_oauth_now: bool
    block_token_issuance_now: bool
    block_account_seq_now: bool
    block_order_account_balance_fills_now: bool
    block_db_and_file_io_now: bool
    block_streamlit_and_llm_now: bool
    block_recommendation_ranking_action_now: bool


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokePrerequisite:
    """One symbolic prerequisite for a future live smoke."""

    prerequisite_id: str
    category: str
    passed: bool
    required: bool
    evidence_label: str
    blocking_reason: str


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokeExecutionGate:
    """Closed execution gate for MS-15.00 planning."""

    planning_passed: bool
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
    explicit_approval_required: bool
    blocking_reasons: tuple[str, ...]
    prerequisite_summary: Mapping[str, int]


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokePlan:
    """Aggregate symbolic plan for first read-only live smoke."""

    policy: TossApiReadOnlyLiveSmokePlanningPolicy
    targets: tuple[TossApiReadOnlyLiveSmokeTarget, ...]
    allowlist: TossApiReadOnlyLiveSmokeAllowlist
    blocklist: TossApiReadOnlyLiveSmokeBlocklist
    prerequisites: tuple[TossApiReadOnlyLiveSmokePrerequisite, ...]
    execution_gate: TossApiReadOnlyLiveSmokeExecutionGate
    contract_preflight: TossApiContractValidationResult
    fake_transport_preflight: TossApiFakeTransportValidationResult
    config_guardrail_preflight: TossApiConfigGuardrailPreflightResult
    live_readiness_preflight: TossApiLiveReadinessPreflightResult
    no_secret_dry_run: TossApiNoSecretDryRunResult
    capability_flags: TossApiExternalCapabilityFlags
    safe_summary: Mapping[str, object]


@dataclass(frozen=True)
class TossApiReadOnlyLiveSmokePlanningValidationResult:
    """Validation result for the symbolic live smoke plan."""

    passed: bool
    failures: tuple[str, ...]
    checked_policy_flags: tuple[str, ...]
    checked_target_ids: tuple[str, ...]
    checked_allowlist_items: tuple[str, ...]
    checked_blocklist_items: tuple[str, ...]
    checked_prerequisites: tuple[str, ...]
    checked_gate_flags: tuple[str, ...]
    diagnostics: tuple[str, ...]


def build_toss_api_readonly_live_smoke_planning_policy() -> (
    TossApiReadOnlyLiveSmokePlanningPolicy
):
    """Build the closed planning-only MS-15.00 policy."""

    return TossApiReadOnlyLiveSmokePlanningPolicy(
        planning_version=TOSS_API_READONLY_LIVE_SMOKE_PLAN_VERSION,
        planning_scope=TOSS_API_READONLY_LIVE_SMOKE_PLAN_SCOPE,
        planning_only=True,
        uses_contract_preflight=True,
        uses_fake_transport_preflight=True,
        uses_config_guardrail_preflight=True,
        uses_live_readiness_preflight=True,
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
        explicit_user_approval_required_for_live_stage=True,
    )


def build_toss_api_readonly_live_smoke_targets() -> (
    tuple[TossApiReadOnlyLiveSmokeTarget, ...]
):
    """Build symbolic read-only planning targets without live paths."""

    return (
        _build_readonly_live_smoke_target(
            target_id="symbolic_market_data_readonly_smoke",
            target_kind="symbolic_market_data_readonly",
            description="Symbolic market data read-only smoke target",
        ),
        _build_readonly_live_smoke_target(
            target_id="symbolic_rate_limit_handling_smoke",
            target_kind="symbolic_rate_limit_handling",
            description="Symbolic rate-limit handling smoke target",
        ),
        _build_readonly_live_smoke_target(
            target_id="symbolic_redaction_probe_smoke",
            target_kind="symbolic_redaction_probe",
            description="Symbolic redaction probe smoke target",
        ),
    )


def build_toss_api_readonly_live_smoke_allowlist() -> (
    TossApiReadOnlyLiveSmokeAllowlist
):
    """Build the planning-only allowlist."""

    return TossApiReadOnlyLiveSmokeAllowlist(
        allowed_items=ALLOWLIST_ITEMS,
        allowed_target_ids=READONLY_LIVE_SMOKE_TARGET_IDS,
        readonly_only=True,
        market_data_only=True,
        planning_only=True,
        redacted_output_only=True,
    )


def build_toss_api_readonly_live_smoke_blocklist() -> (
    TossApiReadOnlyLiveSmokeBlocklist
):
    """Build the MS-15.00 blocklist."""

    return TossApiReadOnlyLiveSmokeBlocklist(
        blocked_items=BLOCKLIST_ITEMS,
        block_live_execution_now=True,
        block_credential_request_now=True,
        block_oauth_now=True,
        block_token_issuance_now=True,
        block_account_seq_now=True,
        block_order_account_balance_fills_now=True,
        block_db_and_file_io_now=True,
        block_streamlit_and_llm_now=True,
        block_recommendation_ranking_action_now=True,
    )


def build_toss_api_readonly_live_smoke_prerequisites(
    contract_preflight: TossApiContractValidationResult | None = None,
    fake_transport_preflight: TossApiFakeTransportValidationResult | None = None,
    config_guardrail_preflight: TossApiConfigGuardrailPreflightResult | None = None,
    live_readiness_preflight: TossApiLiveReadinessPreflightResult | None = None,
    no_secret_dry_run: TossApiNoSecretDryRunResult | None = None,
) -> tuple[TossApiReadOnlyLiveSmokePrerequisite, ...]:
    """Build prerequisites from MS-14 symbolic preflight results."""

    contract_result = (
        contract_preflight or run_toss_api_client_contract_preflight_checks()
    )
    fake_result = (
        fake_transport_preflight or run_toss_api_fake_transport_preflight_checks()
    )
    config_result = (
        config_guardrail_preflight or run_toss_api_config_guardrail_preflight_checks()
    )
    live_result = (
        live_readiness_preflight or run_toss_api_live_readiness_preflight_checks()
    )
    dry_run_result = no_secret_dry_run or run_toss_api_no_secret_dry_run()

    return (
        _build_prerequisite(
            prerequisite_id="ms1400_contract_preflight_passed",
            category="contract_preflight",
            passed=contract_result.passed,
            evidence_label="contract_preflight_passed",
        ),
        _build_prerequisite(
            prerequisite_id="ms1401_fake_transport_preflight_passed",
            category="fake_transport_preflight",
            passed=fake_result.passed,
            evidence_label="fake_transport_preflight_passed",
        ),
        _build_prerequisite(
            prerequisite_id="ms1402_config_guardrail_preflight_passed",
            category="config_guardrail_preflight",
            passed=config_result.passed,
            evidence_label="config_guardrail_preflight_passed",
        ),
        _build_prerequisite(
            prerequisite_id="ms1403_live_readiness_preflight_passed",
            category="live_readiness_preflight",
            passed=live_result.passed,
            evidence_label="live_readiness_preflight_passed",
        ),
        _build_prerequisite(
            prerequisite_id="ms1403_no_secret_dry_run_passed",
            category="no_secret_dry_run",
            passed=dry_run_result.passed,
            evidence_label="no_secret_dry_run_passed",
        ),
        _build_prerequisite(
            prerequisite_id="explicit_live_stage_approval_not_present",
            category="manual_future_approval",
            passed=True,
            evidence_label="approval_required_for_future_stage",
            required=False,
            blocking_reason="future_manual_approval_required",
        ),
    )


def build_toss_api_readonly_live_smoke_execution_gate(
    prerequisites: tuple[TossApiReadOnlyLiveSmokePrerequisite, ...] | None = None,
) -> TossApiReadOnlyLiveSmokeExecutionGate:
    """Build the closed execution gate for MS-15.00 planning."""

    active_prerequisites = (
        prerequisites or build_toss_api_readonly_live_smoke_prerequisites()
    )
    failed_required_count = sum(
        1
        for prerequisite in active_prerequisites
        if prerequisite.required and not prerequisite.passed
    )
    passed_count = sum(1 for prerequisite in active_prerequisites if prerequisite.passed)

    return TossApiReadOnlyLiveSmokeExecutionGate(
        planning_passed=failed_required_count == 0,
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
        explicit_approval_required=True,
        blocking_reasons=(
            "explicit_future_live_stage_required",
            "runtime_access_disabled_now",
            "user_secret_prompt_disabled",
        ),
        prerequisite_summary={
            "total": len(active_prerequisites),
            "passed": passed_count,
            "failed_required": failed_required_count,
        },
    )


def build_toss_api_readonly_live_smoke_plan() -> TossApiReadOnlyLiveSmokePlan:
    """Build a deterministic symbolic live smoke plan."""

    policy = build_toss_api_readonly_live_smoke_planning_policy()
    targets = build_toss_api_readonly_live_smoke_targets()
    allowlist = build_toss_api_readonly_live_smoke_allowlist()
    blocklist = build_toss_api_readonly_live_smoke_blocklist()
    contract_preflight = run_toss_api_client_contract_preflight_checks()
    fake_transport_preflight = run_toss_api_fake_transport_preflight_checks()
    config_guardrail_preflight = run_toss_api_config_guardrail_preflight_checks()
    live_readiness_preflight = run_toss_api_live_readiness_preflight_checks()
    no_secret_dry_run = run_toss_api_no_secret_dry_run()
    prerequisites = build_toss_api_readonly_live_smoke_prerequisites(
        contract_preflight=contract_preflight,
        fake_transport_preflight=fake_transport_preflight,
        config_guardrail_preflight=config_guardrail_preflight,
        live_readiness_preflight=live_readiness_preflight,
        no_secret_dry_run=no_secret_dry_run,
    )
    execution_gate = build_toss_api_readonly_live_smoke_execution_gate(prerequisites)
    capability_flags = build_toss_api_external_capability_flags()
    safe_summary = {
        "safe_plan_version": policy.planning_version,
        "safe_target_count": len(targets),
        "safe_prerequisite_count": len(prerequisites),
        "safe_planning_passed": execution_gate.planning_passed,
        "safe_next_step": "explicit_future_live_stage_required",
    }

    return TossApiReadOnlyLiveSmokePlan(
        policy=policy,
        targets=targets,
        allowlist=allowlist,
        blocklist=blocklist,
        prerequisites=prerequisites,
        execution_gate=execution_gate,
        contract_preflight=contract_preflight,
        fake_transport_preflight=fake_transport_preflight,
        config_guardrail_preflight=config_guardrail_preflight,
        live_readiness_preflight=live_readiness_preflight,
        no_secret_dry_run=no_secret_dry_run,
        capability_flags=capability_flags,
        safe_summary=safe_summary,
    )


def validate_toss_api_readonly_live_smoke_plan(
    plan: TossApiReadOnlyLiveSmokePlan | None = None,
) -> TossApiReadOnlyLiveSmokePlanningValidationResult:
    """Validate the symbolic read-only live smoke plan."""

    active_plan = plan or build_toss_api_readonly_live_smoke_plan()
    failures: list[str] = []
    failures.extend(_validate_planning_policy(active_plan.policy))
    failures.extend(_validate_targets(active_plan.targets))
    failures.extend(_validate_allowlist(active_plan.allowlist))
    failures.extend(_validate_blocklist(active_plan.blocklist))
    failures.extend(_validate_prerequisites(active_plan.prerequisites))
    failures.extend(_validate_execution_gate(active_plan.execution_gate))

    for result in (
        active_plan.contract_preflight,
        active_plan.fake_transport_preflight,
        active_plan.config_guardrail_preflight,
        active_plan.live_readiness_preflight,
    ):
        failures.extend(result.failures)
    if not active_plan.no_secret_dry_run.passed:
        failures.append("no_secret_dry_run_must_pass")
    if any(active_plan.capability_flags.__dict__.values()):
        failures.append("external_capability_flags_must_all_be_false")

    redacted_probe = redact_mapping(
        {"access_token": "dummy-sensitive-value"},
        build_toss_api_redaction_policy(),
    )
    if redacted_probe["access_token"] != build_toss_api_redaction_policy().redaction_placeholder:
        failures.append("redaction_probe_must_mask_sensitive_value")

    sensitive_validation = validate_no_sensitive_output(
        active_plan.safe_summary,
        build_toss_api_redaction_policy(),
    )
    failures.extend(sensitive_validation.failures)

    return TossApiReadOnlyLiveSmokePlanningValidationResult(
        passed=not failures,
        failures=tuple(failures),
        checked_policy_flags=_planning_policy_flag_names(),
        checked_target_ids=tuple(target.target_id for target in active_plan.targets),
        checked_allowlist_items=active_plan.allowlist.allowed_items,
        checked_blocklist_items=active_plan.blocklist.blocked_items,
        checked_prerequisites=tuple(
            prerequisite.prerequisite_id
            for prerequisite in active_plan.prerequisites
        ),
        checked_gate_flags=_execution_gate_flag_names(),
        diagnostics=(
            "pure_no_io_readonly_live_smoke_planning",
            "symbolic_readonly_targets_only",
            "live_execution_blocked_now",
            "redacted_output_only",
        ),
    )


def run_toss_api_readonly_live_smoke_planning_preflight_checks() -> (
    TossApiReadOnlyLiveSmokePlanningValidationResult
):
    """Run deterministic MS-15.00 planning checks without I/O."""

    return validate_toss_api_readonly_live_smoke_plan(
        build_toss_api_readonly_live_smoke_plan()
    )


def _build_readonly_live_smoke_target(
    *,
    target_id: str,
    target_kind: str,
    description: str,
) -> TossApiReadOnlyLiveSmokeTarget:
    return TossApiReadOnlyLiveSmokeTarget(
        target_id=target_id,
        target_kind=target_kind,
        description=description,
        readonly=True,
        market_data_only=True,
        account_data_allowed=False,
        order_data_allowed=False,
        balance_data_allowed=False,
        fills_data_allowed=False,
        actual_url_defined=False,
        actual_endpoint_path_defined=False,
        live_call_allowed_now=False,
        planning_only=True,
    )


def _build_prerequisite(
    *,
    prerequisite_id: str,
    category: str,
    passed: bool,
    evidence_label: str,
    required: bool = True,
    blocking_reason: str = "required_symbolic_preflight_must_pass",
) -> TossApiReadOnlyLiveSmokePrerequisite:
    return TossApiReadOnlyLiveSmokePrerequisite(
        prerequisite_id=prerequisite_id,
        category=category,
        passed=passed,
        required=required,
        evidence_label=evidence_label,
        blocking_reason=blocking_reason,
    )


def _validate_planning_policy(
    policy: TossApiReadOnlyLiveSmokePlanningPolicy,
) -> tuple[str, ...]:
    required_true_flags = _planning_policy_true_flag_names()
    required_false_flags = _planning_policy_false_flag_names()
    failures = [
        f"{flag}_must_be_true"
        for flag in required_true_flags
        if not getattr(policy, flag)
    ]
    failures.extend(
        f"{flag}_must_be_false"
        for flag in required_false_flags
        if getattr(policy, flag)
    )
    return tuple(failures)


def _validate_targets(
    targets: tuple[TossApiReadOnlyLiveSmokeTarget, ...],
) -> tuple[str, ...]:
    failures: list[str] = []
    if tuple(target.target_id for target in targets) != READONLY_LIVE_SMOKE_TARGET_IDS:
        failures.append("readonly_live_smoke_target_ids_must_match_contract")
    for target in targets:
        if not target.readonly:
            failures.append(f"target_must_be_readonly:{target.target_id}")
        if not target.market_data_only:
            failures.append(f"target_must_be_market_data_only:{target.target_id}")
        for false_flag in (
            "account_data_allowed",
            "order_data_allowed",
            "balance_data_allowed",
            "fills_data_allowed",
            "actual_url_defined",
            "actual_endpoint_path_defined",
            "live_call_allowed_now",
        ):
            if getattr(target, false_flag):
                failures.append(f"{false_flag}_must_be_false:{target.target_id}")
        if not target.planning_only:
            failures.append(f"target_must_be_planning_only:{target.target_id}")
    return tuple(failures)


def _validate_allowlist(
    allowlist: TossApiReadOnlyLiveSmokeAllowlist,
) -> tuple[str, ...]:
    failures: list[str] = []
    if allowlist.allowed_items != ALLOWLIST_ITEMS:
        failures.append("allowlist_items_must_match_contract")
    if allowlist.allowed_target_ids != READONLY_LIVE_SMOKE_TARGET_IDS:
        failures.append("allowlist_target_ids_must_match_contract")
    for flag in (
        "readonly_only",
        "market_data_only",
        "planning_only",
        "redacted_output_only",
    ):
        if not getattr(allowlist, flag):
            failures.append(f"{flag}_must_be_true")
    return tuple(failures)


def _validate_blocklist(
    blocklist: TossApiReadOnlyLiveSmokeBlocklist,
) -> tuple[str, ...]:
    failures: list[str] = []
    if blocklist.blocked_items != BLOCKLIST_ITEMS:
        failures.append("blocklist_items_must_match_contract")
    for flag in (
        "block_live_execution_now",
        "block_credential_request_now",
        "block_oauth_now",
        "block_token_issuance_now",
        "block_account_seq_now",
        "block_order_account_balance_fills_now",
        "block_db_and_file_io_now",
        "block_streamlit_and_llm_now",
        "block_recommendation_ranking_action_now",
    ):
        if not getattr(blocklist, flag):
            failures.append(f"{flag}_must_be_true")
    return tuple(failures)


def _validate_prerequisites(
    prerequisites: tuple[TossApiReadOnlyLiveSmokePrerequisite, ...],
) -> tuple[str, ...]:
    failures: list[str] = []
    if tuple(item.prerequisite_id for item in prerequisites) != PREREQUISITE_IDS:
        failures.append("prerequisite_ids_must_match_contract")
    for prerequisite in prerequisites:
        if prerequisite.required and not prerequisite.passed:
            failures.append(f"required_prerequisite_failed:{prerequisite.prerequisite_id}")
    return tuple(failures)


def _validate_execution_gate(
    gate: TossApiReadOnlyLiveSmokeExecutionGate,
) -> tuple[str, ...]:
    failures: list[str] = []
    if not gate.planning_passed:
        failures.append("planning_passed_must_be_true")
    if not gate.explicit_approval_required:
        failures.append("explicit_approval_required_must_be_true")
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
        if getattr(gate, flag):
            failures.append(f"{flag}_must_be_false")
    return tuple(failures)


def _planning_policy_true_flag_names() -> tuple[str, ...]:
    return (
        "planning_only",
        "uses_contract_preflight",
        "uses_fake_transport_preflight",
        "uses_config_guardrail_preflight",
        "uses_live_readiness_preflight",
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
        "explicit_user_approval_required_for_live_stage",
    )


def _planning_policy_false_flag_names() -> tuple[str, ...]:
    return (
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


def _planning_policy_flag_names() -> tuple[str, ...]:
    return (*_planning_policy_true_flag_names(), *_planning_policy_false_flag_names())


def _execution_gate_flag_names() -> tuple[str, ...]:
    return (
        "planning_passed",
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
