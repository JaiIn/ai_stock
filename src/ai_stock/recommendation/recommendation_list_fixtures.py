"""Pure recommendation list fixture expansion for MS-12.01.

This module defines deterministic in-memory fixture expectations on top of the
MS-12.00 recommendation list preflight contract. It performs no Streamlit,
file, database, environment, network, model, account, order, clock, or random
I/O. It does not create actual recommendation lists, rank candidates, issue
trade actions, load features, or render UI.
"""

from dataclasses import dataclass
from enum import Enum

from ai_stock.recommendation.recommendation_list_preflight import (
    ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES,
    FORBIDDEN_RECOMMENDATION_LIST_INPUT_SOURCES,
    FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_FIELDS,
    FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_KEYWORDS,
    RECOMMENDATION_LIST_PREFLIGHT_REQUIRED_FALSE_FLAGS,
    RecommendationListPreflightItem,
    build_recommendation_list_items_from_all_fixtures,
    build_recommendation_list_items_from_scoring_results,
    build_recommendation_list_preflight_policy,
    summarize_recommendation_list_preflight_items,
    validate_recommendation_list_preflight_item,
)
from ai_stock.recommendation.scoring_fixture_hardening import (
    run_scoring_fixture_hardening_checks,
)
from ai_stock.recommendation.scoring_fixtures import (
    ScoringFixtureRecord,
    build_all_scoring_fixtures,
    build_scoring_all_fixture_matrix,
    build_scoring_basic_ready_fixture,
    build_scoring_disabled_blocked_fixture,
    build_scoring_duplicates_blocked_fixture,
    build_scoring_empty_input_fixture,
    build_scoring_fixture_policy,
    build_scoring_forbidden_field_sanitized_fixture,
    build_scoring_missing_data_blocked_fixture,
    build_scoring_mixed_review_fixture,
    evaluate_all_scoring_fixtures,
    score_extracted_feature_sets_from_scoring_fixture,
)
from ai_stock.recommendation.scoring_preflight import (
    ALLOWED_SCORE_COMPONENT_NAMES,
    SCORE_SCALE,
)


class RecommendationListFixtureScenario(str, Enum):
    """Allowed deterministic recommendation list fixture scenarios."""

    LIST_BASIC_READY_FOR_REVIEW = "list_basic_ready_for_review"
    LIST_MIXED_REVIEW = "list_mixed_review"
    LIST_DUPLICATES_BLOCKED = "list_duplicates_blocked"
    LIST_DISABLED_BLOCKED = "list_disabled_blocked"
    LIST_MISSING_DATA_BLOCKED = "list_missing_data_blocked"
    LIST_FORBIDDEN_FIELD_SANITIZED = "list_forbidden_field_sanitized"
    LIST_EMPTY_INPUT = "list_empty_input"
    LIST_ALL_FIXTURE_MATRIX = "list_all_fixture_matrix"


ALLOWED_RECOMMENDATION_LIST_FIXTURE_SCENARIOS: tuple[str, ...] = tuple(
    scenario.value for scenario in RecommendationListFixtureScenario
)

FORBIDDEN_RECOMMENDATION_LIST_FIXTURE_SCENARIOS: tuple[str, ...] = (
    "real_account_holdings_fixture",
    "real_balance_fixture",
    "real_fills_fixture",
    "real_order_history_fixture",
    "toss_api_response_fixture",
    "oauth_response_fixture",
    "openai_llm_response_fixture",
    "accountSeq_based_fixture",
    "raw_api_response_fixture",
    "raw_db_row_fixture",
    "db_table_row_fixture",
    "file_path_fixture",
    "feature_file_fixture",
    "watchlist_file_fixture",
    "credential_token_key_fixture",
    "actual_recommendation_fixture",
    "ranking_fixture",
    "buy_sell_hold_fixture",
    "target_price_fixture",
    "expected_return_fixture",
    "profit_probability_fixture",
)

