"""Pure safety and mock-only policy contracts for recommendation stages."""

from ai_stock.recommendation.mock_policy_model import (
    ALLOWED_MOCK_LABELS,
    FORBIDDEN_MOCK_LABELS,
    MockRecommendationInput,
    MockRecommendationLabel,
    MockRecommendationPolicy,
    MockRecommendationResult,
    MockRecommendationValidationResult,
    build_default_mock_recommendation_policy,
    build_mock_recommendation_result,
    validate_mock_recommendation_input,
    validate_mock_recommendation_policy,
    validate_mock_recommendation_result,
)

from ai_stock.recommendation.safety_preflight import (
    ALLOWED_EXPLANATION_LANGUAGE,
    FORBIDDEN_RECOMMENDATION_LANGUAGE,
    REQUIRED_DISCLAIMERS,
    MockOnlyRecommendationPlan,
    RecommendationSafetyPreflightPolicy,
    RecommendationSafetyPreflightResult,
    build_default_recommendation_safety_preflight_policy,
    summarize_recommendation_safety_preflight,
    validate_recommendation_safety_preflight_policy,
)

__all__ = [
    "ALLOWED_EXPLANATION_LANGUAGE",
    "ALLOWED_MOCK_LABELS",
    "FORBIDDEN_MOCK_LABELS",
    "FORBIDDEN_RECOMMENDATION_LANGUAGE",
    "REQUIRED_DISCLAIMERS",
    "MockRecommendationInput",
    "MockRecommendationLabel",
    "MockRecommendationPolicy",
    "MockRecommendationResult",
    "MockRecommendationValidationResult",
    "MockOnlyRecommendationPlan",
    "RecommendationSafetyPreflightPolicy",
    "RecommendationSafetyPreflightResult",
    "build_default_mock_recommendation_policy",
    "build_default_recommendation_safety_preflight_policy",
    "build_mock_recommendation_result",
    "summarize_recommendation_safety_preflight",
    "validate_mock_recommendation_input",
    "validate_mock_recommendation_policy",
    "validate_mock_recommendation_result",
    "validate_recommendation_safety_preflight_policy",
]
