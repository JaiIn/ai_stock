"""Pure deterministic scoring preflight contract for MS-11.00.

This module builds a data-quality scoring preflight shape from already
in-memory MS-10.02 extracted feature sets. It performs no Streamlit, file,
database, environment, network, model, account, order, clock, or random I/O.
It does not rank, recommend, trade, load features, or render UI.
"""

from dataclasses import dataclass, fields
from enum import Enum

from ai_stock.recommendation.feature_extraction_fixtures import (
    FeatureExtractionFixtureRecord,
    build_all_feature_extraction_fixtures,
    evaluate_all_feature_extraction_fixtures,
    evaluate_feature_extraction_fixture,
)
from ai_stock.recommendation.feature_extraction_preflight import (
    FEATURE_EXTRACTION_REQUIRED_FALSE_FLAGS,
    FORBIDDEN_EXTRACTION_OUTPUT_LABELS,
    FORBIDDEN_FEATURE_EXTRACTION_SOURCES,
    ExtractedFeatureSet,
    FeatureExtractionStatus,
    build_feature_extraction_policy,
    extract_feature_sets_from_all_fixtures,
    extract_feature_sets_from_fixture,
    validate_extracted_feature_set,
)
from ai_stock.recommendation.watchlist_fixtures import (
    WatchlistFixtureRecord,
    build_basic_manual_symbols_fixture,
    build_duplicates_and_disabled_fixture,
    build_empty_watchlist_fixture,
    build_forbidden_fields_sanitized_fixture,
    build_insufficient_data_review_fixture,
    build_mixed_valid_invalid_symbols_fixture,
)


class ScoringPreflightStatus(str, Enum):
    """Allowed non-directive score preflight states for MS-11.00."""

    SCORE_READY = "score_ready"
    SCORE_NEEDS_REVIEW = "score_needs_review"
    SCORE_BLOCKED_QUALITY = "score_blocked_quality"
    SCORE_MISSING_DATA = "score_missing_data"
    SCORE_INVALID_CANDIDATE = "score_invalid_candidate"
    SCORE_DUPLICATE_CANDIDATE = "score_duplicate_candidate"
    SCORE_DISABLED_CANDIDATE = "score_disabled_candidate"
    SCORE_FORBIDDEN_FIELD_SANITIZED = "score_forbidden_field_sanitized"
    SCORE_EMPTY_INPUT = "score_empty_input"


ALLOWED_SCORING_SOURCES: tuple[str, ...] = (
    "in_memory_extracted_feature_set",
    "watchlist_fixture_extraction",
    "all_fixture_extraction",
    "feature_extraction_fixture_evaluation",
)

FORBIDDEN_SCORING_SOURCES: tuple[str, ...] = (
    *FORBIDDEN_FEATURE_EXTRACTION_SOURCES,
    "file_path",
    "feature_file",
    "watchlist_file",
    "database",
    "sqlite",
    "db_table",
    "toss_api",
    "oauth",
    "openai",
    "llm",
    "account",
    "holdings",
    "order",
    "balance",
    "fills",
    "raw_api_response",
    "raw_db_row",
    "credential",
    "token",
    "accountSeq",
)

ALLOWED_SCORING_STATUSES: tuple[str, ...] = tuple(
    status.value for status in ScoringPreflightStatus
)

ALLOWED_SCORE_COMPONENT_NAMES: tuple[str, ...] = (
    "data_completeness",
    "quality_reliability",
    "review_penalty",
    "extraction_readiness",
    "sanitization_penalty",
)

FORBIDDEN_SCORE_COMPONENT_NAMES: tuple[str, ...] = (
    "market_attractiveness",
    "return_prediction",
    "price_target_signal",
    "trade_signal",
    "position_sizing",
    "score_to_order",
    "buy",
    "sell",
    "hold",
    "strong_buy",
    "target_price",
    "expected_return",
    "profit_probability",
    "rank",
    "recommendation",
    "action",
)

