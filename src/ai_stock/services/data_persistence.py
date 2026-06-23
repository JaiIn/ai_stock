"""Local-only persistence service for already parsed domain models.

This module intentionally depends only on repository and model layers. It does
not import Toss API clients, token providers, authenticated request contexts, or
HTTP transports.
"""

import sqlite3
from collections.abc import Iterable

from ai_stock.models import Candle, ExchangeRate, PriceSnapshot, StockInfo
from ai_stock.repositories import (
    MarketDataRepository,
    MarketInfoRepository,
    StockRepository,
    initialize_schema,
)


class LocalDataPersistenceService:
    """Persist parsed market/reference models into a local SQLite repository."""

    def __init__(
        self,
        connection: sqlite3.Connection,
        *,
        initialize: bool = True,
    ) -> None:
        self._connection = connection
        if initialize:
            initialize_schema(self._connection)
        self._stocks = StockRepository(self._connection)
        self._market_data = MarketDataRepository(self._connection)
        self._market_info = MarketInfoRepository(self._connection)

    def save_stocks(self, stocks: Iterable[StockInfo]) -> int:
        """Upsert stock metadata and return the number of processed items."""
        count = 0
        for stock in stocks:
            self._stocks.upsert_stock(stock)
            count += 1
        return count

    def list_stocks(self) -> list[StockInfo]:
        """Return persisted stock metadata ordered by stock code."""
        return self._stocks.list_stocks()

    def save_price_snapshots(
        self,
        snapshots: Iterable[PriceSnapshot],
    ) -> list[int]:
        """Append price snapshots and return inserted row IDs."""
        return [
            self._market_data.insert_price_snapshot(snapshot)
            for snapshot in snapshots
        ]

    def list_price_snapshots(
        self,
        stock_code: str | None = None,
    ) -> list[PriceSnapshot]:
        """Return persisted price snapshots, optionally filtered by stock code."""
        return self._market_data.list_price_snapshots(stock_code)

    def save_candles(
        self,
        stock_code: str,
        interval: str,
        candles: Iterable[Candle],
    ) -> list[int]:
        """Append candles for one stock/interval pair and return inserted row IDs."""
        return [
            self._market_data.insert_candle(stock_code, interval, candle)
            for candle in candles
        ]

    def list_candles(
        self,
        stock_code: str,
        interval: str | None = None,
    ) -> list[Candle]:
        """Return persisted candles for one stock, optionally filtered by interval."""
        return self._market_data.list_candles(stock_code, interval)

    def save_exchange_rates(
        self,
        rates: Iterable[ExchangeRate],
    ) -> list[int]:
        """Append exchange rates and return inserted row IDs."""
        return [self._market_info.insert_exchange_rate(rate) for rate in rates]

    def list_exchange_rates(
        self,
        base_currency: str | None = None,
        quote_currency: str | None = None,
    ) -> list[ExchangeRate]:
        """Return persisted exchange rates, optionally filtered by currency pair."""
        return self._market_info.list_exchange_rates(base_currency, quote_currency)
