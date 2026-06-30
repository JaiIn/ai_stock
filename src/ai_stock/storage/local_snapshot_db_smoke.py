"""Fake-only snapshot ingestion smoke for one local SQLite file.

The smoke uses parsed in-process models and existing repository services only.
It does not import Toss clients, OAuth providers, HTTP transports, environment
configuration, account data, or order code.
"""

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from decimal import Decimal
from pathlib import Path
import subprocess
from typing import Protocol

from ai_stock.models import Candle, CandlePage, ExchangeRate, PriceSnapshot, StockInfo
from ai_stock.repositories import close_connection, create_connection
from ai_stock.services import (
    LocalDataPersistenceService,
    ReadOnlySnapshotIngestionRequest,
    ReadOnlySnapshotIngestionService,
)

PLANNED_DB_RELATIVE_PATH = "data/local/ai_stock.sqlite3"
SMOKE_SYMBOL = "005930"
SMOKE_BASE_CURRENCY = "USD"
SMOKE_QUOTE_CURRENCY = "KRW"
SMOKE_CANDLE_INTERVAL = "1d"
SMOKE_CANDLE_COUNT = 1
SMOKE_ADJUSTED = True

_PRICE = Decimal("70123.4500")
_CANDLE_OPEN = Decimal("70000.00")
_CANDLE_HIGH = Decimal("71000.10")
_CANDLE_LOW = Decimal("69900.20")
_CANDLE_CLOSE = Decimal("70500.30")
_CANDLE_VOLUME = Decimal("1234567")
_EXCHANGE_RATE = Decimal("1375.2500")
_PRICE_TIMESTAMP = "2026-06-30T09:00:00+09:00"
_CANDLE_TIMESTAMP = "2026-06-30T00:00:00+09:00"
_RATE_TIMESTAMP = "2026-06-30T00:00:00+09:00"


class GitTrackingInspector(Protocol):
    """Read-only Git state required for safe smoke diagnostics."""

    def is_tracked(self, path: Path) -> bool:
        """Return whether the file is tracked."""

    def is_ignored(self, path: Path) -> bool:
        """Return whether the file is ignored."""

    def directory_has_tracked_files(self, path: Path) -> bool:
        """Return whether Git tracks files below the directory."""


class RepositoryGitTrackingInspector:
    """Inspect local Git state without modifying the repository."""

    def __init__(self, repository_root: Path) -> None:
        self._repository_root = repository_root.resolve()

    def is_tracked(self, path: Path) -> bool:
        relative_path = self._relative_path(path)
        result = self._run_git(
            "ls-files",
            "--error-unmatch",
            "--",
            relative_path,
        )
        return result.returncode == 0

    def is_ignored(self, path: Path) -> bool:
        relative_path = self._relative_path(path)
        result = self._run_git("check-ignore", "--quiet", "--", relative_path)
        return result.returncode == 0

    def directory_has_tracked_files(self, path: Path) -> bool:
        relative_path = self._relative_path(path)
        result = self._run_git("ls-files", "--", relative_path)
        return bool(result.stdout.strip())

    def _relative_path(self, path: Path) -> str:
        absolute_path = (
            path.resolve() if path.is_absolute() else (Path.cwd() / path).resolve()
        )
        try:
            return absolute_path.relative_to(self._repository_root).as_posix()
        except ValueError as exc:
            raise ValueError("Git inspection path must stay inside the repository.") from exc

    def _run_git(self, *arguments: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ("git", *arguments),
            cwd=self._repository_root,
            check=False,
            capture_output=True,
            text=True,
            timeout=10,
        )


class FakeStockInfoProvider:
    """Return one parsed stock model."""

    def get_stock_info(self, symbol: str) -> Sequence[StockInfo]:
        return (
            StockInfo(
                stock_code=symbol,
                stock_name="Samsung Electronics",
                market="KOSPI",
                currency="KRW",
            ),
        )


class FakePriceSnapshotProvider:
    """Return one parsed price model."""

    def get_price_snapshots(self, symbol: str) -> Sequence[PriceSnapshot]:
        return (
            PriceSnapshot(
                stock_code=symbol,
                price=_PRICE,
                timestamp=_PRICE_TIMESTAMP,
                currency="KRW",
            ),
        )


