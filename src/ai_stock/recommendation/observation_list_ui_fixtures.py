"""Pure observation-list UI fixture expansion for MS-13.01.

This module defines deterministic in-memory fixture expectations on top of the
MS-13.00 observation-list UI preflight contract. It performs no Streamlit,
file, database, environment, network, model, account, order, clock, or random
I/O. It does not render UI, create actual recommendation lists, rank
candidates, issue trade actions, load features, or modify app code.
"""

from dataclasses import dataclass, replace
from enum import Enum

from ai_stock.recommendation.observation_list_ui_preflight import (
    ALLOWED_OBSERVATION_LIST_BADGE_LABELS,
    FORBIDDEN_OBSERVATION_LIST_BADGE_LABELS,
    FORBIDDEN_OBSERVATION_LIST_COLUMN_KEYS,
    FORBIDDEN_OBSERVATION_LIST_UI_OUTPUT_KEYWORDS,
    OBSERVATION_LIST_UI_REQUIRED_DISCLAIMER_LABELS,
    OBSERVATION_LIST_UI_REQUIRED_FALSE_FLAGS,
    ObservationListUIRow,
    build_observation_list_ui_preflight_policy,
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
    build_list_all_fixture_matrix,
    build_list_basic_ready_for_review_fixture,
    build_list_disabled_blocked_fixture,
    build_list_duplicates_blocked_fixture,
    build_list_empty_input_fixture,
    build_list_forbidden_field_sanitized_fixture,
    build_list_missing_data_blocked_fixture,
    build_list_mixed_review_fixture,
    build_recommendation_list_fixture_policy,
    build_recommendation_list_items_from_fixture,
    evaluate_all_recommendation_list_fixtures,
)
from ai_stock.recommendation.recommendation_list_preflight import (
    build_recommendation_list_preflight_policy,
)


class ObservationListUIFixtureScenario(str, Enum):
    """Allowed deterministic observation-list UI fixture scenarios."""

    UI_BASIC_READY_FOR_REVIEW = "ui_basic_ready_for_review"
    UI_MIXED_REVIEW = "ui_mixed_review"
    UI_DUPLICATES_BLOCKED = "ui_duplicates_blocked"
    UI_DISABLED_BLOCKED = "ui_disabled_blocked"
    UI_MISSING_DATA_BLOCKED = "ui_missing_data_blocked"
    UI_FORBIDDEN_FIELD_SANITIZED = "ui_forbidden_field_sanitized"
    UI_EMPTY_INPUT = "ui_empty_input"
    UI_ALL_FIXTURE_MATRIX = "ui_all_fixture_matrix"


ALLOWED_OBSERVATION_LIST_UI_FIXTURE_SCENARIOS: tuple[str, ...] = tuple(
    scenario.value for scenario in ObservationListUIFixtureScenario
)

FORBIDDEN_OBSERVATION_LIST_UI_FIXTURE_SCENARIOS: tuple[str, ...] = (
    "streamlit_render_fixture",
    "button_callback_fixture",
    "session_state_fixture",
    "api_refresh_fixture",
    "oauth_login_fixture",
    "credential_input_fixture",
    "accountSeq_input_fixture",
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
    "actual_recommendation_list_fixture",
    "ranking_fixture",
    "buy_sell_hold_fixture",
    "target_price_fixture",
    "expected_return_fixture",
    "profit_probability_fixture",
)

OBSERVATION_LIST_UI_FIXTURE_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    OBSERVATION_LIST_UI_REQUIRED_FALSE_FLAGS
)

OBSERVATION_LIST_UI_FIXTURE_FORBIDDEN_ABSENT_KEYWORDS: tuple[str, ...] = (
    *FORBIDDEN_OBSERVATION_LIST_UI_OUTPUT_KEYWORDS,
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
)

OBSERVATION_LIST_UI_COMPONENT_SUMMARY_KEYWORDS: tuple[str, ...] = (
    "data_completeness",
    "quality_reliability",
    "review_penalty",
    "sanitized_observation_detail",
    "sanitization_penalty",
)


