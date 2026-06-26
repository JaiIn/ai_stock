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
        parsed = Decimal(value)
    except InvalidOperation as error:
        raise ValueError(
            f"Response field '{field_name}' must be a decimal string."
        ) from error
    if not parsed.is_finite():
        raise ValueError(f"Response field '{field_name}' must be finite.")
    return parsed


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


def _optional_int(payload: Mapping[str, Any], field_name: str) -> int | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Response field '{field_name}' must be an integer.")
    return value


@dataclass(frozen=True, slots=True)
class PriceSnapshot:
    """Minimal current-price result for one stock symbol."""

    stock_code: str
    price: Decimal
    timestamp: str | None
    currency: str | None = None

    @property
    def symbol(self) -> str:
        """Expose the official field name without breaking storage callers."""

        return self.stock_code

    @property
    def last_price(self) -> Decimal:
        """Expose the official field name without breaking storage callers."""

        return self.price

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "PriceSnapshot":
        """Parse the legacy local payload shape used by existing storage tests."""

        return cls(
            stock_code=_required_text(payload, "symbol"),
            price=_required_decimal(payload, "lastPrice"),
            timestamp=_required_text(payload, "timestamp"),
            currency=_optional_text(payload, "currency"),
        )

    @classmethod
    def from_official_mapping(
        cls,
        payload: Mapping[str, Any],
    ) -> "PriceSnapshot":
        """Parse the official PriceResponse schema."""

        return cls(
            stock_code=_required_text(payload, "symbol"),
            price=_required_decimal(payload, "lastPrice"),
            timestamp=_optional_text(payload, "timestamp"),
            currency=_required_text(payload, "currency"),
        )


@dataclass(frozen=True, slots=True)
class PriceError:
    """Safe Prices error metadata without raw request or response bodies."""

    request_id: str
    code: str
    message: str
    field: str | None = None
    allowed_values: tuple[str, ...] = ()
    constraint_min: int | None = None
    constraint_max: int | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "PriceError":
        data = payload.get("data")
        field = None
        allowed_values: tuple[str, ...] = ()
        constraint_min = None
        constraint_max = None
        if data is not None:
            if not isinstance(data, Mapping):
                raise ValueError("Response field 'data' must be an object.")
            field = _optional_text(data, "field")
            allowed_values = _optional_text_tuple(data, "allowedValues")
            constraint = data.get("constraint")
            if constraint is not None:
                if not isinstance(constraint, Mapping):
                    raise ValueError(
                        "Response field 'constraint' must be an object."
                    )
                constraint_min = _optional_int(constraint, "min")
                constraint_max = _optional_int(constraint, "max")
        return cls(
            request_id=_required_text(payload, "requestId"),
            code=_required_text(payload, "code"),
            message=_required_text(payload, "message"),
            field=field,
            allowed_values=allowed_values,
            constraint_min=constraint_min,
            constraint_max=constraint_max,
        )


@dataclass(frozen=True, slots=True)
class CandleError:
    """Safe Candles error metadata without raw request or response bodies."""

    request_id: str
    code: str
    message: str
    field: str | None = None
    allowed_values: tuple[str, ...] = ()
    constraint_min: int | None = None
    constraint_max: int | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "CandleError":
        data = payload.get("data")
        field = None
        allowed_values: tuple[str, ...] = ()
        constraint_min = None
        constraint_max = None
        if data is not None:
            if not isinstance(data, Mapping):
                raise ValueError("Response field 'data' must be an object.")
            field = _optional_text(data, "field")
            allowed_values = _optional_text_tuple(data, "allowedValues")
            constraint = data.get("constraint")
            if constraint is not None:
                if not isinstance(constraint, Mapping):
                    raise ValueError(
                        "Response field 'constraint' must be an object."
                    )
                constraint_min = _optional_int(constraint, "min")
                constraint_max = _optional_int(constraint, "max")
        return cls(
            request_id=_required_text(payload, "requestId"),
            code=_required_text(payload, "code"),
            message=_required_text(payload, "message"),
            field=field,
            allowed_values=allowed_values,
            constraint_min=constraint_min,
            constraint_max=constraint_max,
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

    @classmethod
    def from_official_mapping(cls, payload: Mapping[str, Any]) -> "Candle":
        """Parse the official Candle schema with required currency."""

        return cls(
            timestamp=_required_text(payload, "timestamp"),
            open=_required_decimal(payload, "openPrice"),
            high=_required_decimal(payload, "highPrice"),
            low=_required_decimal(payload, "lowPrice"),
            close=_required_decimal(payload, "closePrice"),
            volume=_required_decimal(payload, "volume"),
            currency=_required_text(payload, "currency"),
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

    @classmethod
    def from_official_mapping(cls, payload: Mapping[str, Any]) -> "CandlePage":
        """Parse the official CandlePageResponse schema."""

        items = payload.get("candles")
        if not isinstance(items, list) or not all(
            isinstance(item, Mapping) for item in items
        ):
            raise ValueError("Response field 'candles' must be an array of objects.")
        return cls(
            candles=tuple(Candle.from_official_mapping(item) for item in items),
            next_before=_optional_text(payload, "nextBefore"),
        )
