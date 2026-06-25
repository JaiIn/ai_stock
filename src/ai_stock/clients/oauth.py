"""Approved OAuth token endpoint provider with secret-safe failures."""

from collections.abc import Mapping

import httpx

from ai_stock.clients.exceptions import (
    TossAuthenticationError,
    TossClientConfigError,
)
from ai_stock.models.auth import OAuthTokenRequest, OAuthTokenResponse

OAUTH_TOKEN_PATH = "/oauth2/token"


class TossOAuthTokenProvider:
    """Issue one in-memory token through the fixed OAuth endpoint only."""

    def __init__(
        self,
        http_client: httpx.Client,
        *,
        allow_live_api: bool,
        allow_real_order: bool,
        dry_run_only: bool,
    ) -> None:
        self._http_client = http_client
        self._allow_live_api = allow_live_api
        self._allow_real_order = allow_real_order
        self._dry_run_only = dry_run_only

    def acquire_token(
        self,
        request: OAuthTokenRequest | None = None,
    ) -> OAuthTokenResponse:
        """Request a token without logging or persisting credentials or response data."""

        self._validate_safety()
        credentials = _validated_credentials(request)
        try:
            response = self._http_client.post(
                OAUTH_TOKEN_PATH,
                data={
                    "grant_type": credentials.grant_type,
                    "client_id": credentials.client_id,
                    "client_secret": credentials.client_secret,
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )
        except httpx.HTTPError as error:
            raise TossAuthenticationError(
                "OAuth token endpoint request failed without credential output."
            ) from error

        if response.status_code >= 400:
            raise TossAuthenticationError(
                "OAuth token endpoint rejected the request.",
                status_code=response.status_code,
                request_id=response.headers.get("X-Request-Id"),
            )

        return _parse_token_response(response)

    def _validate_safety(self) -> None:
        if not self._allow_live_api:
            raise TossClientConfigError(
                "ALLOW_LIVE_API=true is required for the OAuth smoke test."
            )
        if self._allow_real_order:
            raise TossClientConfigError(
                "ALLOW_REAL_ORDER=true blocks the OAuth smoke test."
            )
        if not self._dry_run_only:
            raise TossClientConfigError(
                "DRY_RUN_ONLY=true is required for the OAuth smoke test."
            )


def _validated_credentials(
    request: OAuthTokenRequest | None,
) -> OAuthTokenRequest:
    if request is None or not request.client_id or not request.client_secret:
        raise TossClientConfigError(
            "OAuth client credentials are missing from the local environment."
        )
    if request.grant_type != "client_credentials":
        raise TossClientConfigError(
            "OAuth grant_type must be client_credentials."
        )
    return request


def _parse_token_response(response: httpx.Response) -> OAuthTokenResponse:
    try:
        payload = response.json()
    except ValueError as error:
        raise TossAuthenticationError(
            "OAuth token endpoint returned invalid JSON.",
            status_code=response.status_code,
            request_id=response.headers.get("X-Request-Id"),
        ) from error
    if not isinstance(payload, Mapping):
        raise TossAuthenticationError(
            "OAuth token endpoint returned an invalid response object.",
            status_code=response.status_code,
            request_id=response.headers.get("X-Request-Id"),
        )

    access_token = payload.get("access_token")
    token_type = payload.get("token_type")
    expires_in = payload.get("expires_in")
    if (
        not isinstance(access_token, str)
        or not access_token
        or not isinstance(token_type, str)
        or not token_type
        or not isinstance(expires_in, int)
    ):
        raise TossAuthenticationError(
            "OAuth token endpoint response fields were invalid.",
            status_code=response.status_code,
            request_id=response.headers.get("X-Request-Id"),
        )
    try:
        return OAuthTokenResponse(
            access_token=access_token,
            token_type=token_type,
            expires_in=expires_in,
        )
    except ValueError as error:
        raise TossAuthenticationError(
            "OAuth token endpoint response values were invalid.",
            status_code=response.status_code,
            request_id=response.headers.get("X-Request-Id"),
        ) from error
