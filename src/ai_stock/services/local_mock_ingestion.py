"""Local mock-payload ingestion pipeline.

This service converts fake/mock payloads into existing domain models and then
persists them through LocalDataPersistenceService. It intentionally does not
construct API clients, auth contexts, HTTP transports, or outbound requests.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from ai_stock.models import Candle, ExchangeRate, PriceSnapshot, StockInfo
from ai_stock.services.data_persistence import LocalDataPersistenceService

Payload = Mapping[str, Any]


def _payload_items(payload: Payload | Sequence[Payload], result_key: str) -> list[Payload]:
    if isinstance(payload, Mapping):
        value = payload.get(result_key, payload.get("result", payload))
    else:
        value = payload

    if isinstance(value, Mapping):
        return [value]
    if isinstance(value, Sequence) and not isinstance(value, str):
        items = list(value)
        if all(isinstance(item, Mapping) for item in items):
            return items
    raise ValueError(f"Payload field '{result_key}' must be an object or list.")


class LocalMockIngestionService:
    """Parse fake payloads and persist them through the local data service."""

    def __init__(self, persistence: LocalDataPersistenceService) -> None:
        self._persistence = persistence

    def ingest_stocks_payload(self, payload: Payload | Sequence[Payload]) -> int:
        stocks = [
            StockInfo.from_mapping(item)
            for item in _payload_items(payload, "stocks")
        ]
        return self._persistence.save_stocks(stocks)

    def ingest_price_snapshots_payload(
        self,
        payload: Payload | Sequence[Payload],
    ) -> list[int]:
        snapshots = [
            PriceSnapshot.from_mapping(item)
            for item in _payload_items(payload, "prices")
        ]
        return self._persistence.save_price_snapshots(snapshots)

    def ingest_candles_payload(
        self,
        stock_code: str,
        interval: str,
        payload: Payload | Sequence[Payload],
    ) -> list[int]:
        candles = [
            Candle.from_mapping(item)
            for item in _payload_items(payload, "candles")
        ]
        return self._persistence.save_candles(stock_code, interval, candles)

    def ingest_exchange_rates_payload(
        self,
        base_currency: str,
        quote_currency: str,
        payload: Payload | Sequence[Payload],
    ) -> list[int]:
        rates = [
            ExchangeRate.from_mapping(base_currency, quote_currency, item)
            for item in _payload_items(payload, "exchangeRates")
        ]
        return self._persistence.save_exchange_rates(rates)

    def ingest_market_dataset(self, dataset: Payload) -> dict[str, int]:
        """Ingest a minimal local market dataset without external I/O."""
        counts: dict[str, int] = {}
        if "stocks" in dataset:
            counts["stocks"] = self.ingest_stocks_payload(dataset["stocks"])
        if "prices" in dataset:
            counts["price_snapshots"] = len(
                self.ingest_price_snapshots_payload(dataset["prices"])
            )
        if "candles" in dataset:
            candle_payload = dataset["candles"]
            if not isinstance(candle_payload, Mapping):
                raise ValueError("Dataset field 'candles' must be an object.")
            stock_code = _required_dataset_text(candle_payload, "stockCode")
            interval = _required_dataset_text(candle_payload, "interval")
            counts["candles"] = len(
                self.ingest_candles_payload(stock_code, interval, candle_payload)
            )
        if "exchangeRates" in dataset:
            rate_payload = dataset["exchangeRates"]
            if not isinstance(rate_payload, Mapping):
                raise ValueError("Dataset field 'exchangeRates' must be an object.")
            base_currency = _required_dataset_text(rate_payload, "baseCurrency")
            quote_currency = _required_dataset_text(rate_payload, "quoteCurrency")
            counts["exchange_rates"] = len(
                self.ingest_exchange_rates_payload(
                    base_currency,
                    quote_currency,
                    rate_payload,
                )
            )
        return counts


def _required_dataset_text(payload: Payload, field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Dataset field '{field_name}' is required.")
    return value
