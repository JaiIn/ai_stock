"""One-endpoint live read-only smoke client with safe phase diagnostics."""

from dataclasses import dataclass
from enum import Enum
import re

import httpx

from ai_stock.clients.exceptions import TossApiError, TossClientConfigError
from ai_stock.clients.market_info import (
    TossMarketInfoClient,
    build_exchange_rate_params,
)
from ai_stock.clients.oauth import TossOAuthTokenProvider
from ai_stock.models.auth import OAuthTokenResponse
from ai_stock.models.auth import OAuthTokenRequest
from ai_stock.models.market_info import ExchangeRate
from ai_stock.risk import LiveApiSafetyGate, TossEndpointMetadata

EXCHANGE_RATE_PATH = "/api/v1/exchange-rate"
OAUTH_TOKEN_ENDPOINT = "/oauth2/token"
DEFAULT_BASE_CURRENCY = "USD"
DEFAULT_QUOTE_CURRENCY = "KRW"


class ReadOnlySmokePhase(str, Enum):
    """Safe phase names for diagnostics without request or response payloads."""

    CONFIG_VALIDATION = "config_validation"
    OAUTH_TOKEN = "oauth_token"
    SAFETY_GATE = "safety_gate"
    READONLY_EXCHANGE_RATE = "readonly_exchange_rate"
    RESPONSE_PARSE = "response_parse"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ReadOnlySmokeDiagnosticResult:
    """Safe smoke result that never contains credentials, headers, or raw bodies."""

    phase: ReadOnlySmokePhase
    success: bool
    http_status_code: int | None
    safe_error_code: str | None
    safe_error_type: str | None
    safe_error_message: str | None
    endpoint: str
    method: str
    token_type: str | None = None
    expires_in: int | None = None
    exchange_rate: ExchangeRate | None = None

    def safe_dict(self) -> dict[str, object]:
        """Return only approved diagnostic and parsed-field-presence metadata."""

        result: dict[str, object] = {
            "success": self.success,
            "phase": self.phase.value,
            "endpoint": f"{self.method} {self.endpoint}",
            "http_status_code": self.http_status_code,
            "safe_error_code": self.safe_error_code,
            "safe_error_type": self.safe_error_type,
            "safe_error_message": self.safe_error_message,
        }
        if self.success and self.exchange_rate is not None:
            result.update(
                {
                    "token_type": self.token_type,
                    "expires_in": self.expires_in,
                    "base_currency": self.exchange_rate.base_currency,
                    "quote_currency": self.exchange_rate.quote_currency,
                    "rate_present": self.exchange_rate.rate.is_finite(),
                    "mid_rate_present": (
                        self.exchange_rate.mid_rate is not None
                        and self.exchange_rate.mid_rate.is_finite()
                    ),
                    "basis_point_present": (
                        self.exchange_rate.basis_point is not None
                        and self.exchange_rate.basis_point.is_finite()
                    ),
                    "rate_change_type_present": (
                        self.exchange_rate.rate_change_type is not None
                    ),
                    "valid_from_present": self.exchange_rate.valid_from is not None,
                    "valid_until_present": self.exchange_rate.valid_until is not None,
                }
            )
        return result


class ReadOnlySmokeFailure(RuntimeError):
    """Carry only a safe diagnostic result across smoke-test layers."""

    def __init__(self, diagnostic: ReadOnlySmokeDiagnosticResult) -> None:
        self.diagnostic = diagnostic
        super().__init__(diagnostic.safe_error_message or "Read-only smoke test failed.")


@dataclass(frozen=True, slots=True)
class ReadOnlySmokeResult:
    """Safe result metadata and parsed model without raw response storage."""

    status_code: int
    exchange_rate: ExchangeRate


