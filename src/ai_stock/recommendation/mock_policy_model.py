"""Deterministic mock-only recommendation policy model for MS-08.02.

The module accepts only caller-supplied snapshot summaries. It performs no file,
database, environment, network, UI, model, account, order, or clock I/O and
never produces an investment directive.
"""

from dataclasses import dataclass
from enum import Enum

from ai_stock.recommendation.safety_preflight import (
    ALLOWED_EXPLANATION_LANGUAGE,
    FORBIDDEN_RECOMMENDATION_LANGUAGE,
    REQUIRED_DISCLAIMERS,
)


class MockRecommendationLabel(str, Enum):
    """Non-directive labels permitted for deterministic mock explanations."""

    OBSERVATION_ONLY = "observation_only"
    RISK_REVIEW = "risk_review"
    INSUFFICIENT_DATA = "insufficient_data"
    NEUTRAL_REVIEW = "neutral_review"
    NOT_EVALUATED = "not_evaluated"


ALLOWED_MOCK_LABELS: tuple[str, ...] = tuple(
    label.value for label in MockRecommendationLabel
)

FORBIDDEN_MOCK_LABELS: tuple[str, ...] = (
    "buy",
    "sell",
    "hold",
    "strong_buy",
    "strong_sell",
    "매수",
    "매도",
    "보유",
)


@dataclass(frozen=True)
class MockRecommendationPolicy:
    """Immutable fail-closed policy for the MS-08.02 mock-only model."""

    stage_name: str = "MS-08.02"
    mode: str = "mock_only_policy_model"
    mock_policy_model_allowed: bool = True
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
    streamlit_ui_change_allowed: bool = False
    real_trade_allowed: bool = False
    required_disclaimers: tuple[str, ...] = REQUIRED_DISCLAIMERS
    forbidden_recommendation_language: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LANGUAGE
    )
    allowed_explanation_language: tuple[str, ...] = ALLOWED_EXPLANATION_LANGUAGE
    allowed_labels: tuple[str, ...] = ALLOWED_MOCK_LABELS
    forbidden_labels: tuple[str, ...] = FORBIDDEN_MOCK_LABELS


@dataclass(frozen=True)
class MockRecommendationInput:
    """Caller-supplied summary; this module never loads its own data."""

    symbol: str
    has_stock_info: bool
    has_price_snapshot: bool
    has_candle: bool
    has_exchange_rate: bool
    completeness_flags: tuple[str, ...] = ()
    risk_flags: tuple[str, ...] = ()
    observation_notes: tuple[str, ...] = ()


@dataclass(frozen=True)
class MockRecommendationResult:
    """Safe explanation result without advice, action, or trade semantics."""

    stage_name: str
    mode: str
    symbol: str
    label: str
    explanations: tuple[str, ...]
    required_disclaimers: tuple[str, ...]
    is_investment_advice: bool = False
    action_allowed: bool = False
    real_trade_allowed: bool = False


@dataclass(frozen=True)
class MockRecommendationValidationResult:
    """Deterministic validation outcome for policy, input, or result."""

    passed: bool
    violations: tuple[str, ...]


def build_default_mock_recommendation_policy() -> MockRecommendationPolicy:
    """Build the fixed MS-08.02 mock-only policy."""

    return MockRecommendationPolicy()


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


def _is_safe_symbol(symbol: object) -> bool:
    if not isinstance(symbol, str):
        return False
    normalized = symbol.strip()
    if not normalized or len(normalized) > 32:
        return False
    return all(
        character.isascii()
        and (character.isalnum() or character in "._-")
        for character in normalized
    )


def _is_string_tuple(value: object) -> bool:
    return isinstance(value, tuple) and all(
        isinstance(item, str) for item in value
    )


def _nonempty_count(values: tuple[str, ...]) -> int:
    return sum(bool(value.strip()) for value in values)


def validate_mock_recommendation_policy(
    policy: MockRecommendationPolicy,
) -> MockRecommendationValidationResult:
    """Validate all fail-closed MS-08.02 policy boundaries."""

    violations: list[str] = []

    if policy.stage_name != "MS-08.02":
        violations.append("stage_name_must_equal_MS-08.02")
    if policy.mode != "mock_only_policy_model":
        violations.append("mode_must_equal_mock_only_policy_model")
    if not policy.mock_policy_model_allowed:
        violations.append("mock_policy_model_allowed_must_be_true")

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
        "streamlit_ui_change_allowed",
        "real_trade_allowed",
    )
    for field_name in required_false_fields:
        if getattr(policy, field_name):
            violations.append(f"{field_name}_must_be_false")

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
    if set(policy.allowed_labels) & set(policy.forbidden_labels):
        violations.append("allowed_and_forbidden_labels_must_not_overlap")

    violation_tuple = tuple(violations)
    return MockRecommendationValidationResult(
        passed=not violation_tuple,
        violations=violation_tuple,
    )


