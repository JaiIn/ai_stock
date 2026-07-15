"""Pure scoring fixture expansion for MS-11.01.

This module defines deterministic in-memory scoring fixture expectations on
top of the MS-11.00 scoring preflight contract. It performs no Streamlit,
file, database, environment, network, model, account, order, clock, or random
I/O. It does not rank, recommend, trade, load features, or render UI.
"""

from dataclasses import dataclass
from enum import Enum

from ai_stock.recommendation.feature_extraction_fixtures import (
    build_all_feature_extraction_fixtures,
    evaluate_all_feature_extraction_fixtures,
)
from ai_stock.recommendation.scoring_preflight import (
    ALLOWED_SCORE_COMPONENT_NAMES,
    ALLOWED_SCORING_STATUSES,
    FORBIDDEN_SCORING_OUTPUT_FIELDS,
    FORBIDDEN_SCORING_SOURCES,
    SCORE_SCALE,
    SCORING_PREFLIGHT_REQUIRED_FALSE_FLAGS,
    ScoringPreflightResult,
    build_scoring_preflight_policy,
    score_extracted_feature_sets_from_all_fixtures,
    score_extracted_feature_sets_from_feature_extraction_fixture,
    score_extracted_feature_sets_from_fixture,
    summarize_scoring_preflight_results,
    validate_scoring_preflight_result,
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


class ScoringFixtureScenario(str, Enum):
    """Allowed deterministic scoring fixture scenarios for MS-11.01."""

    SCORING_BASIC_READY = "scoring_basic_ready"
    SCORING_MIXED_REVIEW = "scoring_mixed_review"
    SCORING_DUPLICATES_BLOCKED = "scoring_duplicates_blocked"
    SCORING_DISABLED_BLOCKED = "scoring_disabled_blocked"
    SCORING_MISSING_DATA_BLOCKED = "scoring_missing_data_blocked"
    SCORING_FORBIDDEN_FIELD_SANITIZED = "scoring_forbidden_field_sanitized"
    SCORING_EMPTY_INPUT = "scoring_empty_input"
    SCORING_ALL_FIXTURE_MATRIX = "scoring_all_fixture_matrix"


ALLOWED_SCORING_FIXTURE_SCENARIOS: tuple[str, ...] = tuple(
    scenario.value for scenario in ScoringFixtureScenario
)

FORBIDDEN_SCORING_FIXTURE_SCENARIOS: tuple[str, ...] = (
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
    "recommendation_fixture",
    "ranking_fixture",
    "buy_sell_hold_fixture",
    "target_price_fixture",
    "expected_return_fixture",
)

SCORING_FIXTURE_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    SCORING_PREFLIGHT_REQUIRED_FALSE_FLAGS
)

FORBIDDEN_SCORING_OUTPUT_KEYWORDS: tuple[str, ...] = (
    "redacted-not-output",
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
    "target_price=",
    "expected_return=",
    "profit_probability=",
    "must_buy=",
    "must_sell=",
)


@dataclass(frozen=True)
class ScoringFixturePolicy:
    """Immutable fail-closed policy for MS-11.01 scoring fixtures."""

    stage_name: str = "MS-11.01"
    mode: str = "scoring_fixture_expansion"
    allowed_scenarios: tuple[str, ...] = ALLOWED_SCORING_FIXTURE_SCENARIOS
    forbidden_scenarios: tuple[str, ...] = FORBIDDEN_SCORING_FIXTURE_SCENARIOS
    allowed_scoring_statuses: tuple[str, ...] = ALLOWED_SCORING_STATUSES
    allowed_score_component_names: tuple[str, ...] = ALLOWED_SCORE_COMPONENT_NAMES
    forbidden_scoring_sources: tuple[str, ...] = FORBIDDEN_SCORING_SOURCES
    forbidden_output_fields: tuple[str, ...] = FORBIDDEN_SCORING_OUTPUT_FIELDS
    required_false_flags: tuple[str, ...] = SCORING_FIXTURE_REQUIRED_FALSE_FLAGS
    forbidden_absent_keywords: tuple[str, ...] = FORBIDDEN_SCORING_OUTPUT_KEYWORDS
    total_score_semantics: str = "data_quality_extraction_readiness_only"
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
class ScoringFixtureRecord:
    """Scoring fixture expectations without directive output fields."""

    scenario: str
    description: str
    source_fixture_name: str
    expected_scoring_statuses: tuple[str, ...]
    expected_ready_count: int
    expected_needs_review_count: int
    expected_usable_for_future_ranking_count: int
    expected_total_score_min: int
    expected_total_score_max: int
    expected_component_names: tuple[str, ...]
    expected_blocked_reason_keywords: tuple[str, ...]
    expected_warning_keywords: tuple[str, ...]
    expected_diagnostic_keywords: tuple[str, ...]
    expected_required_false_flags: tuple[str, ...]
    expected_forbidden_absent_keywords: tuple[str, ...]


