"""Minimal non-sensitive metadata models for Toss response errors."""

from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class TossErrorPayload:
    """Error metadata safe to retain in exceptions and reports."""

    request_id: str | None = None
    code: str | None = None

    @classmethod
    def from_mapping(
        cls,
        payload: Mapping[str, Any],
        fallback_request_id: str | None = None,
    ) -> "TossErrorPayload":
        request_id = payload.get("requestId") or fallback_request_id
        code = payload.get("code")
        return cls(
            request_id=str(request_id) if request_id is not None else None,
            code=str(code) if code is not None else None,
        )
