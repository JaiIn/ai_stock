"""Offline tests for authenticated Toss request contexts."""

import unittest

import httpx

from ai_stock.clients import (
    ACCOUNT_HEADER,
    AUTHORIZATION_HEADER,
    AuthenticatedRequestContextFactory,
    MockTokenProvider,
    TossClientConfig,
    TossClientConfigError,
    TossClientFoundation,
)


class AuthenticatedRequestContextTests(unittest.TestCase):
    def setUp(self) -> None:
        self.token = "mock-token-for-request-context"
        self.account_seq = "fake-account-seq"
        self.factory = AuthenticatedRequestContextFactory(
            MockTokenProvider(access_token=self.token)
        )

    def test_non_account_context_requires_no_account_identifier(self) -> None:
        context = self.factory.create()

        self.assertFalse(context.has_account)
        self.assertEqual(
            context.request_headers()[AUTHORIZATION_HEADER],
            f"Bearer {self.token}",
        )
        self.assertNotIn(ACCOUNT_HEADER, context.request_headers())

    def test_account_header_uses_documented_name(self) -> None:
        context = self.factory.create(account_seq=self.account_seq)

        headers = context.request_headers(require_account=True)

        self.assertEqual(headers[ACCOUNT_HEADER], self.account_seq)
        self.assertEqual(headers[AUTHORIZATION_HEADER], f"Bearer {self.token}")

    def test_missing_required_account_raises_safe_config_error(self) -> None:
        context = self.factory.create()

        with self.assertRaises(TossClientConfigError) as raised:
            context.request_headers(require_account=True)

        self.assertNotIn(self.token, str(raised.exception))
        self.assertNotIn(self.account_seq, str(raised.exception))

    def test_repr_and_safe_dict_hide_token_and_account(self) -> None:
        context = self.factory.create(account_seq=self.account_seq)

        safe_output = repr(context.safe_dict())

        self.assertNotIn(self.token, repr(context))
        self.assertNotIn(self.account_seq, repr(context))
        self.assertNotIn(self.token, safe_output)
        self.assertNotIn(self.account_seq, safe_output)
        self.assertTrue(context.safe_dict()["account_header_present"])

    def test_foundation_builds_request_without_network_send(self) -> None:
        network_called = False

        def fail_if_called(request: httpx.Request) -> httpx.Response:
            nonlocal network_called
            network_called = True
            raise AssertionError(f"unexpected network send: {request.url}")

        http_client = httpx.Client(transport=httpx.MockTransport(fail_if_called))
        self.addCleanup(http_client.close)
        foundation = TossClientFoundation(
            TossClientConfig(base_url="https://mock.invalid"),
            http_client=http_client,
        )
        context = self.factory.create(account_seq=self.account_seq)

        request = foundation.build_authenticated_request(
            context,
            "GET",
            "/api/v1/holdings",
            require_account=True,
        )

        self.assertEqual(request.headers[AUTHORIZATION_HEADER], f"Bearer {self.token}")
        self.assertEqual(request.headers[ACCOUNT_HEADER], self.account_seq)
        self.assertFalse(network_called)

    def test_safe_request_context_excludes_body_and_raw_credentials(self) -> None:
        foundation = TossClientFoundation(
            TossClientConfig(base_url="https://mock.invalid")
        )
        self.addCleanup(foundation.close)
        context = self.factory.create(account_seq=self.account_seq)
        request = foundation.build_authenticated_request(
            context,
            "POST",
            "/mock-only",
            json={"private": "mock-request-body"},
        )

        safe_output = foundation.safe_request_context(request)

        self.assertNotIn("mock-request-body", repr(safe_output))
        self.assertNotIn(self.token, repr(safe_output))
        self.assertNotIn(self.account_seq, repr(safe_output))


if __name__ == "__main__":
    unittest.main()
