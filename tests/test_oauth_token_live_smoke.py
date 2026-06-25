"""Offline contract tests for the approved OAuth token provider."""

import json
import unittest
from urllib.parse import parse_qs

import httpx

from ai_stock.clients import (
    OAUTH_TOKEN_PATH,
    TossAuthenticationError,
    TossClientConfigError,
    TossOAuthTokenProvider,
)
from ai_stock.models import OAuthTokenRequest


class TossOAuthTokenProviderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client_id = "synthetic-client-id-value"
        self.client_secret = "synthetic-client-secret-value"
        self.raw_token = "synthetic-live-access-token-value"
        self.seen_requests: list[httpx.Request] = []

    def make_provider(
        self,
        handler,
        *,
        allow_live_api: bool = True,
        allow_real_order: bool = False,
        dry_run_only: bool = True,
    ) -> tuple[TossOAuthTokenProvider, httpx.Client]:
        client = httpx.Client(
            base_url="https://mock.invalid",
            transport=httpx.MockTransport(handler),
        )
        self.addCleanup(client.close)
        return (
            TossOAuthTokenProvider(
                client,
                allow_live_api=allow_live_api,
                allow_real_order=allow_real_order,
                dry_run_only=dry_run_only,
            ),
            client,
        )

    def request(self) -> OAuthTokenRequest:
        return OAuthTokenRequest(
            client_id=self.client_id,
            client_secret=self.client_secret,
        )

    def test_form_request_and_response_parsing_use_only_oauth_endpoint(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            self.seen_requests.append(request)
            form = parse_qs(request.content.decode("utf-8"))
            self.assertEqual(request.method, "POST")
            self.assertEqual(request.url.path, OAUTH_TOKEN_PATH)
            self.assertEqual(
                request.headers["Content-Type"],
                "application/x-www-form-urlencoded",
            )
            self.assertEqual(form["grant_type"], ["client_credentials"])
            self.assertEqual(form["client_id"], [self.client_id])
            self.assertEqual(form["client_secret"], [self.client_secret])
            return httpx.Response(
                200,
                json={
                    "access_token": self.raw_token,
                    "token_type": "Bearer",
                    "expires_in": 3600,
                },
                request=request,
            )

        provider, _ = self.make_provider(handler)
        token = provider.acquire_token(self.request())

        self.assertEqual(len(self.seen_requests), 1)
        self.assertEqual(token.token_type, "Bearer")
        self.assertEqual(token.expires_in, 3600)
        self.assertNotIn(self.raw_token, repr(token))
        self.assertNotIn(self.raw_token, json.dumps(token.safe_dict()))

    def test_missing_credentials_are_rejected_before_transport(self) -> None:
        called = False

        def handler(request: httpx.Request) -> httpx.Response:
            nonlocal called
            called = True
            raise AssertionError(f"unexpected request: {request.url}")

        provider, _ = self.make_provider(handler)
        with self.assertRaises(TossClientConfigError):
            provider.acquire_token(OAuthTokenRequest())

        self.assertFalse(called)

    def test_allow_live_api_false_blocks_before_transport(self) -> None:
        provider, _ = self.make_provider(
            lambda request: self.fail_transport(request),
            allow_live_api=False,
        )

        with self.assertRaises(TossClientConfigError):
            provider.acquire_token(self.request())

    def test_allow_real_order_true_blocks_before_transport(self) -> None:
        provider, _ = self.make_provider(
            lambda request: self.fail_transport(request),
            allow_real_order=True,
        )

        with self.assertRaises(TossClientConfigError):
            provider.acquire_token(self.request())

    def test_dry_run_only_false_blocks_before_transport(self) -> None:
        provider, _ = self.make_provider(
            lambda request: self.fail_transport(request),
            dry_run_only=False,
        )

        with self.assertRaises(TossClientConfigError):
            provider.acquire_token(self.request())

    def test_http_failure_does_not_expose_credentials_or_response_body(self) -> None:
        response_secret = "synthetic-response-secret-value"

        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                401,
                json={"error": response_secret},
                request=request,
            )

        provider, _ = self.make_provider(handler)
        with self.assertRaises(TossAuthenticationError) as raised:
            provider.acquire_token(self.request())

        message = str(raised.exception)
        self.assertNotIn(self.client_id, message)
        self.assertNotIn(self.client_secret, message)
        self.assertNotIn(response_secret, message)

    def test_invalid_response_never_exposes_raw_token(self) -> None:
        def handler(request: httpx.Request) -> httpx.Response:
            return httpx.Response(
                200,
                json={
                    "access_token": self.raw_token,
                    "token_type": "Bearer",
                    "expires_in": 0,
                },
                request=request,
            )

        provider, _ = self.make_provider(handler)
        with self.assertRaises(TossAuthenticationError) as raised:
            provider.acquire_token(self.request())

        self.assertNotIn(self.raw_token, str(raised.exception))

    def fail_transport(self, request: httpx.Request) -> httpx.Response:
        raise AssertionError(f"transport must not run: {request.url.path}")


if __name__ == "__main__":
    unittest.main()
