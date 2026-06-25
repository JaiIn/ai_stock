"""Single-symbol Stock Info live smoke path with safe diagnostics."""

from dataclasses import dataclass
from enum import Enum
import re

import httpx

from ai_stock.clients.exceptions import TossApiError, TossClientConfigError
from ai_stock.clients.oauth import OAUTH_TOKEN_PATH, TossOAuthTokenProvider
from ai_stock.clients.stock_info import TossStockInfoClient
from ai_stock.models.auth import OAuthTokenRequest, OAuthTokenResponse
from ai_stock.models.stock_info import StockInfo
from ai_stock.risk import LiveApiSafetyGate, TossEndpointMetadata

STOCKS_PATH = "/api/v1/stocks"
DEFAULT_STOCK_SYMBOL = "005930"


class StockInfoSmokePhase(str, Enum):
    """Safe phases for the approved Stock Info smoke flow."""

    CONFIG_VALIDATION = "config_validation"
    OAUTH_TOKEN = "oauth_token"
    SAFETY_GATE = "safety_gate"
    READONLY_STOCK_INFO = "readonly_stock_info"
    RESPONSE_PARSE = "response_parse"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class StockInfoSmokeDiagnosticResult:
    """Safe diagnostic metadata without credentials, headers, or raw bodies."""

    phase: StockInfoSmokePhase
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
    stocks: tuple[StockInfo, ...] = ()

    def safe_dict(self) -> dict[str, object]:
        """Return only approved diagnostics and parsed field-presence metadata."""

        result: dict[str, object] = {
            "success": self.success,
            "phase": self.phase.value,
            "endpoint": f"{self.method} {self.endpoint}",
            "http_status_code": self.http_status_code,
            "safe_error_code": self.safe_error_code,
            "safe_error_type": self.safe_error_type,
            "safe_error_message": self.safe_error_message,
            "requested_symbols": self.requested_symbol,
        }
        if self.success:
            first = self.stocks[0] if self.stocks else None
            result.update(
                {
                    "token_type": self.token_type,
                    "expires_in": self.expires_in,
                    "result_count": len(self.stocks),
                    "requested_symbol_present": any(
                        stock.stock_code == self.requested_symbol
                        for stock in self.stocks
                    ),
                    "symbol_present": first is not None and bool(first.stock_code),
                    "name_present": first is not None and bool(first.stock_name),
                    "market_present": first is not None and first.market is not None,
                    "currency_present": (
                        first is not None and first.currency is not None
                    ),
                    "shares_outstanding_present": (
                        first is not None
                        and first.shares_outstanding is not None
                    ),
                    "optional_fields_supported": first is not None,
                }
            )
        return result


class StockInfoSmokeFailure(RuntimeError):
    """Carry one safe diagnostic result across smoke layers."""

    def __init__(self, diagnostic: StockInfoSmokeDiagnosticResult) -> None:
        self.diagnostic = diagnostic
        super().__init__(diagnostic.safe_error_message or "Stock Info smoke failed.")


@dataclass(frozen=True, slots=True)
class StockInfoSmokeResult:
    """Parsed single-request result without raw response storage."""

    status_code: int
    stocks: tuple[StockInfo, ...]