@dataclass(frozen=True)
class ObservationListUIFixturePolicy:
    """Immutable fail-closed policy for MS-13.01 UI fixtures."""

    stage_name: str = "MS-13.01"
    mode: str = "observation_list_ui_fixture_expansion"
    allowed_scenarios: tuple[str, ...] = ALLOWED_OBSERVATION_LIST_UI_FIXTURE_SCENARIOS
    forbidden_scenarios: tuple[str, ...] = (
        FORBIDDEN_OBSERVATION_LIST_UI_FIXTURE_SCENARIOS
    )
    allowed_status_badges: tuple[str, ...] = ALLOWED_OBSERVATION_LIST_BADGE_LABELS
    forbidden_status_badges: tuple[str, ...] = (
        FORBIDDEN_OBSERVATION_LIST_BADGE_LABELS
    )
    forbidden_column_keys: tuple[str, ...] = FORBIDDEN_OBSERVATION_LIST_COLUMN_KEYS
    forbidden_absent_keywords: tuple[str, ...] = (
        OBSERVATION_LIST_UI_FIXTURE_FORBIDDEN_ABSENT_KEYWORDS
    )
    required_disclaimer_labels: tuple[str, ...] = (
        OBSERVATION_LIST_UI_REQUIRED_DISCLAIMER_LABELS
    )
    required_false_flags: tuple[str, ...] = (
        OBSERVATION_LIST_UI_FIXTURE_REQUIRED_FALSE_FLAGS
    )
    score_snapshot_label_semantics: str = "data_quality_preflight_display_only"
    display_bucket_semantics: str = "review_grouping_label_only"
    usability_label_semantics: str = "future_list_readiness_display_only"
    streamlit_import_allowed: bool = False
    actual_ui_render_allowed: bool = False
    button_allowed: bool = False
    callback_allowed: bool = False
    session_state_allowed: bool = False
    live_refresh_allowed: bool = False
    credential_input_allowed: bool = False
    account_seq_input_allowed: bool = False
    actual_recommendation_allowed: bool = False
    actual_recommendation_list_allowed: bool = False
    ranking_allowed: bool = False
    action_allowed: bool = False
    watchlist_persistence_allowed: bool = False
    feature_file_loader_allowed: bool = False
    watchlist_file_loader_allowed: bool = False
    fixture_file_loader_allowed: bool = False
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
class ObservationListUIFixtureRecord:
    """UI row fixture expectations without directive fields."""

    scenario: str
    description: str
    source_fixture_name: str
    expected_status_badges: tuple[str, ...]
    expected_display_buckets: tuple[str, ...]
    expected_row_count: int
    expected_component_summary_keywords: tuple[str, ...]
    expected_disclaimer_keywords: tuple[str, ...]
    expected_guardrail_false_flags: tuple[str, ...]
    expected_forbidden_absent_keywords: tuple[str, ...]
    expected_warning_keywords: tuple[str, ...]
    expected_diagnostic_keywords: tuple[str, ...]


@dataclass(frozen=True)
class ObservationListUIFixtureEvaluationResult:
    """Expected-vs-actual evaluation result for one UI fixture."""

    scenario: str
    passed: bool
    failures: tuple[str, ...]
    actual_row_count: int
    actual_status_badges: tuple[str, ...]
    actual_display_buckets: tuple[str, ...]
    actual_score_snapshot_labels: tuple[str, ...]
    actual_component_summaries: tuple[str, ...]
    actual_warning_summaries: tuple[str, ...]
    actual_diagnostic_summaries: tuple[str, ...]
    actual_disclaimer_labels: tuple[str, ...]
    actual_guardrail_flags: tuple[str, ...]
    forbidden_absent_check_passed: bool


def build_observation_list_ui_fixture_policy() -> ObservationListUIFixturePolicy:
    """Build the fixed MS-13.01 observation-list UI fixture policy."""

    build_observation_list_ui_preflight_policy()
    build_recommendation_list_preflight_policy()
    build_recommendation_list_fixture_policy()
    build_recommendation_list_fixture_hardening_policy()
    run_recommendation_list_fixture_hardening_checks()
    evaluate_all_recommendation_list_fixtures()
    return ObservationListUIFixturePolicy()


