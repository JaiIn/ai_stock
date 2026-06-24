"""Minimal market-data models based on the local Toss API references."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Response field '{field_name}' is required.")
    return value


def _optional_text(payload: Mapping[str, Any], field_name: str) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Response field '{field_name}' must be text.")
    return value


def _required_decimal(payload: Mapping[str, Any], field_name: str) -> Decimal:
    value = payload.get(field_name)
    if not isinstance(value, str):
        raise ValueError(f"Response field '{field_name}' must be a decimal string.")
    try:
        return Decimal(value)
    except InvalidOperation as error:
        raise ValueError(
            f"Response field '{field_name}' must be a decimal string."
        ) from error


@dataclass(frozen=True, slots=True)
class PriceSnapshot:
    """Minimal current-price result for one stock symbol."""

    stock_code: str
    price: Decimal
    timestamp: str
    currency: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "PriceSnapshot":
        return cls(
            stock_code=_required_text(payload, "symbol"),
            price=_required_decimal(payload, "lastPrice"),
            timestamp=_required_text(payload, "timestamp"),
            currency=_optional_text(payload, "currency"),
        )


@dataclass(frozen=True, slots=True)
class Candle:
    """Minimal OHLCV candle using Decimal for every numeric value."""

    timestamp: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    currency: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "Candle":
        return cls(
            timestamp=_required_text(payload, "timestamp"),
            open=_required_decimal(payload, "openPrice"),
            high=_required_decimal(payload, "highPrice"),
            low=_required_decimal(payload, "lowPrice"),
            close=_required_decimal(payload, "closePrice"),
            volume=_required_decimal(payload, "volume"),
            currency=_optional_text(payload, "currency"),
        )


@dataclass(frozen=True, slots=True)
class CandlePage:
    """Official getCandles result object with optional pagination cursor."""

    candles: tuple[Candle, ...]
    next_before: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "CandlePage":
        items = payload.get("candles")
        if not isinstance(items, list) or not all(
            isinstance(item, Mapping) for item in items
        ):
            raise ValueError("Response field 'candles' must be an array of objects.")
        return cls(
            candles=tuple(Candle.from_mapping(item) for item in items),
            next_before=_optional_text(payload, "nextBefore"),
        )
