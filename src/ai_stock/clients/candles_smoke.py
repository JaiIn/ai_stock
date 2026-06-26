"""Single-symbol Candles live smoke path with safe diagnostics."""

from dataclasses import dataclass
from enum import Enum
import re

import httpx

from ai_stock.clients.exceptions import TossApiError, TossClientConfigError
from ai_stock.clients.market_data import TossMarketDataClient
from ai_stock.clients.oauth import OAUTH_TOKEN_PATH, TossOAuthTokenProvider
from ai_stock.models.auth import OAuthTokenRequest, OAuthTokenResponse
from ai_stock.models.market_data import CandlePage
from ai_stock.risk import LiveApiSafetyGate, TossEndpointMetadata

CANDLES_PATH = "/api/v1/candles"
DEFAULT_CANDLE_SYMBOL = "005930"
DEFAULT_CANDLE_INTERVAL = "1d"
DEFAULT_CANDLE_COUNT = 1
DEFAULT_CANDLE_ADJUSTED = True


class CandlesSmokePhase(str, Enum):
    """Safe phases for the approved Candles smoke flow."""

    CONFIG_VALIDATION = "config_validation"
    OAUTH_TOKEN = "oauth_token"
    SAFETY_GATE = "safety_gate"
    READONLY_CANDLES = "readonly_candles"
    RESPONSE_PARSE = "response_parse"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class CandlesSmokeDiagnosticResult:
    """Safe diagnostics without credentials, headers, or raw bodies."""

    phase: CandlesSmokePhase
    success: bool
    http_status_code: int | None
    safe_error_code: str | None
    safe_error_type: str | None
    safe_error_message: str | None
    endpoint: str
    method: str
    requested_symbol: str
    requested_interval: str
    requested_count: int
    requested_adjusted: bool
    token_type: str | None = None
    expires_in: int | None = None
    page: CandlePage | None = None

    def safe_dict(self) -> dict[str, object]:
        """Return only approved diagnostics and parsed-field presence metadata."""

        result: dict[str, object] = {
            "success": self.success,
            "phase": self.phase.value,
            "endpoint": f"{self.method} {self.endpoint}",
            "http_status_code": self.http_status_code,
            "safe_error_code": self.safe_error_code,
            "safe_error_type": self.safe_error_type,
            "safe_error_message": self.safe_error_message,
            "requested_symbol": self.requested_symbol,
            "requested_interval": self.requested_interval,
            "requested_count": self.requested_count,
            "requested_adjusted": self.requested_adjusted,
            "before_parameter_used": False,
        }
        if self.success:
            candles = self.page.candles if self.page is not None else ()
            first = candles[0] if candles else None
            result.update(
                {
                    "token_type": self.token_type,
                    "expires_in": self.expires_in,
                    "candles_count": len(candles),
                    "timestamp_present": first is not None and bool(first.timestamp),
                    "open_present": first is not None,
                    "high_present": first is not None,
                    "low_present": first is not None,
                    "close_present": first is not None,
                    "volume_present": first is not None,
                    "currency_present": (
                        first is not None and bool(first.currency)
                    ),
                    "next_before_supported": self.page is not None,
                    "decimal_conversion_success": first is not None,
                }
            )
        return result


class CandlesSmokeFailure(RuntimeError):
    """Carry one safe diagnostic result across smoke layers."""

    def __init__(self, diagnostic: CandlesSmokeDiagnosticResult) -> None:
        self.diagnostic = diagnostic
        super().__init__(diagnostic.safe_error_message or "Candles smoke failed.")


@dataclass(frozen=True, slots=True)
class CandlesSmokeResult:
    """Parsed Candles result without raw response storage."""

    status_code: int
    page: CandlePage


