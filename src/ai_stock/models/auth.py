"""Network-neutral models for the Toss OAuth token flow."""

from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone

from ai_stock.utils.masking import mask_secret, sanitize_mapping


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


@dataclass(frozen=True, slots=True)
class OAuthTokenRequest:
    """Credentials for a future token request without HTTP behavior."""

    client_id: str | None = field(default=None, repr=False)
    client_secret: str | None = field(default=None, repr=False)
    grant_type: str = "client_credentials"

    def safe_dict(self) -> dict[str, object]:
        """Return request metadata with credentials masked."""

        return sanitize_mapping(
            {
                "toss_client_id": self.client_id,
                "toss_client_secret": self.client_secret,
                "grant_type": self.grant_type,
            }
        )


@dataclass(frozen=True, slots=True)
class OAuthTokenResponse:
    """In-memory token value and expiry metadata."""

    access_token: str = field(repr=False)
    token_type: str = "Bearer"
    expires_in: int = 3600
    issued_at: datetime = field(default_factory=_utc_now)

    def __post_init__(self) -> None:
        if not self.access_token:
            raise ValueError("access_token must not be empty")
        if self.expires_in <= 0:
            raise ValueError("expires_in must be positive")
        if self.issued_at.tzinfo is None:
            raise ValueError("issued_at must be timezone-aware")

    @property
    def expires_at(self) -> datetime:
        """Return the absolute token expiry time."""

        return self.issued_at + timedelta(seconds=self.expires_in)

    def is_expired(
        self,
        *,
        at: datetime | None = None,
        leeway_seconds: int = 0,
    ) -> bool:
        """Return whether the token is expired, optionally with refresh leeway."""

        if leeway_seconds < 0:
            raise ValueError("leeway_seconds must be non-negative")
        check_time = at or _utc_now()
        if check_time.tzinfo is None:
            raise ValueError("at must be timezone-aware")
        return check_time + timedelta(seconds=leeway_seconds) >= self.expires_at

    def authorization_header(self) -> dict[str, str]:
        """Build an authorization header for future request construction."""

        return {"Authorization": f"{self.token_type} {self.access_token}"}

    def safe_authorization_header(self) -> dict[str, str]:
        """Build a masked authorization header for diagnostics."""

        value = f"{self.token_type} {self.access_token}"
        return {"Authorization": mask_secret(value)}

    def safe_dict(self) -> dict[str, object]:
        """Return token metadata without exposing the token value."""

        return {
            "access_token": mask_secret(self.access_token),
            "token_type": self.token_type,
            "expires_in": self.expires_in,
            "issued_at": self.issued_at.isoformat(),
            "expires_at": self.expires_at.isoformat(),
        }