class FakeCandlePageProvider:
    """Return one parsed daily candle page."""

    def get_candles(
        self,
        symbol: str,
        *,
        interval: str,
        count: int,
        adjusted: bool,
    ) -> CandlePage:
        del symbol, interval, count, adjusted
        return CandlePage(
            candles=(
                Candle(
                    timestamp=_CANDLE_TIMESTAMP,
                    open=_CANDLE_OPEN,
                    high=_CANDLE_HIGH,
                    low=_CANDLE_LOW,
                    close=_CANDLE_CLOSE,
                    volume=_CANDLE_VOLUME,
                    currency="KRW",
                ),
            ),
            next_before=None,
        )


class FakeExchangeRateProvider:
    """Return one parsed exchange-rate model."""

    def get_exchange_rates(
        self,
        base_currency: str,
        quote_currency: str,
    ) -> Sequence[ExchangeRate]:
        return (
            ExchangeRate(
                base_currency=base_currency,
                quote_currency=quote_currency,
                exchange_rate=_EXCHANGE_RATE,
                date_time=_RATE_TIMESTAMP,
            ),
        )


@dataclass(frozen=True, slots=True)
class FakeSnapshotLocalDbFileSmokeResult:
    """Safe smoke diagnostics without payload, secret, or account fields."""

    success: bool
    phase: str
    requested_symbol: str
    planned_db_relative_path: str
    db_file_creation_allowed_this_stage: bool
    actual_db_file_created: bool
    db_file_git_tracked: bool
    data_directory_git_tracked: bool
    sqlite_file_ignored_by_git: bool
    saved_stock_count: int
    saved_price_snapshot_count: int
    saved_candle_count: int
    saved_exchange_rate_count: int
    repository_round_trip_verified: bool
    decimal_values_preserved: bool
    timestamp_values_preserved: bool
    currency_fields_present: bool
    candle_ohlcv_present: bool
    stock_warnings_deferred: bool
    actual_network_call_performed: bool
    oauth_token_endpoint_called: bool
    env_file_read: bool
    account_seq_used: bool
    real_order_related_call_performed: bool
    safe_message: str

    def safe_dict(self) -> dict[str, bool | int | str]:
        """Return only explicitly safe diagnostic fields."""

        return asdict(self)