RECOMMENDATION_LIST_FIXTURE_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    RECOMMENDATION_LIST_PREFLIGHT_REQUIRED_FALSE_FLAGS
)

FORBIDDEN_RECOMMENDATION_LIST_FIXTURE_OUTPUT_KEYWORDS: tuple[str, ...] = (
    *FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_KEYWORDS,
    "ranking_position=",
)


@dataclass(frozen=True)
class RecommendationListFixturePolicy:
    """Immutable fail-closed policy for MS-12.01 list fixtures."""

    stage_name: str = "MS-12.01"
    mode: str = "recommendation_list_fixture_expansion"
    allowed_scenarios: tuple[str, ...] = ALLOWED_RECOMMENDATION_LIST_FIXTURE_SCENARIOS
    forbidden_scenarios: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_FIXTURE_SCENARIOS
    )
    allowed_item_statuses: tuple[str, ...] = ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES
    allowed_score_component_names: tuple[str, ...] = ALLOWED_SCORE_COMPONENT_NAMES
    forbidden_input_sources: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_INPUT_SOURCES
    )
    forbidden_output_fields: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_FIELDS
    )
    required_false_flags: tuple[str, ...] = (
        RECOMMENDATION_LIST_FIXTURE_REQUIRED_FALSE_FLAGS
    )
    forbidden_absent_keywords: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_FIXTURE_OUTPUT_KEYWORDS
    )
    score_snapshot_semantics: str = "data_quality_extraction_readiness_snapshot_only"
    display_bucket_semantics: str = "review_grouping_label_only"
    usable_for_future_list_semantics: str = "future_list_readiness_only"
    actual_recommendation_allowed: bool = False
    actual_recommendation_list_allowed: bool = False
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
    recommendation_required: bool = False
    ranking_required: bool = False
    ui_required: bool = False
    streamlit_required: bool = False
    http_smoke_required: bool = False


@dataclass(frozen=True)
class RecommendationListFixtureRecord:
    """Recommendation list fixture expectations without directive fields."""

    scenario: str
    description: str
    source_fixture_name: str
    expected_item_statuses: tuple[str, ...]
    expected_ready_for_review_count: int
    expected_needs_review_count: int
    expected_usable_for_future_list_count: int
    expected_display_buckets: tuple[str, ...]
    expected_score_snapshot_min: int
    expected_score_snapshot_max: int
    expected_component_names: tuple[str, ...]
    expected_blocked_reason_keywords: tuple[str, ...]
    expected_warning_keywords: tuple[str, ...]
    expected_diagnostic_keywords: tuple[str, ...]
    expected_required_false_flags: tuple[str, ...]
    expected_forbidden_absent_keywords: tuple[str, ...]


@dataclass(frozen=True)
class RecommendationListFixtureEvaluationResult:
    """Expected-vs-actual evaluation result for one list fixture."""

    scenario: str
    passed: bool
    failures: tuple[str, ...]
    actual_item_statuses: tuple[str, ...]
    actual_ready_for_review_count: int
    actual_needs_review_count: int
    actual_usable_for_future_list_count: int
    actual_display_buckets: tuple[str, ...]
    actual_score_snapshots: tuple[int, ...]
    actual_component_names: tuple[str, ...]
    actual_blocked_reasons: tuple[str, ...]
    actual_warnings: tuple[str, ...]
    actual_diagnostics: tuple[str, ...]
    actual_required_flags: tuple[str, ...]
    forbidden_absent_check_passed: bool


def build_recommendation_list_fixture_policy() -> RecommendationListFixturePolicy:
    """Build the fixed MS-12.01 recommendation list fixture policy."""

    build_recommendation_list_preflight_policy()
    build_scoring_fixture_policy()
    run_scoring_fixture_hardening_checks()
    evaluate_all_scoring_fixtures()
    return RecommendationListFixturePolicy()


