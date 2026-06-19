"""Tests for secret masking helpers."""

import unittest

from ai_stock.utils.masking import mask_secret, sanitize_mapping


class MaskSecretTests(unittest.TestCase):
    def test_empty_values_remain_empty(self) -> None:
        self.assertEqual(mask_secret(None), "")
        self.assertEqual(mask_secret(""), "")

    def test_short_values_are_fully_masked(self) -> None:
        self.assertEqual(mask_secret("short"), "*****")

    def test_long_values_keep_only_edges(self) -> None:
        self.assertEqual(mask_secret("abcdefghij", keep=2), "ab...ij")

    def test_sensitive_mapping_values_are_masked_recursively(self) -> None:
        raw_secret = "client-secret-value"
        sanitized = sanitize_mapping(
            {
                "APP_ENV": "local",
                "nested": {
                    "TOSS_CLIENT_SECRET": raw_secret,
                    "Authorization": "bearer-token-value",
                },
            }
        )

        self.assertEqual(sanitized["APP_ENV"], "local")
        self.assertNotIn(raw_secret, repr(sanitized))
        self.assertNotIn("bearer-token-value", repr(sanitized))


if __name__ == "__main__":
    unittest.main()