def _expected_false_flags() -> tuple[str, ...]:
    return tuple(
        f"{flag}=false" for flag in OBSERVATION_LIST_UI_FIXTURE_REQUIRED_FALSE_FLAGS
    )


def _fixture_record(
    *,
    scenario: ObservationListUIFixtureScenario,
    description: str,
    source_fixture_name: str,
    expected_status_badges: tuple[str, ...],
    expected_display_buckets: tuple[str, ...],
    expected_row_count: int,
    expected_warning_keywords: tuple[str, ...] = (),
    expected_diagnostic_keywords: tuple[str, ...] = (),
) -> ObservationListUIFixtureRecord:
    return ObservationListUIFixtureRecord(
        scenario=scenario.value,
        description=description,
        source_fixture_name=source_fixture_name,
        expected_status_badges=expected_status_badges,
        expected_display_buckets=expected_display_buckets,
        expected_row_count=expected_row_count,
        expected_component_summary_keywords=(
            OBSERVATION_LIST_UI_COMPONENT_SUMMARY_KEYWORDS
        ),
        expected_disclaimer_keywords=OBSERVATION_LIST_UI_REQUIRED_DISCLAIMER_LABELS,
        expected_guardrail_false_flags=_expected_false_flags(),
        expected_forbidden_absent_keywords=(
            OBSERVATION_LIST_UI_FIXTURE_FORBIDDEN_ABSENT_KEYWORDS
        ),
        expected_warning_keywords=expected_warning_keywords,
        expected_diagnostic_keywords=expected_diagnostic_keywords,
    )


def build_ui_basic_ready_for_review_fixture() -> ObservationListUIFixtureRecord:
    """Build expectations for ready observation UI rows."""

    return _fixture_record(
        scenario=ObservationListUIFixtureScenario.UI_BASIC_READY_FOR_REVIEW,
        description="Ready list items produce review-ready observation UI rows.",
        source_fixture_name="list_basic_ready_for_review",
        expected_status_badges=("review_ready", "review_ready"),
        expected_display_buckets=("review_ready",),
        expected_row_count=2,
        expected_warning_keywords=(
            "observation_item_preflight_only",
            "score_snapshot_quality_preflight_only",
            "display_bucket_review_group_only",
        ),
        expected_diagnostic_keywords=("deterministic_in_memory_list_item_shape",),
    )


def build_ui_mixed_review_fixture() -> ObservationListUIFixtureRecord:
    """Build expectations for mixed valid and invalid observation UI rows."""

    return _fixture_record(
        scenario=ObservationListUIFixtureScenario.UI_MIXED_REVIEW,
        description="Invalid list items remain non-directive UI rows.",
        source_fixture_name="list_mixed_review",
        expected_status_badges=(
            "review_ready",
            "invalid_candidate",
            "invalid_candidate",
        ),
        expected_display_buckets=("review_ready", "invalid_candidate_review"),
        expected_row_count=3,
        expected_warning_keywords=("invalid_symbol_review",),
        expected_diagnostic_keywords=(
            "symbol_required",
            "symbol_must_be_safe_ascii_identifier",
        ),
    )


def build_ui_duplicates_blocked_fixture() -> ObservationListUIFixtureRecord:
    """Build expectations for duplicate-blocked observation UI rows."""

    return _fixture_record(
        scenario=ObservationListUIFixtureScenario.UI_DUPLICATES_BLOCKED,
        description="Duplicate list items remain blocked observation UI rows.",
        source_fixture_name="list_duplicates_blocked",
        expected_status_badges=(
            "review_ready",
            "duplicate_candidate",
            "disabled_candidate",
        ),
        expected_display_buckets=(
            "review_ready",
            "duplicate_candidate_review",
            "disabled_candidate_review",
        ),
        expected_row_count=3,
        expected_warning_keywords=("duplicate_candidate_needs_review",),
        expected_diagnostic_keywords=("duplicate_symbol",),
    )


