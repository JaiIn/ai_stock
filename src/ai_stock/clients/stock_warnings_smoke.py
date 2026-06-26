"""Single-symbol Stock Warnings live smoke path with safe diagnostics."""

from dataclasses import dataclass
from enum import Enum
import re

import httpx

from ai_stock.clients.exceptions import TossApiError, TossClientConfigError
from ai_stock.clients.oauth import OAUTH_TOKEN_PATH, TossOAuthTokenProvider
from ai_stock.clients.stock_info import TossStockInfoClient
from ai_stock.models.auth import OAuthTokenRequest, OAuthTokenResponse
from ai_stock.models.stock_info import StockWarning
from ai_stock.risk import LiveApiSafetyGate, TossEndpointMetadata

DEFAULT_WARNING_SYMBOL = "005930"
WARNINGS_PATH_TEMPLATE = "/api/v1/stocks/{symbol}/warnings"


class StockWarningsSmokePhase(str, Enum):
    """Safe phases for the approved Stock Warnings smoke flow."""

    CONFIG_VALIDATION = "config_validation"
    OAUTH_TOKEN = "oauth_token"
    SAFETY_GATE = "safety_gate"
    READONLY_STOCK_WARNINGS = "readonly_stock_warnings"
    RESPONSE_PARSE = "response_parse"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class StockWarningsSmokeDiagnosticResult:
    """Safe diagnostics without credentials, headers, or raw bodies."""

    phase: StockWarningsSmokePhase
    success: bool
    http_status_code: int | None
    safe_error_code: str | None
    safe_error_type: str | None
    safe_error_message: str | None
    endpoint: str
    method: str
    requested_symbol: str
    token_type: str | None = None
    expires_in: int | None = None
    warnings: tuple[StockWarning, ...] = ()

    def safe_dict(self) -> dict[str, object]:
        """Return only approved diagnostics and parsed-field presence."""

        result: dict[str, object] = {
            "success": self.success,
            "phase": self.phase.value,
            "endpoint": f"{self.method} {self.endpoint}",
            "http_status_code": self.http_status_code,
            "safe_error_code": self.safe_error_code,
            "safe_error_type": self.safe_error_type,
            "safe_error_message": self.safe_error_message,
            "requested_symbol": self.requested_symbol,
        }
        if self.success:
            first = self.warnings[0] if self.warnings else None
            result.update(
                {
                    "token_type": self.token_type,
                    "expires_in": self.expires_in,
                    "warning_count": len(self.warnings),
                    "parsed_symbol_present": any(
                        warning.stock_code == self.requested_symbol
                        for warning in self.warnings
                    ),
                    "warning_type_present": (
                        first is not None and bool(first.warning_type)
                    ),
                    "exchange_field_supported": first is not None,
                    "start_date_field_supported": first is not None,
                    "end_date_field_supported": first is not None,
                    "empty_warning_array_supported": not self.warnings,
                }
            )
        return result


class StockWarningsSmokeFailure(RuntimeError):
    """Carry one safe diagnostic result across smoke layers."""

    def __init__(self, diagnostic: StockWarningsSmokeDiagnosticResult) -> None:
        self.diagnostic = diagnostic
        super().__init__(
            diagnostic.safe_error_message or "Stock Warnings smoke failed."
        )


@dataclass(frozen=True, slots=True)
class StockWarningsSmokeResult:
    """Parsed warnings result without raw response storage."""

    status_code: int
    warnings: tuple[StockWarning, ...]


