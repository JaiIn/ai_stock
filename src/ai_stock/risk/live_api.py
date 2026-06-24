"""Metadata-only safety gate for future Toss live API integration."""

from dataclasses import dataclass
from enum import Enum
import re

from ai_stock.config.settings import Settings


class LiveApiSafetyError(RuntimeError):
    """Raised when endpoint metadata violates the live API safety policy."""


class LiveApiRiskLevel(str, Enum):
    """Risk classification returned without exposing request credentials."""

    LOW = "low"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class TossEndpointMetadata:
    """Non-sensitive endpoint attributes inspected before any future send."""

    method: str
    path: str
    endpoint_category: str
    requires_auth: bool = True
    requires_account_seq: bool = False


@dataclass(frozen=True, slots=True)
class LiveApiSafetyDecision:
    """Result of evaluating one request candidate without transmitting it."""

    allowed: bool
    reason: str
    endpoint_category: str
    is_read_only: bool
    requires_auth: bool
    requires_account_seq: bool
    dry_run_only: bool
    risk_level: LiveApiRiskLevel


_READ_ONLY_ALLOWLIST = (
    ("GET", re.compile(r"^/api/v1/stocks$")),
    ("GET", re.compile(r"^/api/v1/stocks/[^/]+/warnings$")),
    ("GET", re.compile(r"^/api/v1/prices$")),
    ("GET", re.compile(r"^/api/v1/candles$")),
    ("GET", re.compile(r"^/api/v1/exchange-rate$")),
)

_WRITE_ORDER_DENYLIST = (
    ("POST", re.compile(r"^/api/v1/orders$")),
    ("POST", re.compile(r"^/api/v1/orders/[^/]+/modify$")),
    ("POST", re.compile(r"^/api/v1/orders/[^/]+/cancel$")),
)

_WRITE_CATEGORIES = frozenset({"order", "write", "trading", "mutation"})
_MUTATING_METHODS = frozenset({"POST", "PUT", "PATCH", "DELETE"})


class LiveApiSafetyGate:
    """Fail-closed policy over endpoint metadata and local safety flags."""

    def evaluate(
        self,
        metadata: TossEndpointMetadata,
        *,
        live_api_enabled: bool,
        real_order_allowed: bool,
        dry_run_only: bool,
        send_requested: bool = False,
    ) -> LiveApiSafetyDecision:
        """Return a decision without creating a client, context, token, or request."""

        method = metadata.method.strip().upper()
        path = _normalize_path(metadata.path)
        category = metadata.endpoint_category.strip().lower() or "unknown"
        is_read_only = method == "GET"

        def blocked(reason: str, risk: LiveApiRiskLevel) -> LiveApiSafetyDecision:
            return LiveApiSafetyDecision(
                allowed=False,
                reason=reason,
                endpoint_category=category,
                is_read_only=is_read_only,
                requires_auth=metadata.requires_auth,
                requires_account_seq=metadata.requires_account_seq,
                dry_run_only=dry_run_only,
                risk_level=risk,
            )

        if real_order_allowed:
            return blocked(
                "ALLOW_REAL_ORDER=true is forbidden by the local safety policy.",
                LiveApiRiskLevel.CRITICAL,
            )
        if _matches(method, path, _WRITE_ORDER_DENYLIST):
            return blocked(
                "Order mutation endpoints are permanently denylisted.",
                LiveApiRiskLevel.CRITICAL,
            )
        if category in _WRITE_CATEGORIES or method in _MUTATING_METHODS:
            return blocked(
                "Write, trading, mutation, and non-read-only methods are blocked.",
                LiveApiRiskLevel.CRITICAL,
            )
        if metadata.requires_account_seq:
            return blocked(
                "Account-scoped endpoints require separate user approval.",
                LiveApiRiskLevel.HIGH,
            )
        if not _matches(method, path, _READ_ONLY_ALLOWLIST):
            return blocked(
                "Unknown or pending endpoints are blocked by default.",
                LiveApiRiskLevel.HIGH,
            )
        if not live_api_enabled:
            return blocked(
                "ALLOW_LIVE_API=false blocks live API candidates.",
                LiveApiRiskLevel.HIGH,
            )
        if dry_run_only and send_requested:
            return blocked(
                "DRY_RUN_ONLY=true permits evaluation but blocks network send.",
                LiveApiRiskLevel.HIGH,
            )

        reason = (
            "Read-only endpoint approved for dry-run evaluation only."
            if dry_run_only
            else "Read-only endpoint passed the metadata safety policy."
        )
        return LiveApiSafetyDecision(
            allowed=True,
            reason=reason,
            endpoint_category=category,
            is_read_only=True,
            requires_auth=metadata.requires_auth,
            requires_account_seq=False,
            dry_run_only=dry_run_only,
            risk_level=LiveApiRiskLevel.LOW,
        )

    def evaluate_settings(
        self,
        metadata: TossEndpointMetadata,
        settings: Settings,
        *,
        send_requested: bool = False,
    ) -> LiveApiSafetyDecision:
        """Evaluate using the existing local Settings safety flags."""

        return self.evaluate(
            metadata,
            live_api_enabled=settings.allow_live_api,
            real_order_allowed=settings.allow_real_order,
            dry_run_only=settings.dry_run_only,
            send_requested=send_requested,
        )

    def check_or_raise(
        self,
        metadata: TossEndpointMetadata,
        *,
        live_api_enabled: bool,
        real_order_allowed: bool,
        dry_run_only: bool,
        send_requested: bool = False,
    ) -> LiveApiSafetyDecision:
        """Return an allowed decision or raise a non-sensitive safety error."""

        decision = self.evaluate(
            metadata,
            live_api_enabled=live_api_enabled,
            real_order_allowed=real_order_allowed,
            dry_run_only=dry_run_only,
            send_requested=send_requested,
        )
        if not decision.allowed:
            raise LiveApiSafetyError(decision.reason)
        return decision


def _normalize_path(path: str) -> str:
    normalized = path.strip().split("?", maxsplit=1)[0]
    if not normalized.startswith("/"):
        normalized = f"/{normalized}"
    if normalized != "/":
        normalized = normalized.rstrip("/")
    return normalized


def _matches(
    method: str,
    path: str,
    policies: tuple[tuple[str, re.Pattern[str]], ...],
) -> bool:
    return any(
        method == allowed_method and pattern.fullmatch(path) is not None
        for allowed_method, pattern in policies
    )
