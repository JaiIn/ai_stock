"""Single-pass live read-only snapshot persistence to an existing SQLite file."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import httpx

from ai_stock.clients.config import TossClientConfig
from ai_stock.clients.exceptions import TossApiError, TossClientConfigError
from ai_stock.clients.foundation import TossClientFoundation
from ai_stock.clients.market_data import TossMarketDataClient
from ai_stock.clients.market_info import TossMarketInfoClient
from ai_stock.clients.oauth import OAUTH_TOKEN_PATH, TossOAuthTokenProvider
from ai_stock.clients.request_context import AuthenticatedRequestContext
from ai_stock.clients.stock_info import TossStockInfoClient
from ai_stock.models import (
    Candle,
    CandlePage,
    ExchangeRate,
    OAuthTokenRequest,
    PriceSnapshot,
    StockInfo,
)
from ai_stock.repositories import close_connection, create_connection
from ai_stock.risk import LiveApiSafetyGate, TossEndpointMetadata
from ai_stock.services.data_persistence import LocalDataPersistenceService
from ai_stock.services.live_readonly_snapshot_ingestion_smoke import (
    CANDLES_PATH,
    EXCHANGE_RATE_PATH,
    PRICES_PATH,
    SMOKE_BASE_CURRENCY,
    SMOKE_CANDLE_ADJUSTED,
    SMOKE_CANDLE_COUNT,
    SMOKE_CANDLE_INTERVAL,
    SMOKE_QUOTE_CURRENCY,
    SMOKE_SYMBOL,
    STOCKS_PATH,
    EndpointHttpStatus,
    LiveSnapshotIngestionPhase,
    _ParsedCandleProvider,
    _ParsedExchangeRateProvider,
    _ParsedPriceProvider,
    _ParsedStockProvider,
    _StrictFiveCallSession,
    _safe_error_code,
    _safe_error_message,
    _safe_error_type,
    _send_allowed,
    _validate_configuration,
)
from ai_stock.services.readonly_snapshot_ingestion import (
    ReadOnlySnapshotIngestionRequest,
    ReadOnlySnapshotIngestionService,
)
from ai_stock.storage.live_snapshot_local_db_preflight import (
    PLANNED_DB_RELATIVE_PATH,
)
from ai_stock.storage.local_snapshot_db_smoke import (
    GitTrackingInspector,
    RepositoryGitTrackingInspector,
)


@dataclass(frozen=True, slots=True)
class RepositoryCounts:
    stocks: int = 0
    price_snapshots: int = 0
    candles: int = 0
    exchange_rates: int = 0


@dataclass(frozen=True, slots=True)
class DbFileMetadata:
    size_bytes: int | None
    modified_time_utc: str | None


@dataclass(frozen=True, slots=True)
class LiveSnapshotLocalDbSmokeDiagnostic:
    success: bool
    phase: str
    failed_endpoint: str | None
    endpoint_http_statuses: tuple[EndpointHttpStatus, ...]
    safe_error_code: str | None
    safe_error_type: str | None
    safe_error_message: str | None
    oauth_token_endpoint_call_count: int
    business_api_call_count: int
    total_network_call_count: int
    requested_symbol: str
    exchange_rate_pair: str
    candle_interval: str
    candle_count: int
    candle_adjusted: bool
    candle_before_used: bool
    repository_counts_before: RepositoryCounts
    repository_counts_after: RepositoryCounts
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
    planned_db_relative_path: str
    db_file_write_allowed_this_stage: bool
    actual_db_file_modified_this_stage: bool
    db_write_performed: bool
    db_file_metadata_before: DbFileMetadata
    db_file_metadata_after: DbFileMetadata
    db_file_git_tracked: bool
    data_directory_git_tracked: bool
    sqlite_file_ignored_by_git: bool
    account_seq_used: bool
    real_order_related_call_performed: bool
    token_raw_output_or_storage: bool
    credential_raw_output_or_storage: bool
    authorization_bearer_raw_output_or_storage: bool
    raw_response_body_stored: bool

    def safe_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(slots=True)
class _State:
    phase: LiveSnapshotIngestionPhase = LiveSnapshotIngestionPhase.CONFIG_VALIDATION
    failed_endpoint: str | None = None
    before: RepositoryCounts = RepositoryCounts()
    after: RepositoryCounts = RepositoryCounts()
    saved_stock_count: int = 0
    saved_price_snapshot_count: int = 0
    saved_candle_count: int = 0
    saved_exchange_rate_count: int = 0
    round_trip: bool = False
    decimals: bool = False
    timestamps: bool = False
    currencies: bool = False
    ohlcv: bool = False
    db_write_performed: bool = False


def execute_live_snapshot_local_db_file_smoke(
    http_client: httpx.Client,
    request: OAuthTokenRequest,
    safety_gate: LiveApiSafetyGate,
    database_path: str | Path,
    *,
    allow_live_api: bool,
    allow_real_order: bool,
    dry_run_only: bool,
    live_file_smoke_allowed: bool,
    git_inspector: GitTrackingInspector | None = None,
) -> LiveSnapshotLocalDbSmokeDiagnostic:
    """Execute exactly five approved calls and append to an existing file DB."""

    path = Path(database_path)
    session = _StrictFiveCallSession(http_client)
    state = _State()
    before_meta = _metadata(path)
    error_code = error_type = error_message = None
    connection = None
    inspector = git_inspector or RepositoryGitTrackingInspector(Path.cwd())
    try:
        _validate_path_and_git(path, inspector)
        state.before = _repository_counts(path)
        _validate_configuration(
            allow_live_api=allow_live_api,
            allow_real_order=allow_real_order,
            dry_run_only=dry_run_only,
            live_ingestion_smoke_allowed=live_file_smoke_allowed,
        )
        state.phase = LiveSnapshotIngestionPhase.OAUTH_TOKEN
        state.failed_endpoint = f"POST {OAUTH_TOKEN_PATH}"
        token = TossOAuthTokenProvider(
            session,  # type: ignore[arg-type]
            allow_live_api=allow_live_api,
            allow_real_order=allow_real_order,
            dry_run_only=dry_run_only,
        ).acquire_token(request)
        context = AuthenticatedRequestContext.from_token(token)
        if context.has_account:
            raise TossClientConfigError("Account context is forbidden.")
        foundation = TossClientFoundation(
            TossClientConfig(allow_live_api=True),
            http_client=session,  # type: ignore[arg-type]
        )
        stock_client = TossStockInfoClient(foundation, context)
        market_data_client = TossMarketDataClient(foundation, context)
        market_info_client = TossMarketInfoClient(foundation, context)

        state.phase = LiveSnapshotIngestionPhase.STOCKS
        state.failed_endpoint = f"GET {STOCKS_PATH}"
        stocks = _send_allowed(
            session,
            safety_gate,
            _metadata_for(STOCKS_PATH, "stock_info"),
            request_factory=lambda: stock_client.get_stocks([SMOKE_SYMBOL]),
            parser=TossStockInfoClient.parse_stocks_response,
            allow_live_api=allow_live_api,
            allow_real_order=allow_real_order,
            dry_run_only=dry_run_only,
        )
        state.phase = LiveSnapshotIngestionPhase.PRICES
        state.failed_endpoint = f"GET {PRICES_PATH}"
        prices = _send_allowed(
            session,
            safety_gate,
            _metadata_for(PRICES_PATH, "market_data"),
            request_factory=lambda: market_data_client.get_prices([SMOKE_SYMBOL]),
            parser=TossMarketDataClient.parse_prices_response,
            allow_live_api=allow_live_api,
            allow_real_order=allow_real_order,
            dry_run_only=dry_run_only,
        )
        state.phase = LiveSnapshotIngestionPhase.CANDLES
        state.failed_endpoint = f"GET {CANDLES_PATH}"
        candle_page = _send_allowed(
            session,
            safety_gate,
            _metadata_for(CANDLES_PATH, "market_data"),
            request_factory=lambda: market_data_client.get_candles(
                SMOKE_SYMBOL,
                interval=SMOKE_CANDLE_INTERVAL,
                count=SMOKE_CANDLE_COUNT,
                adjusted=SMOKE_CANDLE_ADJUSTED,
            ),
            parser=TossMarketDataClient.parse_candles_response,
            allow_live_api=allow_live_api,
            allow_real_order=allow_real_order,
            dry_run_only=dry_run_only,
        )
        state.phase = LiveSnapshotIngestionPhase.EXCHANGE_RATE
        state.failed_endpoint = f"GET {EXCHANGE_RATE_PATH}"
        exchange_rate = _send_allowed(
            session,
            safety_gate,
            _metadata_for(EXCHANGE_RATE_PATH, "market_info"),
            request_factory=lambda: market_info_client.get_exchange_rate(
                base_currency=SMOKE_BASE_CURRENCY,
                quote_currency=SMOKE_QUOTE_CURRENCY,
            ),
            parser=TossMarketInfoClient.parse_exchange_rate_response,
            allow_live_api=allow_live_api,
            allow_real_order=allow_real_order,
            dry_run_only=dry_run_only,
        )
        if not session.completed:
            raise TossClientConfigError("Approved call plan was not completed.")

        state.phase = LiveSnapshotIngestionPhase.PERSISTENCE
        state.failed_endpoint = None
        connection = create_connection(path)
        state.db_write_performed = True
        persistence = LocalDataPersistenceService(connection)
        ingestion = ReadOnlySnapshotIngestionService(
            persistence,
            stock_provider=_ParsedStockProvider(stocks),
            price_provider=_ParsedPriceProvider(prices),
            candle_provider=_ParsedCandleProvider(candle_page),
            exchange_rate_provider=_ParsedExchangeRateProvider(exchange_rate),
        ).ingest_snapshot(
            ReadOnlySnapshotIngestionRequest(
                symbol=SMOKE_SYMBOL,
                exchange_base_currency=SMOKE_BASE_CURRENCY,
                exchange_quote_currency=SMOKE_QUOTE_CURRENCY,
                candle_interval=SMOKE_CANDLE_INTERVAL,
                candle_count=SMOKE_CANDLE_COUNT,
                adjusted=SMOKE_CANDLE_ADJUSTED,
            )
        )
        state.saved_stock_count = ingestion.saved_stock_count
        state.saved_price_snapshot_count = ingestion.saved_price_snapshot_count
        state.saved_candle_count = ingestion.saved_candle_count
        state.saved_exchange_rate_count = ingestion.saved_exchange_rate_count
        close_connection(connection)
        connection = None

        state.phase = LiveSnapshotIngestionPhase.REPOSITORY_VERIFICATION
        state.after = _repository_counts(path)
        _verify(state, path, stocks, prices, candle_page, exchange_rate)
        state.phase = LiveSnapshotIngestionPhase.COMPLETE
    except TossApiError as error:
        error_code = _safe_error_code(error.error_code)
        error_type = _safe_error_type(state.phase, error.status_code)
        error_message = _safe_error_message(error.status_code)
    except httpx.HTTPError as error:
        error_type = (
            "timeout" if isinstance(error, httpx.TimeoutException) else "network_error"
        )
        error_message = (
            "Network request timed out."
            if isinstance(error, httpx.TimeoutException)
            else "Network request failed."
        )
    except (TossClientConfigError, ValueError, FileNotFoundError):
        error_type = "validation_failed"
        error_message = "Live snapshot file DB validation failed safely."
    except RuntimeError:
        error_type = "runtime_failure"
        error_message = "Live snapshot file DB smoke failed safely."
    finally:
        if connection is not None:
            close_connection(connection)

    after_meta = _metadata(path)
    modified = before_meta != after_meta
    tracked = inspector.is_tracked(path)
    data_tracked = inspector.directory_has_tracked_files(Path("data"))
    ignored = inspector.is_ignored(path)
    success = (
        state.phase is LiveSnapshotIngestionPhase.COMPLETE
        and session.completed
        and state.round_trip
        and state.db_write_performed
        and modified
        and not tracked
        and not data_tracked
        and ignored
    )
    return LiveSnapshotLocalDbSmokeDiagnostic(
        success=success,
        phase=(
            "live_snapshot_local_db_file_smoke"
            if success
            else state.phase.value
        ),
        failed_endpoint=None if success else state.failed_endpoint,
        endpoint_http_statuses=session.endpoint_http_statuses,
        safe_error_code=error_code,
        safe_error_type=error_type,
        safe_error_message=error_message,
        oauth_token_endpoint_call_count=session.oauth_call_count,
        business_api_call_count=session.business_call_count,
        total_network_call_count=session.total_call_count,
        requested_symbol=SMOKE_SYMBOL,
        exchange_rate_pair=f"{SMOKE_BASE_CURRENCY}/{SMOKE_QUOTE_CURRENCY}",
        candle_interval=SMOKE_CANDLE_INTERVAL,
        candle_count=SMOKE_CANDLE_COUNT,
        candle_adjusted=SMOKE_CANDLE_ADJUSTED,
        candle_before_used=False,
        repository_counts_before=state.before,
        repository_counts_after=state.after,
        saved_stock_count=state.saved_stock_count,
        saved_price_snapshot_count=state.saved_price_snapshot_count,
        saved_candle_count=state.saved_candle_count,
        saved_exchange_rate_count=state.saved_exchange_rate_count,
        repository_round_trip_verified=state.round_trip,
        decimal_values_preserved=state.decimals,
        timestamp_values_preserved=state.timestamps,
        currency_fields_present=state.currencies,
        candle_ohlcv_present=state.ohlcv,
        stock_warnings_deferred=True,
        planned_db_relative_path=PLANNED_DB_RELATIVE_PATH,
        db_file_write_allowed_this_stage=True,
        actual_db_file_modified_this_stage=modified,
        db_write_performed=state.db_write_performed,
        db_file_metadata_before=before_meta,
        db_file_metadata_after=after_meta,
        db_file_git_tracked=tracked,
        data_directory_git_tracked=data_tracked,
        sqlite_file_ignored_by_git=ignored,
        account_seq_used=False,
        real_order_related_call_performed=False,
        token_raw_output_or_storage=False,
        credential_raw_output_or_storage=False,
        authorization_bearer_raw_output_or_storage=False,
        raw_response_body_stored=False,
    )


def _metadata(path: Path) -> DbFileMetadata:
    if not path.is_file():
        return DbFileMetadata(None, None)
    stat = path.stat()
    modified = datetime.fromtimestamp(stat.st_mtime, tz=UTC).isoformat()
    return DbFileMetadata(stat.st_size, modified)


def _validate_path_and_git(path: Path, inspector: GitTrackingInspector) -> None:
    if not path.is_file():
        raise FileNotFoundError("Existing database file is required.")
    if path.suffix.casefold() not in {".sqlite", ".sqlite3", ".db"}:
        raise ValueError("SQLite file extension is required.")
    if (
        inspector.is_tracked(path)
        or inspector.directory_has_tracked_files(Path("data"))
        or not inspector.is_ignored(path)
    ):
        raise RuntimeError("Git safety checks rejected the database path.")


def _metadata_for(path: str, category: str) -> TossEndpointMetadata:
    return TossEndpointMetadata(
        method="GET",
        path=path,
        endpoint_category=category,
        requires_auth=True,
        requires_account_seq=False,
    )


def _repository_counts(path: Path) -> RepositoryCounts:
    connection = create_connection(path)
    try:
        persistence = LocalDataPersistenceService(connection, initialize=False)
        return RepositoryCounts(
            stocks=len(persistence.list_stocks()),
            price_snapshots=len(persistence.list_price_snapshots(SMOKE_SYMBOL)),
            candles=len(
                persistence.list_candles(SMOKE_SYMBOL, SMOKE_CANDLE_INTERVAL)
            ),
            exchange_rates=len(
                persistence.list_exchange_rates(
                    SMOKE_BASE_CURRENCY,
                    SMOKE_QUOTE_CURRENCY,
                )
            ),
        )
    finally:
        close_connection(connection)


def _verify(
    state: _State,
    path: Path,
    stocks: Sequence[StockInfo],
    prices: Sequence[PriceSnapshot],
    candle_page: CandlePage,
    exchange_rate: ExchangeRate,
) -> None:
    if (
        state.after.stocks < state.before.stocks
        or state.after.price_snapshots != state.before.price_snapshots + 1
        or state.after.candles != state.before.candles + 1
        or state.after.exchange_rates != state.before.exchange_rates + 1
    ):
        raise ValueError("Repository count change was invalid.")
    connection = create_connection(path)
    try:
        persistence = LocalDataPersistenceService(connection, initialize=False)
        stored_stocks = persistence.list_stocks()
        stored_prices = persistence.list_price_snapshots(SMOKE_SYMBOL)
        stored_candles = persistence.list_candles(
            SMOKE_SYMBOL, SMOKE_CANDLE_INTERVAL
        )
        stored_rates = persistence.list_exchange_rates(
            SMOKE_BASE_CURRENCY, SMOKE_QUOTE_CURRENCY
        )
    finally:
        close_connection(connection)
    source_price = prices[0]
    source_candle = candle_page.candles[0]
    state.decimals = (
        any(item.price == source_price.price for item in stored_prices)
        and any(_candle_values(item) == _candle_values(source_candle) for item in stored_candles)
        and any(item.exchange_rate == exchange_rate.exchange_rate for item in stored_rates)
    )
    state.timestamps = (
        any(item.timestamp == source_price.timestamp for item in stored_prices)
        and any(item.timestamp == source_candle.timestamp for item in stored_candles)
        and any(item.date_time == exchange_rate.date_time for item in stored_rates)
    )
    state.currencies = (
        any(item.stock_code == SMOKE_SYMBOL and item.currency for item in stored_stocks)
        and bool(source_price.currency)
        and bool(source_candle.currency)
    )
    state.ohlcv = all(isinstance(value, Decimal) for value in _candle_values(source_candle))
    state.round_trip = all(
        (
            any(item.stock_code == SMOKE_SYMBOL for item in stored_stocks),
            state.decimals,
            state.timestamps,
            state.currencies,
            state.ohlcv,
            len(stocks) == 1,
        )
    )
    if not state.round_trip:
        raise ValueError("Repository round-trip verification failed.")


def _candle_values(candle: Candle) -> tuple[Decimal, ...]:
    return candle.open, candle.high, candle.low, candle.close, candle.volume