@dataclass(frozen=True)
class ScoringFixtureEvaluationResult:
    """Expected-vs-actual evaluation result for one scoring fixture."""

    scenario: str
    passed: bool
    failures: tuple[str, ...]
    actual_scoring_statuses: tuple[str, ...]
    actual_ready_count: int
    actual_needs_review_count: int
    actual_usable_for_future_ranking_count: int
    actual_total_scores: tuple[int, ...]
    actual_score_components: tuple[str, ...]
    actual_blocked_reasons: tuple[str, ...]
    actual_warnings: tuple[str, ...]
    actual_diagnostics: tuple[str, ...]
    actual_required_flags: tuple[str, ...]
    forbidden_absent_check_passed: bool


def build_scoring_fixture_policy() -> ScoringFixturePolicy:
    """Build the fixed MS-11.01 scoring fixture expansion policy."""

    build_scoring_preflight_policy()
    evaluate_all_feature_extraction_fixtures()
    return ScoringFixturePolicy()


def _expected_false_flags() -> tuple[str, ...]:
    return tuple(f"{flag}=false" for flag in SCORING_FIXTURE_REQUIRED_FALSE_FLAGS)


def _fixture_record(
    *,
    scenario: ScoringFixtureScenario,
    description: str,
    source_fixture_name: str,
    expected_scoring_statuses: tuple[str, ...],
    expected_ready_count: int,
    expected_needs_review_count: int,
    expected_usable_for_future_ranking_count: int,
    expected_total_score_min: int,
    expected_total_score_max: int,
    expected_blocked_reason_keywords: tuple[str, ...] = (),
    expected_warning_keywords: tuple[str, ...] = (),
    expected_diagnostic_keywords: tuple[str, ...] = (),
) -> ScoringFixtureRecord:
    return ScoringFixtureRecord(
        scenario=scenario.value,
        description=description,
        source_fixture_name=source_fixture_name,
        expected_scoring_statuses=expected_scoring_statuses,
        expected_ready_count=expected_ready_count,
        expected_needs_review_count=expected_needs_review_count,
        expected_usable_for_future_ranking_count=(
            expected_usable_for_future_ranking_count
        ),
        expected_total_score_min=expected_total_score_min,
        expected_total_score_max=expected_total_score_max,
        expected_component_names=ALLOWED_SCORE_COMPONENT_NAMES,
        expected_blocked_reason_keywords=expected_blocked_reason_keywords,
        expected_warning_keywords=expected_warning_keywords,
        expected_diagnostic_keywords=expected_diagnostic_keywords,
        expected_required_false_flags=_expected_false_flags(),
        expected_forbidden_absent_keywords=FORBIDDEN_SCORING_OUTPUT_KEYWORDS,
    )


def build_scoring_basic_ready_fixture() -> ScoringFixtureRecord:
    """Build expectations for valid manual scoring readiness."""

    return _fixture_record(
        scenario=ScoringFixtureScenario.SCORING_BASIC_READY,
        description="Valid manual symbols produce ready preflight scores.",
        source_fixture_name="basic_manual_symbols",
        expected_scoring_statuses=("score_ready", "score_ready"),
        expected_ready_count=2,
        expected_needs_review_count=0,
        expected_usable_for_future_ranking_count=2,
        expected_total_score_min=SCORE_SCALE,
        expected_total_score_max=SCORE_SCALE,
        expected_warning_keywords=(
            "quality_preflight_score_only",
            "no_trade_directive",
        ),
        expected_diagnostic_keywords=("deterministic_in_memory_score_shape",),
    )


def build_scoring_mixed_review_fixture() -> ScoringFixtureRecord:
    """Build expectations for mixed valid and invalid scoring input."""

    return _fixture_record(
        scenario=ScoringFixtureScenario.SCORING_MIXED_REVIEW,
        description="Invalid symbols remain review-only score states.",
        source_fixture_name="mixed_valid_invalid_symbols",
        expected_scoring_statuses=(
            "score_ready",
            "score_invalid_candidate",
            "score_invalid_candidate",
        ),
        expected_ready_count=1,
        expected_needs_review_count=2,
        expected_usable_for_future_ranking_count=1,
        expected_total_score_min=20,
        expected_total_score_max=SCORE_SCALE,
        expected_blocked_reason_keywords=("quality_invalid_candidate",),
        expected_warning_keywords=("invalid_symbol_review",),
        expected_diagnostic_keywords=(
            "symbol_required",
            "symbol_must_be_safe_ascii_identifier",
        ),
    )