FORBIDDEN_SCORING_ACTION_LABELS: tuple[str, ...] = (
    *FORBIDDEN_EXTRACTION_OUTPUT_LABELS,
    "buy",
    "sell",
    "hold",
    "strong_buy",
    "must_buy",
    "must_sell",
)

FORBIDDEN_SCORING_RECOMMENDATION_LABELS: tuple[str, ...] = (
    "rank",
    "ranking",
    "recommendation",
    "action",
    "target_price",
    "expected_return",
    "profit_probability",
)

FORBIDDEN_SCORING_OUTPUT_FIELDS: tuple[str, ...] = (
    "accountSeq",
    "access_token",
    "authorization",
    "bearer",
    "api_key",
    "secret_key",
    "client_secret",
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
    "buy",
    "sell",
    "hold",
    "strong_buy",
    "recommendation",
    "action",
    "rank",
    "target_price",
    "expected_return",
    "profit_probability",
)

SCORING_PREFLIGHT_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    FEATURE_EXTRACTION_REQUIRED_FALSE_FLAGS
)

SCORE_SCALE = 100


@dataclass(frozen=True)
class ScoringPreflightSummaryFlags:
    """All required external capability flags remain false for MS-11.00."""

    credential_required: bool = False
    db_read_required: bool = False
    db_write_required: bool = False
    file_read_required: bool = False
    file_write_required: bool = False
    toss_api_required: bool = False
    openai_required: bool = False
    oauth_required: bool = False
    account_seq_required: bool = False
    real_order_required: bool = False
    scoring_required: bool = False
    ranking_required: bool = False
    recommendation_required: bool = False
    ui_required: bool = False
    streamlit_required: bool = False
    http_smoke_required: bool = False


@dataclass(frozen=True)
class ScoringPreflightPolicy:
    """Immutable fail-closed policy for deterministic scoring preflight."""

    stage_name: str = "MS-11.00"
    mode: str = "deterministic_scoring_model_preflight"
    allowed_scoring_sources: tuple[str, ...] = ALLOWED_SCORING_SOURCES
    forbidden_scoring_sources: tuple[str, ...] = FORBIDDEN_SCORING_SOURCES
    allowed_scoring_statuses: tuple[str, ...] = ALLOWED_SCORING_STATUSES
    allowed_score_component_names: tuple[str, ...] = ALLOWED_SCORE_COMPONENT_NAMES
    forbidden_score_component_names: tuple[str, ...] = (
        FORBIDDEN_SCORE_COMPONENT_NAMES
    )
    forbidden_action_labels: tuple[str, ...] = FORBIDDEN_SCORING_ACTION_LABELS
    forbidden_recommendation_labels: tuple[str, ...] = (
        FORBIDDEN_SCORING_RECOMMENDATION_LABELS
    )
    forbidden_output_fields: tuple[str, ...] = FORBIDDEN_SCORING_OUTPUT_FIELDS
    required_false_flags: tuple[str, ...] = SCORING_PREFLIGHT_REQUIRED_FALSE_FLAGS
    observation_only_policy: str = "quality_score_shape_only"
    no_recommendation_policy: str = "no_investment_directive_output"
    no_ranking_policy: str = "no_ordered_candidate_list_output"
    no_action_policy: str = "no_trade_directive_output"
    deterministic_only_policy: str = "in_memory_extracted_feature_set_only"
    actual_recommendation_allowed: bool = False
    ranking_allowed: bool = False
    action_allowed: bool = False
    watchlist_persistence_allowed: bool = False
    feature_file_loader_allowed: bool = False
    watchlist_file_loader_allowed: bool = False
    ui_change_allowed: bool = False
    credential_required: bool = False
    db_read_required: bool = False
    db_write_required: bool = False
    file_read_required: bool = False
    file_write_required: bool = False
    toss_api_required: bool = False
    openai_required: bool = False
    oauth_required: bool = False
    account_seq_required: bool = False
    real_order_required: bool = False
    scoring_required: bool = False
    ranking_required: bool = False
    recommendation_required: bool = False
    ui_required: bool = False
    streamlit_required: bool = False
    http_smoke_required: bool = False


