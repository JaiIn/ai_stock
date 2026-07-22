"""Tests for the MS-15.02 read-only live smoke explicit approval gate."""

from dataclasses import fields, is_dataclass
import ast
from pathlib import Path
import re
import unittest

from ai_stock.clients import (
    TossApiReadOnlyLiveSmokeApprovalDecision,
    TossApiReadOnlyLiveSmokeApprovalGateResult,
    TossApiReadOnlyLiveSmokeApprovalIntent,
    TossApiReadOnlyLiveSmokeApprovalPolicy,
    TossApiReadOnlyLiveSmokeApprovalRequirement,
    TossApiReadOnlyLiveSmokeApprovalValidationResult,
    build_toss_api_readonly_live_smoke_approval_intent,
    build_toss_api_readonly_live_smoke_approval_policy,
    build_toss_api_readonly_live_smoke_approval_requirements,
    evaluate_toss_api_readonly_live_smoke_approval_decision,
    run_toss_api_client_contract_preflight_checks,
    run_toss_api_config_guardrail_preflight_checks,
    run_toss_api_fake_transport_preflight_checks,
    run_toss_api_live_readiness_preflight_checks,
    run_toss_api_no_secret_dry_run,
    run_toss_api_readonly_live_smoke_approval_gate,
    run_toss_api_readonly_live_smoke_approval_preflight_checks,
    run_toss_api_readonly_live_smoke_disabled_preflight_checks,
    run_toss_api_readonly_live_smoke_disabled_skeleton,
    run_toss_api_readonly_live_smoke_planning_preflight_checks,
    validate_toss_api_readonly_live_smoke_approval_gate_result,
)


