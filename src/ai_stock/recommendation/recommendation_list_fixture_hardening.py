"""Pure recommendation list fixture hardening checks for MS-12.02.

This module adds deterministic safety and stability checks on top of the
MS-12.00 recommendation list preflight contract and MS-12.01 recommendation
list fixtures. It performs no Streamlit, file, database, environment, network,
model, account, order, clock, or random I/O. It does not create actual
recommendation lists, rank candidates, issue trade actions, load features, or
render UI.
"""

from dataclasses import dataclass, replace
from functools import lru_cache

from ai_stock.recommendation.recommendation_list_fixtures import (
    ALLOWED_RECOMMENDATION_LIST_FIXTURE_SCENARIOS,
    FORBIDDEN_RECOMMENDATION_LIST_FIXTURE_OUTPUT_KEYWORDS,
    RECOMMENDATION_LIST_FIXTURE_REQUIRED_FALSE_FLAGS,
    RecommendationListFixtureEvaluationResult,
    RecommendationListFixtureRecord,
    build_all_recommendation_list_fixtures,
    build_list_basic_ready_for_review_fixture,
    build_recommendation_list_items_from_all_list_fixtures,
    build_recommendation_list_items_from_fixture,
    evaluate_all_recommendation_list_fixtures,
    evaluate_recommendation_list_fixture,
)
from ai_stock.recommendation.recommendation_list_preflight import (
    ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES,
    FORBIDDEN_RECOMMENDATION_LIST_ACTION_LABELS,
    FORBIDDEN_RECOMMENDATION_LIST_INPUT_SOURCES,
    FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_FIELDS,
    FORBIDDEN_RECOMMENDATION_LIST_RANKING_LABELS,
    FORBIDDEN_RECOMMENDATION_LIST_RECOMMENDATION_LABELS,
    RecommendationListPreflightItem,
    build_recommendation_list_preflight_policy,
    summarize_recommendation_list_preflight_items,
    validate_recommendation_list_preflight_item,
)
from ai_stock.recommendation.scoring_preflight import (
    ALLOWED_SCORE_COMPONENT_NAMES,
    SCORE_SCALE,
    build_scoring_preflight_policy,
)


RECOMMENDATION_LIST_FIXTURE_HARDENING_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    RECOMMENDATION_LIST_FIXTURE_REQUIRED_FALSE_FLAGS
)

FORBIDDEN_RECOMMENDATION_LIST_HARDENING_OUTPUT_KEYWORDS: tuple[str, ...] = (
    *FORBIDDEN_RECOMMENDATION_LIST_FIXTURE_OUTPUT_KEYWORDS,
    "priority=",
    "order=",
)

REQUIRED_RECOMMENDATION_LIST_DISPLAY_BUCKETS: tuple[str, ...] = (
    "review_ready",
    "invalid_candidate_review",
    "duplicate_candidate_review",
    "disabled_candidate_review",
    "missing_data_review",
    "sanitized_candidate_review",
    "empty_input_review",
)


@dataclass(frozen=True)
class RecommendationListFixtureHardeningPolicy:
    """Immutable safety policy for MS-12.02 list fixture hardening."""

    hardening_version: str = "MS-12.02"
    hardening_scope: str = (
        "recommendation_list_fixture_safety_determinism_guardrail"
    )
    required_scenarios: tuple[str, ...] = (
        ALLOWED_RECOMMENDATION_LIST_FIXTURE_SCENARIOS
    )
    required_item_statuses: tuple[str, ...] = (
        ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES
    )
    required_display_buckets: tuple[str, ...] = (
        REQUIRED_RECOMMENDATION_LIST_DISPLAY_BUCKETS
    )
    required_component_names: tuple[str, ...] = ALLOWED_SCORE_COMPONENT_NAMES
    forbidden_status_keywords: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_ACTION_LABELS
        + FORBIDDEN_RECOMMENDATION_LIST_RECOMMENDATION_LABELS
        + FORBIDDEN_RECOMMENDATION_LIST_RANKING_LABELS
        + ("priority", "order")
    )
    forbidden_output_keywords: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_HARDENING_OUTPUT_KEYWORDS
    )
    forbidden_output_fields: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_FIELDS
    )
    forbidden_input_sources: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_INPUT_SOURCES
    )
    required_false_flags: tuple[str, ...] = (
        RECOMMENDATION_LIST_FIXTURE_HARDENING_REQUIRED_FALSE_FLAGS
    )
    deterministic_repeat_count: int = 3
    min_fixture_count: int = 8
    min_item_count: int = 11
    score_snapshot_min: int = 0
    score_snapshot_max: int = SCORE_SCALE
    observation_only_notes: tuple[str, ...] = (
        "score_snapshot_is_data_quality_preflight_only",
        "display_bucket_is_review_grouping_only",
        "usable_for_future_list_is_not_ranking_flag",
        "no_actual_recommendation_list",
        "no_trade_directive",
    )
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
class RecommendationListFixtureHardeningResult:
    """Aggregate hardening result for deterministic list fixtures."""

    passed: bool
    failures: tuple[str, ...]
    checked_scenarios: tuple[str, ...]
    checked_item_count: int
    checked_item_statuses: tuple[str, ...]
    checked_display_buckets: tuple[str, ...]
    checked_component_names: tuple[str, ...]
    checked_score_snapshot_bounds: tuple[int, int]
    checked_required_false_flags: tuple[str, ...]
    checked_forbidden_output_absence: bool
    deterministic_repeated_run_passed: bool
    summary_stability_passed: bool
    evaluator_failure_injection_passed: bool
    observation_only_guardrail_passed: bool
    diagnostics: tuple[str, ...]


