"""Offline tests for the Toss OAuth mock flow."""

import unittest
from datetime import datetime, timedelta, timezone

from ai_stock.clients import (
    InMemoryTokenStore,
    LiveTokenProvider,
    MockTokenProvider,
    TossAuthenticationError,
    TossClientConfig,
    TossClientConfigError,
)
from ai_stock.models import OAuthTokenRequest, OAuthTokenResponse


class OAuthModelTests(unittest.TestCase):
    def test_request_safe_output_masks_optional_credentials(self) -> None:
        client_id = "mock-client-id-value"
        client_secret = "mock-client-secret-value"
        request = OAuthTokenRequest(client_id=client_id, client_secret=client_secret)

        self.assertNotIn(client_id, repr(request))
        self.assertNotIn(client_secret, repr(request))
        self.assertNotIn(client_id, repr(request.safe_dict()))
        self.assertNotIn(client_secret, repr(request.safe_dict()))

    def test_token_representation_and_safe_output_hide_raw_token(self) -> None:
        raw_token = "mock-access-token-value"
        token = OAuthTokenResponse(access_token=raw_token)

        self.assertNotIn(raw_token, repr(token))
        self.assertNotIn(raw_token, repr(token.safe_dict()))
        self.assertNotIn(raw_token, repr(token.safe_authorization_header()))
        self.assertEqual(
            token.authorization_header(),
            {"Authorization": f"Bearer {raw_token}"},
        )

    def test_expiry_is_expressed_and_checked(self) -> None:
        issued_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
        token = OAuthTokenResponse(
            access_token="mock-token-placeholder",
            expires_in=60,
            issued_at=issued_at,
        )

        self.assertEqual(token.expires_at, issued_at + timedelta(seconds=60))
        self.assertFalse(token.is_expired(at=issued_at + timedelta(seconds=59)))
        self.assertTrue(token.is_expired(at=issued_at + timedelta(seconds=60)))


class TokenProviderTests(unittest.TestCase):
    def test_mock_provider_requires_no_credentials_and_stores_token(self) -> None:
        store = InMemoryTokenStore()
        provider = MockTokenProvider(token_store=store)

        token = provider.acquire_token()

        self.assertIs(store.get(), token)
        self.assertIs(store.get_valid(), token)

    def test_store_does_not_return_expired_token_as_valid(self) -> None:
        store = InMemoryTokenStore()
        store.save(
            OAuthTokenResponse(
                access_token="mock-token-placeholder",
                expires_in=1,
                issued_at=datetime.now(timezone.utc) - timedelta(seconds=2),
            )
        )

        self.assertIsNone(store.get_valid())

    def test_live_provider_is_blocked_when_live_api_is_disabled(self) -> None:
        provider = LiveTokenProvider(TossClientConfig(base_url="https://mock.invalid"))
        request = OAuthTokenRequest(
            client_id="mock-client-id-value",
            client_secret="mock-client-secret-value",
        )

        with self.assertRaises(TossClientConfigError) as raised:
            provider.acquire_token(request)

        self.assertNotIn("mock-client-id-value", str(raised.exception))
        self.assertNotIn("mock-client-secret-value", str(raised.exception))

    def test_live_provider_has_no_token_http_implementation(self) -> None:
        provider = LiveTokenProvider(
            TossClientConfig(
                base_url="https://mock.invalid",
                allow_live_api=True,
            )
        )

        with self.assertRaises(TossAuthenticationError):
            provider.acquire_token()


if __name__ == "__main__":
    unittest.main()
