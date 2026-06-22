"""Request-building foundation that intentionally performs no network sends."""

from collections.abc import Mapping
from types import TracebackType
from typing import Any, Self

import httpx

from ai_stock.clients.config import TossClientConfig
from ai_stock.clients.exceptions import TossClientConfigError
from ai_stock.clients.request_context import AuthenticatedRequestContext
from ai_stock.utils.masking import sanitize_mapping


class TossClientFoundation:
    """Build Toss requests and enforce the explicit live-call gate."""

    def __init__(
        self,
        config: TossClientConfig,
        *,
        http_client: httpx.Client | None = None,
    ) -> None:
        self._config = config
        self._owns_client = http_client is None
        self._http_client = http_client or httpx.Client(
            timeout=config.timeout_seconds,
            headers=dict(config.default_headers),
        )

    @property
    def config(self) -> TossClientConfig:
        return self._config

    def ensure_live_api_allowed(self) -> None:
        """Block live network work unless explicitly enabled by injected settings."""

        if not self._config.allow_live_api:
            raise TossClientConfigError("Live Toss API calls are disabled.")

    def build_headers(
        self,
        *,
        access_token: str | None = None,
        account_seq: str | None = None,
        extra_headers: Mapping[str, str] | None = None,
    ) -> dict[str, str]:
        """Build request headers without logging or storing credential values."""

        headers = dict(self._config.default_headers)
        if extra_headers:
            headers.update(extra_headers)
        if access_token:
            headers["Authorization"] = f"Bearer {access_token}"
        if account_seq:
            headers["X-Tossinvest-Account"] = account_seq
        return headers

    def build_request(
        self,
        method: str,
        path: str,
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
        access_token: str | None = None,
        account_seq: str | None = None,
    ) -> httpx.Request:
        """Build, but never send, an httpx request."""

        url = f"{self._config.base_url}/{path.lstrip('/')}"
        request_headers = self.build_headers(
            access_token=access_token,
            account_seq=account_seq,
            extra_headers=headers,
        )
        return self._http_client.build_request(
            method,
            url,
            params=params,
            json=json,
            headers=request_headers,
            timeout=self._config.timeout_seconds,
        )

    def build_authenticated_request(
        self,
        context: AuthenticatedRequestContext,
        method: str,
        path: str,
        *,
        require_account: bool = False,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        headers: Mapping[str, str] | None = None,
    ) -> httpx.Request:
        """Build, but never send, a request using an authenticated context."""

        request_headers = dict(headers or {})
        request_headers.update(
            context.request_headers(require_account=require_account)
        )
        return self.build_request(
            method,
            path,
            params=params,
            json=json,
            headers=request_headers,
        )

    @staticmethod
    def safe_request_context(request: httpx.Request) -> dict[str, object]:
        """Create log-safe request metadata without a body or raw credentials."""

        return {
            "method": request.method,
            "url": str(request.url),
            "headers": sanitize_mapping(dict(request.headers)),
        }

    def close(self) -> None:
        if self._owns_client:
            self._http_client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        self.close()