def build_scoring_duplicates_blocked_fixture() -> ScoringFixtureRecord:
    """Build expectations for duplicate scoring blocking."""

    return _fixture_record(
        scenario=ScoringFixtureScenario.SCORING_DUPLICATES_BLOCKED,
        description="Duplicate candidates are blocked for future ranking.",
        source_fixture_name="duplicates_and_disabled",
        expected_scoring_statuses=(
            "score_ready",
            "score_duplicate_candidate",
            "score_disabled_candidate",
        ),
        expected_ready_count=1,
        expected_needs_review_count=2,
        expected_usable_for_future_ranking_count=1,
        expected_total_score_min=20,
        expected_total_score_max=SCORE_SCALE,
        expected_blocked_reason_keywords=("quality_duplicate_candidate",),
        expected_warning_keywords=("duplicate_candidate_needs_review",),
        expected_diagnostic_keywords=("duplicate_symbol",),
    )


def build_scoring_disabled_blocked_fixture() -> ScoringFixtureRecord:
    """Build expectations for disabled scoring blocking."""

    return _fixture_record(
        scenario=ScoringFixtureScenario.SCORING_DISABLED_BLOCKED,
        description="Disabled candidates are non-ready score states.",
        source_fixture_name="duplicates_and_disabled",
        expected_scoring_statuses=(
            "score_ready",
            "score_duplicate_candidate",
            "score_disabled_candidate",
        ),
        expected_ready_count=1,
        expected_needs_review_count=2,
        expected_usable_for_future_ranking_count=1,
        expected_total_score_min=20,
        expected_total_score_max=SCORE_SCALE,
        expected_blocked_reason_keywords=("quality_disabled_candidate",),
        expected_warning_keywords=("disabled_candidate_not_selectable",),
        expected_diagnostic_keywords=("candidate_disabled",),
    )


def build_scoring_missing_data_blocked_fixture() -> ScoringFixtureRecord:
    """Build expectations for missing data scoring blocking."""

    return _fixture_record(
        scenario=ScoringFixtureScenario.SCORING_MISSING_DATA_BLOCKED,
        description="Insufficient data remains blocked for score readiness.",
        source_fixture_name="insufficient_data_review",
        expected_scoring_statuses=("score_missing_data",),
        expected_ready_count=0,
        expected_needs_review_count=1,
        expected_usable_for_future_ranking_count=0,
        expected_total_score_min=20,
        expected_total_score_max=20,
        expected_blocked_reason_keywords=("quality_insufficient_data",),
        expected_warning_keywords=(
            "insufficient_data_review",
            "missing_feature_review",
        ),
        expected_diagnostic_keywords=("extraction_missing_data",),
    )


def build_scoring_forbidden_field_sanitized_fixture() -> ScoringFixtureRecord:
    """Build expectations for forbidden-field sanitization scoring."""

    return _fixture_record(
        scenario=ScoringFixtureScenario.SCORING_FORBIDDEN_FIELD_SANITIZED,
        description="Forbidden fields remain diagnostics-only in scoring.",
        source_fixture_name="forbidden_fields_sanitized",
        expected_scoring_statuses=("score_forbidden_field_sanitized",),
        expected_ready_count=0,
        expected_needs_review_count=1,
        expected_usable_for_future_ranking_count=0,
        expected_total_score_min=0,
        expected_total_score_max=0,
        expected_blocked_reason_keywords=("quality_forbidden_field_sanitized",),
        expected_diagnostic_keywords=(
            "forbidden_field_detected:accountSeq",
            "forbidden_field_detected:target_price",
            "forbidden_field_detected:score",
            "forbidden_fields_reported_in_diagnostics_only",
            "forbidden_field_sanitized",
        ),
    )


def build_scoring_empty_input_fixture() -> ScoringFixtureRecord:
    """Build expectations for safe empty input scoring."""

    return _fixture_record(
        scenario=ScoringFixtureScenario.SCORING_EMPTY_INPUT,
        description="Empty watchlist input remains a safe score state.",
        source_fixture_name="empty_watchlist",
        expected_scoring_statuses=("score_empty_input",),
        expected_ready_count=0,
        expected_needs_review_count=1,
        expected_usable_for_future_ranking_count=0,
        expected_total_score_min=20,
        expected_total_score_max=20,
        expected_blocked_reason_keywords=("quality_empty_input",),
        expected_warning_keywords=(
            "empty_watchlist_safe_state",
            "missing_feature_review",
        ),
        expected_diagnostic_keywords=("empty_source_items",),
    )


