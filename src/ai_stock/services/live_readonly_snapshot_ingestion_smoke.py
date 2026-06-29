"""Single-pass live read-only snapshot ingestion smoke orchestration."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from decimal import Decimal
from enum import Enum
import re
from typing import Any

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
from ai_stock.services.readonly_snapshot_ingestion import (
    ReadOnlySnapshotIngestionRequest,
    ReadOnlySnapshotIngestionService,
)

SMOKE_SYMBOL = "005930"
SMOKE_BASE_CURRENCY = "USD"
SMOKE_QUOTE_CURRENCY = "KRW"
SMOKE_CANDLE_INTERVAL = "1d"
SMOKE_CANDLE_COUNT = 1
SMOKE_CANDLE_ADJUSTED = True

STOCKS_PATH = "/api/v1/stocks"
PRICES_PATH = "/api/v1/prices"
CANDLES_PATH = "/api/v1/candles"
EXCHANGE_RATE_PATH = "/api/v1/exchange-rate"


class LiveSnapshotIngestionPhase(str, Enum):
    """Safe phases for the fixed live ingestion flow."""

    CONFIG_VALIDATION = "config_validation"
    OAUTH_TOKEN = "oauth_token"
    STOCKS = "readonly_stocks"
    PRICES = "readonly_prices"
    CANDLES = "readonly_candles"
    EXCHANGE_RATE = "readonly_exchange_rate"
    PERSISTENCE = "in_memory_persistence"
    REPOSITORY_VERIFICATION = "repository_verification"
    COMPLETE = "live_readonly_snapshot_ingestion"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class EndpointHttpStatus:
    """Safe status for one attempted endpoint."""

    endpoint: str
    status_code: int | None


@dataclass(frozen=True, slots=True)
class LiveReadOnlySnapshotIngestionDiagnostic:
    """Safe diagnostics without credentials, headers, requests, or response bodies."""

    success: bool
    phase: LiveSnapshotIngestionPhase
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
    actual_db_file_created: bool
    account_seq_used: bool
    real_order_related_call_performed: bool
    token_raw_output_or_storage: bool
    credential_raw_output_or_storage: bool
    authorization_bearer_raw_output_or_storage: bool
    raw_response_body_stored: bool

    def safe_dict(self) -> dict[str, object]:
        """Return the approved non-sensitive diagnostic shape."""

        return {
            "success": self.success,
            "phase": self.phase.value,
            "failed_endpoint": self.failed_endpoint,
            "endpoint_http_status_codes": {
                item.endpoint: item.status_code
                for item in self.endpoint_http_statuses
            },
            "safe_error_code": self.safe_error_code,
            "safe_error_type": self.safe_error_type,
            "safe_error_message": self.safe_error_message,
            "oauth_token_endpoint_call_count": (
                self.oauth_token_endpoint_call_count
            ),
            "business_api_call_count": self.business_api_call_count,
            "total_network_call_count": self.total_network_call_count,
            "requested_symbol": self.requested_symbol,
            "exchange_rate_pair": self.exchange_rate_pair,
            "candle_query": {
                "interval": self.candle_interval,
                "count": self.candle_count,
                "adjusted": self.candle_adjusted,
                "before_parameter_used": self.candle_before_used,
            },
            "saved_stock_count": self.saved_stock_count,
            "saved_price_snapshot_count": self.saved_price_snapshot_count,
            "saved_candle_count": self.saved_candle_count,
            "saved_exchange_rate_count": self.saved_exchange_rate_count,
            "repository_round_trip_verified": (
                self.repository_round_trip_verified
            ),
            "decimal_values_preserved": self.decimal_values_preserved,
            "timestamp_values_preserved": self.timestamp_values_preserved,
            "currency_fields_present": self.currency_fields_present,
            "candle_ohlcv_present": self.candle_ohlcv_present,
            "stock_warnings_deferred": self.stock_warnings_deferred,
            "actual_db_file_created": self.actual_db_file_created,
            "account_seq_used": self.account_seq_used,
            "real_order_related_call_performed": (
                self.real_order_related_call_performed
            ),
            "token_raw_output_or_storage": self.token_raw_output_or_storage,
            "credential_raw_output_or_storage": (
                self.credential_raw_output_or_storage
            ),
            "authorization_bearer_raw_output_or_storage": (
                self.authorization_bearer_raw_output_or_storage
            ),
            "raw_response_body_stored": self.raw_response_body_stored,
        }


@dataclass(frozen=True, slots=True)
class _ExpectedCall:
    method: str
    path: str
    query: tuple[tuple[str, str], ...] = ()

    @property
    def endpoint(self) -> str:
        return f"{self.method} {self.path}"


_EXPECTED_CALLS = (
    _ExpectedCall("POST", OAUTH_TOKEN_PATH),
    _ExpectedCall("GET", STOCKS_PATH, (("symbols", SMOKE_SYMBOL),)),
    _ExpectedCall("GET", PRICES_PATH, (("symbols", SMOKE_SYMBOL),)),
    _ExpectedCall(
        "GET",
        CANDLES_PATH,
        (
            ("symbol", SMOKE_SYMBOL),
            ("interval", SMOKE_CANDLE_INTERVAL),
            ("count", str(SMOKE_CANDLE_COUNT)),
            ("adjusted", "true"),
        ),
    ),
    _ExpectedCall(
        "GET",
        EXCHANGE_RATE_PATH,
        (
            ("baseCurrency", SMOKE_BASE_CURRENCY),
            ("quoteCurrency", SMOKE_QUOTE_CURRENCY),
        ),
    ),
)


class _StrictFiveCallSession:
    """Wrap one client and reject out-of-order, altered, or extra sends."""

    def __init__(self, client: httpx.Client) -> None:
        self._client = client
        self._attempted: list[_ExpectedCall] = []
        self._statuses: dict[str, int | None] = {}

    @property
    def attempted_calls(self) -> tuple[_ExpectedCall, ...]:
        return tuple(self._attempted)

    @property
    def endpoint_http_statuses(self) -> tuple[EndpointHttpStatus, ...]:
        return tuple(
            EndpointHttpStatus(
                endpoint=call.endpoint,
                status_code=self._statuses.get(call.endpoint),
            )
            for call in self._attempted
        )

    @property
    def oauth_call_count(self) -> int:
        return sum(call.path == OAUTH_TOKEN_PATH for call in self._attempted)

    @property
    def business_call_count(self) -> int:
        return len(self._attempted) - self.oauth_call_count

    @property
    def total_call_count(self) -> int:
        return len(self._attempted)

    @property
    def completed(self) -> bool:
        return tuple(self._attempted) == _EXPECTED_CALLS

    def post(self, path: str, **kwargs: Any) -> httpx.Response:
        expected = self._validate_attempt("POST", path, ())
        try:
            response = self._client.post(path, **kwargs)
        except httpx.HTTPError:
            self._statuses[expected.endpoint] = None
            raise
        self._statuses[expected.endpoint] = response.status_code
        return response

    def build_request(self, *args: Any, **kwargs: Any) -> httpx.Request:
        return self._client.build_request(*args, **kwargs)

    def send(self, request: httpx.Request) -> httpx.Response:
        query = tuple(sorted(request.url.params.multi_items()))
        expected = self._validate_attempt(
            request.method,
            request.url.path,
            query,
        )
        try:
            response = self._client.send(request, follow_redirects=False)
        except httpx.HTTPError:
            self._statuses[expected.endpoint] = None
            raise
        self._statuses[expected.endpoint] = response.status_code
        return response

    def _validate_attempt(
        self,
        method: str,
        path: str,
        query: tuple[tuple[str, str], ...],
    ) -> _ExpectedCall:
        index = len(self._attempted)
        if index >= len(_EXPECTED_CALLS):
            raise TossClientConfigError("The approved five-call limit was exceeded.")
        expected = _EXPECTED_CALLS[index]
        normalized_query = tuple(sorted(query))
        if (
            method.upper() != expected.method
            or path != expected.path
            or normalized_query != tuple(sorted(expected.query))
        ):
            raise TossClientConfigError(
                "The network request did not match the approved call plan."
            )
        self._attempted.append(expected)
        self._statuses[expected.endpoint] = None
        return expected


@dataclass(slots=True)
class _SmokeState:
    phase: LiveSnapshotIngestionPhase = LiveSnapshotIngestionPhase.CONFIG_VALIDATION
    failed_endpoint: str | None = None
    saved_stock_count: int = 0
    saved_price_snapshot_count: int = 0
    saved_candle_count: int = 0
    saved_exchange_rate_count: int = 0
    repository_round_trip_verified: bool = False
    decimal_values_preserved: bool = False
    timestamp_values_preserved: bool = False
    currency_fields_present: bool = False
    candle_ohlcv_present: bool = False


class _ParsedStockProvider:
    def __init__(self, stocks: Sequence[StockInfo]) -> None:
        self._stocks = tuple(stocks)

    def get_stock_info(self, symbol: str) -> tuple[StockInfo, ...]:
        if len(self._stocks) != 1 or self._stocks[0].stock_code != symbol:
            raise ValueError("Parsed StockInfo did not match the requested symbol.")
        return self._stocks


class _ParsedPriceProvider:
    def __init__(self, prices: Sequence[PriceSnapshot]) -> None:
        self._prices = tuple(prices)

    def get_price_snapshots(self, symbol: str) -> tuple[PriceSnapshot, ...]:
        if len(self._prices) != 1 or self._prices[0].stock_code != symbol:
            raise ValueError("Parsed PriceSnapshot did not match the requested symbol.")
        return self._prices


class _ParsedCandleProvider:
    def __init__(self, page: CandlePage) -> None:
        self._page = page

    def get_candles(
        self,
        symbol: str,
        *,
        interval: str,
        count: int,
        adjusted: bool,
    ) -> CandlePage:
        if (
            symbol != SMOKE_SYMBOL
            or interval != SMOKE_CANDLE_INTERVAL
            or count != SMOKE_CANDLE_COUNT
            or adjusted is not SMOKE_CANDLE_ADJUSTED
            or len(self._page.candles) != 1
        ):
            raise ValueError("Parsed CandlePage did not match the approved query.")
        return self._page


class _ParsedExchangeRateProvider:
    def __init__(self, rate: ExchangeRate) -> None:
        self._rate = rate

    def get_exchange_rates(
        self,
        base_currency: str,
        quote_currency: str,
    ) -> tuple[ExchangeRate, ...]:
        if (
            self._rate.base_currency != base_currency
            or self._rate.quote_currency != quote_currency
        ):
            raise ValueError("Parsed ExchangeRate did not match the requested pair.")
        return (self._rate,)


def execute_live_readonly_snapshot_ingestion_smoke(
    http_client: httpx.Client,
    request: OAuthTokenRequest,
    safety_gate: LiveApiSafetyGate,
    *,
    allow_live_api: bool,
    allow_real_order: bool,
    dry_run_only: bool,
    live_ingestion_smoke_allowed: bool,
) -> LiveReadOnlySnapshotIngestionDiagnostic:
    """Perform the approved five-call flow once, then persist in memory."""

    session = _StrictFiveCallSession(http_client)
    state = _SmokeState()
    connection = None
    try:
        _validate_configuration(
            allow_live_api=allow_live_api,
            allow_real_order=allow_real_order,
            dry_run_only=dry_run_only,
            live_ingestion_smoke_allowed=live_ingestion_smoke_allowed,
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
            TossEndpointMetadata(
                method="GET",
                path=STOCKS_PATH,
                endpoint_category="stock_info",
                requires_auth=True,
                requires_account_seq=False,
            ),
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
            TossEndpointMetadata(
                method="GET",
                path=PRICES_PATH,
                endpoint_category="market_data",
                requires_auth=True,
                requires_account_seq=False,
            ),
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
            TossEndpointMetadata(
                method="GET",
                path=CANDLES_PATH,
                endpoint_category="market_data",
                requires_auth=True,
                requires_account_seq=False,
            ),
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
            TossEndpointMetadata(
                method="GET",
                path=EXCHANGE_RATE_PATH,
                endpoint_category="market_info",
                requires_auth=True,
                requires_account_seq=False,
            ),
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
            raise TossClientConfigError("The approved call plan was not completed.")

        state.phase = LiveSnapshotIngestionPhase.PERSISTENCE
        state.failed_endpoint = None
        connection = create_connection(":memory:")
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

        state.phase = LiveSnapshotIngestionPhase.REPOSITORY_VERIFICATION
        _verify_repository_round_trip(
            state,
            persistence=persistence,
            stocks=stocks,
            prices=prices,
            candle_page=candle_page,
            exchange_rate=exchange_rate,
        )
        state.phase = LiveSnapshotIngestionPhase.COMPLETE
        return _diagnostic(
            state,
            session,
            success=True,
            safe_error_code=None,
            safe_error_type=None,
            safe_error_message=None,
        )
    except TossApiError as error:
        return _diagnostic(
            state,
            session,
            success=False,
            safe_error_code=_safe_error_code(error.error_code),
            safe_error_type=_safe_error_type(state.phase, error.status_code),
            safe_error_message=_safe_error_message(error.status_code),
        )
    except httpx.HTTPError as error:
        error_type = (
            "timeout" if isinstance(error, httpx.TimeoutException) else "network_error"
        )
        message = (
            "Network request timed out."
            if isinstance(error, httpx.TimeoutException)
            else "Network request failed."
        )
        return _diagnostic(
            state,
            session,
            success=False,
            safe_error_code=None,
            safe_error_type=error_type,
            safe_error_message=message,
        )
    except (TossClientConfigError, ValueError):
        return _diagnostic(
            state,
            session,
            success=False,
            safe_error_code=None,
            safe_error_type="validation_failed",
            safe_error_message="Live snapshot ingestion validation failed safely.",
        )
    except RuntimeError:
        return _diagnostic(
            state,
            session,
            success=False,
            safe_error_code=None,
            safe_error_type="runtime_failure",
            safe_error_message="Live snapshot ingestion failed safely.",
        )
    finally:
        if connection is not None:
            close_connection(connection)


def _validate_configuration(
    *,
    allow_live_api: bool,
    allow_real_order: bool,
    dry_run_only: bool,
    live_ingestion_smoke_allowed: bool,
) -> None:
    if not allow_live_api:
        raise TossClientConfigError("Live API must be explicitly enabled.")
    if allow_real_order:
        raise TossClientConfigError("Real-order mode is forbidden.")
    if not dry_run_only:
        raise TossClientConfigError("Dry-run-only mode is required.")
    if not live_ingestion_smoke_allowed:
        raise TossClientConfigError("Explicit live ingestion approval is required.")


def _send_allowed(
    session: _StrictFiveCallSession,
    safety_gate: LiveApiSafetyGate,
    metadata: TossEndpointMetadata,
    *,
    request_factory: Callable[[], httpx.Request],
    parser: Callable[[httpx.Response], Any],
    allow_live_api: bool,
    allow_real_order: bool,
    dry_run_only: bool,
) -> Any:
    decision = safety_gate.evaluate(
        metadata,
        live_api_enabled=allow_live_api,
        real_order_allowed=allow_real_order,
        dry_run_only=dry_run_only,
        send_requested=False,
    )
    if (
        not decision.allowed
        or not decision.is_read_only
        or decision.requires_account_seq
    ):
        raise TossClientConfigError("Safety Gate blocked the business endpoint.")
    request = request_factory()
    if "X-Tossinvest-Account" in request.headers:
        raise TossClientConfigError("Account header is forbidden.")
    response = session.send(request)
    return parser(response)


def _verify_repository_round_trip(
    state: _SmokeState,
    *,
    persistence: LocalDataPersistenceService,
    stocks: Sequence[StockInfo],
    prices: Sequence[PriceSnapshot],
    candle_page: CandlePage,
    exchange_rate: ExchangeRate,
) -> None:
    stored_stocks = persistence.list_stocks()
    stored_prices = persistence.list_price_snapshots(SMOKE_SYMBOL)
    stored_candles = persistence.list_candles(
        SMOKE_SYMBOL,
        SMOKE_CANDLE_INTERVAL,
    )
    stored_rates = persistence.list_exchange_rates(
        SMOKE_BASE_CURRENCY,
        SMOKE_QUOTE_CURRENCY,
    )
    expected_counts = (
        len(stored_stocks),
        len(stored_prices),
        len(stored_candles),
        len(stored_rates),
    )
    if expected_counts != (1, 1, 1, 1):
        raise ValueError("Repository round-trip counts were invalid.")

    source_price = prices[0]
    source_candle = candle_page.candles[0]
    source_rate = exchange_rate
    stored_price = stored_prices[0]
    stored_candle = stored_candles[0]
    stored_rate = stored_rates[0]
    decimal_values_preserved = (
        stored_price.price == source_price.price
        and _candle_decimals(stored_candle) == _candle_decimals(source_candle)
        and stored_rate.exchange_rate == source_rate.exchange_rate
    )
    timestamp_values_preserved = (
        stored_price.timestamp == source_price.timestamp
        and stored_candle.timestamp == source_candle.timestamp
        and stored_rate.date_time == source_rate.date_time
    )
    currency_fields_present = (
        bool(stocks[0].currency)
        and bool(source_price.currency)
        and bool(source_candle.currency)
    )
    candle_ohlcv_present = all(
        isinstance(value, Decimal)
        for value in _candle_decimals(source_candle)
    )
    if not (
        decimal_values_preserved
        and timestamp_values_preserved
        and currency_fields_present
        and candle_ohlcv_present
    ):
        raise ValueError("Repository round-trip values were invalid.")

    state.repository_round_trip_verified = True
    state.decimal_values_preserved = decimal_values_preserved
    state.timestamp_values_preserved = timestamp_values_preserved
    state.currency_fields_present = currency_fields_present
    state.candle_ohlcv_present = candle_ohlcv_present


def _candle_decimals(candle: Candle) -> tuple[Decimal, ...]:
    return (
        candle.open,
        candle.high,
        candle.low,
        candle.close,
        candle.volume,
    )


def _diagnostic(
    state: _SmokeState,
    session: _StrictFiveCallSession,
    *,
    success: bool,
    safe_error_code: str | None,
    safe_error_type: str | None,
    safe_error_message: str | None,
) -> LiveReadOnlySnapshotIngestionDiagnostic:
    return LiveReadOnlySnapshotIngestionDiagnostic(
        success=success,
        phase=state.phase,
        failed_endpoint=None if success else state.failed_endpoint,
        endpoint_http_statuses=session.endpoint_http_statuses,
        safe_error_code=safe_error_code,
        safe_error_type=safe_error_type,
        safe_error_message=safe_error_message,
        oauth_token_endpoint_call_count=session.oauth_call_count,
        business_api_call_count=session.business_call_count,
        total_network_call_count=session.total_call_count,
        requested_symbol=SMOKE_SYMBOL,
        exchange_rate_pair=f"{SMOKE_BASE_CURRENCY}/{SMOKE_QUOTE_CURRENCY}",
        candle_interval=SMOKE_CANDLE_INTERVAL,
        candle_count=SMOKE_CANDLE_COUNT,
        candle_adjusted=SMOKE_CANDLE_ADJUSTED,
        candle_before_used=False,
        saved_stock_count=state.saved_stock_count,
        saved_price_snapshot_count=state.saved_price_snapshot_count,
        saved_candle_count=state.saved_candle_count,
        saved_exchange_rate_count=state.saved_exchange_rate_count,
        repository_round_trip_verified=state.repository_round_trip_verified,
        decimal_values_preserved=state.decimal_values_preserved,
        timestamp_values_preserved=state.timestamp_values_preserved,
        currency_fields_present=state.currency_fields_present,
        candle_ohlcv_present=state.candle_ohlcv_present,
        stock_warnings_deferred=True,
        actual_db_file_created=False,
        account_seq_used=False,
        real_order_related_call_performed=False,
        token_raw_output_or_storage=False,
        credential_raw_output_or_storage=False,
        authorization_bearer_raw_output_or_storage=False,
        raw_response_body_stored=False,
    )


def _safe_error_code(error_code: str | None) -> str | None:
    if error_code is None:
        return None
    return error_code if re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", error_code) else None


def _safe_error_type(
    phase: LiveSnapshotIngestionPhase,
    status_code: int | None,
) -> str:
    if phase is LiveSnapshotIngestionPhase.OAUTH_TOKEN:
        return "oauth_failed"
    if status_code == 429:
        return "rate_limited"
    if status_code is not None and status_code >= 500:
        return "server_error"
    if status_code is not None and status_code >= 400:
        return "http_error"
    return "response_parse_failed"


def _safe_error_message(status_code: int | None) -> str:
    if status_code is None:
        return "Request or response parsing failed safely."
    return f"HTTP request failed with status {status_code}."
