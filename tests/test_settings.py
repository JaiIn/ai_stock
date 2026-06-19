"""Tests for local-only settings behavior."""

import importlib.util
import os
import unittest
from unittest.mock import patch

SETTINGS_DEPS_AVAILABLE = all(
    importlib.util.find_spec(package) is not None
    for package in ("pydantic", "pydantic_settings")
)

if SETTINGS_DEPS_AVAILABLE:
    from ai_stock.config.settings import ExecutionMode, Settings


@unittest.skipUnless(
    SETTINGS_DEPS_AVAILABLE,
    "pydantic and pydantic-settings are not installed",
)
class SettingsTests(unittest.TestCase):
    def test_mock_defaults_load_without_credentials(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None)

        self.assertEqual(settings.execution_mode, ExecutionMode.MOCK)
        self.assertEqual(settings.app_host, "127.0.0.1")
        self.assertFalse(settings.allow_live_api)
        self.assertFalse(settings.allow_real_order)
        self.assertTrue(settings.dry_run_only)
        self.assertIsNone(settings.toss_client_secret)

    def test_safe_dict_does_not_expose_sensitive_values(self) -> None:
        raw_secret = "client-secret-value"
        settings = Settings(_env_file=None, toss_client_secret=raw_secret)

        self.assertNotIn(raw_secret, repr(settings.to_safe_dict()))

    def test_real_orders_cannot_be_enabled(self) -> None:
        with self.assertRaises(ValueError):
            Settings(_env_file=None, allow_real_order=True)


if __name__ == "__main__":
    unittest.main()
