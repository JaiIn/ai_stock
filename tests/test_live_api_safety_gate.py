"""Unit tests for the metadata-only live API safety gate."""

import socket
import unittest
from unittest.mock import patch

from ai_stock.config import Settings
from ai_stock.risk import (
    LiveApiRiskLevel,
    LiveApiSafetyError,
    LiveApiSafetyGate,
    TossEndpointMetadata,
)


def _endpoint(
    method: str,
    path: str,
    *,
    category: str = "market-data",
    requires_account_seq: bool = False,
) -> TossEndpointMetadata:
    return TossEndpointMetadata(
        method=method,
        path=path,
        endpoint_category=category,
        requires_auth=True,
        requires_account_seq=requires_account_seq,
    )


class LiveApiSafetyGateTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gate = LiveApiSafetyGate()

    def evaluate_safe(
        self,
        metadata: TossEndpointMetadata,
        *,
        live_api_enabled: bool = True,
        real_order_allowed: bool = False,
        dry_run_only: bool = True,
        send_requested: bool = False,
    ):
        return self.gate.evaluate(
            metadata,
            live_api_enabled=live_api_enabled,
            real_order_allowed=real_order_allowed,
            dry_run_only=dry_run_only,
            send_requested=send_requested,
        )

    def test_documented_read_only_allowlist_supports_dry_run_evaluation(self) -> None:
        endpoints = [
            _endpoint("GET", "/api/v1/stocks", category="stock-info"),
            _endpoint(
                "GET",
                "/api/v1/stocks/005930/warnings",
                category="stock-info",
            ),
            _endpoint("GET", "/api/v1/prices"),
            _endpoint("GET", "/api/v1/candles"),
            _endpoint("GET", "/api/v1/exchange-rate", category="market-info"),
        ]

        for metadata in endpoints:
            with self.subTest(path=metadata.path):
                decision = self.evaluate_safe(metadata)
                self.assertTrue(decision.allowed)
                self.assertTrue(decision.is_read_only)
                self.assertTrue(decision.dry_run_only)
                self.assertEqual(decision.risk_level, LiveApiRiskLevel.LOW)

    def test_stock_info_metadata_is_read_only_and_account_free(self) -> None:
        endpoints = (
            "/api/v1/stocks",
            "/api/v1/stocks/005930/warnings",
        )

        for path in endpoints:
            with self.subTest(path=path):
                decision = self.evaluate_safe(
                    _endpoint("GET", path, category="stock-info")
                )
                self.assertTrue(decision.allowed)
                self.assertTrue(decision.is_read_only)
                self.assertTrue(decision.requires_auth)
                self.assertFalse(decision.requires_account_seq)

    def test_stock_info_with_account_scope_is_blocked(self) -> None:
        decision = self.evaluate_safe(
            _endpoint(
                "GET",
                "/api/v1/stocks",
                category="stock-info",
                requires_account_seq=True,
            )
        )

        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_account_seq)

    def test_prices_metadata_is_read_only_and_account_free(self) -> None:
        decision = self.evaluate_safe(
            _endpoint("GET", "/api/v1/prices", category="market-data")
        )

        self.assertTrue(decision.allowed)
        self.assertTrue(decision.is_read_only)
        self.assertTrue(decision.requires_auth)
        self.assertFalse(decision.requires_account_seq)

    def test_prices_with_account_scope_is_blocked(self) -> None:
        decision = self.evaluate_safe(
            _endpoint(
                "GET",
                "/api/v1/prices",
                category="market-data",
                requires_account_seq=True,
            )
        )

        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_account_seq)

    def test_candles_metadata_is_read_only_and_account_free(self) -> None:
        decision = self.evaluate_safe(
            _endpoint("GET", "/api/v1/candles", category="market-data")
        )

        self.assertTrue(decision.allowed)
        self.assertTrue(decision.is_read_only)
        self.assertTrue(decision.requires_auth)
        self.assertFalse(decision.requires_account_seq)

    def test_candles_with_account_scope_is_blocked(self) -> None:
        decision = self.evaluate_safe(
            _endpoint(
                "GET",
                "/api/v1/candles",
                category="market-data",
                requires_account_seq=True,
            )
        )

        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_account_seq)

    def test_allow_live_api_false_blocks_candidate(self) -> None:
        decision = self.evaluate_safe(
            _endpoint("GET", "/api/v1/prices"),
            live_api_enabled=False,
        )

        self.assertFalse(decision.allowed)
        self.assertIn("ALLOW_LIVE_API=false", decision.reason)

    def test_dry_run_only_blocks_send_candidate(self) -> None:
        decision = self.evaluate_safe(
            _endpoint("GET", "/api/v1/prices"),
            send_requested=True,
        )

        self.assertFalse(decision.allowed)
        self.assertIn("DRY_RUN_ONLY=true", decision.reason)

    def test_order_mutation_endpoints_are_always_blocked(self) -> None:
        paths = [
            "/api/v1/orders",
            "/api/v1/orders/order-123/modify",
            "/api/v1/orders/order-123/cancel",
        ]

        for path in paths:
            with self.subTest(path=path):
                decision = self.evaluate_safe(
                    _endpoint("POST", path, category="order"),
                    dry_run_only=False,
                )
                self.assertFalse(decision.allowed)
                self.assertEqual(decision.risk_level, LiveApiRiskLevel.CRITICAL)

    def test_write_category_and_mutating_method_are_blocked(self) -> None:
        cases = [
            _endpoint("GET", "/api/v1/prices", category="write"),
            _endpoint("PATCH", "/api/v1/profile", category="account"),
        ]

        for metadata in cases:
            with self.subTest(method=metadata.method, category=metadata.endpoint_category):
                self.assertFalse(self.evaluate_safe(metadata).allowed)

    def test_account_scoped_read_only_endpoint_is_blocked(self) -> None:
        decision = self.evaluate_safe(
            _endpoint(
                "GET",
                "/api/v1/holdings",
                category="asset",
                requires_account_seq=True,
            )
        )

        self.assertFalse(decision.allowed)
        self.assertTrue(decision.requires_account_seq)
        self.assertEqual(decision.risk_level, LiveApiRiskLevel.HIGH)

    def test_allow_real_order_true_is_critical_and_blocked(self) -> None:
        decision = self.evaluate_safe(
            _endpoint("GET", "/api/v1/prices"),
            real_order_allowed=True,
        )

        self.assertFalse(decision.allowed)
        self.assertEqual(decision.risk_level, LiveApiRiskLevel.CRITICAL)
        self.assertIn("ALLOW_REAL_ORDER=true", decision.reason)

    def test_unknown_and_pending_endpoints_fail_closed(self) -> None:
        for path in ("/api/v1/unknown", "/api/v1/orderbook"):
            with self.subTest(path=path):
                decision = self.evaluate_safe(_endpoint("GET", path))
                self.assertFalse(decision.allowed)
                self.assertIn("blocked by default", decision.reason)

    def test_settings_adapter_uses_existing_safe_flags(self) -> None:
        settings = Settings(
            _env_file=None,
            allow_live_api=True,
            allow_real_order=False,
            dry_run_only=True,
        )

        decision = self.gate.evaluate_settings(
            _endpoint("GET", "/api/v1/exchange-rate", category="market-info"),
            settings,
        )

        self.assertTrue(decision.allowed)
        self.assertTrue(decision.dry_run_only)

    def test_check_or_raise_uses_safe_reason_only(self) -> None:
        with self.assertRaises(LiveApiSafetyError) as raised:
            self.gate.check_or_raise(
                _endpoint("POST", "/api/v1/orders", category="order"),
                live_api_enabled=True,
                real_order_allowed=False,
                dry_run_only=True,
            )

        self.assertNotIn("token", str(raised.exception).lower())
        self.assertNotIn("accountseq", str(raised.exception).lower())

    def test_evaluation_does_not_open_network_socket(self) -> None:
        with patch.object(
            socket,
            "socket",
            side_effect=AssertionError("network socket creation is forbidden"),
        ):
            decision = self.evaluate_safe(_endpoint("GET", "/api/v1/candles"))

        self.assertTrue(decision.allowed)


if __name__ == "__main__":
    unittest.main()