def _expected_false_flags() -> tuple[str, ...]:
    return tuple(
        f"{flag}=false" for flag in RECOMMENDATION_LIST_FIXTURE_REQUIRED_FALSE_FLAGS
    )


def _fixture_record(
    *,
    scenario: RecommendationListFixtureScenario,
    description: str,
    source_fixture_name: str,
    expected_item_statuses: tuple[str, ...],
    expected_ready_for_review_count: int,
    expected_needs_review_count: int,
    expected_usable_for_future_list_count: int,
    expected_display_buckets: tuple[str, ...],
    expected_score_snapshot_min: int,
    expected_score_snapshot_max: int,
    expected_blocked_reason_keywords: tuple[str, ...] = (),
    expected_warning_keywords: tuple[str, ...] = (),
    expected_diagnostic_keywords: tuple[str, ...] = (),
) -> RecommendationListFixtureRecord:
    return RecommendationListFixtureRecord(
        scenario=scenario.value,
        description=description,
        source_fixture_name=source_fixture_name,
        expected_item_statuses=expected_item_statuses,
        expected_ready_for_review_count=expected_ready_for_review_count,
        expected_needs_review_count=expected_needs_review_count,
        expected_usable_for_future_list_count=expected_usable_for_future_list_count,
        expected_display_buckets=expected_display_buckets,
        expected_score_snapshot_min=expected_score_snapshot_min,
        expected_score_snapshot_max=expected_score_snapshot_max,
        expected_component_names=ALLOWED_SCORE_COMPONENT_NAMES,
        expected_blocked_reason_keywords=expected_blocked_reason_keywords,
        expected_warning_keywords=expected_warning_keywords,
        expected_diagnostic_keywords=expected_diagnostic_keywords,
        expected_required_false_flags=_expected_false_flags(),
        expected_forbidden_absent_keywords=(
            FORBIDDEN_RECOMMENDATION_LIST_FIXTURE_OUTPUT_KEYWORDS
        ),
    )


def build_list_basic_ready_for_review_fixture() -> RecommendationListFixtureRecord:
    """Build expectations for ready observation-only list items."""

    return _fixture_record(
        scenario=RecommendationListFixtureScenario.LIST_BASIC_READY_FOR_REVIEW,
        description="Ready scoring results become review-ready observation items.",
        source_fixture_name="scoring_basic_ready",
        expected_item_statuses=("item_ready_for_review", "item_ready_for_review"),
        expected_ready_for_review_count=2,
        expected_needs_review_count=0,
        expected_usable_for_future_list_count=2,
        expected_display_buckets=("review_ready",),
        expected_score_snapshot_min=SCORE_SCALE,
        expected_score_snapshot_max=SCORE_SCALE,
        expected_warning_keywords=(
            "observation_item_preflight_only",
            "score_snapshot_quality_preflight_only",
            "display_bucket_review_group_only",
        ),
        expected_diagnostic_keywords=("deterministic_in_memory_list_item_shape",),
    )


def build_list_mixed_review_fixture() -> RecommendationListFixtureRecord:
    """Build expectations for mixed ready and invalid observation items."""

    return _fixture_record(
        scenario=RecommendationListFixtureScenario.LIST_MIXED_REVIEW,
        description="Invalid candidates remain review-only list item states.",
        source_fixture_name="scoring_mixed_review",
        expected_item_statuses=(
            "item_ready_for_review",
            "item_invalid_candidate",
            "item_invalid_candidate",
        ),
        expected_ready_for_review_count=1,
        expected_needs_review_count=2,
        expected_usable_for_future_list_count=1,
        expected_display_buckets=("review_ready", "invalid_candidate_review"),
        expected_score_snapshot_min=20,
        expected_score_snapshot_max=SCORE_SCALE,
        expected_blocked_reason_keywords=("quality_invalid_candidate",),
        expected_warning_keywords=("invalid_symbol_review",),
        expected_diagnostic_keywords=(
            "symbol_required",
            "symbol_must_be_safe_ascii_identifier",
        ),
    )


