"""Tests for the MS-14.02 Toss API credential/config guardrail."""

from dataclasses import fields, is_dataclass
import ast
from pathlib import Path
import re
import unittest

from ai_stock.clients import (
    TossApiConfigFieldPolicy,
    TossApiConfigGuardrailPolicy,
    TossApiConfigGuardrailPreflightResult,
    TossApiConfigRedactionResult,
    TossApiConfigSourcePolicy,
    TossApiConfigValidationResult,
    TossApiCredentialReadinessDecision,
    build_toss_api_config_field_policies,
    build_toss_api_config_guardrail_policy,
    build_toss_api_config_source_policy,
    build_toss_api_credential_readiness_decision,
    build_toss_api_external_capability_flags,
    redact_toss_api_config_mapping,
    run_toss_api_config_guardrail_preflight_checks,
    validate_toss_api_config_field_policies,
    validate_toss_api_config_guardrail_policy,
    validate_toss_api_config_mapping,
    validate_toss_api_config_source_policy,
    validate_toss_api_credential_readiness_decision,
)


MODULE_PATH = Path("src/ai_stock/clients/toss_api_config_guardrail.py")
FORBIDDEN_SAFE_OUTPUT_TEXT = (
    "access_token",
    "refresh_token",
    "authorization",
    "bearer",
    "api_key",
    "secret_key",
    "client_secret",
    "app_key",
    "app_secret",
    "token",
    "accountSeq",
    "account_seq",
    "account_number",
    "account_balance",
    "holdings",
    "fills",
    "order_id",
    "raw_response",
    "raw_request",
    "db_row",
    "file_path",
    "env_path",
    ".env.local",
    ".env",
    "buy",
    "sell",
    "hold",
    "strong_buy",
    "recommendation",
    "action",
    "rank",
    "ranking",
    "ranking_position",
    "priority",
    "order",
    "target_price",
    "expected_return",
    "profit_probability",
    "must_buy",
    "must_sell",
)


