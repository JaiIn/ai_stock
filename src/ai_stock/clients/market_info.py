"""Request-only Toss market-info client with offline response parsing."""

from collections.abc import Mapping

import httpx

from ai_stock.clients.exceptions import TossApiError, TossClientConfigError
from ai_stock.clients.foundation import TossClientFoundation
from ai_stock.clients.request_context import AuthenticatedRequestContext
from ai_stock.clients.response import extract_toss_result
from ai_stock.models.market_info import ExchangeRate, ExchangeRateError

SUPPORTED_EXCHANGE_CURRENCIES = frozenset({"KRW", "USD"})


class TossMarketInfoClient:
    """Build market-info requests without transmitting them."""

    def __init__(
        self,
        foundation: TossClientFoundation,
        context: AuthenticatedRequestContext,
    ) -> None:
        self._foundation = foundation
        self._context = context

    def get_exchange_rate(
        self,
        *,
        base_currency: str,
        quote_currency: str,
        date_time: str | None = None,
    ) -> httpx.Request:
        """Build the documented getExchangeRate request without sending it."""

        params = build_exchange_rate_params(
            base_currency=base_currency,
            quote_currency=quote_currency,
            date_time=date_time,
        )
        return self._foundation.build_authenticated_request(
            self._context,
            "GET",
            "/api/v1/exchange-rate",
            params=params,
        )

    @staticmethod
    def parse_exchange_rate_response(
        response: httpx.Response,
    ) -> ExchangeRate:
        """Parse a fake getExchangeRate result object."""

        result = extract_toss_result(response)
        if not isinstance(result, Mapping):
            raise TossApiError("getExchangeRate result must be an object.")
        try:
            return ExchangeRate.from_mapping(result)
        except ValueError as error:
            raise TossApiError(
                "getExchangeRate result contained invalid exchange-rate data."
            ) from error

    @staticmethod
    def parse_exchange_rate_error_response(
        response: httpx.Response,
    ) -> ExchangeRateError:
        """Extract only documented, non-raw error metadata."""

        try:
            payload = response.json()
        except ValueError as error:
            raise TossApiError(
                "getExchangeRate error response was not valid JSON.",
                status_code=response.status_code,
            ) from error
        if not isinstance(payload, Mapping):
            raise TossApiError(
                "getExchangeRate error response must be an object.",
                status_code=response.status_code,
            )
        error_payload = payload.get("error")
        if not isinstance(error_payload, Mapping):
            raise TossApiError(
                "getExchangeRate error response did not contain an error object.",
                status_code=response.status_code,
            )
        try:
            return ExchangeRateError.from_mapping(error_payload)
        except ValueError as error:
            raise TossApiError(
                "getExchangeRate error response contained invalid metadata.",
                status_code=response.status_code,
            ) from error


def build_exchange_rate_params(
    *,
    base_currency: str,
    quote_currency: str,
    date_time: str | None = None,
) -> dict[str, str]:
    """Build the official required query without transmitting it."""

    normalized_base = _normalize_currency(base_currency, "baseCurrency")
    normalized_quote = _normalize_currency(quote_currency, "quoteCurrency")
    if normalized_base == normalized_quote:
        raise TossClientConfigError(
            "baseCurrency and quoteCurrency must be different."
        )
    params = {
        "baseCurrency": normalized_base,
        "quoteCurrency": normalized_quote,
    }
    if date_time is not None:
        normalized_date_time = date_time.strip()
        if not normalized_date_time:
            raise TossClientConfigError("dateTime must not be blank.")
        params["dateTime"] = normalized_date_time
    return params


def _normalize_currency(value: str, field_name: str) -> str:
    normalized = value.strip().upper()
    if normalized not in SUPPORTED_EXCHANGE_CURRENCIES:
        raise TossClientConfigError(
            f"{field_name} must be one of KRW or USD."
        )
    return normalized
