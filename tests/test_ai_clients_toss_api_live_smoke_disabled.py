"""Tests for the MS-15.01 read-only live smoke disabled skeleton."""

from dataclasses import fields, is_dataclass
import ast
from pathlib import Path
import re
import unittest

from ai_stock.clients import (
    TossApiReadOnlyLiveSmokeDisabledDecision,
    TossApiReadOnlyLiveSmokeDisabledPolicy,
    TossApiReadOnlyLiveSmokeDisabledRequest,
    TossApiReadOnlyLiveSmokeDisabledResult,
    TossApiReadOnlyLiveSmokeDisabledValidationResult,
    build_toss_api_readonly_live_smoke_disabled_policy,
    build_toss_api_readonly_live_smoke_disabled_request,
    build_toss_api_readonly_live_smoke_plan,
    evaluate_toss_api_readonly_live_smoke_disabled_decision,
    run_toss_api_client_contract_preflight_checks,
    run_toss_api_config_guardrail_preflight_checks,
    run_toss_api_fake_transport_preflight_checks,
    run_toss_api_live_readiness_preflight_checks,
    run_toss_api_no_secret_dry_run,
    run_toss_api_readonly_live_smoke_disabled_preflight_checks,
    run_toss_api_readonly_live_smoke_disabled_skeleton,
    run_toss_api_readonly_live_smoke_planning_preflight_checks,
    validate_toss_api_readonly_live_smoke_disabled_result,
)


MODULE_PATH = Path("src/ai_stock/clients/toss_api_live_smoke_disabled.py")
EXPECTED_NEXT_STAGE = "MS-15.02 read-only live smoke explicit approval gate"
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