MODULE_PATH = Path("src/ai_stock/clients/toss_api_live_smoke_approval.py")
EXPECTED_REQUIREMENTS = (
    "explicit_user_message_required",
    "branch_stage_must_be_live_smoke_stage",
    "read_only_scope_required",
    "credential_request_must_be_separately_approved",
    "env_read_must_be_separately_approved",
    "oauth_token_must_be_separately_approved",
    "live_http_must_be_separately_approved",
    "account_seq_must_remain_blocked",
    "order_scope_must_remain_blocked",
    "account_balance_fills_scope_must_remain_blocked",
    "raw_payload_output_must_remain_blocked",
    "rollback_path_required",
    "redacted_diagnostics_only_required",
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


class TossApiReadOnlyLiveSmokeApprovalTests(unittest.TestCase):
    def test_approval_dataclasses_are_frozen_shapes(self) -> None:
        for model in (
            TossApiReadOnlyLiveSmokeApprovalPolicy,
            TossApiReadOnlyLiveSmokeApprovalIntent,
            TossApiReadOnlyLiveSmokeApprovalRequirement,
            TossApiReadOnlyLiveSmokeApprovalDecision,
            TossApiReadOnlyLiveSmokeApprovalGateResult,
            TossApiReadOnlyLiveSmokeApprovalValidationResult,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(is_dataclass(model))
                self.assertTrue(model.__dataclass_params__.frozen)

    def test_approval_policy_is_no_io_and_closed_now(self) -> None:
        policy = build_toss_api_readonly_live_smoke_approval_policy()

        self.assertEqual(policy.approval_version, "MS-15.02")
        for flag in (
            "approval_gate_only",
            "explicit_user_approval_required",
            "disabled_skeleton_required",
            "planning_gate_required",
            "uses_ms_15_00_plan",
            "uses_ms_15_01_disabled_skeleton",
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
            "credential_request_allowed_now",
        ):
            self.assertFalse(getattr(policy, flag), flag)

    def test_ms15_and_ms14_preflights_are_reused(self) -> None:
        result = run_toss_api_readonly_live_smoke_approval_preflight_checks()

        self.assertTrue(run_toss_api_client_contract_preflight_checks().passed)
        self.assertTrue(run_toss_api_fake_transport_preflight_checks().passed)
        self.assertTrue(run_toss_api_config_guardrail_preflight_checks().passed)
        self.assertTrue(run_toss_api_live_readiness_preflight_checks().passed)
        self.assertTrue(run_toss_api_no_secret_dry_run().passed)
        self.assertTrue(
            run_toss_api_readonly_live_smoke_planning_preflight_checks().passed
        )
        self.assertTrue(
            run_toss_api_readonly_live_smoke_disabled_preflight_checks().passed
        )
        self.assertTrue(run_toss_api_readonly_live_smoke_disabled_skeleton().passed)
        self.assertTrue(result.passed, result.failures)

    def test_approval_intent_is_symbolic_readonly_and_unapproved(self) -> None:
        intent = build_toss_api_readonly_live_smoke_approval_intent()

        self.assertTrue(intent.symbolic_intent_id.startswith("symbolic_"))
        self.assertTrue(intent.requested_stage_label.startswith("symbolic_"))
        self.assertTrue(intent.readonly)
        self.assertTrue(intent.planning_only)
        self.assertFalse(intent.approval_recorded)
        self.assertFalse(intent.live_call_requested)
        self.assertFalse(intent.live_call_approved)
        self.assertFalse(intent.credential_request_approved)
        self.assertFalse(intent.oauth_approved)
        self.assertFalse(intent.token_issuance_approved)
        self.assertFalse(intent.account_seq_approved)
        self.assertFalse(intent.order_approved)
        self.assertFalse(intent.account_data_approved)
        self.assertFalse(intent.raw_payload_approved)

    def test_approval_requirement_list_is_complete_and_closed(self) -> None:
        requirements = build_toss_api_readonly_live_smoke_approval_requirements()

        self.assertEqual(
            tuple(requirement.requirement_id for requirement in requirements),
            EXPECTED_REQUIREMENTS,
        )
        for requirement in requirements:
            with self.subTest(requirement=requirement.requirement_id):
                self.assertTrue(requirement.safe_requirement_id.startswith("safe_"))
                self.assertTrue(requirement.required)
                self.assertFalse(requirement.satisfied_now)

    def test_approval_decision_is_deterministic_and_closed(self) -> None:
        first = evaluate_toss_api_readonly_live_smoke_approval_decision()
        second = evaluate_toss_api_readonly_live_smoke_approval_decision()

        self.assertEqual(first, second)
        self.assertTrue(first.approval_gate_invocation_allowed)
        self.assertTrue(first.planning_gate_passed)
        self.assertTrue(first.disabled_skeleton_passed)
        self.assertFalse(first.explicit_approval_present)
        self.assertFalse(first.live_execution_allowed_now)
        self.assertFalse(first.credential_request_allowed_now)
        self.assertFalse(first.env_read_allowed_now)
        self.assertFalse(first.file_read_allowed_now)
        self.assertFalse(first.oauth_allowed_now)
        self.assertFalse(first.token_issuance_allowed_now)
        self.assertFalse(first.account_seq_allowed_now)
        self.assertFalse(first.order_allowed_now)
        self.assertFalse(first.account_data_allowed_now)
        self.assertFalse(first.balance_allowed_now)
        self.assertFalse(first.fills_allowed_now)
        self.assertFalse(first.openai_key_allowed_now)
        self.assertFalse(first.llm_allowed_now)

    def test_approval_gate_result_is_deterministic_safe_and_closed(self) -> None:
        first = run_toss_api_readonly_live_smoke_approval_gate()
        second = run_toss_api_readonly_live_smoke_approval_gate()

        self.assertEqual(first, second)
        self.assertTrue(first.passed)
        self.assertTrue(first.gate_closed)
        self.assertTrue(first.decision.planning_gate_passed)
        self.assertTrue(first.decision.disabled_skeleton_passed)
        self.assertFalse(first.decision.explicit_approval_present)
        self.assertIn("pure_no_io_approval_gate", first.safe_diagnostics)
        self.assertIn("runtime_execution_closed", first.safe_diagnostics)
        self.assert_no_forbidden_safe_output(first)

    def test_validation_result_confirms_approval_gate_contract(self) -> None:
        result = validate_toss_api_readonly_live_smoke_approval_gate_result()

        self.assertTrue(result.passed, result.failures)
        self.assertIn("approval_gate_only", result.checked_policy_flags)
        self.assertIn("approval_recorded", result.checked_intent_flags)
        self.assertEqual(result.checked_requirement_ids, EXPECTED_REQUIREMENTS)
        self.assertIn(
            "approval_gate_invocation_allowed",
            result.checked_decision_flags,
        )
        self.assertIn("gate_closed", result.checked_result_flags)
        self.assertIn("symbolic_explicit_approval_gate_only", result.diagnostics)

    def test_preflight_result_is_deterministic(self) -> None:
        first = run_toss_api_readonly_live_smoke_approval_preflight_checks()
        second = run_toss_api_readonly_live_smoke_approval_preflight_checks()

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
            "user_signature",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def assert_no_forbidden_safe_output(
        self,
        result: TossApiReadOnlyLiveSmokeApprovalGateResult,
    ) -> None:
        rendered_output = " ".join(
            (
                result.safe_message,
                str(result.safe_diagnostics),
                result.next_stage,
                str(result.decision.blocking_reasons),
                str(result.decision.safe_summary),
                str(result.requirement_ids),
            )
        ).casefold()
        output_tokens = set(re.findall(r"[a-z0-9_.]+", rendered_output))
        for forbidden in FORBIDDEN_SAFE_OUTPUT_TEXT:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden.casefold(), output_tokens)


if __name__ == "__main__":
    unittest.main()