def run_fake_snapshot_local_db_file_smoke(
    database_path: str | Path,
    *,
    planned_db_relative_path: str = PLANNED_DB_RELATIVE_PATH,
    git_inspector: GitTrackingInspector | None = None,
) -> FakeSnapshotLocalDbFileSmokeResult:
    """Create one file DB, ingest one fake snapshot, reopen, and verify it."""

    path = Path(database_path)
    if str(database_path) == ":memory:":
        raise ValueError("A SQLite file path is required.")
    if path.suffix.casefold() not in {".sqlite", ".sqlite3", ".db"}:
        raise ValueError("The smoke database must use a SQLite file extension.")
    if path.exists():
        raise FileExistsError("The smoke database path must not already exist.")

    inspector = git_inspector or RepositoryGitTrackingInspector(Path.cwd())
    if (
        inspector.is_tracked(path)
        or inspector.directory_has_tracked_files(Path("data"))
        or not inspector.is_ignored(path)
    ):
        raise RuntimeError("Git safety checks rejected the local database path.")

    connection = create_connection(path)
    try:
        persistence = LocalDataPersistenceService(connection)
        service = ReadOnlySnapshotIngestionService(
            persistence,
            stock_provider=FakeStockInfoProvider(),
            price_provider=FakePriceSnapshotProvider(),
            candle_provider=FakeCandlePageProvider(),
            exchange_rate_provider=FakeExchangeRateProvider(),
        )
        ingestion = service.ingest_snapshot(
            ReadOnlySnapshotIngestionRequest(
                symbol=SMOKE_SYMBOL,
                exchange_base_currency=SMOKE_BASE_CURRENCY,
                exchange_quote_currency=SMOKE_QUOTE_CURRENCY,
                candle_interval=SMOKE_CANDLE_INTERVAL,
                candle_count=SMOKE_CANDLE_COUNT,
                adjusted=SMOKE_ADJUSTED,
            )
        )
    finally:
        close_connection(connection)

    verification_connection = create_connection(path)
    try:
        verification = LocalDataPersistenceService(
            verification_connection,
            initialize=False,
        )
        stocks = verification.list_stocks()
        prices = verification.list_price_snapshots(SMOKE_SYMBOL)
        candles = verification.list_candles(
            SMOKE_SYMBOL,
            SMOKE_CANDLE_INTERVAL,
        )
        rates = verification.list_exchange_rates(
            SMOKE_BASE_CURRENCY,
            SMOKE_QUOTE_CURRENCY,
        )
    finally:
        close_connection(verification_connection)

    counts_match = (
        len(stocks) == ingestion.saved_stock_count == 1
        and len(prices) == ingestion.saved_price_snapshot_count == 1
        and len(candles) == ingestion.saved_candle_count == 1
        and len(rates) == ingestion.saved_exchange_rate_count == 1
    )
    decimals_preserved = (
        prices[0].price == _PRICE
        and candles[0].open == _CANDLE_OPEN
        and candles[0].high == _CANDLE_HIGH
        and candles[0].low == _CANDLE_LOW
        and candles[0].close == _CANDLE_CLOSE
        and candles[0].volume == _CANDLE_VOLUME
        and rates[0].exchange_rate == _EXCHANGE_RATE
    )
    timestamps_preserved = (
        prices[0].timestamp == _PRICE_TIMESTAMP
        and candles[0].timestamp == _CANDLE_TIMESTAMP
        and rates[0].date_time == _RATE_TIMESTAMP
    )
    currency_fields_present = (
        stocks[0].currency == "KRW"
        and prices[0].currency == "KRW"
        and candles[0].currency == "KRW"
        and rates[0].base_currency == "USD"
        and rates[0].quote_currency == "KRW"
    )
    candle_ohlcv_present = all(
        value is not None
        for value in (
            candles[0].open,
            candles[0].high,
            candles[0].low,
            candles[0].close,
            candles[0].volume,
        )
    )
    actual_db_file_created = path.is_file()
    db_file_git_tracked = inspector.is_tracked(path)
    data_directory_git_tracked = inspector.directory_has_tracked_files(Path("data"))
    sqlite_file_ignored_by_git = inspector.is_ignored(path)
    success = (
        ingestion.success
        and counts_match
        and decimals_preserved
        and timestamps_preserved
        and currency_fields_present
        and candle_ohlcv_present
        and ingestion.stock_warnings_deferred
        and not ingestion.actual_network_call_performed
        and actual_db_file_created
        and not db_file_git_tracked
        and not data_directory_git_tracked
        and sqlite_file_ignored_by_git
    )

    return FakeSnapshotLocalDbFileSmokeResult(
        success=success,
        phase="fake_snapshot_local_db_file_smoke",
        requested_symbol=ingestion.requested_symbol,
        planned_db_relative_path=planned_db_relative_path,
        db_file_creation_allowed_this_stage=True,
        actual_db_file_created=actual_db_file_created,
        db_file_git_tracked=db_file_git_tracked,
        data_directory_git_tracked=data_directory_git_tracked,
        sqlite_file_ignored_by_git=sqlite_file_ignored_by_git,
        saved_stock_count=ingestion.saved_stock_count,
        saved_price_snapshot_count=ingestion.saved_price_snapshot_count,
        saved_candle_count=ingestion.saved_candle_count,
        saved_exchange_rate_count=ingestion.saved_exchange_rate_count,
        repository_round_trip_verified=counts_match,
        decimal_values_preserved=decimals_preserved,
        timestamp_values_preserved=timestamps_preserved,
        currency_fields_present=currency_fields_present,
        candle_ohlcv_present=candle_ohlcv_present,
        stock_warnings_deferred=ingestion.stock_warnings_deferred,
        actual_network_call_performed=False,
        oauth_token_endpoint_called=False,
        env_file_read=False,
        account_seq_used=False,
        real_order_related_call_performed=False,
        safe_message=(
            "Fake snapshot persisted to the approved local SQLite file."
            if success
            else "Fake snapshot local SQLite file verification failed."
        ),
    )
