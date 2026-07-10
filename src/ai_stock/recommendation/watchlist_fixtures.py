"""Pure watchlist source fixtures for MS-09.04.

This module defines deterministic in-memory fixtures for the MS-09.03
manual/local watchlist source adapter. It performs no file, database,
environment, network, UI, model, account, order, clock, or random I/O.
It does not load, store, score, recommend, trade, or display watchlists.
"""

from dataclasses import dataclass
from enum import Enum

from ai_stock.recommendation.candidate_input_preflight import (
    FORBIDDEN_CANDIDATE_LABELS,
)
from ai_stock.recommendation.watchlist_source import (
    ManualWatchlistSourceType,
    WatchlistSourceConfig,
    WatchlistSourceResult,
    build_watchlist_source_result,
)


class WatchlistFixtureScenario(str, Enum):
    """Allowed deterministic fixture scenarios for MS-09.04."""

    BASIC_MANUAL_SYMBOLS = "basic_manual_symbols"
    MIXED_VALID_INVALID_SYMBOLS = "mixed_valid_invalid_symbols"
    DUPLICATES_AND_DISABLED = "duplicates_and_disabled"
    INSUFFICIENT_DATA_REVIEW = "insufficient_data_review"
    FORBIDDEN_FIELDS_SANITIZED = "forbidden_fields_sanitized"
    EMPTY_WATCHLIST = "empty_watchlist"


ALLOWED_WATCHLIST_FIXTURE_SCENARIOS: tuple[str, ...] = tuple(
    scenario.value for scenario in WatchlistFixtureScenario
)

FORBIDDEN_WATCHLIST_FIXTURE_SCENARIOS: tuple[str, ...] = (
    "real_account_holdings_fixture",
    "real_account_balance_fixture",
    "real_fills_fixture",
    "toss_api_response_fixture",
    "db_row_fixture",
    "file_path_fixture",
    "credential_token_accountSeq_fixture",
)

FIXTURE_REQUIRED_FALSE_FLAGS: tuple[str, ...] = (
    "credential_required",
    "db_read_required",
    "db_write_required",
    "file_read_required",
    "file_write_required",
    "toss_api_required",
    "openai_required",
    "oauth_required",
    "account_seq_required",
    "real_order_required",
    "scoring_required",
    "ui_required",
)


@dataclass(frozen=True)
class WatchlistFixturePolicy:
    """Immutable fail-closed policy for MS-09.04 fixtures."""

    stage_name: str = "MS-09.04"
    mode: str = "watchlist_source_test_fixtures"
    allowed_scenarios: tuple[str, ...] = ALLOWED_WATCHLIST_FIXTURE_SCENARIOS
    forbidden_scenarios: tuple[str, ...] = FORBIDDEN_WATCHLIST_FIXTURE_SCENARIOS
    forbidden_labels: tuple[str, ...] = FORBIDDEN_CANDIDATE_LABELS
    required_false_flags: tuple[str, ...] = FIXTURE_REQUIRED_FALSE_FLAGS
    actual_recommendation_allowed: bool = False
    scoring_allowed: bool = False
    watchlist_persistence_allowed: bool = False
    file_loader_allowed: bool = False
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
    ui_required: bool = False


@dataclass(frozen=True)
class WatchlistFixtureRecord:
    """Fixture record plus expected deterministic adapter output."""

    scenario: str
    description: str
    source_config: WatchlistSourceConfig
    expected_watchlist_status: str
    expected_candidate_statuses: tuple[str, ...]
    expected_summary_flags: tuple[str, ...]
    expected_rejection_reason_keywords: tuple[str, ...] = ()
    expected_diagnostics_keywords: tuple[str, ...] = ()


@dataclass(frozen=True)
class WatchlistFixtureEvaluationResult:
    """Expected-vs-actual evaluation result with all required flags false."""

    scenario: str
    passed: bool
    failures: tuple[str, ...]
    actual_watchlist_status: str
    actual_candidate_statuses: tuple[str, ...]
    actual_summary_flags: tuple[str, ...]
    diagnostics: tuple[str, ...]
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
    ui_required: bool


def build_watchlist_fixture_policy() -> WatchlistFixturePolicy:
    """Build the fixed MS-09.04 fixture policy."""

    return WatchlistFixturePolicy()


def _expected_false_flags() -> tuple[str, ...]:
    return tuple(f"{flag}=false" for flag in FIXTURE_REQUIRED_FALSE_FLAGS)


def _actual_false_flags(result: WatchlistSourceResult) -> tuple[str, ...]:
    return tuple(
        f"{flag}={str(bool(getattr(result, flag))).lower()}"
        for flag in FIXTURE_REQUIRED_FALSE_FLAGS
    )


