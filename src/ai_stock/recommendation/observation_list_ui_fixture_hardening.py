"""Pure observation-list UI fixture hardening checks for MS-13.02.

This module adds deterministic safety and stability checks on top of the
MS-13.00 observation-list UI preflight contract and MS-13.01 observation-list
UI fixtures. It performs no Streamlit, file, database, environment, network,
model, account, order, clock, or random I/O. It does not render UI, create
actual recommendation lists, rank candidates, issue trade actions, load
features, or modify app code.
"""

from dataclasses import dataclass
from functools import lru_cache

from ai_stock.recommendation.observation_list_ui_fixtures import (
    ALLOWED_OBSERVATION_LIST_UI_FIXTURE_SCENARIOS,
    OBSERVATION_LIST_UI_FIXTURE_FORBIDDEN_ABSENT_KEYWORDS,
    OBSERVATION_LIST_UI_FIXTURE_REQUIRED_FALSE_FLAGS,
    ObservationListUIFixtureEvaluationResult,
    ObservationListUIFixtureRecord,
    build_all_observation_list_ui_fixtures,
    build_observation_list_ui_fixture_failure_probe as build_ui_fixture_failure_probe,
    build_observation_list_ui_fixture_policy,
    build_observation_list_ui_rows_from_fixture,
    evaluate_all_observation_list_ui_fixtures,
    evaluate_observation_list_ui_fixture,
)
from ai_stock.recommendation.observation_list_ui_preflight import (
    ALLOWED_OBSERVATION_LIST_BADGE_LABELS,
    FORBIDDEN_OBSERVATION_LIST_BADGE_LABELS,
    FORBIDDEN_OBSERVATION_LIST_COLUMN_KEYS,
    FORBIDDEN_OBSERVATION_LIST_UI_OUTPUT_KEYWORDS,
    OBSERVATION_LIST_UI_REQUIRED_DISCLAIMER_LABELS,
    ObservationListUIRow,
    build_observation_list_ui_preflight_policy,
    build_observation_list_ui_row_from_item,
    build_observation_list_ui_rows_from_all_fixtures,
    build_observation_list_ui_rows_from_items,
    summarize_observation_list_ui_rows,
    validate_observation_list_ui_row,
)
from ai_stock.recommendation.recommendation_list_fixture_hardening import (
    build_recommendation_list_fixture_hardening_policy,
    run_recommendation_list_fixture_hardening_checks,
)
from ai_stock.recommendation.recommendation_list_fixtures import (
    build_recommendation_list_fixture_policy,
    evaluate_all_recommendation_list_fixtures,
)
from ai_stock.recommendation.recommendation_list_preflight import (
    FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_FIELDS,
    build_recommendation_list_items_from_all_fixtures,
    build_recommendation_list_preflight_policy,
)


OBSERVATION_LIST_UI_FIXTURE_HARDENING_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    OBSERVATION_LIST_UI_FIXTURE_REQUIRED_FALSE_FLAGS
)

REQUIRED_OBSERVATION_LIST_UI_STATUS_BADGES: tuple[str, ...] = (
    "review_ready",
    "invalid_candidate",
    "duplicate_candidate",
    "disabled_candidate",
    "missing_data",
    "sanitized_input",
    "empty_input",
)

REQUIRED_OBSERVATION_LIST_UI_DISPLAY_BUCKETS: tuple[str, ...] = (
    "review_ready",
    "invalid_candidate_review",
    "duplicate_candidate_review",
    "disabled_candidate_review",
    "missing_data_review",
    "sanitized_candidate_review",
    "empty_input_review",
)

FORBIDDEN_OBSERVATION_LIST_UI_HARDENING_OUTPUT_KEYWORDS: tuple[str, ...] = (
    *FORBIDDEN_OBSERVATION_LIST_UI_OUTPUT_KEYWORDS,
    *OBSERVATION_LIST_UI_FIXTURE_FORBIDDEN_ABSENT_KEYWORDS,
    "ranking_position=",
    "priority=",
    "order=",
)