@dataclass(frozen=True)
class ScoringInput:
    """Normalized scoring preflight input from an extracted feature set."""

    symbol: str
    market: str
    scoring_source: str
    extraction_status: str
    extracted_features: tuple[object, ...]
    missing_features: tuple[str, ...]
    blocked_features: tuple[str, ...]
    quality_status: str
    needs_review: bool
    usable_for_future_scoring: bool
    blocked_reasons: tuple[str, ...]
    diagnostics: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class ScoreComponent:
    """Data-quality score component without investment signal semantics."""

    component_name: str
    component_score: int
    component_scale: int
    source_feature_names: tuple[str, ...]
    component_status: str
    warnings: tuple[str, ...]
    diagnostics: tuple[str, ...]


@dataclass(frozen=True)
class ScoringPreflightResult:
    """Deterministic quality score shape without directive output."""

    symbol: str
    market: str
    scoring_status: str
    score_components: tuple[ScoreComponent, ...]
    total_score: int
    score_scale: int
    score_warnings: tuple[str, ...]
    diagnostics: tuple[str, ...]
    needs_review: bool
    usable_for_future_ranking: bool
    blocked_reasons: tuple[str, ...]
    summary_flags: ScoringPreflightSummaryFlags


@dataclass(frozen=True)
class ScoringPreflightValidationResult:
    """Validation result for one scoring preflight result."""

    valid: bool
    rejection_reasons: tuple[str, ...]
    diagnostics: tuple[str, ...]
    forbidden_source_present: bool
    forbidden_component_present: bool
    forbidden_output_label_present: bool
    required_flag_true: bool
    score_out_of_range: bool
    credential_required: bool
    db_read_required: bool
    db_write_required: bool
    file_read_required: bool
    file_write_required: bool
    toss_api_required: bool
    openai_required: bool
    oauth_required: bool
    account_seq_required: bool
    real_order_required: bool
    scoring_required: bool
    ranking_required: bool
    recommendation_required: bool
    ui_required: bool
    streamlit_required: bool
    http_smoke_required: bool


@dataclass(frozen=True)
class ScoringPreflightSummary:
    """Aggregate deterministic scoring preflight counts."""

    total_results: int
    ready_results: int
    needs_review_results: int
    blocked_results: int
    missing_data_results: int
    usable_for_future_ranking_results: int
    average_total_score: int
    diagnostics: tuple[str, ...]
    credential_required: bool = False
    db_read_required: bool = False
    db_write_required: bool = False
    file_read_required: bool = False
    file_write_required: bool = False
    toss_api_required: bool = False
    openai_required: bool = False
    oauth_required: bool = False
    account_seq_required: bool = False
    real_order_required: bool = False
    scoring_required: bool = False
    ranking_required: bool = False
    recommendation_required: bool = False
    ui_required: bool = False
    streamlit_required: bool = False
    http_smoke_required: bool = False


def build_scoring_preflight_policy() -> ScoringPreflightPolicy:
    """Build the fixed MS-11.00 scoring preflight policy."""

    build_feature_extraction_policy()
    return ScoringPreflightPolicy()


def _false_flags() -> ScoringPreflightSummaryFlags:
    return ScoringPreflightSummaryFlags()


def build_scoring_input_from_extracted_feature_set(
    feature_set: ExtractedFeatureSet,
    scoring_source: str = "in_memory_extracted_feature_set",
) -> ScoringInput:
    """Normalize an extracted feature set for scoring preflight."""

    validation = validate_extracted_feature_set(feature_set)
    diagnostics = feature_set.diagnostics + tuple(
        f"extraction_validation:{reason}"
        for reason in validation.rejection_reasons
    )
    return ScoringInput(
        symbol=feature_set.symbol,
        market=feature_set.market,
        scoring_source=scoring_source,
        extraction_status=feature_set.extraction_status,
        extracted_features=feature_set.extracted_features,
        missing_features=feature_set.missing_features,
        blocked_features=feature_set.blocked_features,
        quality_status=feature_set.quality_status,
        needs_review=feature_set.needs_review,
        usable_for_future_scoring=feature_set.usable_for_future_scoring,
        blocked_reasons=feature_set.blocked_reasons,
        diagnostics=diagnostics,
        warnings=feature_set.quality_warnings,
    )