def build_basic_manual_symbols_fixture() -> WatchlistFixtureRecord:
    """Build a valid manual symbol fixture."""

    return WatchlistFixtureRecord(
        scenario=WatchlistFixtureScenario.BASIC_MANUAL_SYMBOLS.value,
        description="Two caller-supplied symbols become valid candidates.",
        source_config=WatchlistSourceConfig(
            source_type=ManualWatchlistSourceType.MANUAL_SYMBOLS.value,
            source_label="fixture:basic_manual_symbols",
            watchlist_name="Fixture Basic Manual Symbols",
            watchlist_description="Pure in-memory symbols for tests.",
            default_market="KOSPI",
            default_tags=("fixture", "manual"),
            default_group="basic",
            default_reason="fixture observation only",
            raw_items=("005930", "000660"),
        ),
        expected_watchlist_status="valid_watchlist",
        expected_candidate_statuses=("valid_candidate", "valid_candidate"),
        expected_summary_flags=_expected_false_flags(),
    )


def build_mixed_valid_invalid_symbols_fixture() -> WatchlistFixtureRecord:
    """Build a mixed fixture with valid and invalid symbols."""

    return WatchlistFixtureRecord(
        scenario=WatchlistFixtureScenario.MIXED_VALID_INVALID_SYMBOLS.value,
        description="Invalid symbols are represented as safe validation states.",
        source_config=WatchlistSourceConfig(
            source_type=ManualWatchlistSourceType.MANUAL_SYMBOLS.value,
            source_label="fixture:mixed_valid_invalid_symbols",
            watchlist_name="Fixture Mixed Symbols",
            raw_items=("005930", " ", "A" * 33),
        ),
        expected_watchlist_status="contains_invalid_candidates",
        expected_candidate_statuses=(
            "valid_candidate",
            "invalid_symbol",
            "invalid_symbol",
        ),
        expected_summary_flags=_expected_false_flags(),
    )


def build_duplicates_and_disabled_fixture() -> WatchlistFixtureRecord:
    """Build a fixture with duplicate and disabled candidates."""

    return WatchlistFixtureRecord(
        scenario=WatchlistFixtureScenario.DUPLICATES_AND_DISABLED.value,
        description="Duplicates and disabled items remain non-directive states.",
        source_config=WatchlistSourceConfig(
            source_type=ManualWatchlistSourceType.MANUAL_WATCHLIST_ITEMS.value,
            source_label="fixture:duplicates_and_disabled",
            watchlist_name="Fixture Duplicates And Disabled",
            raw_items=(
                {"symbol": "005930"},
                {"symbol": " 005930 "},
                {"symbol": "MSFT", "enabled": False},
            ),
        ),
        expected_watchlist_status="contains_duplicate_candidates",
        expected_candidate_statuses=(
            "valid_candidate",
            "duplicate_candidate",
            "disabled_candidate",
        ),
        expected_summary_flags=_expected_false_flags(),
    )


def build_insufficient_data_review_fixture() -> WatchlistFixtureRecord:
    """Build a fixture for safe insufficient-data review status."""

    return WatchlistFixtureRecord(
        scenario=WatchlistFixtureScenario.INSUFFICIENT_DATA_REVIEW.value,
        description="Partial data produces an insufficient-data review state.",
        source_config=WatchlistSourceConfig(
            source_type=ManualWatchlistSourceType.MANUAL_WATCHLIST_ITEMS.value,
            source_label="fixture:insufficient_data_review",
            watchlist_name="Fixture Insufficient Data Review",
            raw_items=(
                {
                    "symbol": "005930",
                    "data_availability_hint": "partial_data",
                },
            ),
        ),
        expected_watchlist_status="needs_review",
        expected_candidate_statuses=("insufficient_data",),
        expected_summary_flags=_expected_false_flags(),
    )