class TossCandlesSmokeClient:
    """Call only the approved single-symbol getCandles endpoint."""

    def __init__(
        self,
        http_client: httpx.Client,
        safety_gate: LiveApiSafetyGate,
        *,
        allow_live_api: bool,
        allow_real_order: bool,
        dry_run_only: bool,
        candles_live_smoke_allowed: bool,
    ) -> None:
        self._http_client = http_client
        self._safety_gate = safety_gate
        self._allow_live_api = allow_live_api
        self._allow_real_order = allow_real_order
        self._dry_run_only = dry_run_only
        self._candles_live_smoke_allowed = candles_live_smoke_allowed

    def get_candles_once(
        self,
        token: OAuthTokenResponse,
        *,
        symbol: str = DEFAULT_CANDLE_SYMBOL,
        interval: str = DEFAULT_CANDLE_INTERVAL,
        count: int = DEFAULT_CANDLE_COUNT,
        adjusted: bool = DEFAULT_CANDLE_ADJUSTED,
    ) -> CandlesSmokeResult:
        """Perform the sole approved Candles GET without retries or raw dumps."""

        normalized_symbol = _validated_symbol(symbol)
        _validate_query(interval=interval, count=count, adjusted=adjusted)
        if not self._candles_live_smoke_allowed:
            raise CandlesSmokeFailure(
                _failure(
                    CandlesSmokePhase.CONFIG_VALIDATION,
                    safe_error_type="approval_required",
                    safe_error_message="Explicit Candles smoke approval is required.",
                    requested_symbol=normalized_symbol,
                    requested_interval=interval,
                    requested_count=count,
                    requested_adjusted=adjusted,
                )
            )

        metadata = TossEndpointMetadata(
            method="GET",
            path=CANDLES_PATH,
            endpoint_category="market_data",
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
            raise CandlesSmokeFailure(
                _failure(
                    CandlesSmokePhase.SAFETY_GATE,
                    safe_error_type="safety_gate_blocked",
                    safe_error_message="Safety gate blocked the Candles request.",
                    requested_symbol=normalized_symbol,
                    requested_interval=interval,
                    requested_count=count,
                    requested_adjusted=adjusted,
                )
            )

        try:
            response = self._http_client.get(
                CANDLES_PATH,
                params={
                    "symbol": normalized_symbol,
                    "interval": interval,
                    "count": count,
                    "adjusted": adjusted,
                },
                headers=token.authorization_header(),
            )
        except httpx.HTTPError as error:
            raise CandlesSmokeFailure(
                _network_failure(
                    error,
                    requested_symbol=normalized_symbol,
                    requested_interval=interval,
                    requested_count=count,
                    requested_adjusted=adjusted,
                )
            ) from error

        try:
            page = TossMarketDataClient.parse_candles_response(response)
        except TossApiError as error:
            phase = (
                CandlesSmokePhase.READONLY_CANDLES
                if response.status_code >= 400
                else CandlesSmokePhase.RESPONSE_PARSE
            )
            raise CandlesSmokeFailure(
                _api_failure(
                    phase,
                    error,
                    fallback_status=response.status_code,
                    requested_symbol=normalized_symbol,
                    requested_interval=interval,
                    requested_count=count,
                    requested_adjusted=adjusted,
                )
            ) from error
        return CandlesSmokeResult(status_code=response.status_code, page=page)


def execute_candles_single_symbol_smoke(
    http_client: httpx.Client,
    request: OAuthTokenRequest,
    safety_gate: LiveApiSafetyGate,
    *,
    allow_live_api: bool,
    allow_real_order: bool,
    dry_run_only: bool,
    candles_live_smoke_allowed: bool,
    symbol: str = DEFAULT_CANDLE_SYMBOL,
    interval: str = DEFAULT_CANDLE_INTERVAL,
    count: int = DEFAULT_CANDLE_COUNT,
    adjusted: bool = DEFAULT_CANDLE_ADJUSTED,
) -> CandlesSmokeDiagnosticResult:
    """Run exactly one OAuth request and one single-symbol Candles request."""

    try:
        normalized_symbol = _validated_symbol(symbol)
        _validate_query(interval=interval, count=count, adjusted=adjusted)
    except ValueError:
        return _failure(
            CandlesSmokePhase.CONFIG_VALIDATION,
            safe_error_type="invalid_query",
            safe_error_message="The approved Candles query is invalid.",
            requested_symbol="invalid",
            requested_interval=interval,
            requested_count=count,
            requested_adjusted=adjusted,
        )

    try:
        token = TossOAuthTokenProvider(
            http_client,
            allow_live_api=allow_live_api,
            allow_real_order=allow_real_order,
            dry_run_only=dry_run_only,
        ).acquire_token(request)
    except TossApiError as error:
        return _api_failure(
            CandlesSmokePhase.OAUTH_TOKEN,
            error,
            endpoint=OAUTH_TOKEN_PATH,
            method="POST",
            requested_symbol=normalized_symbol,
            requested_interval=interval,
            requested_count=count,
            requested_adjusted=adjusted,
        )
    except (TossClientConfigError, ValueError):
        return _failure(
            CandlesSmokePhase.CONFIG_VALIDATION,
            endpoint=OAUTH_TOKEN_PATH,
            method="POST",
            safe_error_type="invalid_configuration",
            safe_error_message="OAuth smoke configuration is invalid.",
            requested_symbol=normalized_symbol,
            requested_interval=interval,
            requested_count=count,
            requested_adjusted=adjusted,
        )

    try:
        result = TossCandlesSmokeClient(
            http_client,
            safety_gate,
            allow_live_api=allow_live_api,
            allow_real_order=allow_real_order,
            dry_run_only=dry_run_only,
            candles_live_smoke_allowed=candles_live_smoke_allowed,
        ).get_candles_once(
            token,
            symbol=normalized_symbol,
            interval=interval,
            count=count,
            adjusted=adjusted,
        )
    except CandlesSmokeFailure as error:
        return error.diagnostic
    except (RuntimeError, ValueError):
        return _failure(
            CandlesSmokePhase.UNKNOWN,
            safe_error_type="unknown_failure",
            safe_error_message="Candles smoke test failed safely.",
            requested_symbol=normalized_symbol,
            requested_interval=interval,
            requested_count=count,
            requested_adjusted=adjusted,
        )

    return CandlesSmokeDiagnosticResult(
        phase=CandlesSmokePhase.READONLY_CANDLES,
        success=True,
        http_status_code=result.status_code,
        safe_error_code=None,
        safe_error_type=None,
        safe_error_message=None,
        endpoint=CANDLES_PATH,
        method="GET",
        requested_symbol=normalized_symbol,
        requested_interval=interval,
        requested_count=count,
        requested_adjusted=adjusted,
        token_type=token.token_type,
        expires_in=token.expires_in,
        page=result.page,
    )


def _validated_symbol(symbol: str) -> str:
    normalized = symbol.strip()
    if re.fullmatch(r"[A-Za-z0-9.-]+", normalized) is None:
        raise ValueError("Invalid stock symbol.")
    return normalized


def _validate_query(*, interval: str, count: int, adjusted: bool) -> None:
    if interval != DEFAULT_CANDLE_INTERVAL:
        raise ValueError("Only the approved daily interval is allowed.")
    if isinstance(count, bool) or count != DEFAULT_CANDLE_COUNT:
        raise ValueError("Only the approved count=1 query is allowed.")
    if adjusted is not DEFAULT_CANDLE_ADJUSTED:
        raise ValueError("Only the approved adjusted=true query is allowed.")


def _api_failure(
    phase: CandlesSmokePhase,
    error: TossApiError,
    *,
    endpoint: str = CANDLES_PATH,
    method: str = "GET",
    fallback_status: int | None = None,
    requested_symbol: str,
    requested_interval: str,
    requested_count: int,
    requested_adjusted: bool,
) -> CandlesSmokeDiagnosticResult:
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
        requested_interval=requested_interval,
        requested_count=requested_count,
        requested_adjusted=requested_adjusted,
    )