class TossApiConfigGuardrailTests(unittest.TestCase):
    def test_config_guardrail_dataclasses_are_frozen_shapes(self) -> None:
        for model in (
            TossApiConfigGuardrailPolicy,
            TossApiConfigSourcePolicy,
            TossApiConfigFieldPolicy,
            TossApiConfigRedactionResult,
            TossApiConfigValidationResult,
            TossApiCredentialReadinessDecision,
            TossApiConfigGuardrailPreflightResult,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(is_dataclass(model))
                self.assertTrue(model.__dataclass_params__.frozen)

    def test_policy_reuses_contract_and_credential_name_policy(self) -> None:
        policy = build_toss_api_config_guardrail_policy()

        self.assertEqual(policy.guardrail_version, "MS-14.02")
        self.assertEqual(policy.contract_policy.contract_version, "MS-14.00")
        self.assertTrue(policy.uses_contract_policy)
        self.assertFalse(policy.credential_name_policy.required_now)
        self.assertTrue(policy.credential_name_policy.mask_required)
        for flag in (
            "no_network",
            "no_oauth",
            "no_credentials_now",
            "no_env_read",
            "no_file_read",
            "no_file_write",
            "no_account_seq",
            "no_orders",
            "no_account_assets",
            "no_balance",
            "no_fills",
            "no_db",
            "no_streamlit",
            "no_llm",
            "no_recommendation",
            "no_ranking",
            "credential_names_defined",
            "redaction_required",
            "mask_required",
            "fail_closed_on_sensitive_output",
        ):
            self.assertTrue(getattr(policy, flag), flag)
        for flag in (
            "credential_required_now",
            "credential_values_allowed",
            "env_read_allowed",
            "file_read_allowed",
            "live_http_ready",
            "oauth_ready",
            "account_seq_required_now",
            "order_required_now",
            "streamlit_required",
            "http_smoke_required",
            "raw_payload_allowed",
        ):
            self.assertFalse(getattr(policy, flag), flag)

    def test_external_capability_flags_remain_false(self) -> None:
        flags = build_toss_api_external_capability_flags()

        self.assertTrue(fields(type(flags)))
        self.assertFalse(any(flags.__dict__.values()))

    def test_credential_readiness_decision_blocks_secret_requests_now(self) -> None:
        decision = build_toss_api_credential_readiness_decision()

        self.assertFalse(decision.credential_required_now)
        self.assertFalse(decision.toss_key_required_now)
        self.assertFalse(decision.toss_secret_required_now)
        self.assertFalse(decision.openai_key_required_now)
        self.assertFalse(decision.access_token_required_now)
        self.assertFalse(decision.account_seq_required_now)
        self.assertFalse(decision.live_http_allowed_now)
        self.assertFalse(decision.oauth_allowed_now)
        self.assertFalse(decision.safe_to_request_user_secret_now)
        result = validate_toss_api_credential_readiness_decision(decision)
        self.assertTrue(result.passed, result.failures)

    def test_config_source_policy_is_symbolic_validation_only(self) -> None:
        source_policy = build_toss_api_config_source_policy()

        self.assertIn(source_policy.source_kind, source_policy.allowed_later_sources)
        self.assertFalse(source_policy.read_now)
        self.assertFalse(source_policy.write_now)
        self.assertFalse(source_policy.required_now)
        self.assertTrue(source_policy.validation_only)
        self.assertNotIn(".env.local", repr(source_policy))
        self.assertNotIn(".env", repr(source_policy))
        result = validate_toss_api_config_source_policy(source_policy)
        self.assertTrue(result.passed, result.failures)

    def test_config_field_policies_are_symbolic_name_only(self) -> None:
        field_policies = build_toss_api_config_field_policies()
        names = {field.symbolic_field_name for field in field_policies}

        self.assertEqual(
            names,
            {
                "symbolic_toss_app_key",
                "symbolic_toss_app_secret",
                "symbolic_toss_access_token_later",
                "symbolic_toss_refresh_token_later",
                "symbolic_openai_api_key_later",
                "symbolic_account_seq_later",
            },
        )
        for field_policy in field_policies:
            with self.subTest(field=field_policy.symbolic_field_name):
                self.assertFalse(field_policy.required_now)
                self.assertFalse(field_policy.value_allowed)
                self.assertFalse(field_policy.raw_output_allowed)
                self.assertTrue(field_policy.mask_required)
                self.assertFalse(field_policy.print_allowed)
                self.assertFalse(field_policy.log_allowed)
                self.assertFalse(field_policy.persist_allowed)

        result = validate_toss_api_config_field_policies(field_policies)
        self.assertTrue(result.passed, result.failures)

    def test_dummy_sensitive_input_is_masked_without_raw_output(self) -> None:
        raw_dummy = "dummy-sensitive-value-not-a-real-secret"
        result = redact_toss_api_config_mapping(
            {
                "access_token": raw_dummy,
                "api_key": "dummy-key-value-not-real",
                "safe_symbolic_label": "validation_only",
            }
        )

        self.assertTrue(result.passed, result.failures)
        self.assertIn("[REDACTED]", result.safe_config_preview.values())
        self.assertNotIn(raw_dummy, repr(result))
        self.assertNotIn("dummy-key-value-not-real", repr(result))
        self.assert_no_forbidden_safe_output(result)

    def test_validate_config_mapping_fails_closed_on_unmasked_sensitive_output(
        self,
    ) -> None:
        result = validate_toss_api_config_mapping(
            {
                "access_token": "dummy-sensitive-value-not-real",
                "api_key": "dummy-key-value-not-real",
            }
        )

        self.assertTrue(result.passed, result.failures)
        self.assertTrue(result.checked_redaction_labels)

    def test_preflight_runner_is_deterministic_and_passes(self) -> None:
        first = run_toss_api_config_guardrail_preflight_checks()
        second = run_toss_api_config_guardrail_preflight_checks()

        self.assertEqual(first, second)
        self.assertTrue(first.passed, first.failures)
        self.assertFalse(first.capability_flags.live_http_ready)
        self.assertFalse(first.capability_flags.oauth_ready)
        self.assertFalse(first.capability_flags.credential_required_now)
        self.assertIn("symbolic_config_only", first.diagnostics)
        self.assertIn("redacted_output_only", first.diagnostics)
        self.assert_no_forbidden_safe_output(first.redaction_result)

    def test_policy_validation_passes(self) -> None:
        result = validate_toss_api_config_guardrail_policy()

        self.assertTrue(result.passed, result.failures)
        self.assertIn("credential_required_now", result.checked_policy_flags)
        self.assertIn("mask_required", result.checked_policy_flags)
        self.assertIn(
            "config_guardrail_policy_validation",
            result.diagnostics,
        )

    def test_module_has_no_disallowed_imports_or_runtime_access(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported_modules: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)

        self.assertFalse(
            {
                "requests",
                "httpx",
                "aiohttp",
                "urllib.request",
                "socket",
                "os",
                "dotenv",
                "sqlite3",
                "streamlit",
                "openai",
            }
            & imported_modules
        )
        for forbidden in (
            "os.environ",
            "os.getenv",
            "dotenv",
            ".env.local",
            "Path(",
            "open(",
            "read_text(",
            "read_bytes(",
            "write_text(",
            "write_bytes(",
            "connect(",
            ".send(",
            ".post(",
            ".request(",
            "Bearer ",
            "http://",
            "https://",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def test_no_oauth_token_or_order_account_balance_fills_implementation(
        self,
    ) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")

        for forbidden in (
            "oauth_token_endpoint",
            "authorization_header",
            "account_lookup",
            "balance_lookup",
            "fills_lookup",
            "place_order",
            "recommendation_result",
            "ranking_result",
            "buy_signal",
            "sell_signal",
            "hold_signal",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def assert_no_forbidden_safe_output(
        self,
        result: TossApiConfigRedactionResult,
    ) -> None:
        rendered_output = " ".join(
            (
                str(tuple(result.safe_config_preview.keys())),
                str(tuple(result.safe_config_preview.values())),
                str(result.diagnostics),
                str(result.redacted_field_labels),
                str(result.blocked_field_labels),
            )
        ).casefold()
        output_tokens = set(re.findall(r"[a-z0-9_.]+", rendered_output))
        for forbidden in FORBIDDEN_SAFE_OUTPUT_TEXT:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden.casefold(), output_tokens)


if __name__ == "__main__":
    unittest.main()