class TossApiReadOnlyLiveSmokeDisabledTests(unittest.TestCase):
    def test_disabled_dataclasses_are_frozen_shapes(self) -> None:
        for model in (
            TossApiReadOnlyLiveSmokeDisabledPolicy,
            TossApiReadOnlyLiveSmokeDisabledRequest,
            TossApiReadOnlyLiveSmokeDisabledDecision,
            TossApiReadOnlyLiveSmokeDisabledResult,
            TossApiReadOnlyLiveSmokeDisabledValidationResult,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(is_dataclass(model))
                self.assertTrue(model.__dataclass_params__.frozen)

    def test_disabled_policy_is_no_io_and_closed_now(self) -> None:
        policy = build_toss_api_readonly_live_smoke_disabled_policy()

        self.assertEqual(policy.skeleton_version, "MS-15.01")
        for flag in (
            "disabled_skeleton_only",
            "planning_gate_required",
            "uses_ms_15_00_plan",
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
            "disabled_execution_result_only",
            "explicit_user_approval_required_for_live_stage",
        ):
            self.assertTrue(getattr(policy, flag), flag)
        for flag in (
            "credential_required_now",
            "toss_key_required_now",
            "toss_secret_required_now",
            "openai_key_required_now",
            "access_token_required_now",
            "safe_to_request_user_secret_now",
            "live_execution_allowed_now",
        ):
            self.assertFalse(getattr(policy, flag), flag)

    def test_ms15_planning_and_ms14_preflights_are_reused(self) -> None:
        result = run_toss_api_readonly_live_smoke_disabled_preflight_checks()

        self.assertTrue(run_toss_api_client_contract_preflight_checks().passed)
        self.assertTrue(run_toss_api_fake_transport_preflight_checks().passed)
        self.assertTrue(run_toss_api_config_guardrail_preflight_checks().passed)
        self.assertTrue(run_toss_api_live_readiness_preflight_checks().passed)
        self.assertTrue(run_toss_api_no_secret_dry_run().passed)
        self.assertTrue(run_toss_api_readonly_live_smoke_planning_preflight_checks().passed)
        self.assertTrue(result.passed, result.failures)

    def test_disabled_request_is_symbolic_readonly_planning_only(self) -> None:
        request = build_toss_api_readonly_live_smoke_disabled_request()

        self.assertTrue(request.symbolic_request_id.startswith("symbolic_"))
        self.assertTrue(request.target_id.startswith("symbolic_"))
        self.assertIn(request.target_id, {target.target_id for target in build_toss_api_readonly_live_smoke_plan().targets})
        self.assertTrue(request.readonly)
        self.assertTrue(request.planning_only)
        self.assertTrue(request.disabled)
        self.assertFalse(request.live_call_attempted)
        self.assertFalse(request.credential_attached)
        self.assertFalse(request.token_attached)
        self.assertFalse(request.account_seq_attached)
        self.assertFalse(request.raw_payload_attached)

    def test_disabled_decision_is_deterministic_and_closed(self) -> None:
        first = evaluate_toss_api_readonly_live_smoke_disabled_decision()
        second = evaluate_toss_api_readonly_live_smoke_disabled_decision()

        self.assertEqual(first, second)
        self.assertTrue(first.skeleton_invocation_allowed)
        self.assertTrue(first.planning_gate_passed)
        self.assertFalse(first.live_execution_allowed_now)
        self.assertFalse(first.credential_request_allowed_now)
        self.assertFalse(first.oauth_allowed_now)
        self.assertFalse(first.token_issuance_allowed_now)
        self.assertFalse(first.account_seq_allowed_now)
        self.assertFalse(first.order_allowed_now)
        self.assertFalse(first.account_data_allowed_now)
        self.assertFalse(first.balance_allowed_now)
        self.assertFalse(first.fills_allowed_now)
        self.assertFalse(first.openai_key_allowed_now)
        self.assertFalse(first.llm_allowed_now)
        self.assertEqual(first.next_stage, EXPECTED_NEXT_STAGE)
        self.assertTrue(first.explicit_approval_required)

    def test_disabled_result_is_deterministic_safe_and_disabled(self) -> None:
        first = run_toss_api_readonly_live_smoke_disabled_skeleton()
        second = run_toss_api_readonly_live_smoke_disabled_skeleton()

        self.assertEqual(first, second)
        self.assertTrue(first.passed)
        self.assertTrue(first.disabled)
        self.assertEqual(first.next_stage, EXPECTED_NEXT_STAGE)
        self.assertIn("pure_no_io_disabled_skeleton", first.safe_diagnostics)
        self.assertIn("runtime_execution_closed", first.safe_diagnostics)
        self.assert_no_forbidden_safe_output(first)

    def test_validation_result_confirms_disabled_skeleton_contract(self) -> None:
        result = validate_toss_api_readonly_live_smoke_disabled_result()

        self.assertTrue(result.passed, result.failures)
        self.assertIn("disabled_skeleton_only", result.checked_policy_flags)
        self.assertIn("live_call_attempted", result.checked_request_flags)
        self.assertIn("skeleton_invocation_allowed", result.checked_decision_flags)
        self.assertIn("disabled", result.checked_result_flags)
        self.assertIn("symbolic_disabled_skeleton_only", result.diagnostics)

    def test_preflight_result_is_deterministic(self) -> None:
        first = run_toss_api_readonly_live_smoke_disabled_preflight_checks()
        second = run_toss_api_readonly_live_smoke_disabled_preflight_checks()

        self.assertEqual(first, second)
        self.assertTrue(first.passed, first.failures)
        self.assertTrue(fields(type(first)))

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
            ".env.example",
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

    def test_no_live_endpoint_or_model_implementation_terms(self) -> None:
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
            "live_client",
            "account_client",
            "order_client",
            "actual_request_body",
            "actual_response_body",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def assert_no_forbidden_safe_output(
        self,
        result: TossApiReadOnlyLiveSmokeDisabledResult,
    ) -> None:
        rendered_output = " ".join(
            (
                result.safe_message,
                str(result.safe_diagnostics),
                result.next_stage,
                result.decision.disabled_reason,
            )
        ).casefold()
        output_tokens = set(re.findall(r"[a-z0-9_.]+", rendered_output))
        for forbidden in FORBIDDEN_SAFE_OUTPUT_TEXT:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden.casefold(), output_tokens)


if __name__ == "__main__":
    unittest.main()