def _scoring_status_from_input(scoring_input: ScoringInput) -> str:
    extraction_status = scoring_input.extraction_status
    if (
        extraction_status == FeatureExtractionStatus.EXTRACTION_READY.value
        and scoring_input.usable_for_future_scoring
    ):
        return ScoringPreflightStatus.SCORE_READY.value
    if extraction_status == FeatureExtractionStatus.EXTRACTION_DUPLICATE_CANDIDATE.value:
        return ScoringPreflightStatus.SCORE_DUPLICATE_CANDIDATE.value
    if extraction_status == FeatureExtractionStatus.EXTRACTION_DISABLED_CANDIDATE.value:
        return ScoringPreflightStatus.SCORE_DISABLED_CANDIDATE.value
    if extraction_status == FeatureExtractionStatus.EXTRACTION_MISSING_DATA.value:
        return ScoringPreflightStatus.SCORE_MISSING_DATA.value
    if extraction_status == FeatureExtractionStatus.EXTRACTION_INVALID_CANDIDATE.value:
        return ScoringPreflightStatus.SCORE_INVALID_CANDIDATE.value
    if (
        extraction_status
        == FeatureExtractionStatus.EXTRACTION_FORBIDDEN_FIELD_SANITIZED.value
    ):
        return ScoringPreflightStatus.SCORE_FORBIDDEN_FIELD_SANITIZED.value
    if extraction_status == FeatureExtractionStatus.EXTRACTION_EMPTY_INPUT.value:
        return ScoringPreflightStatus.SCORE_EMPTY_INPUT.value
    if scoring_input.needs_review:
        return ScoringPreflightStatus.SCORE_NEEDS_REVIEW.value
    return ScoringPreflightStatus.SCORE_BLOCKED_QUALITY.value


def _component_status(component_score: int) -> str:
    if component_score == SCORE_SCALE:
        return "component_ready"
    if component_score == 0:
        return "component_blocked"
    return "component_needs_review"


def _feature_names(scoring_input: ScoringInput) -> tuple[str, ...]:
    return tuple(
        getattr(feature, "feature_name")
        for feature in scoring_input.extracted_features
    )


def _component(
    component_name: str,
    component_score: int,
    source_feature_names: tuple[str, ...],
    warnings: tuple[str, ...] = (),
    diagnostics: tuple[str, ...] = (),
) -> ScoreComponent:
    return ScoreComponent(
        component_name=component_name,
        component_score=component_score,
        component_scale=SCORE_SCALE,
        source_feature_names=source_feature_names,
        component_status=_component_status(component_score),
        warnings=warnings,
        diagnostics=diagnostics,
    )


