"""Minimal market-info models for offline Toss response parsing."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any


def _required_decimal(payload: Mapping[str, Any], field_name: str) -> Decimal:
    value = payload.get(field_name)
    if not isinstance(value, str):
        raise ValueError(f"Response field '{field_name}' must be a decimal string.")
    try:
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise ValueError(
            f"Response field '{field_name}' must be a decimal string."
        ) from error
    if not parsed.is_finite():
        raise ValueError(f"Response field '{field_name}' must be finite.")
    return parsed


def _optional_text(payload: Mapping[str, Any], field_name: str) -> str | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError(f"Response field '{field_name}' must be text.")
    return value


@dataclass(frozen=True, slots=True)
class ExchangeRate:
    """Minimal reference exchange rate for one requested currency pair."""

    base_currency: str
    quote_currency: str
    exchange_rate: Decimal
    date_time: str | None = None

    @classmethod
    def from_mapping(
        cls,
        base_currency: str,
        quote_currency: str,
        payload: Mapping[str, Any],
    ) -> "ExchangeRate":
        if not base_currency or not quote_currency:
            raise ValueError("Exchange rate currencies are required.")
        return cls(
            base_currency=base_currency,
            quote_currency=quote_currency,
            exchange_rate=_required_decimal(payload, "exchangeRate"),
            date_time=_optional_text(payload, "dateTime"),
        )