def build_scoring_all_fixture_matrix() -> ScoringFixtureRecord:
    """Build expectations for the complete scoring fixture matrix."""

    return _fixture_record(
        scenario=ScoringFixtureScenario.SCORING_ALL_FIXTURE_MATRIX,
        description="All MS-09.04 fixtures produce safe score states.",
        source_fixture_name="all_ms09_fixture_matrix",
        expected_scoring_statuses=(
            "score_ready",
            "score_ready",
            "score_ready",
            "score_invalid_candidate",
            "score_invalid_candidate",
            "score_ready",
            "score_duplicate_candidate",
            "score_disabled_candidate",
            "score_missing_data",
            "score_forbidden_field_sanitized",
            "score_empty_input",
        ),
        expected_ready_count=4,
        expected_needs_review_count=7,
        expected_usable_for_future_ranking_count=4,
        expected_total_score_min=0,
        expected_total_score_max=SCORE_SCALE,
        expected_blocked_reason_keywords=(
            "quality_invalid_candidate",
            "quality_duplicate_candidate",
            "quality_disabled_candidate",
            "quality_insufficient_data",
            "quality_forbidden_field_sanitized",
            "quality_empty_input",
        ),
        expected_warning_keywords=(
            "quality_preflight_score_only",
            "no_trade_directive",
            "invalid_symbol_review",
            "duplicate_candidate_needs_review",
            "disabled_candidate_not_selectable",
            "insufficient_data_review",
            "empty_watchlist_safe_state",
        ),
        expected_diagnostic_keywords=(
            "deterministic_in_memory_score_shape",
            "symbol_required",
            "duplicate_symbol",
            "candidate_disabled",
            "forbidden_field_detected:accountSeq",
            "empty_source_items",
        ),
    )


def build_all_scoring_fixtures() -> tuple[ScoringFixtureRecord, ...]:
    """Build every deterministic MS-11.01 scoring fixture."""

    return (
        build_scoring_basic_ready_fixture(),
        build_scoring_mixed_review_fixture(),
        build_scoring_duplicates_blocked_fixture(),
        build_scoring_disabled_blocked_fixture(),
        build_scoring_missing_data_blocked_fixture(),
        build_scoring_forbidden_field_sanitized_fixture(),
        build_scoring_empty_input_fixture(),
        build_scoring_all_fixture_matrix(),
    )


def _source_fixture_by_name(source_fixture_name: str) -> WatchlistFixtureRecord:
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


def _flatten_result_groups(
    groups: tuple[tuple[ScoringPreflightResult, ...], ...],
) -> tuple[ScoringPreflightResult, ...]:
    return tuple(result for group in groups for result in group)


def _scoring_results_for_fixture(
    fixture: ScoringFixtureRecord,
) -> tuple[ScoringPreflightResult, ...]:
    policy = build_scoring_preflight_policy()
    build_all_feature_extraction_fixtures()
    if fixture.source_fixture_name == "all_ms09_fixture_matrix":
        return _flatten_result_groups(
            score_extracted_feature_sets_from_all_fixtures(policy)
        )
    return score_extracted_feature_sets_from_fixture(
        _source_fixture_by_name(fixture.source_fixture_name),
        policy,
    )


def _actual_false_flags(
    results: tuple[ScoringPreflightResult, ...],
) -> tuple[str, ...]:
    return tuple(
        f"{flag}={str(any(bool(getattr(result.summary_flags, flag)) for result in results)).lower()}"
        for flag in SCORING_FIXTURE_REQUIRED_FALSE_FLAGS
    )


def _flatten_component_names(
    results: tuple[ScoringPreflightResult, ...],
) -> tuple[str, ...]:
    return tuple(
        component.component_name
        for result in results
        for component in result.score_components
    )


def _unique_component_names(
    results: tuple[ScoringPreflightResult, ...],
) -> tuple[str, ...]:
    names = _flatten_component_names(results)
    return tuple(name for name in ALLOWED_SCORE_COMPONENT_NAMES if name in names)


