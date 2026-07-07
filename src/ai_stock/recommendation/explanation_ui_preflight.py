"""Pure explanation UI contract preflight for MS-08.03.

This module only converts a caller-supplied mock recommendation result into a
safe display view model contract. It performs no file, database, environment,
network, UI, model, account, order, clock, or random I/O.
"""

from dataclasses import dataclass
from enum import Enum

from ai_stock.recommendation.mock_policy_model import (
    ALLOWED_MOCK_LABELS,
    FORBIDDEN_MOCK_LABELS,
    MockRecommendationResult,
    build_default_mock_recommendation_policy,
    validate_mock_recommendation_result,
)
from ai_stock.recommendation.safety_preflight import (
    ALLOWED_EXPLANATION_LANGUAGE,
    FORBIDDEN_RECOMMENDATION_LANGUAGE,
    REQUIRED_DISCLAIMERS,
)


class RecommendationExplanationSectionName(str, Enum):
    """Display section names allowed for the future explanation panel."""

    SUMMARY = "summary"
    OBSERVATION = "observation"
    RISK_REVIEW = "risk_review"
    DATA_COMPLETENESS = "data_completeness"
    DISCLAIMER = "disclaimer"
    DIAGNOSTICS = "diagnostics"
    NEXT_CHECKS = "next_checks"


SAFE_EXPLANATION_SECTIONS: tuple[str, ...] = tuple(
    section.value for section in RecommendationExplanationSectionName
)

FORBIDDEN_EXPLANATION_SECTIONS: tuple[str, ...] = (
    "buy_button",
    "sell_button",
    "hold_directive",
    "order_ticket",
    "account_balance",
    "account_assets",
    "fills",
    "accountSeq",
    "credential_input",
    "access_token",
    "authorization_header",
    "raw_api_response",
    "raw_db_row",
    "live_api_refresh",
    "oauth_login",
    "auto_trade",
)


@dataclass(frozen=True)
class RecommendationExplanationUIPreflightPolicy:
    """Immutable UI display boundary for MS-08.03."""

    stage_name: str = "MS-08.03"
    mode: str = "recommendation_explanation_ui_preflight"
    streamlit_ui_change_allowed: bool = False
    ui_contract_only: bool = True
    mock_result_display_allowed_future_stage: bool = True
    real_recommendation_allowed: bool = False
    investment_advice_allowed: bool = False
    buy_sell_hold_directive_allowed: bool = False
    llm_call_allowed: bool = False
    external_ai_api_allowed: bool = False
    openai_api_key_required: bool = False
    toss_api_key_required: bool = False
    toss_secret_key_required: bool = False
    oauth_allowed: bool = False
    live_market_api_allowed: bool = False
    account_api_allowed: bool = False
    order_api_allowed: bool = False
    account_seq_required: bool = False
    db_write_allowed: bool = False
    real_trade_allowed: bool = False
    safe_sections: tuple[str, ...] = SAFE_EXPLANATION_SECTIONS
    forbidden_sections: tuple[str, ...] = FORBIDDEN_EXPLANATION_SECTIONS
    required_disclaimers: tuple[str, ...] = REQUIRED_DISCLAIMERS
    forbidden_recommendation_language: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LANGUAGE
    )
    allowed_explanation_language: tuple[str, ...] = ALLOWED_EXPLANATION_LANGUAGE
    allowed_labels: tuple[str, ...] = ALLOWED_MOCK_LABELS
    forbidden_labels: tuple[str, ...] = FORBIDDEN_MOCK_LABELS


@dataclass(frozen=True)
class RecommendationExplanationSection:
    """One safe section intended for a future display panel."""

    name: str
    heading: str
    lines: tuple[str, ...]


@dataclass(frozen=True)
class RecommendationExplanationViewModel:
    """Safe display contract built from an already prepared mock result."""

    title: str
    stage_name: str
    label: str
    safe_summary: tuple[str, ...]
    safe_sections: tuple[RecommendationExplanationSection, ...]
    disclaimers: tuple[str, ...]
    diagnostics: tuple[str, ...]
    action_allowed: bool = False
    is_investment_advice: bool = False
    real_trade_allowed: bool = False
    order_button_allowed: bool = False
    credential_input_allowed: bool = False
    account_seq_input_allowed: bool = False
    live_refresh_allowed: bool = False
    oauth_allowed: bool = False


@dataclass(frozen=True)
class RecommendationExplanationValidationResult:
    """Deterministic validation outcome for policy or view model checks."""

    passed: bool
    violations: tuple[str, ...]


def build_default_recommendation_explanation_ui_policy(
) -> RecommendationExplanationUIPreflightPolicy:
    """Build the fixed MS-08.03 explanation UI preflight policy."""

    return RecommendationExplanationUIPreflightPolicy()


