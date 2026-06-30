"""Run the approved five-call live snapshot local DB file smoke."""

from __future__ import annotations

import json
from pathlib import Path

import httpx
from pydantic import ValidationError

from ai_stock.config import load_settings
from ai_stock.models import OAuthTokenRequest
from ai_stock.risk import LiveApiSafetyGate
from ai_stock.storage.live_snapshot_local_db_preflight import (
    PLANNED_DB_RELATIVE_PATH,
)
from ai_stock.storage.live_snapshot_local_db_smoke import (
    execute_live_snapshot_local_db_file_smoke,
)


def main() -> int:
    path = Path(PLANNED_DB_RELATIVE_PATH)
    if not path.is_file():
        print("[FAIL] Existing local SQLite file is required.")
        return 2
    try:
        settings = load_settings()
    except ValidationError:
        print("[FAIL] Live snapshot file DB configuration is invalid.")
        return 2
    if (
        not settings.allow_live_api
        or settings.allow_real_order
        or not settings.dry_run_only
        or settings.toss_client_id is None
        or settings.toss_client_secret is None
    ):
        print("[FAIL] Live snapshot file DB configuration is unsafe.")
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
    ) as client:
        result = execute_live_snapshot_local_db_file_smoke(
            client,
            request,
            LiveApiSafetyGate(),
            path,
            allow_live_api=settings.allow_live_api,
            allow_real_order=settings.allow_real_order,
            dry_run_only=settings.dry_run_only,
            live_file_smoke_allowed=True,
        )
    label = "PASS" if result.success else "FAIL"
    print(f"[{label}] Live snapshot local DB file smoke.")
    print(json.dumps(result.safe_dict(), ensure_ascii=True, sort_keys=True))
    return 0 if result.success else 1


if __name__ == "__main__":
    raise SystemExit(main())