def evaluate_scoring_fixture(
    fixture: ScoringFixtureRecord,
) -> ScoringFixtureEvaluationResult:
    """Compare MS-11.01 fixture expectations with scoring outputs."""

    results = _scoring_results_for_fixture(fixture)
    summary = summarize_scoring_preflight_results(results)
    actual_scoring_statuses = tuple(result.scoring_status for result in results)
    actual_total_scores = tuple(result.total_score for result in results)
    actual_score_components = _unique_component_names(results)
    actual_blocked_reasons = tuple(
        reason for result in results for reason in result.blocked_reasons
    )
    actual_warnings = tuple(
        warning for result in results for warning in result.score_warnings
    )
    actual_warnings += tuple(
        warning
        for result in results
        for component in result.score_components
        for warning in component.warnings
    )
    actual_diagnostics = tuple(
        diagnostic for result in results for diagnostic in result.diagnostics
    )
    actual_diagnostics += tuple(
        diagnostic
        for result in results
        for component in result.score_components
        for diagnostic in component.diagnostics
    )
    actual_required_flags = _actual_false_flags(results)
    validation_results = tuple(
        validate_scoring_preflight_result(result) for result in results
    )
    rendered_results = repr(results)
    forbidden_absent_check_passed = not any(
        keyword in rendered_results
        for keyword in fixture.expected_forbidden_absent_keywords
    )

    failures: list[str] = []
    if actual_scoring_statuses != fixture.expected_scoring_statuses:
        failures.append("scoring_statuses_mismatch")
    if summary.ready_results != fixture.expected_ready_count:
        failures.append("ready_count_mismatch")
    if summary.needs_review_results != fixture.expected_needs_review_count:
        failures.append("needs_review_count_mismatch")
    if (
        summary.usable_for_future_ranking_results
        != fixture.expected_usable_for_future_ranking_count
    ):
        failures.append("usable_for_future_ranking_count_mismatch")
    if actual_total_scores:
        if min(actual_total_scores) < fixture.expected_total_score_min:
            failures.append("total_score_min_mismatch")
        if max(actual_total_scores) > fixture.expected_total_score_max:
            failures.append("total_score_max_mismatch")
    elif fixture.expected_total_score_min != 0:
        failures.append("total_score_min_mismatch")
    if actual_score_components != fixture.expected_component_names:
        failures.append("score_component_names_mismatch")
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
                f"invalid_scoring_preflight_result:{reason}"
                for reason in validation.rejection_reasons
            )

    return ScoringFixtureEvaluationResult(
        scenario=fixture.scenario,
        passed=not failures,
        failures=tuple(failures),
        actual_scoring_statuses=actual_scoring_statuses,
        actual_ready_count=summary.ready_results,
        actual_needs_review_count=summary.needs_review_results,
        actual_usable_for_future_ranking_count=(
            summary.usable_for_future_ranking_results
        ),
        actual_total_scores=actual_total_scores,
        actual_score_components=actual_score_components,
        actual_blocked_reasons=actual_blocked_reasons,
        actual_warnings=actual_warnings,
        actual_diagnostics=actual_diagnostics,
        actual_required_flags=actual_required_flags,
        forbidden_absent_check_passed=forbidden_absent_check_passed,
    )


def evaluate_all_scoring_fixtures() -> tuple[ScoringFixtureEvaluationResult, ...]:
    """Evaluate every deterministic MS-11.01 scoring fixture."""

    return tuple(
        evaluate_scoring_fixture(fixture) for fixture in build_all_scoring_fixtures()
    )


def score_extracted_feature_sets_from_scoring_fixture(
    fixture: ScoringFixtureRecord,
) -> tuple[ScoringPreflightResult, ...]:
    """Return scoring preflight outputs referenced by one scoring fixture."""

    if fixture.source_fixture_name == "all_ms09_fixture_matrix":
        return _flatten_result_groups(score_extracted_feature_sets_from_all_fixtures())
    return score_extracted_feature_sets_from_fixture(
        _source_fixture_by_name(fixture.source_fixture_name)
    )


def score_extracted_feature_sets_from_all_scoring_fixtures() -> (
    tuple[tuple[ScoringPreflightResult, ...], ...]
):
    """Return grouped scoring preflight outputs for every scoring fixture."""

    return tuple(
        score_extracted_feature_sets_from_scoring_fixture(fixture)
        for fixture in build_all_scoring_fixtures()
    )


def score_extracted_feature_sets_from_extraction_fixture_matrix() -> (
    tuple[tuple[ScoringPreflightResult, ...], ...]
):
    """Reuse MS-10.03 extraction fixture scoring for matrix verification."""

    return tuple(
        score_extracted_feature_sets_from_feature_extraction_fixture(fixture)
        for fixture in build_all_feature_extraction_fixtures()
    )
