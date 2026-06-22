"""Toss API client foundation without live endpoint implementations."""

from ai_stock.clients.config import TossClientConfig
from ai_stock.clients.exceptions import (
    TossApiError,
    TossAuthenticationError,
    TossClientConfigError,
    TossPermissionError,
    TossRateLimitError,
    TossServerError,
)
from ai_stock.clients.foundation import TossClientFoundation
from ai_stock.clients.market_data import TossMarketDataClient
from ai_stock.clients.request_context import (
    ACCOUNT_HEADER,
    AUTHORIZATION_HEADER,
    AuthenticatedRequestContext,
    AuthenticatedRequestContextFactory,
)
from ai_stock.clients.response import extract_toss_result, raise_for_toss_status
from ai_stock.clients.stock_info import TossStockInfoClient
from ai_stock.clients.token_provider import LiveTokenProvider, MockTokenProvider, TokenProvider
from ai_stock.clients.token_store import InMemoryTokenStore

__all__ = [
    "ACCOUNT_HEADER",
    "AUTHORIZATION_HEADER",
    "AuthenticatedRequestContext",
    "AuthenticatedRequestContextFactory",
    "InMemoryTokenStore",
    "LiveTokenProvider",
    "MockTokenProvider",
    "TokenProvider",
    "TossApiError",
    "TossAuthenticationError",
    "TossClientConfig",
    "TossClientConfigError",
    "TossClientFoundation",
    "TossMarketDataClient",
    "TossPermissionError",
    "TossRateLimitError",
    "TossServerError",
    "TossStockInfoClient",
    "extract_toss_result",
    "raise_for_toss_status",
]
