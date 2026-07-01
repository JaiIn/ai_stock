"""Read-only safe audit for the local snapshot SQLite database."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
import sqlite3
import subprocess

STAGE = "MS-06.10"
PHASE = "local_snapshot_db_readonly_audit"
PLANNED_DB_RELATIVE_PATH = "data/local/ai_stock.sqlite3"


@dataclass(frozen=True, slots=True)
class TableSummary:
    count: int
    min_timestamp: str | None = None
    max_timestamp: str | None = None


@dataclass(frozen=True, slots=True)
class LocalSnapshotDbAuditSummary:
    success: bool
    stage: str
    phase: str
    planned_db_relative_path: str
    db_file_exists: bool
    db_file_size_bytes: int | None
    db_file_modified_time_utc: str | None
    db_open_mode: str
    db_write_allowed_this_stage: bool
    actual_db_file_modified_this_stage: bool
    api_call_allowed_this_stage: bool
    oauth_token_endpoint_allowed_this_stage: bool
    env_file_read_allowed_this_stage: bool
    credential_required_this_stage: bool
    account_seq_allowed: bool
    real_order_related_call_allowed: bool
    stock_warnings_included: bool
    stock_warnings_deferred: bool
    sqlite_file_ignored_by_git: bool
    db_file_git_tracked: bool
    data_directory_git_tracked: bool
    stocks: TableSummary
    price_snapshots: TableSummary
    candles: TableSummary
    exchange_rates: TableSummary
    requested_symbol_present: bool
    exchange_rate_pair_present: bool
    minimum_expected_state_valid: bool
    safe_error_type: str | None
    safe_error_message: str | None

    def safe_dict(self) -> dict[str, object]:
        return asdict(self)


def audit_local_snapshot_db_readonly(
    database_path: str | Path = PLANNED_DB_RELATIVE_PATH,
) -> LocalSnapshotDbAuditSummary:
    """Open an existing SQLite file read-only and return aggregate metadata."""

    path = Path(database_path)
    before = _file_metadata(path)
    empty = TableSummary(0)
    if before is None:
        return _summary(
            exists=False,
            metadata=None,
            stocks=empty,
            prices=empty,
            candles=empty,
            rates=empty,
            symbol_present=False,
            pair_present=False,
            modified=False,
            error_type="database_not_found",
            error_message="The local snapshot database file does not exist.",
            path=path,
        )

    try:
        uri = f"{path.resolve().as_uri()}?mode=ro"
        connection = sqlite3.connect(uri, uri=True)
        try:
            connection.execute("PRAGMA query_only = ON")
            stocks = TableSummary(_scalar(connection, "SELECT COUNT(*) FROM stocks"))
            prices = _timestamp_summary(connection, "price_snapshots", "timestamp")
            candles = _timestamp_summary(connection, "candles", "timestamp")
            rates = _timestamp_summary(connection, "exchange_rates", "date_time")
            symbol_present = bool(
                _scalar(
                    connection,
                    "SELECT EXISTS(SELECT 1 FROM stocks WHERE symbol = ?)",
                    ("005930",),
                )
            )
            pair_present = bool(
                _scalar(
                    connection,
                    "SELECT EXISTS(SELECT 1 FROM exchange_rates "
                    "WHERE base_currency = ? AND quote_currency = ?)",
                    ("USD", "KRW"),
                )
            )
        finally:
            connection.close()
    except sqlite3.Error:
        after = _file_metadata(path)
        return _summary(
            exists=True,
            metadata=after or before,
            stocks=empty,
            prices=empty,
            candles=empty,
            rates=empty,
            symbol_present=False,
            pair_present=False,
            modified=after != before,
            error_type="database_read_failed",
            error_message="The local snapshot database audit failed safely.",
            path=path,
        )

    after = _file_metadata(path)
    modified = after != before
    minimum_valid = (
        stocks.count >= 1
        and prices.count >= 2
        and candles.count >= 2
        and rates.count >= 2
        and symbol_present
        and pair_present
    )
    return _summary(
        exists=True,
        metadata=after or before,
        stocks=stocks,
        prices=prices,
        candles=candles,
        rates=rates,
        symbol_present=symbol_present,
        pair_present=pair_present,
        modified=modified,
        error_type=None if minimum_valid and not modified else "validation_failed",
        error_message=(
            None
            if minimum_valid and not modified
            else "The local snapshot database minimum state was not satisfied."
        ),
        path=path,
    )


def _timestamp_summary(
    connection: sqlite3.Connection,
    table: str,
    column: str,
) -> TableSummary:
    row = connection.execute(
        f"SELECT COUNT(*), MIN({column}), MAX({column}) FROM {table}"
    ).fetchone()
    return TableSummary(int(row[0]), row[1], row[2])


def _scalar(
    connection: sqlite3.Connection,
    statement: str,
    parameters: tuple[str, ...] = (),
) -> int:
    row = connection.execute(statement, parameters).fetchone()
    return int(row[0])


def _file_metadata(path: Path) -> tuple[int, str] | None:
    if not path.is_file():
        return None
    stat = path.stat()
    return (
        stat.st_size,
        datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat(),
    )


def _git_state(path: Path) -> tuple[bool, bool, bool]:
    relative = path.as_posix()
    tracked = bool(
        subprocess.run(
            ["git", "ls-files", "--", relative],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    data_tracked = bool(
        subprocess.run(
            ["git", "ls-files", "--", "data"],
            check=True,
            capture_output=True,
            text=True,
        ).stdout.strip()
    )
    ignored = subprocess.run(
        ["git", "check-ignore", "-q", "--", relative],
        check=False,
    ).returncode == 0
    return tracked, data_tracked, ignored


def _summary(
    *,
    exists: bool,
    metadata: tuple[int, str] | None,
    stocks: TableSummary,
    prices: TableSummary,
    candles: TableSummary,
    rates: TableSummary,
    symbol_present: bool,
    pair_present: bool,
    modified: bool,
    error_type: str | None,
    error_message: str | None,
    path: Path,
) -> LocalSnapshotDbAuditSummary:
    tracked, data_tracked, ignored = _git_state(path)
    minimum_valid = (
        stocks.count >= 1
        and prices.count >= 2
        and candles.count >= 2
        and rates.count >= 2
        and symbol_present
        and pair_present
    )
    success = (
        exists
        and minimum_valid
        and not modified
        and not tracked
        and not data_tracked
        and ignored
        and error_type is None
    )
    return LocalSnapshotDbAuditSummary(
        success=success,
        stage=STAGE,
        phase=PHASE,
        planned_db_relative_path=PLANNED_DB_RELATIVE_PATH,
        db_file_exists=exists,
        db_file_size_bytes=metadata[0] if metadata else None,
        db_file_modified_time_utc=metadata[1] if metadata else None,
        db_open_mode="readonly",
        db_write_allowed_this_stage=False,
        actual_db_file_modified_this_stage=modified,
        api_call_allowed_this_stage=False,
        oauth_token_endpoint_allowed_this_stage=False,
        env_file_read_allowed_this_stage=False,
        credential_required_this_stage=False,
        account_seq_allowed=False,
        real_order_related_call_allowed=False,
        stock_warnings_included=False,
        stock_warnings_deferred=True,
        sqlite_file_ignored_by_git=ignored,
        db_file_git_tracked=tracked,
        data_directory_git_tracked=data_tracked,
        stocks=stocks,
        price_snapshots=prices,
        candles=candles,
        exchange_rates=rates,
        requested_symbol_present=symbol_present,
        exchange_rate_pair_present=pair_present,
        minimum_expected_state_valid=minimum_valid,
        safe_error_type=error_type,
        safe_error_message=error_message,
    )
