"""Safety guardrails for paper-trading-only flows."""

from collections.abc import Mapping
from typing import Any


class PaperTradingSafetyError(ValueError):
    """Raised when a non-paper trading mode or live-order flag is detected."""


_FORBIDDEN_TRUE_FLAGS = frozenset(
    {
        "allow_real_order",
        "allow_live_order",
        "real_order",
        "live_order",
        "send_to_broker",
        "submit_to_broker",
        "use_live_account",
        "use_real_account",
    }
)
_FORBIDDEN_TEXT_VALUES = frozenset({"real", "live", "broker", "production"})
_PAPER_TEXT_VALUES = frozenset({"paper", "mock", "simulated", "simulation"})


def assert_paper_trading_only(
    *,
    mode: str = "paper",
    flags: Mapping[str, Any] | None = None,
) -> None:
    """Reject live-trading intent before any simulated trading flow proceeds."""
    normalized_mode = mode.strip().lower() if isinstance(mode, str) else ""
    if normalized_mode not in _PAPER_TEXT_VALUES:
        raise PaperTradingSafetyError("Only paper trading mode is allowed.")

    for key, value in (flags or {}).items():
        normalized_key = key.strip().lower()
        if normalized_key in _FORBIDDEN_TRUE_FLAGS and bool(value):
            raise PaperTradingSafetyError("Live order flags are not allowed.")
        if isinstance(value, str) and value.strip().lower() in _FORBIDDEN_TEXT_VALUES:
            raise PaperTradingSafetyError("Live trading values are not allowed.")