def _contains_forbidden_language(
    values: tuple[str, ...],
    forbidden_phrases: tuple[str, ...],
) -> bool:
    normalized_values = tuple(value.casefold() for value in values)
    return any(
        phrase.casefold() in value
        for value in normalized_values
        for phrase in forbidden_phrases
    )


def _section_names(
    sections: tuple[RecommendationExplanationSection, ...],
) -> tuple[str, ...]:
    return tuple(section.name for section in sections)


def _view_model_strings(
    view_model: RecommendationExplanationViewModel,
) -> tuple[str, ...]:
    section_strings: list[str] = []
    for section in view_model.safe_sections:
        section_strings.append(section.name)
        section_strings.append(section.heading)
        section_strings.extend(section.lines)
    return (
        view_model.title,
        view_model.stage_name,
        view_model.label,
        *view_model.safe_summary,
        *section_strings,
        *view_model.disclaimers,
        *view_model.diagnostics,
    )


def validate_recommendation_explanation_ui_policy(
    policy: RecommendationExplanationUIPreflightPolicy,
) -> RecommendationExplanationValidationResult:
    """Validate all fail-closed MS-08.03 UI display boundaries."""

    violations: list[str] = []

    if policy.stage_name != "MS-08.03":
        violations.append("stage_name_must_equal_MS-08.03")
    if policy.mode != "recommendation_explanation_ui_preflight":
        violations.append(
            "mode_must_equal_recommendation_explanation_ui_preflight"
        )
    if policy.streamlit_ui_change_allowed:
        violations.append("streamlit_ui_change_allowed_must_be_false")
    if not policy.ui_contract_only:
        violations.append("ui_contract_only_must_be_true")
    if not policy.mock_result_display_allowed_future_stage:
        violations.append(
            "mock_result_display_allowed_future_stage_must_be_true"
        )

    required_false_fields = (
        "real_recommendation_allowed",
        "investment_advice_allowed",
        "buy_sell_hold_directive_allowed",
        "llm_call_allowed",
        "external_ai_api_allowed",
        "openai_api_key_required",
        "toss_api_key_required",
        "toss_secret_key_required",
        "oauth_allowed",
        "live_market_api_allowed",
        "account_api_allowed",
        "order_api_allowed",
        "account_seq_required",
        "db_write_allowed",
        "real_trade_allowed",
    )
    for field_name in required_false_fields:
        if getattr(policy, field_name):
            violations.append(f"{field_name}_must_be_false")

    if policy.safe_sections != SAFE_EXPLANATION_SECTIONS:
        violations.append("safe_sections_must_match_contract")
    if policy.forbidden_sections != FORBIDDEN_EXPLANATION_SECTIONS:
        violations.append("forbidden_sections_must_match_contract")
    if set(policy.safe_sections) & set(policy.forbidden_sections):
        violations.append("safe_and_forbidden_sections_must_not_overlap")
    if policy.required_disclaimers != REQUIRED_DISCLAIMERS:
        violations.append("required_disclaimers_must_match_safety_preflight")
    if policy.forbidden_recommendation_language != (
        FORBIDDEN_RECOMMENDATION_LANGUAGE
    ):
        violations.append("forbidden_language_must_match_safety_preflight")
    if policy.allowed_explanation_language != ALLOWED_EXPLANATION_LANGUAGE:
        violations.append(
            "allowed_explanation_language_must_match_safety_preflight"
        )
    if policy.allowed_labels != ALLOWED_MOCK_LABELS:
        violations.append("allowed_labels_must_match_mock_contract")
    if policy.forbidden_labels != FORBIDDEN_MOCK_LABELS:
        violations.append("forbidden_labels_must_match_mock_contract")

    violation_tuple = tuple(violations)
    return RecommendationExplanationValidationResult(
        passed=not violation_tuple,
        violations=violation_tuple,
    )