def build_list_duplicates_blocked_fixture() -> RecommendationListFixtureRecord:
    """Build expectations for duplicate list item blocking."""

    return _fixture_record(
        scenario=RecommendationListFixtureScenario.LIST_DUPLICATES_BLOCKED,
        description="Duplicate candidates are blocked for future list readiness.",
        source_fixture_name="scoring_duplicates_blocked",
        expected_item_statuses=(
            "item_ready_for_review",
            "item_duplicate_candidate",
            "item_disabled_candidate",
        ),
        expected_ready_for_review_count=1,
        expected_needs_review_count=2,
        expected_usable_for_future_list_count=1,
        expected_display_buckets=(
            "review_ready",
            "duplicate_candidate_review",
            "disabled_candidate_review",
        ),
        expected_score_snapshot_min=20,
        expected_score_snapshot_max=SCORE_SCALE,
        expected_blocked_reason_keywords=("quality_duplicate_candidate",),
        expected_warning_keywords=("duplicate_candidate_needs_review",),
        expected_diagnostic_keywords=("duplicate_symbol",),
    )


def build_list_disabled_blocked_fixture() -> RecommendationListFixtureRecord:
    """Build expectations for disabled list item blocking."""

    return _fixture_record(
        scenario=RecommendationListFixtureScenario.LIST_DISABLED_BLOCKED,
        description="Disabled candidates remain non-ready observation items.",
        source_fixture_name="scoring_disabled_blocked",
        expected_item_statuses=(
            "item_ready_for_review",
            "item_duplicate_candidate",
            "item_disabled_candidate",
        ),
        expected_ready_for_review_count=1,
        expected_needs_review_count=2,
        expected_usable_for_future_list_count=1,
        expected_display_buckets=(
            "review_ready",
            "duplicate_candidate_review",
            "disabled_candidate_review",
        ),
        expected_score_snapshot_min=20,
        expected_score_snapshot_max=SCORE_SCALE,
        expected_blocked_reason_keywords=("quality_disabled_candidate",),
        expected_warning_keywords=("disabled_candidate_not_selectable",),
        expected_diagnostic_keywords=("candidate_disabled",),
    )


def build_list_missing_data_blocked_fixture() -> RecommendationListFixtureRecord:
    """Build expectations for missing-data list item blocking."""

    return _fixture_record(
        scenario=RecommendationListFixtureScenario.LIST_MISSING_DATA_BLOCKED,
        description="Missing data remains a blocked observation item.",
        source_fixture_name="scoring_missing_data_blocked",
        expected_item_statuses=("item_missing_data",),
        expected_ready_for_review_count=0,
        expected_needs_review_count=1,
        expected_usable_for_future_list_count=0,
        expected_display_buckets=("missing_data_review",),
        expected_score_snapshot_min=20,
        expected_score_snapshot_max=20,
        expected_blocked_reason_keywords=("quality_insufficient_data",),
        expected_warning_keywords=("insufficient_data_review",),
        expected_diagnostic_keywords=("deterministic_in_memory_list_item_shape",),
    )


def build_list_forbidden_field_sanitized_fixture() -> (
    RecommendationListFixtureRecord
):
    """Build expectations for forbidden-field sanitized observation items."""

    return _fixture_record(
        scenario=RecommendationListFixtureScenario.LIST_FORBIDDEN_FIELD_SANITIZED,
        description="Forbidden fields remain diagnostics-only in list items.",
        source_fixture_name="scoring_forbidden_field_sanitized",
        expected_item_statuses=("item_forbidden_field_sanitized",),
        expected_ready_for_review_count=0,
        expected_needs_review_count=1,
        expected_usable_for_future_list_count=0,
        expected_display_buckets=("sanitized_candidate_review",),
        expected_score_snapshot_min=0,
        expected_score_snapshot_max=0,
        expected_blocked_reason_keywords=("quality_forbidden_field_sanitized",),
        expected_warning_keywords=("score_snapshot_quality_preflight_only",),
        expected_diagnostic_keywords=(
            "forbidden_field_detected:accountSeq",
            "forbidden_fields_reported_in_diagnostics_only",
        ),
    )


