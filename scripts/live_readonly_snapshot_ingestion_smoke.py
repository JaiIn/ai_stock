"""Run the approved five-call live read-only snapshot ingestion smoke."""

from __future__ import annotations

import json

import httpx
from pydantic import ValidationError

from ai_stock.config import load_settings
from ai_stock.models import OAuthTokenRequest
from ai_stock.risk import LiveApiSafetyGate
from ai_stock.services.live_readonly_snapshot_ingestion_smoke import (
    LiveReadOnlySnapshotIngestionDiagnostic,
    LiveSnapshotIngestionPhase,
    execute_live_readonly_snapshot_ingestion_smoke,
)


def main() -> int:
    """Execute the approved flow once and print only safe diagnostics."""

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
        trust_env=False,
    ) as http_client:
        result = execute_live_readonly_snapshot_ingestion_smoke(
            http_client,
            request,
            LiveApiSafetyGate(),
            allow_live_api=settings.allow_live_api,
            allow_real_order=settings.allow_real_order,
            dry_run_only=settings.dry_run_only,
            live_ingestion_smoke_allowed=True,
        )
    _print_result(result)
    return 0 if result.success else 1


def _config_failure(
    safe_error_type: str,
) -> LiveReadOnlySnapshotIngestionDiagnostic:
    return LiveReadOnlySnapshotIngestionDiagnostic(
        success=False,
        phase=LiveSnapshotIngestionPhase.CONFIG_VALIDATION,
        failed_endpoint=None,
        endpoint_http_statuses=(),
        safe_error_code=None,
        safe_error_type=safe_error_type,
        safe_error_message="Live ingestion smoke configuration is invalid.",
        oauth_token_endpoint_call_count=0,
        business_api_call_count=0,
        total_network_call_count=0,
        requested_symbol="005930",
        exchange_rate_pair="USD/KRW",
        candle_interval="1d",
        candle_count=1,
        candle_adjusted=True,
        candle_before_used=False,
        saved_stock_count=0,
        saved_price_snapshot_count=0,
        saved_candle_count=0,
        saved_exchange_rate_count=0,
        repository_round_trip_verified=False,
        decimal_values_preserved=False,
        timestamp_values_preserved=False,
        currency_fields_present=False,
        candle_ohlcv_present=False,
        stock_warnings_deferred=True,
        actual_db_file_created=False,
        account_seq_used=False,
        real_order_related_call_performed=False,
        token_raw_output_or_storage=False,
        credential_raw_output_or_storage=False,
        authorization_bearer_raw_output_or_storage=False,
        raw_response_body_stored=False,
    )


def _print_result(result: LiveReadOnlySnapshotIngestionDiagnostic) -> None:
    label = "PASS" if result.success else "FAIL"
    print(f"[{label}] Live read-only snapshot ingestion smoke.")
    print(json.dumps(result.safe_dict(), ensure_ascii=True, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
