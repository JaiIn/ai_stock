"""Safety contracts for recommendation stages.

No recommendation generation is implemented in this package.
"""

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
    "FORBIDDEN_RECOMMENDATION_LANGUAGE",
    "REQUIRED_DISCLAIMERS",
    "MockOnlyRecommendationPlan",
    "RecommendationSafetyPreflightPolicy",
    "RecommendationSafetyPreflightResult",
    "build_default_recommendation_safety_preflight_policy",
    "summarize_recommendation_safety_preflight",
    "validate_recommendation_safety_preflight_policy",
]