def build_list_empty_input_fixture() -> RecommendationListFixtureRecord:
    """Build expectations for empty-input list item handling."""

    return _fixture_record(
        scenario=RecommendationListFixtureScenario.LIST_EMPTY_INPUT,
        description="Empty input remains a safe observation item state.",
        source_fixture_name="scoring_empty_input",
        expected_item_statuses=("item_empty_input",),
        expected_ready_for_review_count=0,
        expected_needs_review_count=1,
        expected_usable_for_future_list_count=0,
        expected_display_buckets=("empty_input_review",),
        expected_score_snapshot_min=20,
        expected_score_snapshot_max=20,
        expected_blocked_reason_keywords=("quality_empty_input",),
        expected_warning_keywords=("empty_watchlist_safe_state",),
        expected_diagnostic_keywords=("empty_source_items",),
    )


def build_list_all_fixture_matrix() -> RecommendationListFixtureRecord:
    """Build expectations for all fixture-based observation items."""

    return _fixture_record(
        scenario=RecommendationListFixtureScenario.LIST_ALL_FIXTURE_MATRIX,
        description="All scoring fixtures produce safe observation list items.",
        source_fixture_name="scoring_all_fixture_matrix",
        expected_item_statuses=(
            "item_ready_for_review",
            "item_ready_for_review",
            "item_ready_for_review",
            "item_invalid_candidate",
            "item_invalid_candidate",
            "item_ready_for_review",
            "item_duplicate_candidate",
            "item_disabled_candidate",
            "item_missing_data",
            "item_forbidden_field_sanitized",
            "item_empty_input",
        ),
        expected_ready_for_review_count=4,
        expected_needs_review_count=7,
        expected_usable_for_future_list_count=4,
        expected_display_buckets=(
            "review_ready",
            "invalid_candidate_review",
            "duplicate_candidate_review",
            "disabled_candidate_review",
            "missing_data_review",
            "sanitized_candidate_review",
            "empty_input_review",
        ),
        expected_score_snapshot_min=0,
        expected_score_snapshot_max=SCORE_SCALE,
        expected_blocked_reason_keywords=(
            "quality_invalid_candidate",
            "quality_duplicate_candidate",
            "quality_disabled_candidate",
            "quality_insufficient_data",
            "quality_forbidden_field_sanitized",
            "quality_empty_input",
        ),
        expected_warning_keywords=(
            "observation_item_preflight_only",
            "score_snapshot_quality_preflight_only",
            "display_bucket_review_group_only",
            "invalid_symbol_review",
            "duplicate_candidate_needs_review",
            "disabled_candidate_not_selectable",
            "insufficient_data_review",
            "empty_watchlist_safe_state",
        ),
        expected_diagnostic_keywords=(
            "deterministic_in_memory_list_item_shape",
            "symbol_required",
            "duplicate_symbol",
            "candidate_disabled",
            "forbidden_field_detected:accountSeq",
            "empty_source_items",
        ),
    )


def build_all_recommendation_list_fixtures() -> (
    tuple[RecommendationListFixtureRecord, ...]
):
    """Build every deterministic MS-12.01 recommendation list fixture."""

    return (
        build_list_basic_ready_for_review_fixture(),
        build_list_mixed_review_fixture(),
        build_list_duplicates_blocked_fixture(),
        build_list_disabled_blocked_fixture(),
        build_list_missing_data_blocked_fixture(),
        build_list_forbidden_field_sanitized_fixture(),
        build_list_empty_input_fixture(),
        build_list_all_fixture_matrix(),
    )


