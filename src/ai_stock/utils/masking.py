"""Helpers that prevent sensitive settings from being exposed."""

from collections.abc import Mapping
from typing import Any

SENSITIVE_FIELD_NAMES = frozenset(
    {
        "authorization",
        "llm_api_key",
        "openai_api_key",
        "toss_access_token",
        "toss_account_seq",
        "toss_client_id",
        "toss_client_secret",
        "tossinvest_access_token",
        "tossinvest_account_seq",
        "tossinvest_client_id",
        "tossinvest_client_secret",
        "x_tossinvest_account",
    }
)


def mask_secret(value: str | None, keep: int = 4) -> str:
    """Mask a secret while preserving limited context for long values."""

    if not value:
        return ""
    if keep < 0:
        raise ValueError("keep must be non-negative")
    if keep == 0 or len(value) <= keep * 2:
        return "*" * len(value)
    return f"{value[:keep]}...{value[-keep:]}"


def is_sensitive_field(name: str) -> bool:
    """Return whether a setting or header name must be masked."""

    normalized = name.strip().lower().replace("-", "_")
    return normalized in SENSITIVE_FIELD_NAMES


def _secret_text(value: Any) -> str:
    if value is None:
        return ""
    get_secret_value = getattr(value, "get_secret_value", None)
    if callable(get_secret_value):
        return str(get_secret_value())
    return str(value)


def sanitize_mapping(values: Mapping[str, Any]) -> dict[str, Any]:
    """Recursively copy a mapping while masking known sensitive fields."""

    sanitized: dict[str, Any] = {}
    for key, value in values.items():
        if is_sensitive_field(str(key)):
            sanitized[key] = mask_secret(_secret_text(value))
        elif isinstance(value, Mapping):
            sanitized[key] = sanitize_mapping(value)
        else:
            sanitized[key] = value
    return sanitized
