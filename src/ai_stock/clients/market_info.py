"""Request-only Toss market-info client with offline response parsing."""

from collections.abc import Mapping

import httpx

from ai_stock.clients.exceptions import TossApiError, TossClientConfigError
from ai_stock.clients.foundation import TossClientFoundation
from ai_stock.clients.request_context import AuthenticatedRequestContext
from ai_stock.clients.response import extract_toss_result
from ai_stock.models.market_info import ExchangeRate


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
        base_currency: str,
        quote_currency: str,
        *,
        date_time: str | None = None,
    ) -> httpx.Request:
        """Build the documented getExchangeRate request without sending it."""

        base = base_currency.strip()
        quote = quote_currency.strip()
        if not base or not quote:
            raise TossClientConfigError("Base and quote currencies are required.")
        params = {
            "baseCurrency": base,
            "quoteCurrency": quote,
        }
        if date_time is not None:
            params["dateTime"] = date_time
        return self._foundation.build_authenticated_request(
            self._context,
            "GET",
            "/api/v1/exchange-rate",
            params=params,
        )

    @staticmethod
    def parse_exchange_rate_response(
        base_currency: str,
        quote_currency: str,
        response: httpx.Response,
    ) -> ExchangeRate:
        """Parse a fake getExchangeRate result object."""

        result = extract_toss_result(response)
        if not isinstance(result, Mapping):
            raise TossApiError("getExchangeRate result must be an object.")
        try:
            return ExchangeRate.from_mapping(
                base_currency,
                quote_currency,
                result,
            )
        except ValueError as error:
            raise TossApiError(
                "getExchangeRate result contained invalid exchange-rate data."
            ) from error