def _network_failure(
    error: httpx.HTTPError,
    *,
    requested_symbol: str,
    requested_interval: str,
    requested_count: int,
    requested_adjusted: bool,
) -> CandlesSmokeDiagnosticResult:
    if isinstance(error, httpx.TimeoutException):
        error_type, message = "timeout", "Request timed out."
    else:
        error_type, message = "network_error", "Network request failed."
    return _failure(
        CandlesSmokePhase.READONLY_CANDLES,
        safe_error_type=error_type,
        safe_error_message=message,
        requested_symbol=requested_symbol,
        requested_interval=requested_interval,
        requested_count=requested_count,
        requested_adjusted=requested_adjusted,
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
    phase: CandlesSmokePhase,
    *,
    endpoint: str = CANDLES_PATH,
    method: str = "GET",
    http_status_code: int | None = None,
    safe_error_code: str | None = None,
    safe_error_type: str,
    safe_error_message: str,
    requested_symbol: str,
    requested_interval: str,
    requested_count: int,
    requested_adjusted: bool,
) -> CandlesSmokeDiagnosticResult:
    return CandlesSmokeDiagnosticResult(
        phase=phase,
        success=False,
        http_status_code=http_status_code,
        safe_error_code=safe_error_code,
        safe_error_type=safe_error_type,
        safe_error_message=safe_error_message,
        endpoint=endpoint,
        method=method,
        requested_symbol=requested_symbol,
        requested_interval=requested_interval,
        requested_count=requested_count,
        requested_adjusted=requested_adjusted,
    )