class TossStockWarningsSmokeClient:
    """Call only one approved getStockWarnings endpoint."""

    def __init__(
        self,
        http_client: httpx.Client,
        safety_gate: LiveApiSafetyGate,
        *,
        allow_live_api: bool,
        allow_real_order: bool,
        dry_run_only: bool,
        stock_warnings_live_smoke_allowed: bool,
    ) -> None:
        self._http_client = http_client
        self._safety_gate = safety_gate
        self._allow_live_api = allow_live_api
        self._allow_real_order = allow_real_order
        self._dry_run_only = dry_run_only
        self._stock_warnings_live_smoke_allowed = (
            stock_warnings_live_smoke_allowed
        )

    def get_warnings_once(
        self,
        token: OAuthTokenResponse,
        *,
        symbol: str = DEFAULT_WARNING_SYMBOL,
    ) -> StockWarningsSmokeResult:
        """Perform the sole approved warnings GET without retries or raw dumps."""

        normalized_symbol = _validated_symbol(symbol)
        path = _warnings_path(normalized_symbol)
        if not self._stock_warnings_live_smoke_allowed:
            raise StockWarningsSmokeFailure(
                _failure(
                    StockWarningsSmokePhase.CONFIG_VALIDATION,
                    endpoint=path,
                    safe_error_type="approval_required",
                    safe_error_message=(
                        "Explicit Stock Warnings smoke approval is required."
                    ),
                    requested_symbol=normalized_symbol,
                )
            )

        metadata = TossEndpointMetadata(
            method="GET",
            path=path,
            endpoint_category="stock_info",
            requires_auth=True,
            requires_account_seq=False,
        )
        decision = self._safety_gate.evaluate(
            metadata,
            live_api_enabled=self._allow_live_api,
            real_order_allowed=self._allow_real_order,
            dry_run_only=self._dry_run_only,
            send_requested=False,
        )
        if not decision.allowed:
            raise StockWarningsSmokeFailure(
                _failure(
                    StockWarningsSmokePhase.SAFETY_GATE,
                    endpoint=path,
                    safe_error_type="safety_gate_blocked",
                    safe_error_message="Safety gate blocked the warnings request.",
                    requested_symbol=normalized_symbol,
                )
            )

        try:
            response = self._http_client.get(
                path,
                headers=token.authorization_header(),
            )
        except httpx.HTTPError as error:
            raise StockWarningsSmokeFailure(
                _network_failure(
                    error,
                    endpoint=path,
                    requested_symbol=normalized_symbol,
                )
            ) from error

        try:
            warnings = TossStockInfoClient.parse_stock_warnings_response(
                normalized_symbol,
                response,
            )
        except TossApiError as error:
            phase = (
                StockWarningsSmokePhase.READONLY_STOCK_WARNINGS
                if response.status_code >= 400
                else StockWarningsSmokePhase.RESPONSE_PARSE
            )
            raise StockWarningsSmokeFailure(
                _api_failure(
                    phase,
                    error,
                    endpoint=path,
                    fallback_status=response.status_code,
                    requested_symbol=normalized_symbol,
                )
            ) from error
        return StockWarningsSmokeResult(
            status_code=response.status_code,
            warnings=tuple(warnings),
        )


def execute_stock_warnings_single_symbol_smoke(
    http_client: httpx.Client,
    request: OAuthTokenRequest,
    safety_gate: LiveApiSafetyGate,
    *,
    allow_live_api: bool,
    allow_real_order: bool,
    dry_run_only: bool,
    stock_warnings_live_smoke_allowed: bool,
    symbol: str = DEFAULT_WARNING_SYMBOL,
) -> StockWarningsSmokeDiagnosticResult:
    """Run exactly one OAuth request and one single-symbol warnings request."""

    try:
        normalized_symbol = _validated_symbol(symbol)
    except ValueError:
        return _failure(
            StockWarningsSmokePhase.CONFIG_VALIDATION,
            endpoint=WARNINGS_PATH_TEMPLATE,
            safe_error_type="invalid_symbol",
            safe_error_message="The approved Stock Warnings symbol is invalid.",
            requested_symbol="invalid",
        )
    path = _warnings_path(normalized_symbol)

    try:
        token = TossOAuthTokenProvider(
            http_client,
            allow_live_api=allow_live_api,
            allow_real_order=allow_real_order,
            dry_run_only=dry_run_only,
        ).acquire_token(request)
    except TossApiError as error:
        return _api_failure(
            StockWarningsSmokePhase.OAUTH_TOKEN,
            error,
            endpoint=OAUTH_TOKEN_PATH,
            method="POST",
            requested_symbol=normalized_symbol,
        )
    except (TossClientConfigError, ValueError):
        return _failure(
            StockWarningsSmokePhase.CONFIG_VALIDATION,
            endpoint=OAUTH_TOKEN_PATH,
            method="POST",
            safe_error_type="invalid_configuration",
            safe_error_message="OAuth smoke configuration is invalid.",
            requested_symbol=normalized_symbol,
        )

    try:
        result = TossStockWarningsSmokeClient(
            http_client,
            safety_gate,
            allow_live_api=allow_live_api,
            allow_real_order=allow_real_order,
            dry_run_only=dry_run_only,
            stock_warnings_live_smoke_allowed=stock_warnings_live_smoke_allowed,
        ).get_warnings_once(token, symbol=normalized_symbol)
    except StockWarningsSmokeFailure as error:
        return error.diagnostic
    except (RuntimeError, ValueError):
        return _failure(
            StockWarningsSmokePhase.UNKNOWN,
            endpoint=path,
            safe_error_type="unknown_failure",
            safe_error_message="Stock Warnings smoke test failed safely.",
            requested_symbol=normalized_symbol,
        )

    return StockWarningsSmokeDiagnosticResult(
        phase=StockWarningsSmokePhase.READONLY_STOCK_WARNINGS,
        success=True,
        http_status_code=result.status_code,
        safe_error_code=None,
        safe_error_type=None,
        safe_error_message=None,
        endpoint=path,
        method="GET",
        requested_symbol=normalized_symbol,
        token_type=token.token_type,
        expires_in=token.expires_in,
        warnings=result.warnings,
    )


