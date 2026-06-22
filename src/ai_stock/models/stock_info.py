"""Minimal stock information models based on the local Toss API references."""

from collections.abc import Mapping
from dataclasses import dataclass
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


@dataclass(frozen=True, slots=True)
class StockInfo:
    """Basic stock metadata returned by the getStocks operation."""

    stock_code: str
    stock_name: str
    market: str | None = None
    currency: str | None = None
    english_name: str | None = None
    isin_code: str | None = None
    security_type: str | None = None
    status: str | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "StockInfo":
        return cls(
            stock_code=_required_text(payload, "symbol"),
            stock_name=_required_text(payload, "name"),
            market=_optional_text(payload, "market"),
            currency=_optional_text(payload, "currency"),
            english_name=_optional_text(payload, "englishName"),
            isin_code=_optional_text(payload, "isinCode"),
            security_type=_optional_text(payload, "securityType"),
            status=_optional_text(payload, "status"),
        )


@dataclass(frozen=True, slots=True)
class StockWarning:
    """Warning metadata returned for a stock symbol."""

    stock_code: str
    warning_type: str
    exchange: str | None = None
    start_date: str | None = None
    end_date: str | None = None

    @classmethod
    def from_mapping(
        cls,
        stock_code: str,
        payload: Mapping[str, Any],
    ) -> "StockWarning":
        if not stock_code:
            raise ValueError("Stock warning stock_code is required.")
        return cls(
            stock_code=stock_code,
            warning_type=_required_text(payload, "warningType"),
            exchange=_optional_text(payload, "exchange"),
            start_date=_optional_text(payload, "startDate"),
            end_date=_optional_text(payload, "endDate"),
        )