def build_recommendation_list_fixture_hardening_policy() -> (
    RecommendationListFixtureHardeningPolicy
):
    """Build the fixed MS-12.02 list fixture hardening policy."""

    build_recommendation_list_preflight_policy()
    build_scoring_preflight_policy()
    return RecommendationListFixtureHardeningPolicy()


def _expected_false_flags(
    policy: RecommendationListFixtureHardeningPolicy,
) -> tuple[str, ...]:
    return tuple(f"{flag}=false" for flag in policy.required_false_flags)


def _flatten_item_groups(
    groups: tuple[tuple[RecommendationListPreflightItem, ...], ...],
) -> tuple[RecommendationListPreflightItem, ...]:
    return tuple(item for group in groups for item in group)


@lru_cache(maxsize=1)
def _all_fixtures() -> tuple[RecommendationListFixtureRecord, ...]:
    return build_all_recommendation_list_fixtures()


@lru_cache(maxsize=1)
def _all_evaluations() -> tuple[RecommendationListFixtureEvaluationResult, ...]:
    return evaluate_all_recommendation_list_fixtures()


@lru_cache(maxsize=1)
def _all_list_items() -> tuple[RecommendationListPreflightItem, ...]:
    return _flatten_item_groups(build_recommendation_list_items_from_all_list_fixtures())


