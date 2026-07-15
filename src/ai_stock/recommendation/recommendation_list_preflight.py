"""Pure recommendation-list model preflight contract for MS-12.00.

This module defines observation-only list item shapes from already in-memory
MS-11 scoring preflight results. It performs no Streamlit, file, database,
environment, network, model, account, order, clock, or random I/O. It does not
rank, recommend, trade, load features, or render UI.
"""

from dataclasses import dataclass, fields
from enum import Enum

from ai_stock.recommendation.scoring_fixture_hardening import (
    build_scoring_fixture_hardening_policy,
    run_scoring_fixture_hardening_checks,
)
from ai_stock.recommendation.scoring_fixtures import (
    build_all_scoring_fixtures,
    build_scoring_fixture_policy,
    evaluate_all_scoring_fixtures,
    evaluate_scoring_fixture,
)
from ai_stock.recommendation.scoring_preflight import (
    ALLOWED_SCORING_STATUSES,
    FORBIDDEN_SCORING_ACTION_LABELS,
    FORBIDDEN_SCORING_OUTPUT_FIELDS,
    FORBIDDEN_SCORING_RECOMMENDATION_LABELS,
    FORBIDDEN_SCORING_SOURCES,
    SCORE_SCALE,
    SCORING_PREFLIGHT_REQUIRED_FALSE_FLAGS,
    ScoreComponent,
    ScoringPreflightResult,
    ScoringPreflightSummaryFlags,
    build_scoring_preflight_policy,
    score_extracted_feature_set_preflight,
    score_extracted_feature_sets_from_all_fixtures,
    score_extracted_feature_sets_from_fixture,
    summarize_scoring_preflight_results,
    validate_scoring_preflight_result,
)


class RecommendationListItemStatus(str, Enum):
    """Allowed observation-only list item preflight statuses."""

    ITEM_READY_FOR_REVIEW = "item_ready_for_review"
    ITEM_NEEDS_REVIEW = "item_needs_review"
    ITEM_BLOCKED_QUALITY = "item_blocked_quality"
    ITEM_MISSING_DATA = "item_missing_data"
    ITEM_INVALID_CANDIDATE = "item_invalid_candidate"
    ITEM_DUPLICATE_CANDIDATE = "item_duplicate_candidate"
    ITEM_DISABLED_CANDIDATE = "item_disabled_candidate"
    ITEM_FORBIDDEN_FIELD_SANITIZED = "item_forbidden_field_sanitized"
    ITEM_EMPTY_INPUT = "item_empty_input"


ALLOWED_RECOMMENDATION_LIST_INPUT_SOURCES: tuple[str, ...] = (
    "in_memory_scoring_result",
    "scoring_fixture_preflight",
    "all_fixture_scoring_preflight",
    "scoring_fixture_hardening_preflight",
)

FORBIDDEN_RECOMMENDATION_LIST_INPUT_SOURCES: tuple[str, ...] = (
    *FORBIDDEN_SCORING_SOURCES,
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

ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES: tuple[str, ...] = tuple(
    status.value for status in RecommendationListItemStatus
)

FORBIDDEN_RECOMMENDATION_LIST_ACTION_LABELS: tuple[str, ...] = (
    *FORBIDDEN_SCORING_ACTION_LABELS,
    "buy",
    "sell",
    "hold",
    "strong_buy",
    "must_buy",
    "must_sell",
)

FORBIDDEN_RECOMMENDATION_LIST_RECOMMENDATION_LABELS: tuple[str, ...] = (
    *FORBIDDEN_SCORING_RECOMMENDATION_LABELS,
    "recommendation",
    "target_price",
    "expected_return",
    "profit_probability",
)

FORBIDDEN_RECOMMENDATION_LIST_RANKING_LABELS: tuple[str, ...] = (
    "rank",
    "ranking",
    "ranking_position",
    "priority",
    "ordered_candidate_list",
)

FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_FIELDS: tuple[str, ...] = (
    *FORBIDDEN_SCORING_OUTPUT_FIELDS,
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
    "ranking",
    "ranking_position",
    "target_price",
    "expected_return",
    "profit_probability",
    "must_buy",
    "must_sell",
)

FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_KEYWORDS: tuple[str, ...] = (
    "accountSeq=",
    "access_token=",
    "authorization=",
    "bearer=",
    "api_key=",
    "secret_key=",
    "client_secret=",
    "account_balance=",
    "holdings=",
    "fills=",
    "order_id=",
    "raw_response=",
    "raw_request=",
    "db_row=",
    "file_path=",
    "env_path=",
    ".env.local=",
    "buy=",
    "sell=",
    "hold=",
    "strong_buy=",
    "recommendation=",
    "action=",
    "rank=",
    "ranking=",
    "ranking_position=",
    "target_price=",
    "expected_return=",
    "profit_probability=",
    "must_buy=",
    "must_sell=",
)

RECOMMENDATION_LIST_PREFLIGHT_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    SCORING_PREFLIGHT_REQUIRED_FALSE_FLAGS
)


