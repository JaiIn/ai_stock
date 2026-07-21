"""Tests for the MS-14.03 Toss API live-readiness dry-run gate."""

from dataclasses import fields, is_dataclass
import ast
from pathlib import Path
import re
import unittest

from ai_stock.clients import (
    TossApiLiveReadinessChecklistItem,
    TossApiLiveReadinessGateDecision,
    TossApiLiveReadinessPolicy,
    TossApiLiveReadinessPreflightResult,
    TossApiNoSecretDryRunResult,
    build_toss_api_external_capability_flags,
    build_toss_api_live_readiness_checklist,
    build_toss_api_live_readiness_policy,
    evaluate_toss_api_live_readiness_gate,
    run_toss_api_client_contract_preflight_checks,
    run_toss_api_config_guardrail_preflight_checks,
    run_toss_api_fake_transport_preflight_checks,
    run_toss_api_live_readiness_preflight_checks,
    run_toss_api_no_secret_dry_run,
    validate_toss_api_live_readiness_checklist,
    validate_toss_api_live_readiness_policy,
    validate_toss_api_no_secret_dry_run_result,
)


MODULE_PATH = Path("src/ai_stock/clients/toss_api_live_readiness.py")
EXPECTED_CHECKLIST_CATEGORIES = (
    "contract_preflight",
    "fake_transport_preflight",
    "config_guardrail_preflight",
    "credential_request_block",
    "secret_output_block",
    "env_read_block",
    "file_io_block",
    "live_http_block",
    "oauth_block",
    "account_seq_block",
    "order_account_balance_fills_block",
    "db_block",
    "streamlit_block",
    "llm_block",
    "recommendation_ranking_action_block",
    "next_stage_gate",
)
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