def _scoring_fixture_by_name(source_fixture_name: str) -> ScoringFixtureRecord:
    if source_fixture_name == "scoring_basic_ready":
        return build_scoring_basic_ready_fixture()
    if source_fixture_name == "scoring_mixed_review":
        return build_scoring_mixed_review_fixture()
    if source_fixture_name == "scoring_duplicates_blocked":
        return build_scoring_duplicates_blocked_fixture()
    if source_fixture_name == "scoring_disabled_blocked":
        return build_scoring_disabled_blocked_fixture()
    if source_fixture_name == "scoring_missing_data_blocked":
        return build_scoring_missing_data_blocked_fixture()
    if source_fixture_name == "scoring_forbidden_field_sanitized":
        return build_scoring_forbidden_field_sanitized_fixture()
    if source_fixture_name == "scoring_empty_input":
        return build_scoring_empty_input_fixture()
    if source_fixture_name == "scoring_all_fixture_matrix":
        return build_scoring_all_fixture_matrix()
    raise ValueError(f"unknown_scoring_fixture:{source_fixture_name}")


def _list_items_for_fixture(
    fixture: RecommendationListFixtureRecord,
) -> tuple[RecommendationListPreflightItem, ...]:
    policy = build_recommendation_list_preflight_policy()
    build_all_scoring_fixtures()
    if fixture.source_fixture_name == "scoring_all_fixture_matrix":
        return build_recommendation_list_items_from_all_fixtures(policy)
    scoring_results = score_extracted_feature_sets_from_scoring_fixture(
        _scoring_fixture_by_name(fixture.source_fixture_name)
    )
    return build_recommendation_list_items_from_scoring_results(
        scoring_results,
        policy,
    )


def _actual_false_flags(
    items: tuple[RecommendationListPreflightItem, ...],
) -> tuple[str, ...]:
    return tuple(
        f"{flag}={str(any(bool(getattr(item.summary_flags, flag)) for item in items)).lower()}"
        for flag in RECOMMENDATION_LIST_FIXTURE_REQUIRED_FALSE_FLAGS
    )


def _unique_display_buckets(
    items: tuple[RecommendationListPreflightItem, ...],
) -> tuple[str, ...]:
    values = tuple(item.display_bucket for item in items)
    return tuple(dict.fromkeys(values))


def _unique_component_names(
    items: tuple[RecommendationListPreflightItem, ...],
) -> tuple[str, ...]:
    names = tuple(name for item in items for name in item.component_names)
    return tuple(name for name in ALLOWED_SCORE_COMPONENT_NAMES if name in names)


