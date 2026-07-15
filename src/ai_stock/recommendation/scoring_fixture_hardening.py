"""Pure scoring fixture hardening checks for MS-11.02.

This module adds deterministic safety and stability checks on top of the
MS-11.00 scoring preflight contract and MS-11.01 scoring fixtures. It performs
no Streamlit, file, database, environment, network, model, account, order,
clock, or random I/O. It does not rank, recommend, trade, load features, or
render UI.
"""

from dataclasses import dataclass, replace

from ai_stock.recommendation.scoring_fixtures import (
    ALLOWED_SCORING_FIXTURE_SCENARIOS,
    FORBIDDEN_SCORING_OUTPUT_KEYWORDS,
    SCORING_FIXTURE_REQUIRED_FALSE_FLAGS,
    ScoringFixtureEvaluationResult,
    ScoringFixtureRecord,
    build_all_scoring_fixtures,
    build_scoring_basic_ready_fixture,
    build_scoring_fixture_policy,
    evaluate_all_scoring_fixtures,
    evaluate_scoring_fixture,
)
from ai_stock.recommendation.scoring_preflight import (
    ALLOWED_SCORE_COMPONENT_NAMES,
    ALLOWED_SCORING_STATUSES,
    FORBIDDEN_SCORING_ACTION_LABELS,
    FORBIDDEN_SCORING_OUTPUT_FIELDS,
    FORBIDDEN_SCORING_RECOMMENDATION_LABELS,
    FORBIDDEN_SCORING_SOURCES,
    SCORE_SCALE,
    ScoringPreflightResult,
    build_scoring_preflight_policy,
    score_extracted_feature_set_preflight,
    score_extracted_feature_sets_from_all_fixtures,
    score_extracted_feature_sets_from_fixture,
    summarize_scoring_preflight_results,
    validate_scoring_preflight_result,
)


SCORING_FIXTURE_HARDENING_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    SCORING_FIXTURE_REQUIRED_FALSE_FLAGS
)

FORBIDDEN_SCORING_HARDENING_OUTPUT_KEYWORDS: tuple[str, ...] = (
    FORBIDDEN_SCORING_OUTPUT_KEYWORDS
)