def build_ui_disabled_blocked_fixture() -> ObservationListUIFixtureRecord:
    """Build expectations for disabled observation UI rows."""

    return _fixture_record(
        scenario=ObservationListUIFixtureScenario.UI_DISABLED_BLOCKED,
        description="Disabled list items remain non-actionable UI rows.",
        source_fixture_name="list_disabled_blocked",
        expected_status_badges=(
            "review_ready",
            "duplicate_candidate",
            "disabled_candidate",
        ),
        expected_display_buckets=(
            "review_ready",
            "duplicate_candidate_review",
            "disabled_candidate_review",
        ),
        expected_row_count=3,
        expected_warning_keywords=("disabled_candidate_not_selectable",),
        expected_diagnostic_keywords=("candidate_disabled",),
    )


def build_ui_missing_data_blocked_fixture() -> ObservationListUIFixtureRecord:
    """Build expectations for missing-data observation UI rows."""

    return _fixture_record(
        scenario=ObservationListUIFixtureScenario.UI_MISSING_DATA_BLOCKED,
        description="Missing data remains a safe observation UI row.",
        source_fixture_name="list_missing_data_blocked",
        expected_status_badges=("missing_data",),
        expected_display_buckets=("missing_data_review",),
        expected_row_count=1,
        expected_warning_keywords=("insufficient_data_review",),
        expected_diagnostic_keywords=("deterministic_in_memory_list_item_shape",),
    )


def build_ui_forbidden_field_sanitized_fixture() -> ObservationListUIFixtureRecord:
    """Build expectations for sanitized observation UI rows."""

    return _fixture_record(
        scenario=ObservationListUIFixtureScenario.UI_FORBIDDEN_FIELD_SANITIZED,
        description="Forbidden source details are sanitized in UI rows.",
        source_fixture_name="list_forbidden_field_sanitized",
        expected_status_badges=("sanitized_input",),
        expected_display_buckets=("sanitized_candidate_review",),
        expected_row_count=1,
        expected_warning_keywords=("score_snapshot_quality_preflight_only",),
        expected_diagnostic_keywords=(
            "sanitized_observation_detail",
            "forbidden_fields_reported_in_diagnostics_only",
        ),
    )


def build_ui_empty_input_fixture() -> ObservationListUIFixtureRecord:
    """Build expectations for empty-input observation UI rows."""

    return _fixture_record(
        scenario=ObservationListUIFixtureScenario.UI_EMPTY_INPUT,
        description="Empty input remains a safe observation UI row.",
        source_fixture_name="list_empty_input",
        expected_status_badges=("empty_input",),
        expected_display_buckets=("empty_input_review",),
        expected_row_count=1,
        expected_warning_keywords=("empty_watchlist_safe_state",),
        expected_diagnostic_keywords=("empty_source_items",),
    )


def build_ui_all_fixture_matrix() -> ObservationListUIFixtureRecord:
    """Build expectations for the all-fixture observation UI row matrix."""

    return _fixture_record(
        scenario=ObservationListUIFixtureScenario.UI_ALL_FIXTURE_MATRIX,
        description="All list fixtures produce safe observation UI rows.",
        source_fixture_name="list_all_fixture_matrix",
        expected_status_badges=(
            "review_ready",
            "review_ready",
            "review_ready",
            "invalid_candidate",
            "invalid_candidate",
            "review_ready",
            "duplicate_candidate",
            "disabled_candidate",
            "missing_data",
            "sanitized_input",
            "empty_input",
        ),
        expected_display_buckets=(
            "review_ready",
            "invalid_candidate_review",
            "duplicate_candidate_review",
            "disabled_candidate_review",
            "missing_data_review",
            "sanitized_candidate_review",
            "empty_input_review",
        ),
        expected_row_count=11,
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
            "sanitized_observation_detail",
            "empty_source_items",
        ),
    )


def build_all_observation_list_ui_fixtures() -> (
    tuple[ObservationListUIFixtureRecord, ...]
):
    """Build every deterministic MS-13.01 observation UI fixture."""

    return (
        build_ui_basic_ready_for_review_fixture(),
        build_ui_mixed_review_fixture(),
        build_ui_duplicates_blocked_fixture(),
        build_ui_disabled_blocked_fixture(),
        build_ui_missing_data_blocked_fixture(),
        build_ui_forbidden_field_sanitized_fixture(),
        build_ui_empty_input_fixture(),
        build_ui_all_fixture_matrix(),
    )