def build_score_components_from_scoring_input(
    scoring_input: ScoringInput,
    policy: ScoringPreflightPolicy | None = None,
) -> tuple[ScoreComponent, ...]:
    """Build deterministic data-quality score components only."""

    active_policy = policy or build_scoring_preflight_policy()
    source_names = _feature_names(scoring_input)
    has_features = bool(scoring_input.extracted_features)
    is_ready = (
        scoring_input.extraction_status
        == FeatureExtractionStatus.EXTRACTION_READY.value
        and scoring_input.usable_for_future_scoring
    )
    data_completeness_score = (
        SCORE_SCALE
        if has_features and not scoring_input.missing_features
        else 0
    )
    quality_reliability_score = SCORE_SCALE if is_ready else 0
    review_penalty_score = 0 if scoring_input.needs_review else SCORE_SCALE
    extraction_readiness_score = SCORE_SCALE if is_ready else 0
    sanitization_penalty_score = (
        0
        if scoring_input.extraction_status
        == FeatureExtractionStatus.EXTRACTION_FORBIDDEN_FIELD_SANITIZED.value
        else SCORE_SCALE
    )
    components = (
        _component(
            "data_completeness",
            data_completeness_score,
            source_names,
            warnings=(
                ("missing_feature_review",)
                if scoring_input.missing_features
                else ()
            ),
        ),
        _component(
            "quality_reliability",
            quality_reliability_score,
            source_names,
            diagnostics=(scoring_input.quality_status,),
        ),
        _component(
            "review_penalty",
            review_penalty_score,
            source_names,
            warnings=("needs_review",) if scoring_input.needs_review else (),
        ),
        _component(
            "extraction_readiness",
            extraction_readiness_score,
            source_names,
            diagnostics=(scoring_input.extraction_status,),
        ),
        _component(
            "sanitization_penalty",
            sanitization_penalty_score,
            source_names,
            diagnostics=(
                ("forbidden_field_sanitized",)
                if sanitization_penalty_score == 0
                else ()
            ),
        ),
    )
    return tuple(
        component
        for component in components
        if component.component_name in active_policy.allowed_score_component_names
    )


def _total_score(components: tuple[ScoreComponent, ...]) -> int:
    if not components:
        return 0
    return sum(component.component_score for component in components) // len(components)


def score_extracted_feature_set_preflight(
    feature_set: ExtractedFeatureSet,
    policy: ScoringPreflightPolicy | None = None,
    scoring_source: str = "in_memory_extracted_feature_set",
) -> ScoringPreflightResult:
    """Build one deterministic data-quality scoring preflight result."""

    active_policy = policy or build_scoring_preflight_policy()
    scoring_input = build_scoring_input_from_extracted_feature_set(
        feature_set,
        scoring_source=scoring_source,
    )
    components = build_score_components_from_scoring_input(
        scoring_input,
        active_policy,
    )
    scoring_status = _scoring_status_from_input(scoring_input)
    total_score = _total_score(components)
    usable_for_future_ranking = (
        scoring_status == ScoringPreflightStatus.SCORE_READY.value
        and total_score == SCORE_SCALE
        and not scoring_input.needs_review
    )
    return ScoringPreflightResult(
        symbol=scoring_input.symbol,
        market=scoring_input.market,
        scoring_status=scoring_status,
        score_components=components,
        total_score=total_score,
        score_scale=SCORE_SCALE,
        score_warnings=scoring_input.warnings
        + ("quality_preflight_score_only", "no_trade_directive"),
        diagnostics=scoring_input.diagnostics
        + ("deterministic_in_memory_score_shape",),
        needs_review=scoring_input.needs_review,
        usable_for_future_ranking=usable_for_future_ranking,
        blocked_reasons=scoring_input.blocked_reasons,
        summary_flags=_false_flags(),
    )


def score_extracted_feature_sets_from_fixture(
    fixture: WatchlistFixtureRecord,
    policy: ScoringPreflightPolicy | None = None,
) -> tuple[ScoringPreflightResult, ...]:
    """Score preflight extracted feature sets from one in-memory fixture."""

    active_policy = policy or build_scoring_preflight_policy()
    feature_sets = extract_feature_sets_from_fixture(fixture)
    return tuple(
        score_extracted_feature_set_preflight(
            feature_set,
            active_policy,
            scoring_source="watchlist_fixture_extraction",
        )
        for feature_set in feature_sets
    )


def score_extracted_feature_sets_from_all_fixtures(
    policy: ScoringPreflightPolicy | None = None,
) -> tuple[tuple[ScoringPreflightResult, ...], ...]:
    """Score preflight extracted feature sets from every MS-09.04 fixture."""

    active_policy = policy or build_scoring_preflight_policy()
    return tuple(
        tuple(
            score_extracted_feature_set_preflight(
                feature_set,
                active_policy,
                scoring_source="all_fixture_extraction",
            )
            for feature_set in group
        )
        for group in extract_feature_sets_from_all_fixtures()
    )


