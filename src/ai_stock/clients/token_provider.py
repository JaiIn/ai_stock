"""Offline token providers for the OAuth mock flow."""

from typing import Protocol

from ai_stock.clients.config import TossClientConfig
from ai_stock.clients.exceptions import TossAuthenticationError, TossClientConfigError
from ai_stock.clients.token_store import InMemoryTokenStore
from ai_stock.models.auth import OAuthTokenRequest, OAuthTokenResponse


class TokenProvider(Protocol):
    """Interface shared by token providers without prescribing HTTP behavior."""

    def acquire_token(
        self,
        request: OAuthTokenRequest | None = None,
    ) -> OAuthTokenResponse: ...


class MockTokenProvider:
    """Issue a synthetic in-memory token without credentials or network access."""

    def __init__(
        self,
        *,
        token_store: InMemoryTokenStore | None = None,
        access_token: str = "mock-token-placeholder",
        expires_in: int = 3600,
    ) -> None:
        self._token_store = token_store or InMemoryTokenStore()
        self._access_token = access_token
        self._expires_in = expires_in

    @property
    def token_store(self) -> InMemoryTokenStore:
        return self._token_store

    def acquire_token(
        self,
        request: OAuthTokenRequest | None = None,
    ) -> OAuthTokenResponse:
        del request
        token = OAuthTokenResponse(
            access_token=self._access_token,
            expires_in=self._expires_in,
        )
        self._token_store.save(token)
        return token


class LiveTokenProvider:
    """Explicitly block live OAuth until a later approved Micro Stage."""

    def __init__(self, config: TossClientConfig) -> None:
        self._config = config

    def acquire_token(
        self,
        request: OAuthTokenRequest | None = None,
    ) -> OAuthTokenResponse:
        del request
        if not self._config.allow_live_api:
            raise TossClientConfigError("Live OAuth token requests are disabled.")
        raise TossAuthenticationError(
            "Live OAuth token issuance is not implemented."
        )