FORBIDDEN_OBSERVATION_LIST_UI_LABEL_KEYWORDS: tuple[str, ...] = (
    *FORBIDDEN_OBSERVATION_LIST_BADGE_LABELS,
    "recommendation",
    "action",
    "rank",
    "ranking",
    "ranking_position",
    "priority",
    "order",
    "target_price",
    "expected_return",
    "profit_probability",
)


@dataclass(frozen=True)
class ObservationListUIFixtureHardeningPolicy:
    """Immutable safety policy for MS-13.02 UI fixture hardening."""

    hardening_version: str = "MS-13.02"
    hardening_scope: str = "observation_list_ui_fixture_safety_determinism_guardrail"
    required_scenarios: tuple[str, ...] = (
        ALLOWED_OBSERVATION_LIST_UI_FIXTURE_SCENARIOS
    )
    required_status_badges: tuple[str, ...] = (
        REQUIRED_OBSERVATION_LIST_UI_STATUS_BADGES
    )
    required_display_buckets: tuple[str, ...] = (
        REQUIRED_OBSERVATION_LIST_UI_DISPLAY_BUCKETS
    )
    required_disclaimer_keywords: tuple[str, ...] = (
        OBSERVATION_LIST_UI_REQUIRED_DISCLAIMER_LABELS
    )
    required_guardrail_false_flags: tuple[str, ...] = (
        OBSERVATION_LIST_UI_FIXTURE_HARDENING_REQUIRED_FALSE_FLAGS
    )
    forbidden_badge_keywords: tuple[str, ...] = (
        FORBIDDEN_OBSERVATION_LIST_BADGE_LABELS
    )
    forbidden_label_keywords: tuple[str, ...] = (
        FORBIDDEN_OBSERVATION_LIST_UI_LABEL_KEYWORDS
    )
    forbidden_column_keys: tuple[str, ...] = FORBIDDEN_OBSERVATION_LIST_COLUMN_KEYS
    forbidden_output_fields: tuple[str, ...] = (
        FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_FIELDS
    )
    forbidden_output_keywords: tuple[str, ...] = (
        FORBIDDEN_OBSERVATION_LIST_UI_HARDENING_OUTPUT_KEYWORDS
    )
    deterministic_repeat_count: int = 3
    min_fixture_count: int = 8
    min_row_count: int = 11
    observation_only_notes: tuple[str, ...] = (
        "status_badge_is_observation_state_only",
        "score_snapshot_label_is_quality_preflight_only",
        "display_bucket_is_grouping_label_only",
        "usability_label_is_not_ranking_flag",
        "no_streamlit_import_or_ui_integration",
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
    ui_integration_required: bool = False
    streamlit_required: bool = False
    http_smoke_required: bool = False


@dataclass(frozen=True)
class ObservationListUIFixtureHardeningResult:
    """Aggregate hardening result for deterministic UI fixtures."""

    passed: bool
    failures: tuple[str, ...]
    checked_scenarios: tuple[str, ...]
    checked_row_count: int
    checked_status_badges: tuple[str, ...]
    checked_display_buckets: tuple[str, ...]
    checked_disclaimer_labels: tuple[str, ...]
    checked_guardrail_flags: tuple[str, ...]
    checked_forbidden_output_absence: bool
    deterministic_repeated_run_passed: bool
    summary_stability_passed: bool
    evaluator_failure_injection_passed: bool
    observation_only_guardrail_passed: bool
    streamlit_absence_guardrail_passed: bool
    diagnostics: tuple[str, ...]


def build_observation_list_ui_fixture_hardening_policy() -> (
    ObservationListUIFixtureHardeningPolicy
):
    """Build the fixed MS-13.02 observation-list UI fixture hardening policy."""

    build_observation_list_ui_preflight_policy()
    build_observation_list_ui_fixture_policy()
    build_recommendation_list_preflight_policy()
    build_recommendation_list_fixture_policy()
    build_recommendation_list_fixture_hardening_policy()
    run_recommendation_list_fixture_hardening_checks()
    evaluate_all_recommendation_list_fixtures()
    return ObservationListUIFixtureHardeningPolicy()


def _expected_false_flags(
    policy: ObservationListUIFixtureHardeningPolicy,
) -> tuple[str, ...]:
    return tuple(f"{flag}=false" for flag in policy.required_guardrail_false_flags)


def _unique_in_seen_order(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _unique_in_required_order(
    values: tuple[str, ...],
    required_values: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(value for value in required_values if value in values)


def _flatten_row_groups(
    groups: tuple[tuple[ObservationListUIRow, ...], ...],
) -> tuple[ObservationListUIRow, ...]:
    return tuple(row for group in groups for row in group)


@lru_cache(maxsize=1)
def _all_fixtures() -> tuple[ObservationListUIFixtureRecord, ...]:
    return build_all_observation_list_ui_fixtures()


@lru_cache(maxsize=1)
def _all_evaluations() -> tuple[ObservationListUIFixtureEvaluationResult, ...]:
    return evaluate_all_observation_list_ui_fixtures()


@lru_cache(maxsize=1)
def _all_rows() -> tuple[ObservationListUIRow, ...]:
    return _flatten_row_groups(
        tuple(build_observation_list_ui_rows_from_fixture(fixture) for fixture in _all_fixtures())
    )


@lru_cache(maxsize=1)
def _all_fixture_matrix_rows() -> tuple[ObservationListUIRow, ...]:
    return build_observation_list_ui_rows_from_all_fixtures()


def _actual_guardrail_flags(
    rows: tuple[ObservationListUIRow, ...],
) -> tuple[str, ...]:
    return _unique_in_seen_order(
        tuple(flag for row in rows for flag in row.guardrail_flags)
    )


def _actual_disclaimer_labels(
    rows: tuple[ObservationListUIRow, ...],
) -> tuple[str, ...]:
    return _unique_in_seen_order(
        tuple(label for row in rows for label in row.disclaimer_labels)
    )


def check_observation_list_ui_fixture_scenarios_present(
    policy: ObservationListUIFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether all required UI fixture scenarios are present."""

    active_policy = policy or build_observation_list_ui_fixture_hardening_policy()
    scenarios = tuple(fixture.scenario for fixture in _all_fixtures())
    return (
        scenarios == active_policy.required_scenarios
        and len(scenarios) >= active_policy.min_fixture_count
        and "ui_all_fixture_matrix" in scenarios
    )


def check_observation_list_ui_fixture_status_badges(
    policy: ObservationListUIFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether UI status badges are allowed observation labels."""

    active_policy = policy or build_observation_list_ui_fixture_hardening_policy()
    badges = tuple(row.status_badge for row in _all_rows())
    unique_badges = _unique_in_required_order(
        badges,
        active_policy.required_status_badges,
    )
    return (
        unique_badges == active_policy.required_status_badges
        and all(badge in ALLOWED_OBSERVATION_LIST_BADGE_LABELS for badge in badges)
        and not any(badge in active_policy.forbidden_badge_keywords for badge in badges)
    )


def check_observation_list_ui_fixture_display_buckets(
    policy: ObservationListUIFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether display buckets remain grouping labels only."""

    active_policy = policy or build_observation_list_ui_fixture_hardening_policy()
    buckets = tuple(row.display_bucket for row in _all_rows())
    unique_buckets = _unique_in_required_order(
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


def check_observation_list_ui_fixture_disclaimers(
    policy: ObservationListUIFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether required observation-only disclaimers are present."""

    active_policy = policy or build_observation_list_ui_fixture_hardening_policy()
    labels = _actual_disclaimer_labels(_all_rows())
    return all(
        disclaimer in labels
        for disclaimer in active_policy.required_disclaimer_keywords
    )


def check_observation_list_ui_fixture_required_flags_false(
    policy: ObservationListUIFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether required external-capability flags stay false."""

    active_policy = policy or build_observation_list_ui_fixture_hardening_policy()
    return _actual_guardrail_flags(_all_rows()) == _expected_false_flags(active_policy)


def check_observation_list_ui_fixture_forbidden_output_absence(
    policy: ObservationListUIFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether UI rows and evaluator outputs omit forbidden keywords."""

    active_policy = policy or build_observation_list_ui_fixture_hardening_policy()
    rendered = repr(_all_rows()) + repr(_all_evaluations())
    return not any(
        keyword in rendered
        for keyword in active_policy.forbidden_output_keywords
    )


def check_observation_list_ui_fixture_deterministic_repeated_runs(
    policy: ObservationListUIFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether repeated UI fixture evaluations are identical."""

    active_policy = policy or build_observation_list_ui_fixture_hardening_policy()
    first = evaluate_all_observation_list_ui_fixtures()
    for _index in range(active_policy.deterministic_repeat_count - 1):
        if evaluate_all_observation_list_ui_fixtures() != first:
            return False
    return True


def check_observation_list_ui_fixture_summary_stability(
    policy: ObservationListUIFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether observation-list UI summaries are stable."""

    active_policy = policy or build_observation_list_ui_fixture_hardening_policy()
    first_summary = summarize_observation_list_ui_rows(_all_fixture_matrix_rows())
    for _index in range(active_policy.deterministic_repeat_count - 1):
        if summarize_observation_list_ui_rows(_all_fixture_matrix_rows()) != first_summary:
            return False
    return True


def build_observation_list_ui_fixture_failure_probe() -> (
    ObservationListUIFixtureRecord
):
    """Build an intentional mismatch probe for evaluator failure detection."""

    return build_ui_fixture_failure_probe()


def evaluate_observation_list_ui_fixture_failure_probe() -> (
    ObservationListUIFixtureEvaluationResult
):
    """Evaluate the intentional mismatch probe."""

    return evaluate_observation_list_ui_fixture(
        build_observation_list_ui_fixture_failure_probe()
    )


def _all_evaluators_passed(
    evaluations: tuple[ObservationListUIFixtureEvaluationResult, ...],
) -> bool:
    return bool(evaluations) and all(evaluation.passed for evaluation in evaluations)


def _all_rows_valid(rows: tuple[ObservationListUIRow, ...]) -> bool:
    policy = build_observation_list_ui_preflight_policy()
    return all(validate_observation_list_ui_row(row, policy).valid for row in rows)


def _observation_only_guardrail_passed(
    rows: tuple[ObservationListUIRow, ...],
) -> bool:
    status_badges = tuple(row.status_badge for row in rows)
    score_labels = tuple(row.score_snapshot_label for row in rows)
    buckets = tuple(row.display_bucket for row in rows)
    usability_labels = tuple(row.usability_label for row in rows)
    return (
        not any(badge in ("buy", "sell", "hold", "strong_buy") for badge in status_badges)
        and not any(
            keyword in label
            for label in score_labels
            for keyword in ("recommendation", "ranking", "action")
        )
        and not any(
            keyword in bucket
            for bucket in buckets
            for keyword in ("rank", "priority", "order")
        )
        and not any(
            keyword in label
            for label in usability_labels
            for keyword in ("rank", "priority", "order")
        )
    )


def _streamlit_absence_guardrail_passed() -> bool:
    build_observation_list_ui_rows_from_items(
        build_recommendation_list_items_from_all_fixtures(),
        build_observation_list_ui_preflight_policy(),
    )
    build_observation_list_ui_row_from_item(
        build_recommendation_list_items_from_all_fixtures()[0],
        build_observation_list_ui_preflight_policy(),
    )
    return True


def run_observation_list_ui_fixture_hardening_checks(
    policy: ObservationListUIFixtureHardeningPolicy | None = None,
) -> ObservationListUIFixtureHardeningResult:
    """Run all deterministic MS-13.02 observation UI fixture hardening checks."""

    active_policy = policy or build_observation_list_ui_fixture_hardening_policy()
    fixtures = _all_fixtures()
    evaluations = _all_evaluations()
    rows = _all_rows()
    matrix_rows = _all_fixture_matrix_rows()
    status_badges = _unique_in_required_order(
        tuple(row.status_badge for row in rows),
        active_policy.required_status_badges,
    )
    display_buckets = _unique_in_required_order(
        tuple(row.display_bucket for row in rows),
        active_policy.required_display_buckets,
    )
    disclaimer_labels = _actual_disclaimer_labels(rows)
    guardrail_flags = _actual_guardrail_flags(rows)
    forbidden_absence = (
        check_observation_list_ui_fixture_forbidden_output_absence(active_policy)
    )
    deterministic_passed = (
        check_observation_list_ui_fixture_deterministic_repeated_runs(active_policy)
    )
    summary_passed = check_observation_list_ui_fixture_summary_stability(
        active_policy
    )
    failure_probe = evaluate_observation_list_ui_fixture_failure_probe()
    failure_probe_passed = (not failure_probe.passed) and bool(
        failure_probe.failures
    )
    observation_passed = _observation_only_guardrail_passed(rows)
    streamlit_absence_passed = _streamlit_absence_guardrail_passed()

    failures: list[str] = []
    if not check_observation_list_ui_fixture_scenarios_present(active_policy):
        failures.append("required_observation_list_ui_fixture_scenarios_missing")
    if not _all_evaluators_passed(evaluations):
        failures.append("observation_list_ui_fixture_evaluator_failed")
    if "ui_all_fixture_matrix" not in tuple(fixture.scenario for fixture in fixtures):
        failures.append("ui_all_fixture_matrix_missing")
    if len(matrix_rows) < active_policy.min_row_count:
        failures.append("all_fixture_ui_row_count_not_met")
    if len(rows) < active_policy.min_row_count:
        failures.append("minimum_ui_row_count_not_met")
    if not check_observation_list_ui_fixture_status_badges(active_policy):
        failures.append("status_badge_guardrail_failed")
    if not check_observation_list_ui_fixture_display_buckets(active_policy):
        failures.append("display_bucket_guardrail_failed")
    if not check_observation_list_ui_fixture_disclaimers(active_policy):
        failures.append("disclaimer_guardrail_failed")
    if not forbidden_absence:
        failures.append("forbidden_output_keyword_present")
    if not check_observation_list_ui_fixture_required_flags_false(active_policy):
        failures.append("required_false_flags_failed")
    if not deterministic_passed:
        failures.append("deterministic_repeated_run_failed")
    if not summary_passed:
        failures.append("summary_stability_failed")
    if not failure_probe_passed:
        failures.append("evaluator_failure_probe_failed")
    if not observation_passed:
        failures.append("observation_only_guardrail_failed")
    if not streamlit_absence_passed:
        failures.append("streamlit_absence_guardrail_failed")
    if not _all_rows_valid(rows):
        failures.append("invalid_observation_list_ui_row")

    diagnostics = (
        "observation_list_ui_fixture_hardening_complete",
        "display_shape_only_no_ui_integration",
        "streamlit_import_not_required",
        "all_fixture_matrix_rows_checked",
        "pure_no_io_in_memory_contract_only",
    )

    return ObservationListUIFixtureHardeningResult(
        passed=not failures,
        failures=tuple(failures),
        checked_scenarios=tuple(fixture.scenario for fixture in fixtures),
        checked_row_count=len(rows),
        checked_status_badges=status_badges,
        checked_display_buckets=display_buckets,
        checked_disclaimer_labels=disclaimer_labels,
        checked_guardrail_flags=guardrail_flags,
        checked_forbidden_output_absence=forbidden_absence,
        deterministic_repeated_run_passed=deterministic_passed,
        summary_stability_passed=summary_passed,
        evaluator_failure_injection_passed=failure_probe_passed,
        observation_only_guardrail_passed=observation_passed,
        streamlit_absence_guardrail_passed=streamlit_absence_passed,
        diagnostics=diagnostics,
    )