class TossStockInfoSmokeClient:
    """Call only the approved single-symbol getStocks endpoint."""

    def __init__(
        self,
        http_client: httpx.Client,
        safety_gate: LiveApiSafetyGate,
        *,
        allow_live_api: bool,
        allow_real_order: bool,
        dry_run_only: bool,
        stock_info_live_smoke_allowed: bool,
    ) -> None:
        self._http_client = http_client
        self._safety_gate = safety_gate
        self._allow_live_api = allow_live_api
        self._allow_real_order = allow_real_order
        self._dry_run_only = dry_run_only
        self._stock_info_live_smoke_allowed = stock_info_live_smoke_allowed

    def get_stocks_once(
        self,
        token: OAuthTokenResponse,
        *,
        symbol: str = DEFAULT_STOCK_SYMBOL,
    ) -> StockInfoSmokeResult:
        """Perform the sole approved Stock Info GET without retries or raw dumps."""

        normalized_symbol = _validated_symbol(symbol)
        if not self._stock_info_live_smoke_allowed:
            raise StockInfoSmokeFailure(
                _failure(
                    StockInfoSmokePhase.CONFIG_VALIDATION,
                    safe_error_type="approval_required",
                    safe_error_message="Explicit Stock Info smoke approval is required.",
                    requested_symbol=normalized_symbol,
                )
            )

        metadata = TossEndpointMetadata(
            method="GET",
            path=STOCKS_PATH,
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
            raise StockInfoSmokeFailure(
                _failure(
                    StockInfoSmokePhase.SAFETY_GATE,
                    safe_error_type="safety_gate_blocked",
                    safe_error_message="Safety gate blocked the Stock Info request.",
                    requested_symbol=normalized_symbol,
                )
            )

        try:
            response = self._http_client.get(
                STOCKS_PATH,
                params={"symbols": normalized_symbol},
                headers=token.authorization_header(),
            )
        except httpx.HTTPError as error:
            raise StockInfoSmokeFailure(
                _network_failure(error, requested_symbol=normalized_symbol)
            ) from error

        try:
            stocks = TossStockInfoClient.parse_stocks_response(response)
        except TossApiError as error:
            phase = (
                StockInfoSmokePhase.READONLY_STOCK_INFO
                if response.status_code >= 400
                else StockInfoSmokePhase.RESPONSE_PARSE
            )
            raise StockInfoSmokeFailure(
                _api_failure(
                    phase,
                    error,
                    fallback_status=response.status_code,
                    requested_symbol=normalized_symbol,
                )
            ) from error
        return StockInfoSmokeResult(
            status_code=response.status_code,
            stocks=tuple(stocks),
        )


def execute_stock_info_single_symbol_smoke(
    http_client: httpx.Client,
    request: OAuthTokenRequest,
    safety_gate: LiveApiSafetyGate,
    *,
    allow_live_api: bool,
    allow_real_order: bool,
    dry_run_only: bool,
    stock_info_live_smoke_allowed: bool,
    symbol: str = DEFAULT_STOCK_SYMBOL,
) -> StockInfoSmokeDiagnosticResult:
    """Run exactly one OAuth request and one single-symbol Stock Info request."""

    try:
        normalized_symbol = _validated_symbol(symbol)
    except ValueError:
        return _failure(
            StockInfoSmokePhase.CONFIG_VALIDATION,
            safe_error_type="invalid_symbol",
            safe_error_message="The approved Stock Info symbol is invalid.",
            requested_symbol="invalid",
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
            StockInfoSmokePhase.OAUTH_TOKEN,
            error,
            endpoint=OAUTH_TOKEN_PATH,
            method="POST",
            requested_symbol=normalized_symbol,
        )
    except (TossClientConfigError, ValueError):
        return _failure(
            StockInfoSmokePhase.CONFIG_VALIDATION,
            endpoint=OAUTH_TOKEN_PATH,
            method="POST",
            safe_error_type="invalid_configuration",
            safe_error_message="OAuth smoke configuration is invalid.",
            requested_symbol=normalized_symbol,
        )

    try:
        result = TossStockInfoSmokeClient(
            http_client,
            safety_gate,
            allow_live_api=allow_live_api,
            allow_real_order=allow_real_order,
            dry_run_only=dry_run_only,
            stock_info_live_smoke_allowed=stock_info_live_smoke_allowed,
        ).get_stocks_once(token, symbol=normalized_symbol)
    except StockInfoSmokeFailure as error:
        return error.diagnostic
    except (RuntimeError, ValueError):
        return _failure(
            StockInfoSmokePhase.UNKNOWN,
            safe_error_type="unknown_failure",
            safe_error_message="Stock Info smoke test failed safely.",
            requested_symbol=normalized_symbol,
        )

    return StockInfoSmokeDiagnosticResult(
        phase=StockInfoSmokePhase.READONLY_STOCK_INFO,
        success=True,
        http_status_code=result.status_code,
        safe_error_code=None,
        safe_error_type=None,
        safe_error_message=None,
        endpoint=STOCKS_PATH,
        method="GET",
        requested_symbol=normalized_symbol,
        token_type=token.token_type,
        expires_in=token.expires_in,
        stocks=result.stocks,
    )


def _validated_symbol(symbol: str) -> str:
    normalized = symbol.strip()
    if re.fullmatch(r"[A-Za-z0-9.-]+", normalized) is None:
        raise ValueError("Invalid stock symbol.")
    return normalized


def _api_failure(
    phase: StockInfoSmokePhase,
    error: TossApiError,
    *,
    endpoint: str = STOCKS_PATH,
    method: str = "GET",
    fallback_status: int | None = None,
    requested_symbol: str,
) -> StockInfoSmokeDiagnosticResult:
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
    requested_symbol: str,
) -> StockInfoSmokeDiagnosticResult:
    if isinstance(error, httpx.TimeoutException):
        error_type, message = "timeout", "Request timed out."
    else:
        error_type, message = "network_error", "Network request failed."
    return _failure(
        StockInfoSmokePhase.READONLY_STOCK_INFO,
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
    phase: StockInfoSmokePhase,
    *,
    endpoint: str = STOCKS_PATH,
    method: str = "GET",
    http_status_code: int | None = None,
    safe_error_code: str | None = None,
    safe_error_type: str,
    safe_error_message: str,
    requested_symbol: str,
) -> StockInfoSmokeDiagnosticResult:
    return StockInfoSmokeDiagnosticResult(
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
