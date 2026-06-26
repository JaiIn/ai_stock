"""Run the approved OAuth plus single-symbol Candles live smoke test."""

from __future__ import annotations

import json

import httpx
from pydantic import ValidationError

from ai_stock.clients.candles_smoke import (
    CANDLES_PATH,
    DEFAULT_CANDLE_ADJUSTED,
    DEFAULT_CANDLE_COUNT,
    DEFAULT_CANDLE_INTERVAL,
    DEFAULT_CANDLE_SYMBOL,
    CandlesSmokeDiagnosticResult,
    CandlesSmokePhase,
    execute_candles_single_symbol_smoke,
)
from ai_stock.config import load_settings
from ai_stock.models import OAuthTokenRequest
from ai_stock.risk import LiveApiSafetyGate


def main() -> int:
    """Run two fixed requests and print only non-sensitive diagnostics."""

    try:
        settings = load_settings()
    except ValidationError:
        _print_result(_config_failure("invalid_configuration"))
        return 2

    if (
        not settings.allow_live_api
        or settings.allow_real_order
        or not settings.dry_run_only
    ):
        _print_result(_config_failure("unsafe_configuration"))
        return 2
    if settings.toss_client_id is None or settings.toss_client_secret is None:
        _print_result(_config_failure("missing_credentials"))
        return 2

    request = OAuthTokenRequest(
        client_id=settings.toss_client_id.get_secret_value(),
        client_secret=settings.toss_client_secret.get_secret_value(),
    )
    with httpx.Client(
        base_url="https://openapi.tossinvest.com",
        timeout=10.0,
        follow_redirects=False,
    ) as http_client:
        result = execute_candles_single_symbol_smoke(
            http_client,
            request,
            LiveApiSafetyGate(),
            allow_live_api=settings.allow_live_api,
            allow_real_order=settings.allow_real_order,
            dry_run_only=settings.dry_run_only,
            candles_live_smoke_allowed=True,
            symbol=DEFAULT_CANDLE_SYMBOL,
            interval=DEFAULT_CANDLE_INTERVAL,
            count=DEFAULT_CANDLE_COUNT,
            adjusted=DEFAULT_CANDLE_ADJUSTED,
        )
    _print_result(result)
    return 0 if result.success else 1


def _config_failure(safe_error_type: str) -> CandlesSmokeDiagnosticResult:
    return CandlesSmokeDiagnosticResult(
        phase=CandlesSmokePhase.CONFIG_VALIDATION,
        success=False,
        http_status_code=None,
        safe_error_code=None,
        safe_error_type=safe_error_type,
        safe_error_message="Candles smoke safety settings are invalid.",
        endpoint=CANDLES_PATH,
        method="GET",
        requested_symbol=DEFAULT_CANDLE_SYMBOL,
        requested_interval=DEFAULT_CANDLE_INTERVAL,
        requested_count=DEFAULT_CANDLE_COUNT,
        requested_adjusted=DEFAULT_CANDLE_ADJUSTED,
    )


def _print_result(result: CandlesSmokeDiagnosticResult) -> None:
    label = "PASS" if result.success else "FAIL"
    print(f"[{label}] Candles API smoke test diagnostic.")
    print(json.dumps(result.safe_dict(), ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
