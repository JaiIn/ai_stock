"""Injected configuration for the Toss API client foundation."""

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType

import httpx

from ai_stock.clients.exceptions import TossClientConfigError
from ai_stock.utils.masking import sanitize_mapping


@dataclass(frozen=True, slots=True)
class TossClientConfig:
    """Network-neutral settings used to construct requests."""

    base_url: str = "https://openapi.tossinvest.com"
    timeout_seconds: float = 10.0
    default_headers: Mapping[str, str] = field(default_factory=dict)
    allow_live_api: bool = False

    def __post_init__(self) -> None:
        try:
            parsed_url = httpx.URL(self.base_url)
        except httpx.InvalidURL as error:
            raise TossClientConfigError("Toss base URL is invalid.") from error

        if parsed_url.scheme not in {"http", "https"} or not parsed_url.host:
            raise TossClientConfigError("Toss base URL must be an HTTP(S) URL.")
        if self.timeout_seconds <= 0:
            raise TossClientConfigError("Toss client timeout must be positive.")

        normalized_url = self.base_url.rstrip("/")
        normalized_headers = MappingProxyType(dict(self.default_headers))
        object.__setattr__(self, "base_url", normalized_url)
        object.__setattr__(self, "default_headers", normalized_headers)

    def safe_headers(self) -> dict[str, object]:
        """Return default headers with sensitive values masked."""

        return sanitize_mapping(self.default_headers)