@dataclass(frozen=True)
class RecommendationListPreflightSummaryFlags:
    """All external capability flags remain false for MS-12.00."""

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
class RecommendationListPreflightPolicy:
    """Immutable fail-closed policy for list model preflight."""

    preflight_version: str = "MS-12.00"
    preflight_scope: str = "recommendation_list_model_shape_preflight"
    allowed_input_sources: tuple[str, ...] = (
        ALLOWED_RECOMMENDATION_LIST_INPUT_SOURCES
    )
    forbidden_input_sources: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_INPUT_SOURCES
    )
    allowed_item_statuses: tuple[str, ...] = (
        ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES
    )
    allowed_scoring_statuses: tuple[str, ...] = ALLOWED_SCORING_STATUSES
    forbidden_action_labels: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_ACTION_LABELS
    )
    forbidden_recommendation_labels: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_RECOMMENDATION_LABELS
    )
    forbidden_ranking_labels: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_RANKING_LABELS
    )
    forbidden_output_fields: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_FIELDS
    )
    forbidden_output_keywords: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_KEYWORDS
    )
    required_false_flags: tuple[str, ...] = (
        RECOMMENDATION_LIST_PREFLIGHT_REQUIRED_FALSE_FLAGS
    )
    observation_only_policy: str = "candidate_review_item_preflight_only"
    no_action_policy: str = "no_trade_directive_output"
    no_ranking_policy: str = "no_ordered_candidate_list_output"
    no_trade_directive_policy: str = "no_buy_sell_hold_output"
    deterministic_only_policy: str = "in_memory_scoring_result_only"
    actual_recommendation_allowed: bool = False
    ranking_allowed: bool = False
    action_allowed: bool = False
    watchlist_persistence_allowed: bool = False
    feature_file_loader_allowed: bool = False
    watchlist_file_loader_allowed: bool = False
    fixture_file_loader_allowed: bool = False
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
class RecommendationListInput:
    """Normalized list preflight input from a scoring preflight result."""

    symbol: str
    market: str
    list_source: str
    scoring_status: str
    total_score: int
    score_scale: int
    score_components: tuple[ScoreComponent, ...]
    score_warnings: tuple[str, ...]
    diagnostics: tuple[str, ...]
    needs_review: bool
    usable_for_future_ranking: bool
    blocked_reasons: tuple[str, ...]
    summary_flags: ScoringPreflightSummaryFlags


@dataclass(frozen=True)
class RecommendationListPreflightItem:
    """Observation-only candidate review item without directive fields."""

    symbol: str
    market: str
    item_status: str
    display_bucket: str
    score_snapshot: int
    score_scale: int
    component_names: tuple[str, ...]
    needs_review: bool
    usable_for_future_list: bool
    blocked_reasons: tuple[str, ...]
    warnings: tuple[str, ...]
    diagnostics: tuple[str, ...]
    summary_flags: RecommendationListPreflightSummaryFlags


@dataclass(frozen=True)
class RecommendationListPreflightValidationResult:
    """Validation result for one observation-only list preflight item."""

    valid: bool
    rejection_reasons: tuple[str, ...]
    diagnostics: tuple[str, ...]
    forbidden_input_source_present: bool
    forbidden_output_field_present: bool
    forbidden_action_label_present: bool
    forbidden_ranking_label_present: bool
    required_flag_true: bool
    score_snapshot_out_of_range: bool
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
    recommendation_required: bool
    ranking_required: bool
    ui_required: bool
    streamlit_required: bool
    http_smoke_required: bool