class TossApiLiveReadinessTests(unittest.TestCase):
    def test_live_readiness_dataclasses_are_frozen_shapes(self) -> None:
        for model in (
            TossApiLiveReadinessPolicy,
            TossApiLiveReadinessChecklistItem,
            TossApiLiveReadinessGateDecision,
            TossApiLiveReadinessPreflightResult,
            TossApiNoSecretDryRunResult,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(is_dataclass(model))
                self.assertTrue(model.__dataclass_params__.frozen)

    def test_policy_blocks_live_work_and_secret_requests_now(self) -> None:
        policy = build_toss_api_live_readiness_policy()

        self.assertEqual(policy.readiness_version, "MS-14.03")
        for flag in (
            "uses_contract_policy",
            "uses_fake_transport",
            "uses_config_guardrail",
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
            "no_live_http_now",
            "no_secret_dry_run_only",
        ):
            self.assertTrue(getattr(policy, flag), flag)
        for flag in (
            "credential_required_now",
            "toss_key_required_now",
            "toss_secret_required_now",
            "openai_key_required_now",
            "access_token_required_now",
            "safe_to_request_user_secret_now",
            "live_http_ready",
            "oauth_ready",
            "account_seq_required_now",
            "order_required_now",
            "streamlit_required",
            "http_smoke_required",
        ):
            self.assertFalse(getattr(policy, flag), flag)

        result = validate_toss_api_live_readiness_policy(policy)
        self.assertTrue(result.passed, result.failures)

    def test_ms14_preflight_layers_are_reused_and_pass(self) -> None:
        contract_result = run_toss_api_client_contract_preflight_checks()
        fake_result = run_toss_api_fake_transport_preflight_checks()
        config_result = run_toss_api_config_guardrail_preflight_checks()
        live_result = run_toss_api_live_readiness_preflight_checks()

        self.assertTrue(contract_result.passed, contract_result.failures)
        self.assertTrue(fake_result.passed, fake_result.failures)
        self.assertTrue(config_result.passed, config_result.failures)
        self.assertTrue(live_result.passed, live_result.failures)
        self.assertEqual(live_result.contract_preflight, contract_result)
        self.assertEqual(live_result.fake_transport_preflight, fake_result)
        self.assertEqual(live_result.config_guardrail_preflight, config_result)

    def test_external_capability_flags_remain_false(self) -> None:
        flags = build_toss_api_external_capability_flags()

        self.assertTrue(fields(type(flags)))
        self.assertFalse(any(flags.__dict__.values()))

    def test_checklist_has_required_categories_and_is_deterministic(self) -> None:
        first = build_toss_api_live_readiness_checklist()
        second = build_toss_api_live_readiness_checklist()

        self.assertEqual(first, second)
        self.assertEqual(tuple(item.category for item in first), EXPECTED_CHECKLIST_CATEGORIES)
        self.assertTrue(all(item.passed for item in first))
        result = validate_toss_api_live_readiness_checklist(first)
        self.assertTrue(result.passed, result.failures)

    def test_gate_decision_is_deterministic_and_blocks_live_smoke(self) -> None:
        checklist = build_toss_api_live_readiness_checklist()
        first = evaluate_toss_api_live_readiness_gate(checklist)
        second = evaluate_toss_api_live_readiness_gate(checklist)

        self.assertEqual(first, second)
        self.assertTrue(first.passed)
        self.assertFalse(first.live_smoke_allowed_now)
        self.assertFalse(first.safe_to_request_user_secret_now)
        self.assertFalse(first.credential_required_now)
        self.assertFalse(first.toss_key_required_now)
        self.assertFalse(first.toss_secret_required_now)
        self.assertFalse(first.access_token_required_now)
        self.assertFalse(first.oauth_allowed_now)
        self.assertFalse(first.live_http_allowed_now)
        self.assertFalse(first.account_seq_allowed_now)
        self.assertFalse(first.order_allowed_now)
        self.assertFalse(first.openai_key_allowed_now)
        self.assertEqual(
            first.next_allowed_stage,
            "MS-15.00 first read-only live smoke planning",
        )

    def test_no_secret_dry_run_is_deterministic_and_safe(self) -> None:
        first = run_toss_api_no_secret_dry_run()
        second = run_toss_api_no_secret_dry_run()

        self.assertEqual(first, second)
        self.assertTrue(first.passed)
        self.assertEqual(first.policy_version, "MS-14.03")
        self.assertEqual(len(first.checklist_item_ids), len(EXPECTED_CHECKLIST_CATEGORIES))
        self.assertEqual(first.checklist_passed_count, len(EXPECTED_CHECKLIST_CATEGORIES))
        self.assertGreater(first.checklist_blocking_count, 0)
        self.assertIn("dry_run_completed", first.safe_diagnostics)
        self.assert_no_forbidden_safe_output(first)

        result = validate_toss_api_no_secret_dry_run_result(first)
        self.assertTrue(result.passed, result.failures)

    def test_live_readiness_preflight_result_blocks_live_capabilities(self) -> None:
        result = run_toss_api_live_readiness_preflight_checks()

        self.assertTrue(result.passed, result.failures)
        self.assertFalse(result.capability_flags.live_http_ready)
        self.assertFalse(result.capability_flags.oauth_ready)
        self.assertFalse(result.capability_flags.credential_required_now)
        self.assertFalse(result.capability_flags.account_seq_required_now)
        self.assertFalse(result.capability_flags.order_required_now)
        self.assertFalse(result.capability_flags.streamlit_required)
        self.assertFalse(result.capability_flags.http_smoke_required)
        self.assertIn("no_secret_dry_run_only", result.diagnostics)

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

    def test_no_live_oauth_account_or_model_implementation_terms(self) -> None:
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
            "credential_loader",
            "settings_loader",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def assert_no_forbidden_safe_output(
        self,
        result: TossApiNoSecretDryRunResult,
    ) -> None:
        rendered_output = " ".join(
            (
                str(result.safe_diagnostics),
                str(result.gate_decision.blocking_reasons),
                str(result.next_stage_label),
                str(result.gate_decision.next_allowed_stage),
                str(result.gate_decision.checklist_summary),
            )
        ).casefold()
        output_tokens = set(re.findall(r"[a-z0-9_.]+", rendered_output))
        for forbidden in FORBIDDEN_SAFE_OUTPUT_TEXT:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden.casefold(), output_tokens)


if __name__ == "__main__":
    unittest.main()
