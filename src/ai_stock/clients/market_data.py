"""Request-only Toss market-data client with offline response parsing."""

from collections.abc import Mapping, Sequence
from typing import Any

import httpx

from ai_stock.clients.exceptions import TossApiError, TossClientConfigError
from ai_stock.clients.foundation import TossClientFoundation
from ai_stock.clients.request_context import AuthenticatedRequestContext
from ai_stock.clients.response import extract_toss_result
from ai_stock.models.market_data import CandlePage, PriceSnapshot


class TossMarketDataClient:
    """Build documented market-data requests without transmitting them."""

    def __init__(
        self,
        foundation: TossClientFoundation,
        context: AuthenticatedRequestContext,
    ) -> None:
        self._foundation = foundation
        self._context = context

    def get_orderbook(self, symbol: str) -> httpx.Request:
        return self._single_symbol_request("/api/v1/orderbook", symbol)

    def get_prices(self, symbols: Sequence[str]) -> httpx.Request:
        normalized = _symbols(symbols, maximum=200)
        return self._foundation.build_authenticated_request(
            self._context,
            "GET",
            "/api/v1/prices",
            params={"symbols": ",".join(normalized)},
        )

    def get_trades(self, symbol: str, *, count: int = 50) -> httpx.Request:
        if not 1 <= count <= 50:
            raise TossClientConfigError("Trade count must be between 1 and 50.")
        return self._single_symbol_request(
            "/api/v1/trades",
            symbol,
            extra_params={"count": count},
        )

    def get_price_limit(self, symbol: str) -> httpx.Request:
        return self._single_symbol_request("/api/v1/price-limits", symbol)

    def get_candles(
        self,
        symbol: str,
        *,
        interval: str,
        count: int,
        before: str | None = None,
        adjusted: bool | None = None,
    ) -> httpx.Request:
        if interval not in {"1m", "1d"}:
            raise TossClientConfigError("Candle interval must be '1m' or '1d'.")
        if not 1 <= count <= 200:
            raise TossClientConfigError("Candle count must be between 1 and 200.")
        params: dict[str, str | int | bool] = {
            "interval": interval,
            "count": count,
        }
        if before is not None:
            params["before"] = before
        if adjusted is not None:
            params["adjusted"] = adjusted
        return self._single_symbol_request(
            "/api/v1/candles",
            symbol,
            extra_params=params,
        )

    @staticmethod
    def parse_prices_response(response: httpx.Response) -> list[PriceSnapshot]:
        result = extract_toss_result(response)
        items = _result_items(result, operation="getPrices")
        try:
            return [PriceSnapshot.from_mapping(item) for item in items]
        except ValueError as error:
            raise TossApiError("getPrices result contained invalid price data.") from error

    @staticmethod
    def parse_candles_response(response: httpx.Response) -> CandlePage:
        result = extract_toss_result(response)
        if not isinstance(result, Mapping):
            raise TossApiError("getCandles result must be an object.")
        try:
            return CandlePage.from_mapping(result)
        except ValueError as error:
            raise TossApiError("getCandles result contained invalid candle data.") from error

    def _single_symbol_request(
        self,
        path: str,
        symbol: str,
        *,
        extra_params: Mapping[str, str | int | bool] | None = None,
    ) -> httpx.Request:
        normalized = symbol.strip()
        if not normalized:
            raise TossClientConfigError("A stock symbol is required.")
        params: dict[str, str | int | bool] = {"symbol": normalized}
        if extra_params:
            params.update(extra_params)
        return self._foundation.build_authenticated_request(
            self._context,
            "GET",
            path,
            params=params,
        )


def _symbols(symbols: Sequence[str], *, maximum: int) -> list[str]:
    normalized = [symbol.strip() for symbol in symbols if symbol.strip()]
    if not normalized:
        raise TossClientConfigError("At least one stock symbol is required.")
    if len(normalized) > maximum:
        raise TossClientConfigError(f"At most {maximum} stock symbols are allowed.")
    return normalized


def _result_items(result: Any, *, operation: str) -> list[Mapping[str, Any]]:
    if not isinstance(result, list) or not all(
        isinstance(item, Mapping) for item in result
    ):
        raise TossApiError(f"{operation} result must be an array of objects.")
    return result