def validate_mock_recommendation_input(
    recommendation_input: MockRecommendationInput,
    policy: MockRecommendationPolicy,
) -> MockRecommendationValidationResult:
    """Validate caller-supplied values without reading any external source."""

    violations: list[str] = []

    if not _is_safe_symbol(recommendation_input.symbol):
        violations.append("symbol_must_be_safe_ascii_identifier")

    for field_name in (
        "has_stock_info",
        "has_price_snapshot",
        "has_candle",
        "has_exchange_rate",
    ):
        if not isinstance(getattr(recommendation_input, field_name), bool):
            violations.append(f"{field_name}_must_be_bool")

    text_tuple_fields = (
        "completeness_flags",
        "risk_flags",
        "observation_notes",
    )
    text_values: list[str] = []
    for field_name in text_tuple_fields:
        value = getattr(recommendation_input, field_name)
        if not _is_string_tuple(value):
            violations.append(f"{field_name}_must_be_string_tuple")
            continue
        text_values.extend(value)

    if _contains_forbidden_language(
        tuple(text_values),
        policy.forbidden_recommendation_language,
    ):
        violations.append("input_contains_forbidden_recommendation_language")

    violation_tuple = tuple(violations)
    return MockRecommendationValidationResult(
        passed=not violation_tuple,
        violations=violation_tuple,
    )


def build_mock_recommendation_result(
    recommendation_input: MockRecommendationInput,
    policy: MockRecommendationPolicy,
) -> MockRecommendationResult:
    """Build a deterministic non-directive explanation from supplied flags."""

    policy_validation = validate_mock_recommendation_policy(policy)
    input_validation = validate_mock_recommendation_input(
        recommendation_input,
        policy,
    )

    if not policy_validation.passed or not input_validation.passed:
        return MockRecommendationResult(
            stage_name="MS-08.02",
            mode="mock_only_policy_model",
            symbol="invalid_input",
            label=MockRecommendationLabel.NOT_EVALUATED.value,
            explanations=(
                "확인 필요: mock-only 입력 또는 정책 검증에 실패했습니다.",
                "실거래 금지: 외부 호출이나 투자 행동을 수행하지 않습니다.",
            ),
            required_disclaimers=REQUIRED_DISCLAIMERS,
        )

    symbol = recommendation_input.symbol.strip()
    required_data_present = all(
        (
            recommendation_input.has_stock_info,
            recommendation_input.has_price_snapshot,
            recommendation_input.has_candle,
            recommendation_input.has_exchange_rate,
        )
    )
    completeness_count = _nonempty_count(
        recommendation_input.completeness_flags
    )
    risk_count = _nonempty_count(recommendation_input.risk_flags)
    observation_count = _nonempty_count(
        recommendation_input.observation_notes
    )

    if not required_data_present or completeness_count:
        label = MockRecommendationLabel.INSUFFICIENT_DATA.value
        explanations = (
            "데이터 기반 참고: 필수 snapshot summary가 완전하지 않습니다.",
            "확인 필요: 누락 데이터와 completeness flags를 검토하세요.",
        )
    elif risk_count:
        label = MockRecommendationLabel.RISK_REVIEW.value
        explanations = (
            f"리스크 요인: caller-supplied risk flags가 {risk_count}개 있습니다.",
            "모의 판단: 실제 투자 행동으로 연결하지 않습니다.",
        )
    else:
        label = MockRecommendationLabel.OBSERVATION_ONLY.value
        explanations = (
            "관찰 포인트: caller-supplied snapshot summary가 완전합니다.",
            (
                "데이터 기반 참고: 방향성이나 투자 행동을 산출하지 않으며 "
                f"observation notes {observation_count}개를 원문 없이 확인했습니다."
            ),
        )

    return MockRecommendationResult(
        stage_name=policy.stage_name,
        mode=policy.mode,
        symbol=symbol,
        label=label,
        explanations=explanations,
        required_disclaimers=policy.required_disclaimers,
    )


def validate_mock_recommendation_result(
    result: MockRecommendationResult,
    policy: MockRecommendationPolicy,
) -> MockRecommendationValidationResult:
    """Reject directive, advice, trade, disclaimer, and language violations."""

    violations: list[str] = []

    policy_validation = validate_mock_recommendation_policy(policy)
    violations.extend(policy_validation.violations)

    if result.stage_name != policy.stage_name:
        violations.append("result_stage_name_must_match_policy")
    if result.mode != policy.mode:
        violations.append("result_mode_must_match_policy")

    normalized_label = result.label.strip().casefold()
    forbidden_labels = tuple(
        label.casefold() for label in policy.forbidden_labels
    )
    if normalized_label in forbidden_labels:
        violations.append("result_label_is_forbidden_directive")
    if result.label not in policy.allowed_labels:
        violations.append("result_label_must_be_allowed")

    if result.required_disclaimers != policy.required_disclaimers:
        violations.append("result_must_include_all_required_disclaimers")
    if result.is_investment_advice:
        violations.append("is_investment_advice_must_be_false")
    if result.action_allowed:
        violations.append("action_allowed_must_be_false")
    if result.real_trade_allowed:
        violations.append("real_trade_allowed_must_be_false")

    allowed_prefixes = tuple(
        f"{phrase}:" for phrase in policy.allowed_explanation_language
    )
    for explanation in result.explanations:
        if not explanation.startswith(allowed_prefixes):
            violations.append(
                "result_explanation_must_use_allowed_language_prefix"
            )
            break

    output_strings = (
        result.symbol,
        result.label,
        *result.explanations,
        *result.required_disclaimers,
    )
    if _contains_forbidden_language(
        output_strings,
        policy.forbidden_recommendation_language,
    ):
        violations.append("result_contains_forbidden_recommendation_language")

    violation_tuple = tuple(violations)
    return MockRecommendationValidationResult(
        passed=not violation_tuple,
        violations=violation_tuple,
    )