def build_recommendation_explanation_view_model(
    mock_result: MockRecommendationResult,
    policy: RecommendationExplanationUIPreflightPolicy,
) -> RecommendationExplanationViewModel:
    """Build a deterministic display contract from a supplied mock result."""

    summary_section = RecommendationExplanationSection(
        name=RecommendationExplanationSectionName.SUMMARY.value,
        heading="Safe summary",
        lines=(
            f"stage={mock_result.stage_name}",
            f"mode={mock_result.mode}",
            f"label={mock_result.label}",
            "caller_supplied_mock_result_only=True",
        ),
    )
    observation_section = RecommendationExplanationSection(
        name=RecommendationExplanationSectionName.OBSERVATION.value,
        heading="Observation",
        lines=mock_result.explanations,
    )
    risk_review_section = RecommendationExplanationSection(
        name=RecommendationExplanationSectionName.RISK_REVIEW.value,
        heading="Risk review",
        lines=(
            "risk_review_display_is_explanation_only=True",
            "real_recommendation_allowed=False",
        ),
    )
    data_completeness_section = RecommendationExplanationSection(
        name=RecommendationExplanationSectionName.DATA_COMPLETENESS.value,
        heading="Data completeness",
        lines=(
            "mock_result_was_prepared_by_caller=True",
            "db_read_performed_by_ui_preflight=False",
            "api_refresh_performed_by_ui_preflight=False",
        ),
    )
    disclaimer_section = RecommendationExplanationSection(
        name=RecommendationExplanationSectionName.DISCLAIMER.value,
        heading="Disclaimer",
        lines=mock_result.required_disclaimers,
    )
    diagnostics_section = RecommendationExplanationSection(
        name=RecommendationExplanationSectionName.DIAGNOSTICS.value,
        heading="Diagnostics",
        lines=(
            "ui_contract_only=True",
            "streamlit_ui_change_allowed=False",
            "order_button_allowed=False",
            "credential_input_allowed=False",
            "account_seq_input_allowed=False",
            "live_refresh_allowed=False",
            "oauth_allowed=False",
        ),
    )
    next_checks_section = RecommendationExplanationSection(
        name=RecommendationExplanationSectionName.NEXT_CHECKS.value,
        heading="Next checks",
        lines=(
            "future_stage=MS-08.04_mock_only_panel_integration",
            "separate_user_approval_required=True",
        ),
    )

    return RecommendationExplanationViewModel(
        title="Mock-only explanation panel contract",
        stage_name=policy.stage_name,
        label=mock_result.label,
        safe_summary=(
            f"label={mock_result.label}",
            "display_scope=explanation_only",
            "caller_supplied_mock_result_only=True",
        ),
        safe_sections=(
            summary_section,
            observation_section,
            risk_review_section,
            data_completeness_section,
            disclaimer_section,
            diagnostics_section,
            next_checks_section,
        ),
        disclaimers=mock_result.required_disclaimers,
        diagnostics=diagnostics_section.lines,
    )


def validate_recommendation_explanation_view_model(
    view_model: RecommendationExplanationViewModel,
    policy: RecommendationExplanationUIPreflightPolicy,
) -> RecommendationExplanationValidationResult:
    """Reject unsafe display fields, sections, labels, and language."""

    violations: list[str] = []

    policy_validation = validate_recommendation_explanation_ui_policy(policy)
    violations.extend(policy_validation.violations)

    if view_model.stage_name != policy.stage_name:
        violations.append("view_model_stage_name_must_match_policy")

    section_names = _section_names(view_model.safe_sections)
    for section_name in section_names:
        if section_name not in policy.safe_sections:
            violations.append("view_model_section_must_be_safe")
        if section_name in policy.forbidden_sections:
            violations.append("view_model_section_is_forbidden")

    if set(section_names) & set(policy.forbidden_sections):
        violations.append("view_model_contains_forbidden_section")

    normalized_label = view_model.label.strip().casefold()
    forbidden_labels = tuple(
        label.casefold() for label in policy.forbidden_labels
    )
    if normalized_label in forbidden_labels:
        violations.append("view_model_label_is_forbidden_directive")
    if view_model.label not in policy.allowed_labels:
        violations.append("view_model_label_must_be_allowed")

    if view_model.disclaimers != policy.required_disclaimers:
        violations.append("view_model_must_include_all_required_disclaimers")

    required_false_fields = (
        "action_allowed",
        "is_investment_advice",
        "real_trade_allowed",
        "order_button_allowed",
        "credential_input_allowed",
        "account_seq_input_allowed",
        "live_refresh_allowed",
        "oauth_allowed",
    )
    for field_name in required_false_fields:
        if getattr(view_model, field_name):
            violations.append(f"{field_name}_must_be_false")

    if _contains_forbidden_language(
        _view_model_strings(view_model),
        policy.forbidden_recommendation_language,
    ):
        violations.append("view_model_contains_forbidden_recommendation_language")

    mock_policy = build_default_mock_recommendation_policy()
    mock_result = MockRecommendationResult(
        stage_name="MS-08.02",
        mode="mock_only_policy_model",
        symbol="view_model_validation",
        label=view_model.label,
        explanations=tuple(
            line
            for section in view_model.safe_sections
            if section.name
            in (
                RecommendationExplanationSectionName.OBSERVATION.value,
            )
            for line in section.lines
        ),
        required_disclaimers=view_model.disclaimers,
        is_investment_advice=view_model.is_investment_advice,
        action_allowed=view_model.action_allowed,
        real_trade_allowed=view_model.real_trade_allowed,
    )
    mock_validation = validate_mock_recommendation_result(
        mock_result,
        mock_policy,
    )
    violations.extend(
        f"mock_result_{violation}" for violation in mock_validation.violations
    )

    violation_tuple = tuple(violations)
    return RecommendationExplanationValidationResult(
        passed=not violation_tuple,
        violations=violation_tuple,
    )
