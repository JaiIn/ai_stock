"""Tests for the MS-14.01 Toss API fake transport fixtures."""

from dataclasses import fields, is_dataclass
import ast
from pathlib import Path
import re
import unittest

from ai_stock.clients import (
    TossApiFakeFixture,
    TossApiFakeRequest,
    TossApiFakeResponse,
    TossApiFakeTransportPolicy,
    TossApiFakeTransportResult,
    TossApiFakeTransportValidationResult,
    build_toss_api_external_capability_flags,
    build_toss_api_fake_fixtures,
    build_toss_api_fake_request,
    build_toss_api_fake_transport_policy,
    run_toss_api_fake_transport,
    run_toss_api_fake_transport_preflight_checks,
    validate_toss_api_fake_fixture,
    validate_toss_api_fake_transport_policy,
)


MODULE_PATH = Path("src/ai_stock/clients/toss_api_fake_transport.py")
CONTRACT_PATH = Path("src/ai_stock/clients/toss_api_client_contract.py")
FORBIDDEN_RESULT_TEXT = (
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


class TossApiFakeTransportTests(unittest.TestCase):
    def test_fake_transport_dataclasses_are_frozen_shapes(self) -> None:
        for model in (
            TossApiFakeTransportPolicy,
            TossApiFakeRequest,
            TossApiFakeResponse,
            TossApiFakeTransportResult,
            TossApiFakeFixture,
            TossApiFakeTransportValidationResult,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(is_dataclass(model))
                self.assertTrue(model.__dataclass_params__.frozen)

    def test_fake_transport_policy_reuses_ms_14_contract(self) -> None:
        policy = build_toss_api_fake_transport_policy()

        self.assertEqual(policy.fake_transport_version, "MS-14.01")
        self.assertEqual(policy.contract_policy.contract_version, "MS-14.00")
        self.assertTrue(policy.uses_contract_policy)
        self.assertTrue(policy.fake_transport_ready)
        self.assertTrue(policy.redaction_required)
        for flag in (
            "no_network",
            "no_oauth",
            "no_credentials",
            "no_account_seq",
            "no_orders",
            "no_account_assets",
            "no_balance",
            "no_fills",
            "no_db",
            "no_file_io",
            "no_streamlit",
            "no_llm",
            "no_recommendation",
            "no_ranking",
        ):
            self.assertTrue(getattr(policy, flag), flag)
        for flag in (
            "live_http_ready",
            "oauth_ready",
            "credential_required_now",
            "account_seq_required_now",
            "order_required_now",
            "streamlit_required",
            "http_smoke_required",
            "raw_payload_allowed",
        ):
            self.assertFalse(getattr(policy, flag), flag)

    def test_external_capability_flags_from_contract_remain_false(self) -> None:
        flags = build_toss_api_external_capability_flags()

        self.assertTrue(fields(type(flags)))
        self.assertFalse(any(flags.__dict__.values()))

    def test_fake_request_is_symbolic_dry_run_only(self) -> None:
        fake_request = build_toss_api_fake_request()

        self.assertEqual(fake_request.endpoint_kind, "read_only_market_data_placeholder")
        self.assertEqual(fake_request.symbolic_method, "SYMBOLIC_METHOD")
        self.assertTrue(fake_request.dry_run_only)
        self.assertFalse(fake_request.live_call_allowed)
        self.assertTrue(fake_request.redaction_required)
        rendered = repr(fake_request)
        self.assertNotIn("http://", rendered)
        self.assertNotIn("https://", rendered)
        self.assertNotIn("Bearer ", rendered)
        self.assertNotIn("accountSeq", rendered)

    def test_fake_fixtures_are_complete_in_memory_matrix(self) -> None:
        fixtures = build_toss_api_fake_fixtures()

        self.assertEqual(
            tuple(fixture.fixture_name for fixture in fixtures),
            (
                "market_data_ok_placeholder",
                "market_data_empty_placeholder",
                "market_data_error_placeholder",
                "rate_limited_placeholder",
                "redaction_required_placeholder",
                "endpoint_not_allowed_placeholder",
            ),
        )
        for fixture in fixtures:
            with self.subTest(fixture=fixture.fixture_name):
                self.assertFalse(fixture.fake_response.raw_payload_allowed)
                self.assertFalse(fixture.fake_response.sensitive_output_present)
                self.assertNotIn("http://", repr(fixture.fake_response))
                self.assertNotIn("https://", repr(fixture.fake_response))
                self.assertNotIn("Bearer ", repr(fixture.fake_response))

    def test_fake_transport_runner_is_deterministic(self) -> None:
        first = run_toss_api_fake_transport("market_data_ok_placeholder")
        second = run_toss_api_fake_transport("market_data_ok_placeholder")

        self.assertEqual(first, second)
        self.assertTrue(first.passed)
        self.assertEqual(first.response_kind, "safe_market_data_preview")
        self.assertFalse(first.capability_flags.live_http_ready)
        self.assertFalse(first.capability_flags.fake_transport_ready)

    def test_runner_returns_redacted_preview_only(self) -> None:
        result = run_toss_api_fake_transport("redaction_required_placeholder")

        self.assertTrue(result.passed)
        self.assertEqual(result.redacted_body_preview["redacted_preview"], "[REDACTED]")
        self.assert_no_forbidden_result_output(result)

    def test_endpoint_not_allowed_fixture_returns_safe_failure(self) -> None:
        result = run_toss_api_fake_transport("endpoint_not_allowed_placeholder")

        self.assertFalse(result.passed)
        self.assertEqual(result.normalized_status, "safe_contract_failure")
        self.assertEqual(result.failures, ("endpoint_not_allowed",))
        self.assert_no_forbidden_result_output(result)

    def test_rate_limited_fixture_returns_safe_normalized_error(self) -> None:
        result = run_toss_api_fake_transport("rate_limited_placeholder")

        self.assertTrue(result.passed)
        self.assertEqual(result.normalized_status, "rate_limited_safe_error")
        self.assertEqual(result.response_kind, "safe_error_preview")
        self.assert_no_forbidden_result_output(result)

    def test_fixture_validation_and_preflight_checks_pass(self) -> None:
        policy_result = validate_toss_api_fake_transport_policy()
        self.assertTrue(policy_result.passed, policy_result.failures)

        for fixture in build_toss_api_fake_fixtures():
            with self.subTest(fixture=fixture.fixture_name):
                result = validate_toss_api_fake_fixture(fixture)
                self.assertTrue(result.passed, result.failures)

        preflight = run_toss_api_fake_transport_preflight_checks()
        self.assertTrue(preflight.passed, preflight.failures)
        self.assertIn(
            "symbolic_endpoint_contract_reused",
            preflight.diagnostics,
        )
        self.assertIn("redacted_preview_only", preflight.diagnostics)

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

    def test_contract_file_is_reused_without_modifying_contract_source(self) -> None:
        source = CONTRACT_PATH.read_text(encoding="utf-8")

        self.assertIn("TOSS_API_CLIENT_CONTRACT_VERSION = \"MS-14.00\"", source)
        self.assertIn("def run_toss_api_client_contract_preflight_checks", source)

    def assert_no_forbidden_result_output(
        self,
        result: TossApiFakeTransportResult,
    ) -> None:
        rendered_output = " ".join(
            (
                str(tuple(result.redacted_body_preview.values())),
                str(result.diagnostics),
            )
        ).casefold()
        output_tokens = set(re.findall(r"[a-z0-9_.]+", rendered_output))
        for forbidden in FORBIDDEN_RESULT_TEXT:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden.casefold(), output_tokens)


if __name__ == "__main__":
    unittest.main()
