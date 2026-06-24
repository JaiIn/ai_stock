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
    """Official exchange-rate result with a storage-compatible rate field."""

    base_currency: str
    quote_currency: str
    exchange_rate: Decimal
    valid_from: str | None = None
    valid_until: str | None = None
    date_time: str | None = None

    @property
    def rate(self) -> Decimal:
        """Expose the official `rate` field name without breaking storage callers."""

        return self.exchange_rate

    @classmethod
    def from_mapping(
        cls,
        payload_or_base_currency: Mapping[str, Any] | str,
        quote_currency: str | None = None,
        legacy_payload: Mapping[str, Any] | None = None,
    ) -> "ExchangeRate":
        """Parse official fields while retaining legacy local-ingestion compatibility."""

        if isinstance(payload_or_base_currency, Mapping):
            payload = payload_or_base_currency
            base_currency = _required_text(payload, "baseCurrency")
            parsed_quote_currency = _required_text(payload, "quoteCurrency")
            rate = _required_decimal(payload, "rate")
            date_time = None
        else:
            base_currency = payload_or_base_currency
            parsed_quote_currency = quote_currency
            payload = legacy_payload
            if (
                not base_currency
                or not parsed_quote_currency
                or not isinstance(payload, Mapping)
            ):
                raise ValueError("Exchange rate currencies and payload are required.")
            rate = _required_decimal(payload, "exchangeRate")
            date_time = _optional_text(payload, "dateTime")

        return cls(
            base_currency=base_currency,
            quote_currency=parsed_quote_currency,
            exchange_rate=rate,
            valid_from=_optional_text(payload, "validFrom"),
            valid_until=_optional_text(payload, "validUntil"),
            date_time=date_time,
        )


def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Response field '{field_name}' is required.")
    return value