def _unique_in_allowed_order(
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(value for value in allowed_values if value in values)


def _component_names(
    items: tuple[RecommendationListPreflightItem, ...],
) -> tuple[str, ...]:
    return tuple(name for item in items for name in item.component_names)


def _actual_required_false_flags(
    items: tuple[RecommendationListPreflightItem, ...],
    policy: RecommendationListFixtureHardeningPolicy,
) -> tuple[str, ...]:
    return tuple(
        f"{flag}={str(any(bool(getattr(item.summary_flags, flag)) for item in items)).lower()}"
        for flag in policy.required_false_flags
    )


def check_recommendation_list_fixture_scenarios_present(
    policy: RecommendationListFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether all required list fixture scenarios are present."""

    active_policy = policy or build_recommendation_list_fixture_hardening_policy()
    scenarios = tuple(fixture.scenario for fixture in _all_fixtures())
    return (
        scenarios == active_policy.required_scenarios
        and len(scenarios) >= active_policy.min_fixture_count
        and "list_all_fixture_matrix" in scenarios
    )


def check_recommendation_list_fixture_score_snapshot_bounds(
    policy: RecommendationListFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether all score snapshots stay inside policy bounds."""

    active_policy = policy or build_recommendation_list_fixture_hardening_policy()
    snapshots = tuple(item.score_snapshot for item in _all_list_items())
    return bool(snapshots) and all(
        active_policy.score_snapshot_min <= snapshot <= active_policy.score_snapshot_max
        for snapshot in snapshots
    )


def check_recommendation_list_fixture_display_buckets(
    policy: RecommendationListFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether display buckets are allowed review grouping labels."""

    active_policy = policy or build_recommendation_list_fixture_hardening_policy()
    buckets = tuple(item.display_bucket for item in _all_list_items())
    unique_buckets = _unique_in_allowed_order(
        buckets,
        active_policy.required_display_buckets,
    )
    return (
        unique_buckets == active_policy.required_display_buckets
        and all(bucket.endswith("_review") or bucket == "review_ready" for bucket in buckets)
        and not any(
            keyword in bucket
            for bucket in buckets
            for keyword in ("rank", "priority", "order")
        )
    )


def check_recommendation_list_fixture_component_names(
    policy: RecommendationListFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether list item component names are exactly the allowed set."""

    active_policy = policy or build_recommendation_list_fixture_hardening_policy()
    names = _unique_in_allowed_order(
        _component_names(_all_list_items()),
        active_policy.required_component_names,
    )
    return names == active_policy.required_component_names


def check_recommendation_list_fixture_required_flags_false(
    policy: RecommendationListFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether required external-capability flags stay false."""

    active_policy = policy or build_recommendation_list_fixture_hardening_policy()
    items = _all_list_items()
    return _actual_required_false_flags(items, active_policy) == _expected_false_flags(
        active_policy
    )


def check_recommendation_list_fixture_forbidden_output_absence(
    policy: RecommendationListFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether list outputs omit forbidden assignment-form keywords."""

    active_policy = policy or build_recommendation_list_fixture_hardening_policy()
    rendered = repr(_all_list_items()) + repr(_all_evaluations())
    return not any(
        keyword in rendered for keyword in active_policy.forbidden_output_keywords
    )


def check_recommendation_list_fixture_deterministic_repeated_runs(
    policy: RecommendationListFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether repeated list fixture evaluations are identical."""

    active_policy = policy or build_recommendation_list_fixture_hardening_policy()
    first = evaluate_all_recommendation_list_fixtures()
    for _index in range(active_policy.deterministic_repeat_count - 1):
        if evaluate_all_recommendation_list_fixtures() != first:
            return False
    return True


def check_recommendation_list_fixture_summary_stability(
    policy: RecommendationListFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether list summary aggregation is stable."""

    active_policy = policy or build_recommendation_list_fixture_hardening_policy()
    first_items = _all_list_items()
    first_summary = summarize_recommendation_list_preflight_items(first_items)
    for _index in range(active_policy.deterministic_repeat_count - 1):
        items = _all_list_items()
        if summarize_recommendation_list_preflight_items(items) != first_summary:
            return False
    return True


def build_recommendation_list_fixture_failure_probe() -> (
    RecommendationListFixtureRecord
):
    """Build an intentional mismatch probe for evaluator failure detection."""

    return replace(
        build_list_basic_ready_for_review_fixture(),
        expected_item_statuses=("item_empty_input",),
    )


def evaluate_recommendation_list_fixture_failure_probe() -> (
    RecommendationListFixtureEvaluationResult
):
    """Evaluate the intentional mismatch probe."""

    return evaluate_recommendation_list_fixture(
        build_recommendation_list_fixture_failure_probe()
    )


def _all_evaluators_passed(
    evaluations: tuple[RecommendationListFixtureEvaluationResult, ...],
) -> bool:
    return bool(evaluations) and all(evaluation.passed for evaluation in evaluations)


def _allowed_item_statuses_only(
    items: tuple[RecommendationListPreflightItem, ...],
    policy: RecommendationListFixtureHardeningPolicy,
) -> bool:
    statuses = tuple(item.item_status for item in items)
    produced_values = statuses + tuple(item.display_bucket for item in items)
    return all(status in policy.required_item_statuses for status in statuses) and not any(
        forbidden in produced_values for forbidden in policy.forbidden_status_keywords
    )


def _all_items_valid(
    items: tuple[RecommendationListPreflightItem, ...],
) -> bool:
    policy = build_recommendation_list_preflight_policy()
    return all(
        validate_recommendation_list_preflight_item(item, policy).valid
        for item in items
    )


def _observation_only_guardrail_passed(
    items: tuple[RecommendationListPreflightItem, ...],
    policy: RecommendationListFixtureHardeningPolicy,
) -> bool:
    produced_values = (
        tuple(item.item_status for item in items)
        + tuple(item.display_bucket for item in items)
        + tuple(name for item in items for name in item.component_names)
    )
    no_directive_value = not any(
        forbidden in produced_values for forbidden in policy.forbidden_status_keywords
    )
    no_ranking_fields = all(
        not hasattr(item, "rank")
        and not hasattr(item, "ranking_position")
        and not hasattr(item, "action")
        for item in items
    )
    warnings = tuple(warning for item in items for warning in item.warnings)
    has_snapshot_note = all(
        "score_snapshot_quality_preflight_only" in item.warnings for item in items
    )
    has_bucket_note = all(
        "display_bucket_review_group_only" in item.warnings for item in items
    )
    usable_flags_are_boolean = all(
        isinstance(item.usable_for_future_list, bool) for item in items
    )
    return (
        no_directive_value
        and no_ranking_fields
        and has_snapshot_note
        and has_bucket_note
        and usable_flags_are_boolean
        and "observation_item_preflight_only" in warnings
    )


def run_recommendation_list_fixture_hardening_checks(
    policy: RecommendationListFixtureHardeningPolicy | None = None,
) -> RecommendationListFixtureHardeningResult:
    """Run all deterministic MS-12.02 list fixture hardening checks."""

    active_policy = policy or build_recommendation_list_fixture_hardening_policy()
    fixtures = _all_fixtures()
    evaluations = _all_evaluations()
    items = _all_list_items()
    item_statuses = _unique_in_allowed_order(
        tuple(item.item_status for item in items),
        active_policy.required_item_statuses,
    )
    display_buckets = _unique_in_allowed_order(
        tuple(item.display_bucket for item in items),
        active_policy.required_display_buckets,
    )
    component_names = _unique_in_allowed_order(
        _component_names(items),
        active_policy.required_component_names,
    )
    snapshots = tuple(item.score_snapshot for item in items)
    snapshot_bounds = (min(snapshots), max(snapshots)) if snapshots else (0, 0)
    required_false_flags = _actual_required_false_flags(items, active_policy)
    forbidden_output_absence = (
        check_recommendation_list_fixture_forbidden_output_absence(active_policy)
    )
    deterministic_passed = (
        check_recommendation_list_fixture_deterministic_repeated_runs(active_policy)
    )
    summary_passed = check_recommendation_list_fixture_summary_stability(
        active_policy
    )
    failure_probe = evaluate_recommendation_list_fixture_failure_probe()
    failure_probe_passed = (not failure_probe.passed) and bool(
        failure_probe.failures
    )
    observation_passed = _observation_only_guardrail_passed(items, active_policy)

    failures: list[str] = []
    if not check_recommendation_list_fixture_scenarios_present(active_policy):
        failures.append("required_recommendation_list_fixture_scenarios_missing")
    if not _all_evaluators_passed(evaluations):
        failures.append("recommendation_list_fixture_evaluator_failed")
    if "list_all_fixture_matrix" not in tuple(fixture.scenario for fixture in fixtures):
        failures.append("list_all_fixture_matrix_missing")
    if len(items) < active_policy.min_item_count:
        failures.append("minimum_list_item_count_not_met")
    if not check_recommendation_list_fixture_score_snapshot_bounds(active_policy):
        failures.append("score_snapshot_bounds_failed")
    if not check_recommendation_list_fixture_display_buckets(active_policy):
        failures.append("display_bucket_guardrail_failed")
    if not check_recommendation_list_fixture_component_names(active_policy):
        failures.append("component_names_failed")
    if not _allowed_item_statuses_only(items, active_policy):
        failures.append("allowed_item_status_check_failed")
    if not forbidden_output_absence:
        failures.append("forbidden_output_keyword_present")
    if not check_recommendation_list_fixture_required_flags_false(active_policy):
        failures.append("required_false_flags_failed")
    if not deterministic_passed:
        failures.append("deterministic_repeated_run_failed")
    if not summary_passed:
        failures.append("summary_stability_failed")
    if not failure_probe_passed:
        failures.append("evaluator_failure_probe_failed")
    if not observation_passed:
        failures.append("observation_only_guardrail_failed")
    if not _all_items_valid(items):
        failures.append("invalid_recommendation_list_preflight_item")

    diagnostics = (
        "recommendation_list_fixture_hardening_complete",
        "score_snapshot_data_quality_preflight_only",
        "display_bucket_review_grouping_only",
        "usable_for_future_list_not_ranking_flag",
        "no_actual_recommendation_ranking_action_output",
        "pure_no_io_in_memory_contract_only",
    )

    return RecommendationListFixtureHardeningResult(
        passed=not failures,
        failures=tuple(failures),
        checked_scenarios=tuple(fixture.scenario for fixture in fixtures),
        checked_item_count=len(items),
        checked_item_statuses=item_statuses,
        checked_display_buckets=display_buckets,
        checked_component_names=component_names,
        checked_score_snapshot_bounds=snapshot_bounds,
        checked_required_false_flags=required_false_flags,
        checked_forbidden_output_absence=forbidden_output_absence,
        deterministic_repeated_run_passed=deterministic_passed,
        summary_stability_passed=summary_passed,
        evaluator_failure_injection_passed=failure_probe_passed,
        observation_only_guardrail_passed=observation_passed,
        diagnostics=diagnostics,
    )


def build_list_items_for_hardening_probe(
    fixture: RecommendationListFixtureRecord,
) -> tuple[RecommendationListPreflightItem, ...]:
    """Expose existing fixture item path for hardening tests."""

    return build_recommendation_list_items_from_fixture(fixture)
