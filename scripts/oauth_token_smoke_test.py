"""Run the explicitly approved OAuth token endpoint smoke test only."""

from __future__ import annotations

import json

import httpx
from pydantic import ValidationError

from ai_stock.clients import TossClientConfigError, TossOAuthTokenProvider
from ai_stock.config import load_settings
from ai_stock.models import OAuthTokenRequest


def main() -> int:
    """Issue one token in memory and print only masked metadata."""

    try:
        settings = load_settings()
    except ValidationError:
        print("[BLOCKED] Local safety settings are invalid.")
        return 2

    if (
        not settings.allow_live_api
        or settings.allow_real_order
        or not settings.dry_run_only
    ):
        print("[BLOCKED] OAuth smoke test safety flags are not satisfied.")
        return 2

    if settings.toss_client_id is None or settings.toss_client_secret is None:
        print("[BLOCKED] OAuth client credentials are missing from .env.local.")
        return 2

    request = OAuthTokenRequest(
        client_id=settings.toss_client_id.get_secret_value(),
        client_secret=settings.toss_client_secret.get_secret_value(),
    )
    try:
        with httpx.Client(
            base_url="https://openapi.tossinvest.com",
            timeout=10.0,
            follow_redirects=False,
        ) as http_client:
            token = TossOAuthTokenProvider(
                http_client,
                allow_live_api=settings.allow_live_api,
                allow_real_order=settings.allow_real_order,
                dry_run_only=settings.dry_run_only,
            ).acquire_token(request)
    except (TossClientConfigError, httpx.HTTPError, RuntimeError):
        print("[FAIL] OAuth token smoke test failed without sensitive output.")
        return 1

    print("[PASS] OAuth token endpoint smoke test succeeded.")
    print(json.dumps(token.safe_dict(), ensure_ascii=True, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
