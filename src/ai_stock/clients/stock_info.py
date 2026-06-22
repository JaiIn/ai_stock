"""Request-only Toss stock information client with offline response parsing."""

from collections.abc import Mapping, Sequence
from typing import Any
from urllib.parse import quote

import httpx

from ai_stock.clients.exceptions import TossApiError, TossClientConfigError
from ai_stock.clients.foundation import TossClientFoundation
from ai_stock.clients.request_context import AuthenticatedRequestContext
from ai_stock.clients.response import extract_toss_result
from ai_stock.models.stock_info import StockInfo, StockWarning


class TossStockInfoClient:
    """Build stock-info requests and parse supplied responses without sending."""

    def __init__(
        self,
        foundation: TossClientFoundation,
        context: AuthenticatedRequestContext,
    ) -> None:
        self._foundation = foundation
        self._context = context

    def get_stocks(self, symbols: Sequence[str]) -> httpx.Request:
        """Build the getStocks request without network transmission."""

        normalized = [symbol.strip() for symbol in symbols if symbol.strip()]
        if not normalized:
            raise TossClientConfigError("At least one stock symbol is required.")
        if len(normalized) > 200:
            raise TossClientConfigError("At most 200 stock symbols are allowed.")
        return self._foundation.build_authenticated_request(
            self._context,
            "GET",
            "/api/v1/stocks",
            params={"symbols": ",".join(normalized)},
        )

    def get_stock_warnings(self, symbol: str) -> httpx.Request:
        """Build the getStockWarnings request without network transmission."""

        normalized = symbol.strip()
        if not normalized:
            raise TossClientConfigError("A stock symbol is required.")
        encoded_symbol = quote(normalized, safe="")
        return self._foundation.build_authenticated_request(
            self._context,
            "GET",
            f"/api/v1/stocks/{encoded_symbol}/warnings",
        )

    @staticmethod
    def parse_stocks_response(response: httpx.Response) -> list[StockInfo]:
        """Parse a fake or future getStocks result array."""

        result = extract_toss_result(response)
        items = _result_items(result, operation="getStocks")
        try:
            return [StockInfo.from_mapping(item) for item in items]
        except ValueError as error:
            raise TossApiError("getStocks result contained invalid stock data.") from error

    @staticmethod
    def parse_stock_warnings_response(
        symbol: str,
        response: httpx.Response,
    ) -> list[StockWarning]:
        """Parse a fake or future getStockWarnings result array."""

        result = extract_toss_result(response)
        items = _result_items(result, operation="getStockWarnings")
        try:
            return [StockWarning.from_mapping(symbol, item) for item in items]
        except ValueError as error:
            raise TossApiError(
                "getStockWarnings result contained invalid warning data."
            ) from error


def _result_items(result: Any, *, operation: str) -> list[Mapping[str, Any]]:
    if not isinstance(result, list) or not all(
        isinstance(item, Mapping) for item in result
    ):
        raise TossApiError(f"{operation} result must be an array of objects.")
    return result