@dataclass(frozen=True)
class RecommendationListPreflightSummary:
    """Aggregate counts for observation-only list preflight items."""

    total_items: int
    ready_for_review_items: int
    needs_review_items: int
    blocked_items: int
    usable_for_future_list_items: int
    average_score_snapshot: int
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
    recommendation_required: bool = False
    ranking_required: bool = False
    ui_required: bool = False
    streamlit_required: bool = False
    http_smoke_required: bool = False


def build_recommendation_list_preflight_policy() -> (
    RecommendationListPreflightPolicy
):
    """Build the fixed MS-12.00 recommendation list preflight policy."""

    build_scoring_preflight_policy()
    build_scoring_fixture_policy()
    build_scoring_fixture_hardening_policy()
    run_scoring_fixture_hardening_checks()
    return RecommendationListPreflightPolicy()


def _summary_flags() -> RecommendationListPreflightSummaryFlags:
    return RecommendationListPreflightSummaryFlags()


def _item_status_from_scoring_status(scoring_status: str) -> str:
    if scoring_status == "score_ready":
        return RecommendationListItemStatus.ITEM_READY_FOR_REVIEW.value
    if scoring_status == "score_needs_review":
        return RecommendationListItemStatus.ITEM_NEEDS_REVIEW.value
    if scoring_status == "score_duplicate_candidate":
        return RecommendationListItemStatus.ITEM_DUPLICATE_CANDIDATE.value
    if scoring_status == "score_disabled_candidate":
        return RecommendationListItemStatus.ITEM_DISABLED_CANDIDATE.value
    if scoring_status == "score_missing_data":
        return RecommendationListItemStatus.ITEM_MISSING_DATA.value
    if scoring_status == "score_invalid_candidate":
        return RecommendationListItemStatus.ITEM_INVALID_CANDIDATE.value
    if scoring_status == "score_forbidden_field_sanitized":
        return RecommendationListItemStatus.ITEM_FORBIDDEN_FIELD_SANITIZED.value
    if scoring_status == "score_empty_input":
        return RecommendationListItemStatus.ITEM_EMPTY_INPUT.value
    return RecommendationListItemStatus.ITEM_BLOCKED_QUALITY.value


def _display_bucket_from_item_status(item_status: str) -> str:
    if item_status == RecommendationListItemStatus.ITEM_READY_FOR_REVIEW.value:
        return "review_ready"
    if item_status == RecommendationListItemStatus.ITEM_NEEDS_REVIEW.value:
        return "review_needed"
    if item_status == RecommendationListItemStatus.ITEM_MISSING_DATA.value:
        return "missing_data_review"
    if item_status == RecommendationListItemStatus.ITEM_INVALID_CANDIDATE.value:
        return "invalid_candidate_review"
    if item_status == RecommendationListItemStatus.ITEM_DUPLICATE_CANDIDATE.value:
        return "duplicate_candidate_review"
    if item_status == RecommendationListItemStatus.ITEM_DISABLED_CANDIDATE.value:
        return "disabled_candidate_review"
    if (
        item_status
        == RecommendationListItemStatus.ITEM_FORBIDDEN_FIELD_SANITIZED.value
    ):
        return "sanitized_candidate_review"
    if item_status == RecommendationListItemStatus.ITEM_EMPTY_INPUT.value:
        return "empty_input_review"
    return "quality_blocked_review"


def _component_names(
    scoring_result: ScoringPreflightResult,
) -> tuple[str, ...]:
    return tuple(
        component.component_name for component in scoring_result.score_components
    )


def build_recommendation_list_input_from_scoring_result(
    scoring_result: ScoringPreflightResult,
    list_source: str = "in_memory_scoring_result",
) -> RecommendationListInput:
    """Normalize a scoring preflight result for list-model preflight."""

    validation = validate_scoring_preflight_result(scoring_result)
    diagnostics = scoring_result.diagnostics + tuple(
        f"scoring_validation:{reason}"
        for reason in validation.rejection_reasons
    )
    return RecommendationListInput(
        symbol=scoring_result.symbol,
        market=scoring_result.market,
        list_source=list_source,
        scoring_status=scoring_result.scoring_status,
        total_score=scoring_result.total_score,
        score_scale=scoring_result.score_scale,
        score_components=scoring_result.score_components,
        score_warnings=scoring_result.score_warnings,
        diagnostics=diagnostics,
        needs_review=scoring_result.needs_review,
        usable_for_future_ranking=scoring_result.usable_for_future_ranking,
        blocked_reasons=scoring_result.blocked_reasons,
        summary_flags=scoring_result.summary_flags,
    )


