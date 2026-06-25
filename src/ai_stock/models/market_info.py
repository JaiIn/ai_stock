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


def _optional_text_tuple(
    payload: Mapping[str, Any],
    field_name: str,
) -> tuple[str, ...]:
    value = payload.get(field_name)
    if value is None:
        return ()
    if not isinstance(value, list) or not all(
        isinstance(item, str) for item in value
    ):
        raise ValueError(f"Response field '{field_name}' must be a text array.")
    return tuple(value)


@dataclass(frozen=True, slots=True)
class ExchangeRate:
    """Official exchange-rate result with a storage-compatible rate field."""

    base_currency: str
    quote_currency: str
    exchange_rate: Decimal
    valid_from: str | None = None
    valid_until: str | None = None
    mid_rate: Decimal | None = None
    basis_point: Decimal | None = None
    rate_change_type: str | None = None
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
            mid_rate = _required_decimal(payload, "midRate")
            basis_point = _required_decimal(payload, "basisPoint")
            rate_change_type = _required_rate_change_type(payload)
            valid_from = _required_text(payload, "validFrom")
            valid_until = _required_text(payload, "validUntil")
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
            mid_rate = None
            basis_point = None
            rate_change_type = None
            valid_from = _optional_text(payload, "validFrom")
            valid_until = _optional_text(payload, "validUntil")
            date_time = _optional_text(payload, "dateTime")

        return cls(
            base_currency=base_currency,
            quote_currency=parsed_quote_currency,
            exchange_rate=rate,
            valid_from=valid_from,
            valid_until=valid_until,
            mid_rate=mid_rate,
            basis_point=basis_point,
            rate_change_type=rate_change_type,
            date_time=date_time,
        )


@dataclass(frozen=True, slots=True)
class ExchangeRateError:
    """Documented exchange-rate error metadata without raw response storage."""

    request_id: str
    code: str
    message: str
    field: str | None = None
    allowed_values: tuple[str, ...] = ()

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "ExchangeRateError":
        request_id = _required_text(payload, "requestId")
        code = _required_text(payload, "code")
        message = _required_text(payload, "message")
        data = payload.get("data")
        if data is None:
            field = None
            allowed_values = ()
        elif isinstance(data, Mapping):
            field = _optional_text(data, "field")
            allowed_values = _optional_text_tuple(data, "allowedValues")
        else:
            raise ValueError("Response field 'data' must be an object.")
        return cls(
            request_id=request_id,
            code=code,
            message=message,
            field=field,
            allowed_values=allowed_values,
        )


def _required_text(payload: Mapping[str, Any], field_name: str) -> str:
    value = payload.get(field_name)
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Response field '{field_name}' is required.")
    return value


def _required_rate_change_type(payload: Mapping[str, Any]) -> str:
    value = _required_text(payload, "rateChangeType")
    if value not in {"UP", "EQUAL", "DOWN"}:
        raise ValueError(
            "Response field 'rateChangeType' must be UP, EQUAL, or DOWN."
        )
    return value