def _flatten_results(
    groups: tuple[tuple[ScoringPreflightResult, ...], ...],
) -> tuple[ScoringPreflightResult, ...]:
    return tuple(result for group in groups for result in group)


def score_extracted_feature_sets_from_feature_extraction_fixture(
    fixture: FeatureExtractionFixtureRecord,
    policy: ScoringPreflightPolicy | None = None,
) -> tuple[ScoringPreflightResult, ...]:
    """Score preflight results referenced by an MS-10.03 fixture."""

    evaluate_feature_extraction_fixture(fixture)
    if fixture.source_fixture_name == "all_ms09_fixture_matrix":
        return _flatten_results(
            score_extracted_feature_sets_from_all_fixtures(policy)
        )
    active_policy = policy or build_scoring_preflight_policy()
    feature_sets = extract_feature_sets_from_fixture(
        evaluation_source_fixture(fixture.source_fixture_name)
    )
    return tuple(
        score_extracted_feature_set_preflight(
            feature_set,
            active_policy,
            scoring_source="feature_extraction_fixture_evaluation",
        )
        for feature_set in feature_sets
    )


def evaluation_source_fixture(source_fixture_name: str) -> WatchlistFixtureRecord:
    """Resolve source fixture using the MS-10.02 extraction path only."""

    if source_fixture_name == "basic_manual_symbols":
        return build_basic_manual_symbols_fixture()
    if source_fixture_name == "mixed_valid_invalid_symbols":
        return build_mixed_valid_invalid_symbols_fixture()
    if source_fixture_name == "duplicates_and_disabled":
        return build_duplicates_and_disabled_fixture()
    if source_fixture_name == "insufficient_data_review":
        return build_insufficient_data_review_fixture()
    if source_fixture_name == "forbidden_fields_sanitized":
        return build_forbidden_fields_sanitized_fixture()
    if source_fixture_name == "empty_watchlist":
        return build_empty_watchlist_fixture()
    raise ValueError(f"unknown_source_fixture:{source_fixture_name}")


def score_extracted_feature_sets_from_all_feature_extraction_fixtures(
    policy: ScoringPreflightPolicy | None = None,
) -> tuple[tuple[ScoringPreflightResult, ...], ...]:
    """Score preflight outputs for every MS-10.03 extraction fixture."""

    evaluate_all_feature_extraction_fixtures()
    active_policy = policy or build_scoring_preflight_policy()
    return tuple(
        score_extracted_feature_sets_from_feature_extraction_fixture(
            fixture,
            active_policy,
        )
        for fixture in build_all_feature_extraction_fixtures()
    )


def _required_true_flags(
    result: ScoringPreflightResult,
    policy: ScoringPreflightPolicy,
) -> tuple[str, ...]:
    return tuple(
        flag
        for flag in policy.required_false_flags
        if bool(getattr(result.summary_flags, flag))
    )


