"""Run the approved OAuth plus single-symbol Stock Warnings live smoke."""

from __future__ import annotations

import json

import httpx
from pydantic import ValidationError

from ai_stock.clients.stock_warnings_smoke import (
    DEFAULT_WARNING_SYMBOL,
    StockWarningsSmokeDiagnosticResult,
    StockWarningsSmokePhase,
    execute_stock_warnings_single_symbol_smoke,
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
        result = execute_stock_warnings_single_symbol_smoke(
            http_client,
            request,
            LiveApiSafetyGate(),
            allow_live_api=settings.allow_live_api,
            allow_real_order=settings.allow_real_order,
            dry_run_only=settings.dry_run_only,
            stock_warnings_live_smoke_allowed=True,
            symbol=DEFAULT_WARNING_SYMBOL,
        )
    _print_result(result)
    return 0 if result.success else 1


def _config_failure(safe_error_type: str) -> StockWarningsSmokeDiagnosticResult:
    path = f"/api/v1/stocks/{DEFAULT_WARNING_SYMBOL}/warnings"
    return StockWarningsSmokeDiagnosticResult(
        phase=StockWarningsSmokePhase.CONFIG_VALIDATION,
        success=False,
        http_status_code=None,
        safe_error_code=None,
        safe_error_type=safe_error_type,
        safe_error_message="Stock Warnings smoke safety settings are invalid.",
        endpoint=path,
        method="GET",
        requested_symbol=DEFAULT_WARNING_SYMBOL,
    )


def _print_result(result: StockWarningsSmokeDiagnosticResult) -> None:
    label = "PASS" if result.success else "FAIL"
    print(f"[{label}] Stock Warnings API smoke test diagnostic.")
    print(json.dumps(result.safe_dict(), ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