def _validated_symbol(symbol: str) -> str:
    normalized = symbol.strip()
    if re.fullmatch(r"[A-Za-z0-9.-]+", normalized) is None:
        raise ValueError("Invalid stock symbol.")
    return normalized


def _warnings_path(symbol: str) -> str:
    return WARNINGS_PATH_TEMPLATE.format(symbol=symbol)


def _api_failure(
    phase: StockWarningsSmokePhase,
    error: TossApiError,
    *,
    endpoint: str,
    method: str = "GET",
    fallback_status: int | None = None,
    requested_symbol: str,
) -> StockWarningsSmokeDiagnosticResult:
    status = error.status_code if error.status_code is not None else fallback_status
    error_type, message = _status_summary(status)
    if status is None:
        error_type, message = "request_failed", "Request failed."
    return _failure(
        phase,
        endpoint=endpoint,
        method=method,
        http_status_code=status,
        safe_error_code=_safe_error_code(error.error_code),
        safe_error_type=error_type,
        safe_error_message=message,
        requested_symbol=requested_symbol,
    )


def _network_failure(
    error: httpx.HTTPError,
    *,
    endpoint: str,
    requested_symbol: str,
) -> StockWarningsSmokeDiagnosticResult:
    if isinstance(error, httpx.TimeoutException):
        error_type, message = "timeout", "Request timed out."
    else:
        error_type, message = "network_error", "Network request failed."
    return _failure(
        StockWarningsSmokePhase.READONLY_STOCK_WARNINGS,
        endpoint=endpoint,
        safe_error_type=error_type,
        safe_error_message=message,
        requested_symbol=requested_symbol,
    )


def _status_summary(status: int | None) -> tuple[str, str]:
    summaries = {
        401: ("http_unauthorized", "HTTP 401 unauthorized."),
        403: ("http_forbidden", "HTTP 403 forbidden."),
        404: ("http_not_found", "HTTP 404 not found."),
        429: ("http_rate_limited", "HTTP 429 rate limited."),
    }
    if status in summaries:
        return summaries[status]
    if status is not None and status >= 500:
        return "http_server_error", "HTTP server error."
    if status is not None and status >= 400:
        return "http_error", "HTTP request failed."
    return "response_parse_failed", "Response parse failed."


def _safe_error_code(error_code: str | None) -> str | None:
    if error_code is None:
        return None
    return error_code if re.fullmatch(r"[A-Za-z0-9_.-]{1,64}", error_code) else None


def _failure(
    phase: StockWarningsSmokePhase,
    *,
    endpoint: str,
    method: str = "GET",
    http_status_code: int | None = None,
    safe_error_code: str | None = None,
    safe_error_type: str,
    safe_error_message: str,
    requested_symbol: str,
) -> StockWarningsSmokeDiagnosticResult:
    return StockWarningsSmokeDiagnosticResult(
        phase=phase,
        success=False,
        http_status_code=http_status_code,
        safe_error_code=safe_error_code,
        safe_error_type=safe_error_type,
        safe_error_message=safe_error_message,
        endpoint=endpoint,
        method=method,
        requested_symbol=requested_symbol,
    )