def _list_fixture_by_name(source_fixture_name: str) -> object:
    if source_fixture_name == "list_basic_ready_for_review":
        return build_list_basic_ready_for_review_fixture()
    if source_fixture_name == "list_mixed_review":
        return build_list_mixed_review_fixture()
    if source_fixture_name == "list_duplicates_blocked":
        return build_list_duplicates_blocked_fixture()
    if source_fixture_name == "list_disabled_blocked":
        return build_list_disabled_blocked_fixture()
    if source_fixture_name == "list_missing_data_blocked":
        return build_list_missing_data_blocked_fixture()
    if source_fixture_name == "list_forbidden_field_sanitized":
        return build_list_forbidden_field_sanitized_fixture()
    if source_fixture_name == "list_empty_input":
        return build_list_empty_input_fixture()
    if source_fixture_name == "list_all_fixture_matrix":
        return build_list_all_fixture_matrix()
    raise ValueError(f"unknown_observation_list_ui_fixture:{source_fixture_name}")


def build_observation_list_ui_rows_from_fixture(
    fixture: ObservationListUIFixtureRecord,
) -> tuple[ObservationListUIRow, ...]:
    """Build UI rows referenced by one UI fixture."""

    policy = build_observation_list_ui_preflight_policy()
    if fixture.source_fixture_name == "list_all_fixture_matrix":
        return build_observation_list_ui_rows_from_all_fixtures(policy)
    list_fixture = _list_fixture_by_name(fixture.source_fixture_name)
    list_items = build_recommendation_list_items_from_fixture(list_fixture)
    return build_observation_list_ui_rows_from_items(list_items, policy)


