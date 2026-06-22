"""Offline tests for the Toss API client foundation."""

import unittest

import httpx

from ai_stock.clients import (
    TossApiError,
    TossAuthenticationError,
    TossClientConfig,
    TossClientConfigError,
    TossClientFoundation,
    TossPermissionError,
    TossRateLimitError,
    TossServerError,
    extract_toss_result,
    raise_for_toss_status,
)


def _response(
    status_code: int,
    *,
    payload: object,
    headers: dict[str, str] | None = None,
) -> httpx.Response:
    return httpx.Response(
        status_code,
        json=payload,
        headers=headers,
        request=httpx.Request("GET", "https://mock.invalid/test"),
    )


class TossClientFoundationTests(unittest.TestCase):
    def test_defaults_require_no_credentials_and_block_live_calls(self) -> None:
        config = TossClientConfig(base_url="https://mock.invalid")
        foundation = TossClientFoundation(config)
        self.addCleanup(foundation.close)

        with self.assertRaises(TossClientConfigError):
            foundation.ensure_live_api_allowed()

    def test_request_building_does_not_send_network_traffic(self) -> None:
        transport_called = False

        def fail_if_called(request: httpx.Request) -> httpx.Response:
            nonlocal transport_called
            transport_called = True
            raise AssertionError(f"unexpected network send: {request.url}")

        client = httpx.Client(transport=httpx.MockTransport(fail_if_called))
        self.addCleanup(client.close)
        foundation = TossClientFoundation(
            TossClientConfig(
                base_url="https://mock.invalid",
                timeout_seconds=3.0,
                default_headers={"X-Client-Version": "test"},
            ),
            http_client=client,
        )

        request = foundation.build_request(
            "GET",
            "/api/v1/prices",
            params={"symbols": "005930"},
            access_token="synthetic-access-token",
            account_seq="synthetic-account-seq",
        )

        self.assertEqual(request.method, "GET")
        self.assertEqual(request.headers["X-Client-Version"], "test")
        self.assertFalse(transport_called)

    def test_safe_request_context_masks_sensitive_headers(self) -> None:
        foundation = TossClientFoundation(TossClientConfig(base_url="https://mock.invalid"))
        self.addCleanup(foundation.close)
        token = "synthetic-access-token"
        account_seq = "synthetic-account-seq"
        request = foundation.build_request(
            "GET",
            "/api/v1/holdings",
            access_token=token,
            account_seq=account_seq,
        )

        safe_context = foundation.safe_request_context(request)

        self.assertNotIn(token, repr(safe_context))
        self.assertNotIn(account_seq, repr(safe_context))

    def test_invalid_timeout_is_rejected(self) -> None:
        with self.assertRaises(TossClientConfigError):
            TossClientConfig(timeout_seconds=0)


class TossResponseTests(unittest.TestCase):
    def test_success_result_is_extracted(self) -> None:
        response = _response(200, payload={"result": {"price": "1000"}})

        self.assertEqual(extract_toss_result(response), {"price": "1000"})

    def test_status_codes_map_to_expected_exceptions(self) -> None:
        cases = {
            400: TossApiError,
            401: TossAuthenticationError,
            403: TossPermissionError,
            429: TossRateLimitError,
            500: TossServerError,
        }
        for status_code, expected_exception in cases.items():
            with self.subTest(status_code=status_code):
                response = _response(
                    status_code,
                    payload={
                        "error": {
                            "requestId": "request-123",
                            "code": "synthetic-error",
                            "message": "synthetic message",
                        }
                    },
                    headers={"Retry-After": "2"},
                )
                with self.assertRaises(expected_exception):
                    raise_for_toss_status(response)

    def test_rate_limit_retains_only_safe_retry_metadata(self) -> None:
        response = _response(
            429,
            payload={"error": {"code": "rate-limited"}},
            headers={"Retry-After": "3", "Authorization": "Bearer synthetic-token"},
        )

        with self.assertRaises(TossRateLimitError) as raised:
            raise_for_toss_status(response)

        self.assertEqual(raised.exception.retry_after, "3")
        self.assertNotIn("synthetic-token", str(raised.exception))

    def test_remote_error_message_is_not_copied_to_exception(self) -> None:
        sensitive_text = "synthetic-access-token"
        response = _response(
            401,
            payload={
                "error": {
                    "requestId": "request-123",
                    "code": "unauthorized",
                    "message": sensitive_text,
                }
            },
        )

        with self.assertRaises(TossAuthenticationError) as raised:
            raise_for_toss_status(response)

        self.assertNotIn(sensitive_text, str(raised.exception))


if __name__ == "__main__":
    unittest.main()
