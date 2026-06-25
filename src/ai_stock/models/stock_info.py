"""Official Stock Info models for offline Toss response parsing."""

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


def _required_bool(payload: Mapping[str, Any], field_name: str) -> bool:
    value = payload.get(field_name)
    if not isinstance(value, bool):
        raise ValueError(f"Response field '{field_name}' must be boolean.")
    return value


def _optional_bool(payload: Mapping[str, Any], field_name: str) -> bool | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ValueError(f"Response field '{field_name}' must be boolean.")
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


def _optional_decimal(
    payload: Mapping[str, Any],
    field_name: str,
) -> Decimal | None:
    value = payload.get(field_name)
    if value is None:
        return None
    return _required_decimal(payload, field_name)


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
class KoreanMarketDetail:
    """Domestic-market trading flags embedded in official StockInfo results."""

    liquidation_trading: bool
    nxt_supported: bool
    krx_trading_suspended: bool
    nxt_trading_suspended: bool | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "KoreanMarketDetail":
        return cls(
            liquidation_trading=_required_bool(payload, "liquidationTrading"),
            nxt_supported=_required_bool(payload, "nxtSupported"),
            krx_trading_suspended=_required_bool(payload, "krxTradingSuspended"),
            nxt_trading_suspended=_optional_bool(
                payload,
                "nxtTradingSuspended",
            ),
        )


@dataclass(frozen=True, slots=True)
class StockInfo:
    """Official stock metadata with backward-compatible optional attributes."""

    stock_code: str
    stock_name: str
    market: str | None = None
    currency: str | None = None
    english_name: str | None = None
    isin_code: str | None = None
    security_type: str | None = None
    status: str | None = None
    is_common_share: bool | None = None
    list_date: str | None = None
    delist_date: str | None = None
    shares_outstanding: Decimal | None = None
    leverage_factor: Decimal | None = None
    korean_market_detail: KoreanMarketDetail | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "StockInfo":
        """Parse legacy local/mock payloads while preserving minimal compatibility."""

        return cls(
            stock_code=_required_text(payload, "symbol"),
            stock_name=_required_text(payload, "name"),
            market=_optional_text(payload, "market"),
            currency=_optional_text(payload, "currency"),
            english_name=_optional_text(payload, "englishName"),
            isin_code=_optional_text(payload, "isinCode"),
            security_type=_optional_text(payload, "securityType"),
            status=_optional_text(payload, "status"),
            is_common_share=_optional_bool(payload, "isCommonShare"),
            list_date=_optional_text(payload, "listDate"),
            delist_date=_optional_text(payload, "delistDate"),
            shares_outstanding=_optional_decimal(payload, "sharesOutstanding"),
            leverage_factor=_optional_decimal(payload, "leverageFactor"),
            korean_market_detail=_optional_market_detail(payload),
        )

    @classmethod
    def from_official_mapping(cls, payload: Mapping[str, Any]) -> "StockInfo":
        """Parse the official getStocks schema with required-field validation."""

        market_detail_payload = payload.get("koreanMarketDetail")
        if market_detail_payload is None:
            market_detail = None
        elif isinstance(market_detail_payload, Mapping):
            market_detail = KoreanMarketDetail.from_mapping(market_detail_payload)
        else:
            raise ValueError(
                "Response field 'koreanMarketDetail' must be an object or null."
            )
        return cls(
            stock_code=_required_text(payload, "symbol"),
            stock_name=_required_text(payload, "name"),
            market=_required_text(payload, "market"),
            currency=_required_text(payload, "currency"),
            english_name=_required_text(payload, "englishName"),
            isin_code=_required_text(payload, "isinCode"),
            security_type=_required_text(payload, "securityType"),
            status=_required_text(payload, "status"),
            is_common_share=_required_bool(payload, "isCommonShare"),
            list_date=_optional_text(payload, "listDate"),
            delist_date=_optional_text(payload, "delistDate"),
            shares_outstanding=_required_decimal(payload, "sharesOutstanding"),
            leverage_factor=_optional_decimal(payload, "leverageFactor"),
            korean_market_detail=market_detail,
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


@dataclass(frozen=True, slots=True)
class StockInfoError:
    """Safe Stock Info error metadata without raw request or response bodies."""

    request_id: str
    code: str
    message: str
    field: str | None = None
    allowed_values: tuple[str, ...] = ()
    constraint_min: int | None = None
    constraint_max: int | None = None

    @classmethod
    def from_mapping(cls, payload: Mapping[str, Any]) -> "StockInfoError":
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


def _optional_int(payload: Mapping[str, Any], field_name: str) -> int | None:
    value = payload.get(field_name)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise ValueError(f"Response field '{field_name}' must be an integer.")
    return value


def _optional_market_detail(
    payload: Mapping[str, Any],
) -> KoreanMarketDetail | None:
    value = payload.get("koreanMarketDetail")
    if value is None:
        return None
    if not isinstance(value, Mapping):
        raise ValueError(
            "Response field 'koreanMarketDetail' must be an object or null."
        )
    return KoreanMarketDetail.from_mapping(value)
