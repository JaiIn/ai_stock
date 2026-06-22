"""Authenticated request context assembly without network behavior."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

from ai_stock.clients.exceptions import TossClientConfigError
from ai_stock.clients.token_provider import TokenProvider
from ai_stock.models.auth import OAuthTokenResponse
from ai_stock.utils.masking import sanitize_mapping

AUTHORIZATION_HEADER = "Authorization"
ACCOUNT_HEADER = "X-Tossinvest-Account"


@dataclass(frozen=True, slots=True)
class AuthenticatedRequestContext:
    """Hold authentication headers while keeping raw values out of repr output."""

    _headers: Mapping[str, str] = field(repr=False)

    def __post_init__(self) -> None:
        object.__setattr__(self, "_headers", MappingProxyType(dict(self._headers)))

    @classmethod
    def from_token(
        cls,
        token: OAuthTokenResponse,
        *,
        account_seq: str | None = None,
    ) -> "AuthenticatedRequestContext":
        headers = token.authorization_header()
        if account_seq:
            headers[ACCOUNT_HEADER] = account_seq
        return cls(headers)

    @property
    def has_account(self) -> bool:
        return ACCOUNT_HEADER in self._headers

    def request_headers(self, *, require_account: bool = False) -> dict[str, str]:
        """Return headers for request construction after account validation."""

        if require_account and not self.has_account:
            raise TossClientConfigError(
                "An account identifier is required for this request."
            )
        return dict(self._headers)

    def safe_dict(self) -> dict[str, object]:
        """Return redacted metadata suitable for diagnostics."""

        return {
            "headers": sanitize_mapping(self._headers),
            "account_header_present": self.has_account,
        }


class AuthenticatedRequestContextFactory:
    """Create request contexts from an injected mock-compatible token provider."""

    def __init__(self, token_provider: TokenProvider) -> None:
        self._token_provider = token_provider

    def create(
        self,
        *,
        account_seq: str | None = None,
    ) -> AuthenticatedRequestContext:
        token = self._token_provider.acquire_token()
        return AuthenticatedRequestContext.from_token(
            token,
            account_seq=account_seq,
        )