def build_recommendation_list_item_from_scoring_result(
    scoring_result: ScoringPreflightResult,
    policy: RecommendationListPreflightPolicy | None = None,
) -> RecommendationListPreflightItem:
    """Build one observation-only list preflight item from scoring output."""

    active_policy = policy or build_recommendation_list_preflight_policy()
    list_input = build_recommendation_list_input_from_scoring_result(scoring_result)
    item_status = _item_status_from_scoring_status(list_input.scoring_status)
    display_bucket = _display_bucket_from_item_status(item_status)
    usable_for_future_list = (
        item_status == RecommendationListItemStatus.ITEM_READY_FOR_REVIEW.value
        and list_input.usable_for_future_ranking
        and not list_input.needs_review
    )
    component_names = tuple(
        name
        for name in _component_names(scoring_result)
        if name not in active_policy.forbidden_output_fields
    )
    return RecommendationListPreflightItem(
        symbol=list_input.symbol,
        market=list_input.market,
        item_status=item_status,
        display_bucket=display_bucket,
        score_snapshot=list_input.total_score,
        score_scale=list_input.score_scale,
        component_names=component_names,
        needs_review=list_input.needs_review,
        usable_for_future_list=usable_for_future_list,
        blocked_reasons=list_input.blocked_reasons,
        warnings=list_input.score_warnings
        + (
            "observation_item_preflight_only",
            "score_snapshot_quality_preflight_only",
            "display_bucket_review_group_only",
        ),
        diagnostics=list_input.diagnostics
        + ("deterministic_in_memory_list_item_shape",),
        summary_flags=_summary_flags(),
    )


def build_recommendation_list_items_from_scoring_results(
    scoring_results: tuple[ScoringPreflightResult, ...],
    policy: RecommendationListPreflightPolicy | None = None,
) -> tuple[RecommendationListPreflightItem, ...]:
    """Build observation-only list preflight items from scoring results."""

    active_policy = policy or build_recommendation_list_preflight_policy()
    return tuple(
        build_recommendation_list_item_from_scoring_result(result, active_policy)
        for result in scoring_results
    )


def _flatten_result_groups(
    groups: tuple[tuple[ScoringPreflightResult, ...], ...],
) -> tuple[ScoringPreflightResult, ...]:
    return tuple(result for group in groups for result in group)


def build_recommendation_list_items_from_all_fixtures(
    policy: RecommendationListPreflightPolicy | None = None,
) -> tuple[RecommendationListPreflightItem, ...]:
    """Build observation-only list preflight items from all fixtures."""

    active_policy = policy or build_recommendation_list_preflight_policy()
    scoring_results = _flatten_result_groups(
        score_extracted_feature_sets_from_all_fixtures()
    )
    return build_recommendation_list_items_from_scoring_results(
        scoring_results,
        active_policy,
    )


def _required_flag_true(item: RecommendationListPreflightItem) -> bool:
    return any(
        bool(getattr(item.summary_flags, field.name))
        for field in fields(item.summary_flags)
    )


def _forbidden_output_keyword_present(
    item: RecommendationListPreflightItem,
    policy: RecommendationListPreflightPolicy,
) -> bool:
    rendered = repr(item)
    return any(keyword in rendered for keyword in policy.forbidden_output_keywords)