def _unique_in_seen_order(values: tuple[str, ...]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _actual_component_summaries(
    rows: tuple[ObservationListUIRow, ...],
) -> tuple[str, ...]:
    return _unique_in_seen_order(
        tuple(component for row in rows for component in row.component_summary)
    )


def _actual_warning_summaries(
    rows: tuple[ObservationListUIRow, ...],
) -> tuple[str, ...]:
    return tuple(warning for row in rows for warning in row.warning_summary)


def _actual_diagnostic_summaries(
    rows: tuple[ObservationListUIRow, ...],
) -> tuple[str, ...]:
    return tuple(diagnostic for row in rows for diagnostic in row.diagnostic_summary)


def _actual_disclaimer_labels(
    rows: tuple[ObservationListUIRow, ...],
) -> tuple[str, ...]:
    return _unique_in_seen_order(
        tuple(label for row in rows for label in row.disclaimer_labels)
    )


def _actual_guardrail_flags(rows: tuple[ObservationListUIRow, ...]) -> tuple[str, ...]:
    return _unique_in_seen_order(
        tuple(flag for row in rows for flag in row.guardrail_flags)
    )


def _forbidden_guardrail_output_present(
    rows: tuple[ObservationListUIRow, ...],
    fixture: ObservationListUIFixtureRecord,
) -> bool:
    rendered = repr(rows)
    return any(
        keyword in rendered
        for keyword in fixture.expected_forbidden_absent_keywords
    )


def _observation_guardrail_failures(
    rows: tuple[ObservationListUIRow, ...],
) -> tuple[str, ...]:
    failures: list[str] = []
    for row in rows:
        if row.status_badge in ("buy", "sell", "hold", "strong_buy"):
            failures.append("trade_badge_present")
        if any(
            label in row.score_snapshot_label
            for label in ("recommendation", "ranking", "action")
        ):
            failures.append("score_snapshot_label_directive_present")
        if any(label in row.display_bucket for label in ("rank", "priority", "order")):
            failures.append("display_bucket_ordering_semantics_present")
        if any(label in row.usability_label for label in ("rank", "priority", "order")):
            failures.append("usability_label_ranking_semantics_present")
    return tuple(failures)


def evaluate_observation_list_ui_fixture(
    fixture: ObservationListUIFixtureRecord,
) -> ObservationListUIFixtureEvaluationResult:
    """Compare MS-13.01 UI fixture expectations with row preflight outputs."""

    rows = build_observation_list_ui_rows_from_fixture(fixture)
    policy = build_observation_list_ui_preflight_policy()
    summarize_observation_list_ui_rows(rows)
    actual_status_badges = tuple(row.status_badge for row in rows)
    actual_display_buckets = _unique_in_seen_order(
        tuple(row.display_bucket for row in rows)
    )
    actual_score_snapshot_labels = tuple(row.score_snapshot_label for row in rows)
    actual_component_summaries = _actual_component_summaries(rows)
    actual_warning_summaries = _actual_warning_summaries(rows)
    actual_diagnostic_summaries = _actual_diagnostic_summaries(rows)
    actual_disclaimer_labels = _actual_disclaimer_labels(rows)
    actual_guardrail_flags = _actual_guardrail_flags(rows)
    validation_results = tuple(
        validate_observation_list_ui_row(row, policy) for row in rows
    )
    forbidden_absent_check_passed = not _forbidden_guardrail_output_present(
        rows,
        fixture,
    )

    failures: list[str] = []
    if len(rows) != fixture.expected_row_count:
        failures.append("row_count_mismatch")
    if actual_status_badges != fixture.expected_status_badges:
        failures.append("status_badges_mismatch")
    if actual_display_buckets != fixture.expected_display_buckets:
        failures.append("display_buckets_mismatch")
    if actual_guardrail_flags != fixture.expected_guardrail_false_flags:
        failures.append("guardrail_false_flags_mismatch")
    if not forbidden_absent_check_passed:
        failures.append("forbidden_keyword_present")

    for expected_keyword in fixture.expected_component_summary_keywords:
        if not any(expected_keyword in value for value in actual_component_summaries):
            failures.append(f"missing_component_summary:{expected_keyword}")

    for expected_keyword in fixture.expected_disclaimer_keywords:
        if not any(expected_keyword in value for value in actual_disclaimer_labels):
            failures.append(f"missing_disclaimer:{expected_keyword}")

    for expected_keyword in fixture.expected_warning_keywords:
        if not any(expected_keyword in value for value in actual_warning_summaries):
            failures.append(f"missing_warning:{expected_keyword}")

    for expected_keyword in fixture.expected_diagnostic_keywords:
        if not any(expected_keyword in value for value in actual_diagnostic_summaries):
            failures.append(f"missing_diagnostic:{expected_keyword}")

    for validation in validation_results:
        if not validation.valid:
            failures.extend(
                f"invalid_observation_list_ui_row:{reason}"
                for reason in validation.rejection_reasons
            )

    failures.extend(_observation_guardrail_failures(rows))

    return ObservationListUIFixtureEvaluationResult(
        scenario=fixture.scenario,
        passed=not failures,
        failures=tuple(failures),
        actual_row_count=len(rows),
        actual_status_badges=actual_status_badges,
        actual_display_buckets=actual_display_buckets,
        actual_score_snapshot_labels=actual_score_snapshot_labels,
        actual_component_summaries=actual_component_summaries,
        actual_warning_summaries=actual_warning_summaries,
        actual_diagnostic_summaries=actual_diagnostic_summaries,
        actual_disclaimer_labels=actual_disclaimer_labels,
        actual_guardrail_flags=actual_guardrail_flags,
        forbidden_absent_check_passed=forbidden_absent_check_passed,
    )


def evaluate_all_observation_list_ui_fixtures() -> (
    tuple[ObservationListUIFixtureEvaluationResult, ...]
):
    """Evaluate every deterministic MS-13.01 observation UI fixture."""

    return tuple(
        evaluate_observation_list_ui_fixture(fixture)
        for fixture in build_all_observation_list_ui_fixtures()
    )


def build_observation_list_ui_fixture_failure_probe() -> (
    ObservationListUIFixtureRecord
):
    """Build an intentional mismatch probe for evaluator failure detection."""

    return replace(
        build_ui_basic_ready_for_review_fixture(),
        expected_status_badges=("empty_input",),
    )
