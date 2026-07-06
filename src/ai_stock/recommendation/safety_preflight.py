"""Pure safety policy for the MS-08.01 recommendation preflight.

This module performs no file, database, environment, network, UI, or model I/O.
It does not generate recommendations.
"""

from dataclasses import dataclass, field


REQUIRED_DISCLAIMERS: tuple[str, ...] = (
    "이 기능은 투자 조언이 아닙니다.",
    "실제 매수/매도/보유 지시가 아닙니다.",
    "실거래 전 별도 판단이 필요합니다.",
    "모델/룰 기반 출력은 오류가 있을 수 있습니다.",
    "손실 가능성이 있습니다.",
    "이 프로젝트는 local-only 실험 도구입니다.",
)

FORBIDDEN_RECOMMENDATION_LANGUAGE: tuple[str, ...] = (
    "지금 사라",
    "반드시 매수",
    "무조건 상승",
    "확정 수익",
    "손실 없음",
    "원금 보장",
    "몰빵",
    "실주문 실행",
    "계좌에서 매수",
    "자동 주문",
)

ALLOWED_EXPLANATION_LANGUAGE: tuple[str, ...] = (
    "관찰 포인트",
    "리스크 요인",
    "확인 필요",
    "시나리오",
    "모의 판단",
    "데이터 기반 참고",
    "투자 조언 아님",
    "실거래 금지",
)


@dataclass(frozen=True)
class MockOnlyRecommendationPlan:
    """Candidate scope for MS-08.02; it is not enabled by MS-08.01."""

    stage_name: str = "MS-08.02"
    mode: str = "mock_only_policy_model"
    mock_only_input: bool = True
    local_snapshot_read_model_dto_allowed: bool = True
    live_api_refresh_allowed: bool = False
    real_ai_llm_call_allowed: bool = False
    rule_based_placeholder_allowed: bool = True
    deterministic_placeholder_allowed: bool = True
    investment_advice_allowed: bool = False
    real_order_allowed: bool = False
    explanation_focused: bool = True
    direct_buy_sell_instruction_allowed: bool = False
    input_contract: tuple[str, ...] = (
        "mock_fixture_dto",
        "local_snapshot_read_model_dto",
    )
    output_contract: tuple[str, ...] = (
        "observation_points",
        "risk_factors",
        "data_completeness",
        "scenario_explanation",
        "required_disclaimer",
    )


@dataclass(frozen=True)
class RecommendationSafetyPreflightPolicy:
    """Immutable deny-by-default contract for MS-08.01."""

    stage_name: str = "MS-08.01"
    mode: str = "safety_preflight"
    real_recommendation_allowed: bool = False
    mock_recommendation_allowed: bool = False
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
    next_stage_plan: MockOnlyRecommendationPlan = field(
        default_factory=MockOnlyRecommendationPlan
    )


@dataclass(frozen=True)
class RecommendationSafetyPreflightResult:
    """Deterministic validation result for the safety policy."""

    stage_name: str
    mode: str
    passed: bool
    violations: tuple[str, ...]
    summary: tuple[str, ...]


def build_default_recommendation_safety_preflight_policy(
) -> RecommendationSafetyPreflightPolicy:
    """Build the fixed deny-by-default MS-08.01 policy."""

    return RecommendationSafetyPreflightPolicy()


def summarize_recommendation_safety_preflight(
    policy: RecommendationSafetyPreflightPolicy,
) -> tuple[str, ...]:
    """Return a deterministic policy summary without recommendation output."""

    return (
        f"stage={policy.stage_name}",
        f"mode={policy.mode}",
        f"real_recommendation_allowed={policy.real_recommendation_allowed}",
        f"mock_recommendation_allowed={policy.mock_recommendation_allowed}",
        f"llm_call_allowed={policy.llm_call_allowed}",
        f"external_ai_api_allowed={policy.external_ai_api_allowed}",
        f"db_write_allowed={policy.db_write_allowed}",
        f"real_trade_allowed={policy.real_trade_allowed}",
        f"next_stage={policy.next_stage_plan.stage_name}",
    )


def validate_recommendation_safety_preflight_policy(
    policy: RecommendationSafetyPreflightPolicy,
) -> RecommendationSafetyPreflightResult:
    """Validate that the policy preserves every MS-08.01 safety boundary."""

    violations: list[str] = []

    expected_identity = {
        "stage_name": "MS-08.01",
        "mode": "safety_preflight",
    }
    for field_name, expected in expected_identity.items():
        if getattr(policy, field_name) != expected:
            violations.append(f"{field_name}_must_equal_{expected}")

    required_false_fields = (
        "real_recommendation_allowed",
        "mock_recommendation_allowed",
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
        violations.append("required_disclaimers_must_match_contract")
    if policy.forbidden_recommendation_language != FORBIDDEN_RECOMMENDATION_LANGUAGE:
        violations.append("forbidden_language_must_match_contract")
    if policy.allowed_explanation_language != ALLOWED_EXPLANATION_LANGUAGE:
        violations.append("allowed_explanation_language_must_match_contract")

    next_stage = policy.next_stage_plan
    if next_stage.stage_name != "MS-08.02":
        violations.append("next_stage_must_be_MS-08.02")
    required_next_stage_true_fields = (
        "mock_only_input",
        "local_snapshot_read_model_dto_allowed",
        "rule_based_placeholder_allowed",
        "deterministic_placeholder_allowed",
        "explanation_focused",
    )
    for field_name in required_next_stage_true_fields:
        if not getattr(next_stage, field_name):
            violations.append(f"next_stage_{field_name}_must_be_true")
    required_next_stage_false_fields = (
        "live_api_refresh_allowed",
        "real_ai_llm_call_allowed",
        "investment_advice_allowed",
        "real_order_allowed",
        "direct_buy_sell_instruction_allowed",
    )
    for field_name in required_next_stage_false_fields:
        if getattr(next_stage, field_name):
            violations.append(f"next_stage_{field_name}_must_be_false")

    violation_tuple = tuple(violations)
    return RecommendationSafetyPreflightResult(
        stage_name=policy.stage_name,
        mode=policy.mode,
        passed=not violation_tuple,
        violations=violation_tuple,
        summary=summarize_recommendation_safety_preflight(policy),
    )
