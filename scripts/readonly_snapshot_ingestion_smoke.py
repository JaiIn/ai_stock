"""Run a fake-only read-only snapshot ingestion E2E smoke."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal
import json

from ai_stock.models import Candle, CandlePage, ExchangeRate, PriceSnapshot, StockInfo
from ai_stock.repositories import close_connection, create_connection
from ai_stock.services import (
    LocalDataPersistenceService,
    ReadOnlySnapshotIngestionRequest,
    ReadOnlySnapshotIngestionService,
)

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
_PRICE_TIMESTAMP = "2026-06-29T09:00:00+09:00"
_CANDLE_TIMESTAMP = "2026-06-29T00:00:00+09:00"
_RATE_TIMESTAMP = "2026-06-29T00:00:00+09:00"


class FakeStockInfoProvider:
    """Return one already parsed stock model."""

    def get_stock_info(self, symbol: str) -> tuple[StockInfo, ...]:
        return (
            StockInfo(
                stock_code=symbol,
                stock_name="Samsung Electronics",
                market="KOSPI",
                currency="KRW",
            ),
        )


class FakePriceSnapshotProvider:
    """Return one already parsed price model."""

    def get_price_snapshots(self, symbol: str) -> tuple[PriceSnapshot, ...]:
        return (
            PriceSnapshot(
                stock_code=symbol,
                price=_PRICE,
                timestamp=_PRICE_TIMESTAMP,
                currency="KRW",
            ),
        )


class FakeCandlePageProvider:
    """Return one already parsed candle page."""

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
    """Return one already parsed exchange-rate model."""

    def get_exchange_rates(
        self,
        base_currency: str,
        quote_currency: str,
    ) -> tuple[ExchangeRate, ...]:
        return (
            ExchangeRate(
                base_currency=base_currency,
                quote_currency=quote_currency,
                exchange_rate=_EXCHANGE_RATE,
                date_time=_RATE_TIMESTAMP,
            ),
        )


@dataclass(frozen=True, slots=True)
class FakeReadOnlySnapshotIngestionSmokeResult:
    """Safe E2E smoke diagnostics without payload or secret fields."""

    success: bool
    requested_symbol: str
    saved_stock_count: int
    saved_price_snapshot_count: int
    saved_candle_count: int
    saved_exchange_rate_count: int
    stock_warnings_deferred: bool
    repository_round_trip_verified: bool
    decimal_values_preserved: bool
    timestamp_values_preserved: bool
    actual_network_call_performed: bool
    oauth_token_endpoint_called: bool
    actual_db_file_created: bool
    account_seq_used: bool
    real_order_related_call_performed: bool
    safe_message: str

    def safe_dict(self) -> dict[str, bool | int | str]:
        """Return only explicitly safe diagnostic fields."""

        return asdict(self)


def run_fake_readonly_snapshot_ingestion_smoke(
) -> FakeReadOnlySnapshotIngestionSmokeResult:
    """Execute one fake-provider ingestion against in-memory SQLite."""

    connection = create_connection(":memory:")
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

        stocks = persistence.list_stocks()
        prices = persistence.list_price_snapshots(SMOKE_SYMBOL)
        candles = persistence.list_candles(
            SMOKE_SYMBOL,
            SMOKE_CANDLE_INTERVAL,
        )
        rates = persistence.list_exchange_rates(
            SMOKE_BASE_CURRENCY,
            SMOKE_QUOTE_CURRENCY,
        )
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
        success = (
            ingestion.success
            and counts_match
            and decimals_preserved
            and timestamps_preserved
            and ingestion.stock_warnings_deferred
            and not ingestion.actual_network_call_performed
        )
        return FakeReadOnlySnapshotIngestionSmokeResult(
            success=success,
            requested_symbol=ingestion.requested_symbol,
            saved_stock_count=ingestion.saved_stock_count,
            saved_price_snapshot_count=ingestion.saved_price_snapshot_count,
            saved_candle_count=ingestion.saved_candle_count,
            saved_exchange_rate_count=ingestion.saved_exchange_rate_count,
            stock_warnings_deferred=ingestion.stock_warnings_deferred,
            repository_round_trip_verified=counts_match,
            decimal_values_preserved=decimals_preserved,
            timestamp_values_preserved=timestamps_preserved,
            actual_network_call_performed=False,
            oauth_token_endpoint_called=False,
            actual_db_file_created=False,
            account_seq_used=False,
            real_order_related_call_performed=False,
            safe_message=(
                "Fake read-only snapshot ingestion completed in memory."
                if success
                else "Fake read-only snapshot ingestion verification failed."
            ),
        )
    finally:
        close_connection(connection)


def main() -> int:
    """Run the fixed smoke and print safe JSON diagnostics."""

    result = run_fake_readonly_snapshot_ingestion_smoke()
    label = "PASS" if result.success else "FAIL"
    print(f"[{label}] Fake read-only snapshot ingestion E2E smoke.")
    print(json.dumps(result.safe_dict(), ensure_ascii=True, sort_keys=True))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
