"""Status mapping and envelope parsing for fake or future Toss responses."""

from collections.abc import Mapping
from typing import Any

import httpx

from ai_stock.clients.exceptions import (
    TossApiError,
    TossAuthenticationError,
    TossPermissionError,
    TossRateLimitError,
    TossServerError,
)
from ai_stock.models.toss import TossErrorPayload


def _error_payload(response: httpx.Response) -> TossErrorPayload:
    try:
        payload = response.json()
    except ValueError:
        return TossErrorPayload(request_id=response.headers.get("X-Request-Id"))

    if not isinstance(payload, Mapping):
        return TossErrorPayload(request_id=response.headers.get("X-Request-Id"))
    error = payload.get("error")
    if not isinstance(error, Mapping):
        return TossErrorPayload(request_id=response.headers.get("X-Request-Id"))
    return TossErrorPayload.from_mapping(error, response.headers.get("X-Request-Id"))


def raise_for_toss_status(response: httpx.Response) -> None:
    """Map an HTTP failure to a safe Toss exception without response bodies."""

    if response.status_code < 400:
        return

    payload = _error_payload(response)
    common = {
        "status_code": response.status_code,
        "error_code": payload.code,
        "request_id": payload.request_id,
    }
    if response.status_code == 401:
        raise TossAuthenticationError(**common)
    if response.status_code == 403:
        raise TossPermissionError(**common)
    if response.status_code == 429:
        raise TossRateLimitError(
            **common,
            retry_after=response.headers.get("Retry-After"),
        )
    if response.status_code >= 500:
        raise TossServerError(**common)
    raise TossApiError(**common)


def extract_toss_result(response: httpx.Response) -> Any:
    """Return the `result` envelope or raise a safe parsing/API error."""

    raise_for_toss_status(response)
    try:
        payload = response.json()
    except ValueError as error:
        raise TossApiError(
            "Toss API response was not valid JSON.",
            status_code=response.status_code,
            request_id=response.headers.get("X-Request-Id"),
        ) from error

    if not isinstance(payload, Mapping):
        raise TossApiError("Toss API response must be a JSON object.")
    if isinstance(payload.get("error"), Mapping):
        details = TossErrorPayload.from_mapping(
            payload["error"],
            response.headers.get("X-Request-Id"),
        )
        raise TossApiError(
            "Toss API returned an error envelope.",
            status_code=response.status_code,
            error_code=details.code,
            request_id=details.request_id,
        )
    if "result" not in payload:
        raise TossApiError(
            "Toss API response did not contain a result envelope.",
            status_code=response.status_code,
            request_id=response.headers.get("X-Request-Id"),
        )
    return payload["result"]
