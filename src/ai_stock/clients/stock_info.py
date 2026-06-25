"""Request-only Toss stock information client with offline response parsing."""

from collections.abc import Mapping, Sequence
import re
from typing import Any
from urllib.parse import quote

import httpx

from ai_stock.clients.exceptions import TossApiError, TossClientConfigError
from ai_stock.clients.foundation import TossClientFoundation
from ai_stock.clients.request_context import AuthenticatedRequestContext
from ai_stock.clients.response import extract_toss_result
from ai_stock.models.stock_info import StockInfo, StockInfoError, StockWarning

MAX_STOCK_SYMBOLS = 200
_SYMBOL_PATTERN = re.compile(r"^[A-Za-z0-9.-]+$")


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

        normalized = _normalize_symbols(symbols)
        return self._foundation.build_authenticated_request(
            self._context,
            "GET",
            "/api/v1/stocks",
            params={"symbols": ",".join(normalized)},
        )

    def get_stock_warnings(self, symbol: str) -> httpx.Request:
        """Build the getStockWarnings request without network transmission."""

        normalized = _normalize_symbol(symbol)
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
            return [StockInfo.from_official_mapping(item) for item in items]
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

    @staticmethod
    def parse_stock_info_error_response(
        response: httpx.Response,
    ) -> StockInfoError:
        """Extract only documented safe fields from Stock Info errors."""

        try:
            payload = response.json()
        except ValueError as error:
            raise TossApiError(
                "Stock Info error response was not valid JSON.",
                status_code=response.status_code,
            ) from error
        if not isinstance(payload, Mapping):
            raise TossApiError(
                "Stock Info error response must be an object.",
                status_code=response.status_code,
            )
        error_payload = payload.get("error")
        if not isinstance(error_payload, Mapping):
            raise TossApiError(
                "Stock Info error response did not contain an error object.",
                status_code=response.status_code,
            )
        try:
            return StockInfoError.from_mapping(error_payload)
        except ValueError as error:
            raise TossApiError(
                "Stock Info error response contained invalid metadata.",
                status_code=response.status_code,
            ) from error


def _result_items(result: Any, *, operation: str) -> list[Mapping[str, Any]]:
    if not isinstance(result, list) or not all(
        isinstance(item, Mapping) for item in result
    ):
        raise TossApiError(f"{operation} result must be an array of objects.")
    return result


def _normalize_symbols(symbols: Sequence[str]) -> list[str]:
    normalized = [_normalize_symbol(symbol) for symbol in symbols]
    if not normalized:
        raise TossClientConfigError("At least one stock symbol is required.")
    if len(normalized) > MAX_STOCK_SYMBOLS:
        raise TossClientConfigError(
            f"At most {MAX_STOCK_SYMBOLS} stock symbols are allowed."
        )
    return normalized


def _normalize_symbol(symbol: str) -> str:
    normalized = symbol.strip()
    if not normalized:
        raise TossClientConfigError("A stock symbol is required.")
    if _SYMBOL_PATTERN.fullmatch(normalized) is None:
        raise TossClientConfigError(
            "Stock symbols may contain only letters, numbers, '.', and '-'."
        )
    return normalized