def build_forbidden_fields_sanitized_fixture() -> WatchlistFixtureRecord:
    """Build a fixture containing forbidden fields that must be sanitized."""

    return WatchlistFixtureRecord(
        scenario=WatchlistFixtureScenario.FORBIDDEN_FIELDS_SANITIZED.value,
        description=(
            "Forbidden caller fields are diagnosed without copying values into "
            "output models."
        ),
        source_config=WatchlistSourceConfig(
            source_type=ManualWatchlistSourceType.MANUAL_WATCHLIST_ITEMS.value,
            source_label="fixture:forbidden_fields_sanitized",
            watchlist_name="Fixture Forbidden Fields Sanitized",
            raw_items=(
                {
                    "symbol": "005930",
                    "accountSeq": "redacted-not-output",
                    "access_token": "redacted-not-output",
                    "authorization": "redacted-not-output",
                    "target_price": "redacted-not-output",
                    "expected_return": "redacted-not-output",
                    "score": "redacted-not-output",
                    "buy": "redacted-not-output",
                    "sell": "redacted-not-output",
                    "hold": "redacted-not-output",
                },
            ),
        ),
        expected_watchlist_status="valid_watchlist",
        expected_candidate_statuses=("valid_candidate",),
        expected_summary_flags=_expected_false_flags(),
        expected_rejection_reason_keywords=(
            "forbidden_field:accountSeq",
            "forbidden_field:target_price",
            "forbidden_field:score",
            "forbidden_field:buy",
            "forbidden_field:sell",
            "forbidden_field:hold",
        ),
        expected_diagnostics_keywords=(
            "forbidden_field_detected:accountSeq",
            "forbidden_field_detected:target_price",
            "forbidden_field_detected:score",
        ),
    )


def build_empty_watchlist_fixture() -> WatchlistFixtureRecord:
    """Build an empty watchlist fixture."""

    return WatchlistFixtureRecord(
        scenario=WatchlistFixtureScenario.EMPTY_WATCHLIST.value,
        description="Empty caller-supplied records produce an empty watchlist.",
        source_config=WatchlistSourceConfig(
            source_type=ManualWatchlistSourceType.MANUAL_SYMBOLS.value,
            source_label="fixture:empty_watchlist",
            watchlist_name="Fixture Empty Watchlist",
            raw_items=(),
        ),
        expected_watchlist_status="empty_watchlist",
        expected_candidate_statuses=(),
        expected_summary_flags=_expected_false_flags(),
        expected_diagnostics_keywords=("empty_source_items",),
    )


def build_all_watchlist_source_fixtures() -> tuple[WatchlistFixtureRecord, ...]:
    """Build every deterministic MS-09.04 watchlist source fixture."""

    return (
        build_basic_manual_symbols_fixture(),
        build_mixed_valid_invalid_symbols_fixture(),
        build_duplicates_and_disabled_fixture(),
        build_insufficient_data_review_fixture(),
        build_forbidden_fields_sanitized_fixture(),
        build_empty_watchlist_fixture(),
    )


def evaluate_watchlist_fixture(
    fixture: WatchlistFixtureRecord,
) -> WatchlistFixtureEvaluationResult:
    """Compare fixture expectations with the MS-09.03 adapter result."""

    result = build_watchlist_source_result(fixture.source_config)
    actual_candidate_statuses = tuple(
        item.validation_status for item in result.validation.items
    )
    actual_summary_flags = _actual_false_flags(result)
    combined_diagnostics = (
        result.diagnostics
        + result.rejection_reasons
        + result.validation.rejection_reasons
    )
    failures: list[str] = []

    if result.validation.validation_status != fixture.expected_watchlist_status:
        failures.append("watchlist_status_mismatch")
    if actual_candidate_statuses != fixture.expected_candidate_statuses:
        failures.append("candidate_statuses_mismatch")
    if actual_summary_flags != fixture.expected_summary_flags:
        failures.append("summary_flags_mismatch")

    for expected_keyword in fixture.expected_rejection_reason_keywords:
        if not any(expected_keyword in value for value in result.rejection_reasons):
            failures.append(f"missing_rejection_reason:{expected_keyword}")

    for expected_keyword in fixture.expected_diagnostics_keywords:
        if not any(expected_keyword in value for value in combined_diagnostics):
            failures.append(f"missing_diagnostic:{expected_keyword}")

    for flag in FIXTURE_REQUIRED_FALSE_FLAGS:
        if bool(getattr(result, flag)):
            failures.append(f"required_flag_true:{flag}")

    return WatchlistFixtureEvaluationResult(
        scenario=fixture.scenario,
        passed=not failures,
        failures=tuple(failures),
        actual_watchlist_status=result.validation.validation_status,
        actual_candidate_statuses=actual_candidate_statuses,
        actual_summary_flags=actual_summary_flags,
        diagnostics=combined_diagnostics,
        credential_required=result.credential_required,
        db_read_required=result.db_read_required,
        db_write_required=result.db_write_required,
        file_read_required=result.file_read_required,
        file_write_required=result.file_write_required,
        toss_api_required=result.toss_api_required,
        openai_required=result.openai_required,
        oauth_required=result.oauth_required,
        account_seq_required=result.account_seq_required,
        real_order_required=result.real_order_required,
        scoring_required=result.scoring_required,
        ui_required=result.ui_required,
    )
