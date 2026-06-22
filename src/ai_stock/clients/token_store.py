"""Process-local storage for OAuth token responses."""

from ai_stock.models.auth import OAuthTokenResponse


class InMemoryTokenStore:
    """Keep one token in memory without persistence or logging."""

    def __init__(self) -> None:
        self._token: OAuthTokenResponse | None = None

    def save(self, token: OAuthTokenResponse) -> None:
        self._token = token

    def get(self) -> OAuthTokenResponse | None:
        return self._token

    def get_valid(self, *, leeway_seconds: int = 0) -> OAuthTokenResponse | None:
        token = self._token
        if token is None or token.is_expired(leeway_seconds=leeway_seconds):
            return None
        return token

    def clear(self) -> None:
        self._token = None