def validate_recommendation_list_preflight_item(
    item: RecommendationListPreflightItem,
    policy: RecommendationListPreflightPolicy | None = None,
) -> RecommendationListPreflightValidationResult:
    """Validate one observation-only list preflight item."""

    active_policy = policy or build_recommendation_list_preflight_policy()
    forbidden_action_label_present = (
        item.item_status in active_policy.forbidden_action_labels
        or item.display_bucket in active_policy.forbidden_action_labels
    )
    forbidden_ranking_label_present = (
        item.item_status in active_policy.forbidden_ranking_labels
        or item.display_bucket in active_policy.forbidden_ranking_labels
    )
    forbidden_output_field_present = _forbidden_output_keyword_present(
        item,
        active_policy,
    )
    required_flag_true = _required_flag_true(item)
    score_snapshot_out_of_range = not (
        0 <= item.score_snapshot <= item.score_scale == SCORE_SCALE
    )
    rejection_reasons: list[str] = []
    if item.item_status not in active_policy.allowed_item_statuses:
        rejection_reasons.append("item_status_not_allowed")
    if forbidden_action_label_present:
        rejection_reasons.append("forbidden_action_label_present")
    if forbidden_ranking_label_present:
        rejection_reasons.append("forbidden_ranking_label_present")
    if forbidden_output_field_present:
        rejection_reasons.append("forbidden_output_field_present")
    if required_flag_true:
        rejection_reasons.append("required_flag_true")
    if score_snapshot_out_of_range:
        rejection_reasons.append("score_snapshot_out_of_range")

    return RecommendationListPreflightValidationResult(
        valid=not rejection_reasons,
        rejection_reasons=tuple(rejection_reasons),
        diagnostics=(
            "recommendation_list_preflight_item_validated",
            "observation_only_item_shape",
        ),
        forbidden_input_source_present=False,
        forbidden_output_field_present=forbidden_output_field_present,
        forbidden_action_label_present=forbidden_action_label_present,
        forbidden_ranking_label_present=forbidden_ranking_label_present,
        required_flag_true=required_flag_true,
        score_snapshot_out_of_range=score_snapshot_out_of_range,
        credential_required=False,
        db_read_required=False,
        db_write_required=False,
        file_read_required=False,
        file_write_required=False,
        toss_api_required=False,
        openai_required=False,
        oauth_required=False,
        account_seq_required=False,
        real_order_required=False,
        recommendation_required=False,
        ranking_required=False,
        ui_required=False,
        streamlit_required=False,
        http_smoke_required=False,
    )


def summarize_recommendation_list_preflight_items(
    items: tuple[RecommendationListPreflightItem, ...],
) -> RecommendationListPreflightSummary:
    """Summarize observation-only list preflight items."""

    total_score = sum(item.score_snapshot for item in items)
    average_score = total_score // len(items) if items else 0
    ready_count = sum(
        item.item_status
        == RecommendationListItemStatus.ITEM_READY_FOR_REVIEW.value
        for item in items
    )
    needs_review_count = sum(item.needs_review for item in items)
    blocked_count = sum(
        item.item_status
        != RecommendationListItemStatus.ITEM_READY_FOR_REVIEW.value
        for item in items
    )
    usable_count = sum(item.usable_for_future_list for item in items)
    return RecommendationListPreflightSummary(
        total_items=len(items),
        ready_for_review_items=ready_count,
        needs_review_items=needs_review_count,
        blocked_items=blocked_count,
        usable_for_future_list_items=usable_count,
        average_score_snapshot=average_score,
        diagnostics=(
            "list_model_preflight_summary_only",
            "no_ordered_candidate_list_created",
        ),
    )


def validate_recommendation_list_preflight_items(
    items: tuple[RecommendationListPreflightItem, ...],
    policy: RecommendationListPreflightPolicy | None = None,
) -> tuple[RecommendationListPreflightValidationResult, ...]:
    """Validate multiple observation-only list preflight items."""

    active_policy = policy or build_recommendation_list_preflight_policy()
    return tuple(
        validate_recommendation_list_preflight_item(item, active_policy)
        for item in items
    )


def build_recommendation_list_items_from_scoring_fixture_matrix() -> (
    tuple[RecommendationListPreflightItem, ...]
):
    """Build items after reusing scoring fixture and hardening checks."""

    build_all_scoring_fixtures()
    evaluate_all_scoring_fixtures()
    run_scoring_fixture_hardening_checks()
    return build_recommendation_list_items_from_all_fixtures()


def summarize_scoring_results_for_list_preflight(
    scoring_results: tuple[ScoringPreflightResult, ...],
) -> object:
    """Expose existing scoring summary for contract-reuse tests."""

    return summarize_scoring_preflight_results(scoring_results)


def score_feature_set_for_list_preflight_probe(feature_set: object) -> object:
    """Expose existing single scoring path for contract-reuse tests."""

    return score_extracted_feature_set_preflight(feature_set)


def score_fixture_for_list_preflight_probe(fixture: object) -> object:
    """Expose existing fixture scoring path for contract-reuse tests."""

    return score_extracted_feature_sets_from_fixture(fixture)


def evaluate_scoring_fixture_for_list_preflight_probe(fixture: object) -> object:
    """Expose existing scoring fixture evaluator for contract-reuse tests."""

    return evaluate_scoring_fixture(fixture)