@dataclass(frozen=True)
class ScoringFixtureHardeningPolicy:
    """Immutable safety policy for MS-11.02 scoring fixture hardening."""

    hardening_version: str = "MS-11.02"
    hardening_scope: str = "scoring_fixture_safety_determinism_guardrail"
    required_scenarios: tuple[str, ...] = ALLOWED_SCORING_FIXTURE_SCENARIOS
    required_component_names: tuple[str, ...] = ALLOWED_SCORE_COMPONENT_NAMES
    required_statuses: tuple[str, ...] = ALLOWED_SCORING_STATUSES
    forbidden_status_keywords: tuple[str, ...] = (
        FORBIDDEN_SCORING_ACTION_LABELS
        + FORBIDDEN_SCORING_RECOMMENDATION_LABELS
    )
    forbidden_output_keywords: tuple[str, ...] = (
        FORBIDDEN_SCORING_HARDENING_OUTPUT_KEYWORDS
    )
    forbidden_output_fields: tuple[str, ...] = FORBIDDEN_SCORING_OUTPUT_FIELDS
    forbidden_scoring_sources: tuple[str, ...] = FORBIDDEN_SCORING_SOURCES
    required_false_flags: tuple[str, ...] = (
        SCORING_FIXTURE_HARDENING_REQUIRED_FALSE_FLAGS
    )
    deterministic_repeat_count: int = 3
    min_fixture_count: int = 8
    min_result_count: int = 11
    total_score_min: int = 0
    total_score_max: int = SCORE_SCALE
    observation_only_notes: tuple[str, ...] = (
        "total_score_is_data_quality_preflight_only",
        "no_recommendation_result",
        "no_ordered_candidate_list",
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
    scoring_required: bool = False
    ranking_required: bool = False
    recommendation_required: bool = False
    ui_required: bool = False
    streamlit_required: bool = False
    http_smoke_required: bool = False


@dataclass(frozen=True)
class ScoringFixtureHardeningResult:
    """Aggregate hardening result for deterministic scoring fixtures."""

    passed: bool
    failures: tuple[str, ...]
    checked_scenarios: tuple[str, ...]
    checked_result_count: int
    checked_statuses: tuple[str, ...]
    checked_component_names: tuple[str, ...]
    checked_total_score_bounds: tuple[int, int]
    checked_required_false_flags: tuple[str, ...]
    checked_forbidden_output_absence: bool
    deterministic_repeated_run_passed: bool
    summary_stability_passed: bool
    evaluator_failure_injection_passed: bool
    observation_only_guardrail_passed: bool
    diagnostics: tuple[str, ...]


def build_scoring_fixture_hardening_policy() -> ScoringFixtureHardeningPolicy:
    """Build the fixed MS-11.02 scoring fixture hardening policy."""

    build_scoring_preflight_policy()
    build_scoring_fixture_policy()
    return ScoringFixtureHardeningPolicy()


def _expected_false_flags(
    policy: ScoringFixtureHardeningPolicy,
) -> tuple[str, ...]:
    return tuple(f"{flag}=false" for flag in policy.required_false_flags)


def _flatten_result_groups(
    groups: tuple[tuple[ScoringPreflightResult, ...], ...],
) -> tuple[ScoringPreflightResult, ...]:
    return tuple(result for group in groups for result in group)


def _all_scoring_results() -> tuple[ScoringPreflightResult, ...]:
    return _flatten_result_groups(score_extracted_feature_sets_from_all_fixtures())


def _unique_in_allowed_order(
    values: tuple[str, ...],
    allowed_values: tuple[str, ...],
) -> tuple[str, ...]:
    return tuple(value for value in allowed_values if value in values)


def _component_names(
    results: tuple[ScoringPreflightResult, ...],
) -> tuple[str, ...]:
    return tuple(
        component.component_name
        for result in results
        for component in result.score_components
    )


def _actual_required_false_flags(
    results: tuple[ScoringPreflightResult, ...],
    policy: ScoringFixtureHardeningPolicy,
) -> tuple[str, ...]:
    return tuple(
        f"{flag}={str(any(bool(getattr(result.summary_flags, flag)) for result in results)).lower()}"
        for flag in policy.required_false_flags
    )


def check_scoring_fixture_scenarios_present(
    policy: ScoringFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether all required scoring fixture scenarios are present."""

    active_policy = policy or build_scoring_fixture_hardening_policy()
    scenarios = tuple(fixture.scenario for fixture in build_all_scoring_fixtures())
    return (
        scenarios == active_policy.required_scenarios
        and len(scenarios) >= active_policy.min_fixture_count
        and "scoring_all_fixture_matrix" in scenarios
    )


def check_scoring_fixture_total_score_bounds(
    policy: ScoringFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether all scoring preflight totals stay inside policy bounds."""

    active_policy = policy or build_scoring_fixture_hardening_policy()
    scores = tuple(result.total_score for result in _all_scoring_results())
    return bool(scores) and all(
        active_policy.total_score_min <= score <= active_policy.total_score_max
        for score in scores
    )


def check_scoring_fixture_component_names(
    policy: ScoringFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether score component names are exactly the allowed set."""

    active_policy = policy or build_scoring_fixture_hardening_policy()
    names = _unique_in_allowed_order(
        _component_names(_all_scoring_results()),
        active_policy.required_component_names,
    )
    return names == active_policy.required_component_names


def check_scoring_fixture_required_flags_false(
    policy: ScoringFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether required external-capability flags stay false."""

    active_policy = policy or build_scoring_fixture_hardening_policy()
    results = _all_scoring_results()
    return _actual_required_false_flags(results, active_policy) == _expected_false_flags(
        active_policy
    )


def check_scoring_fixture_forbidden_output_absence(
    policy: ScoringFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether scoring outputs omit forbidden assignment-form keywords."""

    active_policy = policy or build_scoring_fixture_hardening_policy()
    rendered = repr(_all_scoring_results()) + repr(evaluate_all_scoring_fixtures())
    return not any(
        keyword in rendered for keyword in active_policy.forbidden_output_keywords
    )


def check_scoring_fixture_deterministic_repeated_runs(
    policy: ScoringFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether repeated scoring fixture evaluations are identical."""

    active_policy = policy or build_scoring_fixture_hardening_policy()
    first = evaluate_all_scoring_fixtures()
    for _index in range(active_policy.deterministic_repeat_count - 1):
        if evaluate_all_scoring_fixtures() != first:
            return False
    return True


def check_scoring_fixture_summary_stability(
    policy: ScoringFixtureHardeningPolicy | None = None,
) -> bool:
    """Return whether summary aggregation is stable for identical inputs."""

    active_policy = policy or build_scoring_fixture_hardening_policy()
    first_results = _all_scoring_results()
    first_summary = summarize_scoring_preflight_results(first_results)
    for _index in range(active_policy.deterministic_repeat_count - 1):
        results = _all_scoring_results()
        if summarize_scoring_preflight_results(results) != first_summary:
            return False
    return True


def build_scoring_fixture_failure_probe() -> ScoringFixtureRecord:
    """Build an intentional mismatch probe for evaluator failure detection."""

    return replace(
        build_scoring_basic_ready_fixture(),
        expected_scoring_statuses=("score_empty_input",),
    )


def evaluate_scoring_fixture_failure_probe() -> ScoringFixtureEvaluationResult:
    """Evaluate the intentional mismatch probe."""

    return evaluate_scoring_fixture(build_scoring_fixture_failure_probe())


def _all_evaluators_passed(
    evaluations: tuple[ScoringFixtureEvaluationResult, ...],
) -> bool:
    return bool(evaluations) and all(evaluation.passed for evaluation in evaluations)


def _allowed_statuses_only(
    results: tuple[ScoringPreflightResult, ...],
    policy: ScoringFixtureHardeningPolicy,
) -> bool:
    statuses = tuple(result.scoring_status for result in results)
    component_statuses = tuple(
        component.component_status
        for result in results
        for component in result.score_components
    )
    return all(status in policy.required_statuses for status in statuses) and not any(
        forbidden in statuses or forbidden in component_statuses
        for forbidden in policy.forbidden_status_keywords
    )


def _all_results_valid(results: tuple[ScoringPreflightResult, ...]) -> bool:
    return all(
        validate_scoring_preflight_result(result).valid for result in results
    )


def _observation_only_guardrail_passed(
    results: tuple[ScoringPreflightResult, ...],
    policy: ScoringFixtureHardeningPolicy,
) -> bool:
    produced_values = tuple(result.scoring_status for result in results) + tuple(
        component.component_name
        for result in results
        for component in result.score_components
    )
    no_directive_value = not any(
        forbidden in produced_values for forbidden in policy.forbidden_status_keywords
    )
    warnings = tuple(warning for result in results for warning in result.score_warnings)
    has_observation_note = all(
        "quality_preflight_score_only" in result.score_warnings
        for result in results
    )
    return (
        no_directive_value
        and has_observation_note
        and "no_trade_directive" in warnings
    )


def run_scoring_fixture_hardening_checks(
    policy: ScoringFixtureHardeningPolicy | None = None,
) -> ScoringFixtureHardeningResult:
    """Run all deterministic MS-11.02 scoring fixture hardening checks."""

    active_policy = policy or build_scoring_fixture_hardening_policy()
    fixtures = build_all_scoring_fixtures()
    evaluations = evaluate_all_scoring_fixtures()
    results = _all_scoring_results()
    statuses = _unique_in_allowed_order(
        tuple(result.scoring_status for result in results),
        active_policy.required_statuses,
    )
    component_names = _unique_in_allowed_order(
        _component_names(results),
        active_policy.required_component_names,
    )
    scores = tuple(result.total_score for result in results)
    score_bounds = (min(scores), max(scores)) if scores else (0, 0)
    required_false_flags = _actual_required_false_flags(results, active_policy)
    forbidden_output_absence = check_scoring_fixture_forbidden_output_absence(
        active_policy
    )
    deterministic_passed = check_scoring_fixture_deterministic_repeated_runs(
        active_policy
    )
    summary_passed = check_scoring_fixture_summary_stability(active_policy)
    failure_probe = evaluate_scoring_fixture_failure_probe()
    failure_probe_passed = (not failure_probe.passed) and bool(
        failure_probe.failures
    )
    observation_passed = _observation_only_guardrail_passed(
        results,
        active_policy,
    )

    failures: list[str] = []
    if not check_scoring_fixture_scenarios_present(active_policy):
        failures.append("required_scoring_fixture_scenarios_missing")
    if not _all_evaluators_passed(evaluations):
        failures.append("scoring_fixture_evaluator_failed")
    if "scoring_all_fixture_matrix" not in tuple(
        fixture.scenario for fixture in fixtures
    ):
        failures.append("scoring_all_fixture_matrix_missing")
    if len(results) < active_policy.min_result_count:
        failures.append("minimum_scoring_result_count_not_met")
    if not check_scoring_fixture_total_score_bounds(active_policy):
        failures.append("total_score_bounds_failed")
    if not check_scoring_fixture_component_names(active_policy):
        failures.append("score_component_names_failed")
    if not _allowed_statuses_only(results, active_policy):
        failures.append("allowed_scoring_status_check_failed")
    if not forbidden_output_absence:
        failures.append("forbidden_output_keyword_present")
    if not check_scoring_fixture_required_flags_false(active_policy):
        failures.append("required_false_flags_failed")
    if not deterministic_passed:
        failures.append("deterministic_repeated_run_failed")
    if not summary_passed:
        failures.append("summary_stability_failed")
    if not failure_probe_passed:
        failures.append("evaluator_failure_probe_failed")
    if not observation_passed:
        failures.append("observation_only_guardrail_failed")
    if not _all_results_valid(results):
        failures.append("invalid_scoring_preflight_result")

    diagnostics = (
        "scoring_fixture_hardening_complete",
        "total_score_data_quality_preflight_only",
        "no_recommendation_ranking_action_output",
        "pure_no_io_in_memory_contract_only",
    )

    return ScoringFixtureHardeningResult(
        passed=not failures,
        failures=tuple(failures),
        checked_scenarios=tuple(fixture.scenario for fixture in fixtures),
        checked_result_count=len(results),
        checked_statuses=statuses,
        checked_component_names=component_names,
        checked_total_score_bounds=score_bounds,
        checked_required_false_flags=required_false_flags,
        checked_forbidden_output_absence=forbidden_output_absence,
        deterministic_repeated_run_passed=deterministic_passed,
        summary_stability_passed=summary_passed,
        evaluator_failure_injection_passed=failure_probe_passed,
        observation_only_guardrail_passed=observation_passed,
        diagnostics=diagnostics,
    )


def score_extracted_feature_set_for_hardening_probe(
    feature_set: object,
) -> ScoringPreflightResult:
    """Expose existing single-result scoring path for hardening tests."""

    return score_extracted_feature_set_preflight(feature_set)


def score_fixture_for_hardening_probe(
    fixture: object,
) -> tuple[ScoringPreflightResult, ...]:
    """Expose existing fixture scoring path for hardening tests."""

    return score_extracted_feature_sets_from_fixture(fixture)