class TossReadOnlySmokeClient:
    """Call only the approved exchange-rate endpoint after a safety decision."""

    def __init__(
        self,
        http_client: httpx.Client,
        safety_gate: LiveApiSafetyGate,
        *,
        allow_live_api: bool,
        allow_real_order: bool,
        dry_run_only: bool,
        read_only_live_smoke_allowed: bool,
    ) -> None:
        self._http_client = http_client
        self._safety_gate = safety_gate
        self._allow_live_api = allow_live_api
        self._allow_real_order = allow_real_order
        self._dry_run_only = dry_run_only
        self._read_only_live_smoke_allowed = read_only_live_smoke_allowed

    def get_exchange_rate_once(
        self,
        token: OAuthTokenResponse,
        *,
        base_currency: str = DEFAULT_BASE_CURRENCY,
        quote_currency: str = DEFAULT_QUOTE_CURRENCY,
    ) -> ReadOnlySmokeResult:
        """Perform the sole approved business GET without logging token or body."""

        if not self._read_only_live_smoke_allowed:
            raise ReadOnlySmokeFailure(
                _failure(
                    ReadOnlySmokePhase.CONFIG_VALIDATION,
                    EXCHANGE_RATE_PATH,
                    "GET",
                    safe_error_type="approval_required",
                    safe_error_message="Explicit read-only smoke approval is required.",
                )
            )

        metadata = TossEndpointMetadata(
            method="GET",
            path=EXCHANGE_RATE_PATH,
            endpoint_category="market_info",
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
            raise ReadOnlySmokeFailure(
                _failure(
                    ReadOnlySmokePhase.SAFETY_GATE,
                    EXCHANGE_RATE_PATH,
                    "GET",
                    safe_error_type="safety_gate_blocked",
                    safe_error_message="Safety gate blocked the read-only request.",
                )
            )

        params = build_exchange_rate_params(
            base_currency=base_currency,
            quote_currency=quote_currency,
        )
        try:
            response = self._http_client.get(
                EXCHANGE_RATE_PATH,
                params=params,
                headers=token.authorization_header(),
            )
        except httpx.HTTPError as error:
            raise ReadOnlySmokeFailure(
                _network_failure(
                    ReadOnlySmokePhase.READONLY_EXCHANGE_RATE,
                    EXCHANGE_RATE_PATH,
                    "GET",
                    error,
                )
            ) from error

        try:
            exchange_rate = TossMarketInfoClient.parse_exchange_rate_response(response)
        except TossApiError as error:
            phase = (
                ReadOnlySmokePhase.READONLY_EXCHANGE_RATE
                if response.status_code >= 400
                else ReadOnlySmokePhase.RESPONSE_PARSE
            )
            raise ReadOnlySmokeFailure(
                _api_failure(
                    phase,
                    EXCHANGE_RATE_PATH,
                    "GET",
                    error,
                    fallback_status=response.status_code,
                )
            ) from error
        return ReadOnlySmokeResult(
            status_code=response.status_code,
            exchange_rate=exchange_rate,
        )


def execute_readonly_exchange_rate_smoke(
    http_client: httpx.Client,
    request: OAuthTokenRequest,
    safety_gate: LiveApiSafetyGate,
    *,
    allow_live_api: bool,
    allow_real_order: bool,
    dry_run_only: bool,
    read_only_live_smoke_allowed: bool,
    base_currency: str = DEFAULT_BASE_CURRENCY,
    quote_currency: str = DEFAULT_QUOTE_CURRENCY,
) -> ReadOnlySmokeDiagnosticResult:
    """Run the fixed OAuth and exchange-rate flow with safe failure diagnostics."""

    try:
        token = TossOAuthTokenProvider(
            http_client,
            allow_live_api=allow_live_api,
            allow_real_order=allow_real_order,
            dry_run_only=dry_run_only,
        ).acquire_token(request)
    except TossApiError as error:
        return _api_failure(
            ReadOnlySmokePhase.OAUTH_TOKEN,
            OAUTH_TOKEN_ENDPOINT,
            "POST",
            error,
        )
    except (TossClientConfigError, ValueError):
        return _failure(
            ReadOnlySmokePhase.CONFIG_VALIDATION,
            OAUTH_TOKEN_ENDPOINT,
            "POST",
            safe_error_type="invalid_configuration",
            safe_error_message="OAuth smoke configuration is invalid.",
        )

    try:
        result = TossReadOnlySmokeClient(
            http_client,
            safety_gate,
            allow_live_api=allow_live_api,
            allow_real_order=allow_real_order,
            dry_run_only=dry_run_only,
            read_only_live_smoke_allowed=read_only_live_smoke_allowed,
        ).get_exchange_rate_once(
            token,
            base_currency=base_currency,
            quote_currency=quote_currency,
        )
    except ReadOnlySmokeFailure as error:
        return error.diagnostic
    except (RuntimeError, ValueError):
        return _failure(
            ReadOnlySmokePhase.UNKNOWN,
            EXCHANGE_RATE_PATH,
            "GET",
            safe_error_type="unknown_failure",
            safe_error_message="Read-only smoke test failed safely.",
        )

    return ReadOnlySmokeDiagnosticResult(
        phase=ReadOnlySmokePhase.READONLY_EXCHANGE_RATE,
        success=True,
        http_status_code=result.status_code,
        safe_error_code=None,
        safe_error_type=None,
        safe_error_message=None,
        endpoint=EXCHANGE_RATE_PATH,
        method="GET",
        token_type=token.token_type,
        expires_in=token.expires_in,
        exchange_rate=result.exchange_rate,
    )


def _api_failure(
    phase: ReadOnlySmokePhase,
    endpoint: str,
    method: str,
    error: TossApiError,
    *,
    fallback_status: int | None = None,
) -> ReadOnlySmokeDiagnosticResult:
    status = error.status_code if error.status_code is not None else fallback_status
    error_type, message = _status_summary(status)
    if status is None:
        cause = error.__cause__
        if isinstance(cause, httpx.TimeoutException):
            error_type, message = "timeout", "Request timed out."
        else:
            error_type, message = "request_failed", "Request failed."
    return _failure(
        phase,
        endpoint,
        method,
        http_status_code=status,
        safe_error_code=_safe_error_code(error.error_code),
        safe_error_type=error_type,
        safe_error_message=message,
    )


def _network_failure(
    phase: ReadOnlySmokePhase,
    endpoint: str,
    method: str,
    error: httpx.HTTPError,
) -> ReadOnlySmokeDiagnosticResult:
    if isinstance(error, httpx.TimeoutException):
        error_type, message = "timeout", "Request timed out."
    else:
        error_type, message = "network_error", "Network request failed."
    return _failure(
        phase,
        endpoint,
        method,
        safe_error_type=error_type,
        safe_error_message=message,
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
    phase: ReadOnlySmokePhase,
    endpoint: str,
    method: str,
    *,
    http_status_code: int | None = None,
    safe_error_code: str | None = None,
    safe_error_type: str,
    safe_error_message: str,
) -> ReadOnlySmokeDiagnosticResult:
    return ReadOnlySmokeDiagnosticResult(
        phase=phase,
        success=False,
        http_status_code=http_status_code,
        safe_error_code=safe_error_code,
        safe_error_type=safe_error_type,
        safe_error_message=safe_error_message,
        endpoint=endpoint,
        method=method,
    )
