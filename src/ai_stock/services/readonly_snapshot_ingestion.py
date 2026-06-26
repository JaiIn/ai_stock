"""Read-only snapshot ingestion service for parsed provider results.

This service intentionally accepts only dependency-injected providers that return
already parsed domain models. It does not import Toss API clients, OAuth
providers, authenticated request contexts, HTTP transports, or environment
configuration.
"""

from collections.abc import Sequence
from dataclasses import dataclass
import re
from typing import Protocol

from ai_stock.models import Candle, CandlePage, ExchangeRate, PriceSnapshot, StockInfo
from ai_stock.services.data_persistence import LocalDataPersistenceService

_SYMBOL_PATTERN = re.compile(r"^[A-Za-z0-9.-]+$")
_CANDLE_INTERVALS = frozenset({"1m", "1d"})


class StockInfoSnapshotProvider(Protocol):
    """Provider for parsed StockInfo snapshots."""

    def get_stock_info(self, symbol: str) -> Sequence[StockInfo]:
        """Return parsed stock metadata for the requested symbol."""


class PriceSnapshotProvider(Protocol):
    """Provider for parsed PriceSnapshot snapshots."""

    def get_price_snapshots(self, symbol: str) -> Sequence[PriceSnapshot]:
        """Return parsed price snapshots for the requested symbol."""


class CandleSnapshotProvider(Protocol):
    """Provider for parsed CandlePage or Candle snapshots."""

    def get_candles(
        self,
        symbol: str,
        *,
        interval: str,
        count: int,
        adjusted: bool,
    ) -> CandlePage | Sequence[Candle]:
        """Return parsed candles for the requested symbol and interval."""


class ExchangeRateSnapshotProvider(Protocol):
    """Provider for parsed ExchangeRate snapshots."""

    def get_exchange_rates(
        self,
        base_currency: str,
        quote_currency: str,
    ) -> Sequence[ExchangeRate]:
        """Return parsed exchange rates for the requested pair."""


@dataclass(frozen=True, slots=True)
class ReadOnlySnapshotIngestionRequest:
    """Approved read-only snapshot request without credentials or account data."""

    symbol: str
    exchange_base_currency: str = "USD"
    exchange_quote_currency: str = "KRW"
    candle_interval: str = "1d"
    candle_count: int = 1
    adjusted: bool = True
    live_mode_enabled: bool = False
    real_order_allowed: bool = False
    order_send_requested: bool = False
    account_scope_requested: bool = False
    account_seq: str | None = None


@dataclass(frozen=True, slots=True)
class ReadOnlySnapshotIngestionResult:
    """Safe ingestion outcome without raw API, credential, or account data."""

    requested_symbol: str
    saved_stock_count: int
    saved_price_snapshot_count: int
    saved_candle_count: int
    saved_exchange_rate_count: int
    stock_warnings_deferred: bool
    skipped_stock_warnings_count: int
    success: bool
    safe_message: str
    actual_network_call_performed: bool = False


class ReadOnlySnapshotIngestionService:
    """Persist one read-only snapshot from fake/mock parsed providers."""

    def __init__(
        self,
        persistence: LocalDataPersistenceService,
        *,
        stock_provider: StockInfoSnapshotProvider,
        price_provider: PriceSnapshotProvider,
        candle_provider: CandleSnapshotProvider,
        exchange_rate_provider: ExchangeRateSnapshotProvider,
    ) -> None:
        self._persistence = persistence
        self._stock_provider = stock_provider
        self._price_provider = price_provider
        self._candle_provider = candle_provider
        self._exchange_rate_provider = exchange_rate_provider

    def ingest_snapshot(
        self,
        request: ReadOnlySnapshotIngestionRequest,
    ) -> ReadOnlySnapshotIngestionResult:
        """Fetch parsed provider snapshots and persist them locally."""

        _validate_request(request)
        symbol = request.symbol.strip()
        stocks = tuple(self._stock_provider.get_stock_info(symbol))
        prices = tuple(self._price_provider.get_price_snapshots(symbol))
        candle_result = self._candle_provider.get_candles(
            symbol,
            interval=request.candle_interval,
            count=request.candle_count,
            adjusted=request.adjusted,
        )
        candles = _candles_from_provider_result(candle_result)
        exchange_rates = tuple(
            self._exchange_rate_provider.get_exchange_rates(
                request.exchange_base_currency,
                request.exchange_quote_currency,
            )
        )

        saved_stocks = self._persistence.save_stocks(stocks)
        saved_price_ids = self._persistence.save_price_snapshots(prices)
        saved_candle_ids = self._persistence.save_candles(
            symbol,
            request.candle_interval,
            candles,
        )
        saved_exchange_rate_ids = self._persistence.save_exchange_rates(
            exchange_rates
        )

        return ReadOnlySnapshotIngestionResult(
            requested_symbol=symbol,
            saved_stock_count=saved_stocks,
            saved_price_snapshot_count=len(saved_price_ids),
            saved_candle_count=len(saved_candle_ids),
            saved_exchange_rate_count=len(saved_exchange_rate_ids),
            stock_warnings_deferred=True,
            skipped_stock_warnings_count=0,
            success=True,
            safe_message=(
                "Read-only snapshot ingested from parsed fake/mock providers; "
                "stock warnings persistence is deferred."
            ),
            actual_network_call_performed=False,
        )


def _candles_from_provider_result(
    candle_result: CandlePage | Sequence[Candle],
) -> tuple[Candle, ...]:
    if isinstance(candle_result, CandlePage):
        return candle_result.candles
    return tuple(candle_result)


def _validate_request(request: ReadOnlySnapshotIngestionRequest) -> None:
    symbol = request.symbol.strip()
    if not symbol:
        raise ValueError("Snapshot symbol is required.")
    if _SYMBOL_PATTERN.fullmatch(symbol) is None:
        raise ValueError(
            "Snapshot symbol may contain only letters, numbers, '.', and '-'."
        )
    if request.candle_interval not in _CANDLE_INTERVALS:
        raise ValueError("Candle interval must be '1m' or '1d'.")
    if isinstance(request.candle_count, bool) or not 1 <= request.candle_count <= 200:
        raise ValueError("Candle count must be between 1 and 200.")
    if not isinstance(request.adjusted, bool):
        raise ValueError("Candle adjusted flag must be boolean.")
    if request.live_mode_enabled:
        raise ValueError("Live mode is not allowed for snapshot ingestion.")
    if request.real_order_allowed or request.order_send_requested:
        raise ValueError("Order-related flags are not allowed.")
    if request.account_scope_requested or request.account_seq is not None:
        raise ValueError("Account-scoped input is not allowed.")
    if not request.exchange_base_currency or not request.exchange_quote_currency:
        raise ValueError("Exchange-rate currency pair is required.")
