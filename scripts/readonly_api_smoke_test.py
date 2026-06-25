"""Run the approved OAuth plus exchange-rate live smoke test only."""

from __future__ import annotations

import json

import httpx
from pydantic import ValidationError

from ai_stock.clients import (
    EXCHANGE_RATE_PATH,
)
from ai_stock.clients.readonly_smoke import (
    ReadOnlySmokeDiagnosticResult,
    ReadOnlySmokePhase,
    execute_readonly_exchange_rate_smoke,
)
from ai_stock.config import load_settings
from ai_stock.models import OAuthTokenRequest
from ai_stock.risk import LiveApiSafetyGate


def main() -> int:
    """Run two fixed requests and print only non-sensitive response metadata."""

    try:
        settings = load_settings()
    except ValidationError:
        _print_result(
            _config_failure(
                "invalid_configuration",
                "Local safety settings are invalid.",
            )
        )
        return 2

    if (
        not settings.allow_live_api
        or settings.allow_real_order
        or not settings.dry_run_only
    ):
        _print_result(
            _config_failure(
                "unsafe_configuration",
                "Read-only smoke safety flags are not satisfied.",
            )
        )
        return 2
    if settings.toss_client_id is None or settings.toss_client_secret is None:
        _print_result(
            _config_failure(
                "missing_credentials",
                "OAuth client credentials are missing.",
            )
        )
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
        result = execute_readonly_exchange_rate_smoke(
            http_client,
            request,
            LiveApiSafetyGate(),
            allow_live_api=settings.allow_live_api,
            allow_real_order=settings.allow_real_order,
            dry_run_only=settings.dry_run_only,
            read_only_live_smoke_allowed=True,
        )
    _print_result(result)
    return 0 if result.success else 1


def _config_failure(
    safe_error_type: str,
    safe_error_message: str,
) -> ReadOnlySmokeDiagnosticResult:
    return ReadOnlySmokeDiagnosticResult(
        phase=ReadOnlySmokePhase.CONFIG_VALIDATION,
        success=False,
        http_status_code=None,
        safe_error_code=None,
        safe_error_type=safe_error_type,
        safe_error_message=safe_error_message,
        endpoint=EXCHANGE_RATE_PATH,
        method="GET",
    )


def _print_result(result: ReadOnlySmokeDiagnosticResult) -> None:
    label = "PASS" if result.success else "FAIL"
    print(f"[{label}] Read-only API smoke test diagnostic.")
    print(json.dumps(result.safe_dict(), ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