def validate_scoring_preflight_result(
    result: ScoringPreflightResult,
    policy: ScoringPreflightPolicy | None = None,
) -> ScoringPreflightValidationResult:
    """Validate one scoring preflight result without external access."""

    active_policy = policy or build_scoring_preflight_policy()
    result_field_names = tuple(field.name for field in fields(ScoringPreflightResult))
    component_field_names = tuple(field.name for field in fields(ScoreComponent))
    produced_values = (
        result.scoring_status,
        *(component.component_name for component in result.score_components),
        *(component.component_status for component in result.score_components),
    )
    forbidden_components = tuple(
        name
        for name in (
            *result_field_names,
            *component_field_names,
            *(component.component_name for component in result.score_components),
        )
        if name in active_policy.forbidden_score_component_names
    )
    forbidden_outputs = tuple(
        value
        for value in produced_values
        if value in active_policy.forbidden_action_labels
        or value in active_policy.forbidden_recommendation_labels
    )
    unknown_statuses = tuple(
        value
        for value in (result.scoring_status,)
        if value not in active_policy.allowed_scoring_statuses
    )
    unknown_components = tuple(
        component.component_name
        for component in result.score_components
        if component.component_name not in active_policy.allowed_score_component_names
    )
    required_true_flags = _required_true_flags(result, active_policy)
    score_out_of_range = not 0 <= result.total_score <= result.score_scale

    rejection_reasons: list[str] = []
    if forbidden_components:
        rejection_reasons.extend(
            f"forbidden_score_component:{component}"
            for component in forbidden_components
        )
    if forbidden_outputs:
        rejection_reasons.extend(
            f"forbidden_output_label:{label}" for label in forbidden_outputs
        )
    if unknown_statuses:
        rejection_reasons.extend(
            f"unknown_scoring_status:{status}" for status in unknown_statuses
        )
    if unknown_components:
        rejection_reasons.extend(
            f"unknown_score_component:{component}" for component in unknown_components
        )
    if required_true_flags:
        rejection_reasons.extend(
            f"required_flag_true:{flag}" for flag in required_true_flags
        )
    if score_out_of_range:
        rejection_reasons.append("score_out_of_range")

    return ScoringPreflightValidationResult(
        valid=not rejection_reasons,
        rejection_reasons=tuple(rejection_reasons),
        diagnostics=result.diagnostics,
        forbidden_source_present=False,
        forbidden_component_present=bool(forbidden_components),
        forbidden_output_label_present=bool(forbidden_outputs),
        required_flag_true=bool(required_true_flags),
        score_out_of_range=score_out_of_range,
        credential_required=result.summary_flags.credential_required,
        db_read_required=result.summary_flags.db_read_required,
        db_write_required=result.summary_flags.db_write_required,
        file_read_required=result.summary_flags.file_read_required,
        file_write_required=result.summary_flags.file_write_required,
        toss_api_required=result.summary_flags.toss_api_required,
        openai_required=result.summary_flags.openai_required,
        oauth_required=result.summary_flags.oauth_required,
        account_seq_required=result.summary_flags.account_seq_required,
        real_order_required=result.summary_flags.real_order_required,
        scoring_required=result.summary_flags.scoring_required,
        ranking_required=result.summary_flags.ranking_required,
        recommendation_required=result.summary_flags.recommendation_required,
        ui_required=result.summary_flags.ui_required,
        streamlit_required=result.summary_flags.streamlit_required,
        http_smoke_required=result.summary_flags.http_smoke_required,
    )


def summarize_scoring_preflight_results(
    results: tuple[ScoringPreflightResult, ...],
) -> ScoringPreflightSummary:
    """Summarize deterministic scoring preflight result counts."""

    blocked_statuses = (
        ScoringPreflightStatus.SCORE_BLOCKED_QUALITY.value,
        ScoringPreflightStatus.SCORE_INVALID_CANDIDATE.value,
        ScoringPreflightStatus.SCORE_DUPLICATE_CANDIDATE.value,
        ScoringPreflightStatus.SCORE_DISABLED_CANDIDATE.value,
        ScoringPreflightStatus.SCORE_FORBIDDEN_FIELD_SANITIZED.value,
        ScoringPreflightStatus.SCORE_EMPTY_INPUT.value,
    )
    average_score = (
        sum(result.total_score for result in results) // len(results)
        if results
        else 0
    )
    return ScoringPreflightSummary(
        total_results=len(results),
        ready_results=sum(
            1
            for result in results
            if result.scoring_status == ScoringPreflightStatus.SCORE_READY.value
        ),
        needs_review_results=sum(1 for result in results if result.needs_review),
        blocked_results=sum(
            1 for result in results if result.scoring_status in blocked_statuses
        ),
        missing_data_results=sum(
            1
            for result in results
            if result.scoring_status == ScoringPreflightStatus.SCORE_MISSING_DATA.value
        ),
        usable_for_future_ranking_results=sum(
            1 for result in results if result.usable_for_future_ranking
        ),
        average_total_score=average_score,
        diagnostics=tuple(
            diagnostic for result in results for diagnostic in result.diagnostics
        ),
    )