def evaluate_recommendation_list_fixture(
    fixture: RecommendationListFixtureRecord,
) -> RecommendationListFixtureEvaluationResult:
    """Compare MS-12.01 fixture expectations with list preflight outputs."""

    items = _list_items_for_fixture(fixture)
    policy = build_recommendation_list_preflight_policy()
    summary = summarize_recommendation_list_preflight_items(items)
    actual_item_statuses = tuple(item.item_status for item in items)
    actual_display_buckets = _unique_display_buckets(items)
    actual_score_snapshots = tuple(item.score_snapshot for item in items)
    actual_component_names = _unique_component_names(items)
    actual_blocked_reasons = tuple(
        reason for item in items for reason in item.blocked_reasons
    )
    actual_warnings = tuple(warning for item in items for warning in item.warnings)
    actual_diagnostics = tuple(
        diagnostic for item in items for diagnostic in item.diagnostics
    )
    actual_required_flags = _actual_false_flags(items)
    validation_results = tuple(
        validate_recommendation_list_preflight_item(item, policy) for item in items
    )
    rendered_items = repr(items)
    forbidden_absent_check_passed = not any(
        keyword in rendered_items
        for keyword in fixture.expected_forbidden_absent_keywords
    )

    failures: list[str] = []
    if actual_item_statuses != fixture.expected_item_statuses:
        failures.append("item_statuses_mismatch")
    if summary.ready_for_review_items != fixture.expected_ready_for_review_count:
        failures.append("ready_for_review_count_mismatch")
    if summary.needs_review_items != fixture.expected_needs_review_count:
        failures.append("needs_review_count_mismatch")
    if (
        summary.usable_for_future_list_items
        != fixture.expected_usable_for_future_list_count
    ):
        failures.append("usable_for_future_list_count_mismatch")
    if actual_display_buckets != fixture.expected_display_buckets:
        failures.append("display_buckets_mismatch")
    if actual_score_snapshots:
        if min(actual_score_snapshots) < fixture.expected_score_snapshot_min:
            failures.append("score_snapshot_min_mismatch")
        if max(actual_score_snapshots) > fixture.expected_score_snapshot_max:
            failures.append("score_snapshot_max_mismatch")
    elif fixture.expected_score_snapshot_min != 0:
        failures.append("score_snapshot_min_mismatch")
    if actual_component_names != fixture.expected_component_names:
        failures.append("component_names_mismatch")
    if actual_required_flags != fixture.expected_required_false_flags:
        failures.append("required_false_flags_mismatch")
    if not forbidden_absent_check_passed:
        failures.append("forbidden_keyword_present")

    for expected_keyword in fixture.expected_blocked_reason_keywords:
        if not any(expected_keyword in value for value in actual_blocked_reasons):
            failures.append(f"missing_blocked_reason:{expected_keyword}")

    for expected_keyword in fixture.expected_warning_keywords:
        if not any(expected_keyword in value for value in actual_warnings):
            failures.append(f"missing_warning:{expected_keyword}")

    for expected_keyword in fixture.expected_diagnostic_keywords:
        if not any(expected_keyword in value for value in actual_diagnostics):
            failures.append(f"missing_diagnostic:{expected_keyword}")

    for validation in validation_results:
        if not validation.valid:
            failures.extend(
                f"invalid_recommendation_list_item:{reason}"
                for reason in validation.rejection_reasons
            )

    return RecommendationListFixtureEvaluationResult(
        scenario=fixture.scenario,
        passed=not failures,
        failures=tuple(failures),
        actual_item_statuses=actual_item_statuses,
        actual_ready_for_review_count=summary.ready_for_review_items,
        actual_needs_review_count=summary.needs_review_items,
        actual_usable_for_future_list_count=summary.usable_for_future_list_items,
        actual_display_buckets=actual_display_buckets,
        actual_score_snapshots=actual_score_snapshots,
        actual_component_names=actual_component_names,
        actual_blocked_reasons=actual_blocked_reasons,
        actual_warnings=actual_warnings,
        actual_diagnostics=actual_diagnostics,
        actual_required_flags=actual_required_flags,
        forbidden_absent_check_passed=forbidden_absent_check_passed,
    )


def evaluate_all_recommendation_list_fixtures() -> (
    tuple[RecommendationListFixtureEvaluationResult, ...]
):
    """Evaluate every deterministic MS-12.01 recommendation list fixture."""

    return tuple(
        evaluate_recommendation_list_fixture(fixture)
        for fixture in build_all_recommendation_list_fixtures()
    )


def build_recommendation_list_items_from_fixture(
    fixture: RecommendationListFixtureRecord,
) -> tuple[RecommendationListPreflightItem, ...]:
    """Return list preflight items referenced by one list fixture."""

    return _list_items_for_fixture(fixture)


def build_recommendation_list_items_from_all_list_fixtures() -> (
    tuple[tuple[RecommendationListPreflightItem, ...], ...]
):
    """Return grouped list preflight items for every list fixture."""

    return tuple(
        build_recommendation_list_items_from_fixture(fixture)
        for fixture in build_all_recommendation_list_fixtures()
    )
