"""Tests for the MS-15.03 credential request timing policy."""

from dataclasses import fields, is_dataclass
import ast
from pathlib import Path
import re
import unittest

from ai_stock.clients import (
    TossApiCredentialRequestCandidateStage,
    TossApiCredentialRequestRequirement,
    TossApiCredentialRequestTimingDecision,
    TossApiCredentialRequestTimingPolicy,
    TossApiCredentialRequestTimingResult,
    TossApiCredentialRequestTimingValidationResult,
    build_toss_api_credential_request_candidate_stages,
    build_toss_api_credential_request_requirements,
    build_toss_api_credential_request_timing_policy,
    evaluate_toss_api_credential_request_timing_decision,
    run_toss_api_credential_request_timing_policy,
    run_toss_api_credential_request_timing_preflight_checks,
    run_toss_api_readonly_live_smoke_approval_gate,
    run_toss_api_readonly_live_smoke_approval_preflight_checks,
    validate_toss_api_credential_request_timing_result,
)


MODULE_PATH = Path("src/ai_stock/clients/toss_api_credential_timing.py")
EXPECTED_REQUIREMENTS = (
    "explicit_user_approval_for_ms_16_00_required",
    "toss_key_secret_request_must_be_separate_step",
    "credential_entry_must_not_be_committed",
    "env_file_read_must_be_separately_approved",
    "oauth_token_issuance_must_be_separately_approved",
    "live_http_call_must_be_separately_approved",
    "raw_response_output_must_be_blocked",
    "authorization_header_output_must_be_blocked",
    "token_output_must_be_blocked",
    "account_seq_must_remain_blocked",
    "account_order_balance_fills_scope_must_remain_blocked",
    "db_write_must_remain_blocked",
    "streamlit_ui_must_remain_unchanged",
    "openai_key_must_not_be_requested",
    "llm_call_must_remain_blocked",
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


class TossApiCredentialRequestTimingTests(unittest.TestCase):
    def test_timing_dataclasses_are_frozen_shapes(self) -> None:
        for model in (
            TossApiCredentialRequestTimingPolicy,
            TossApiCredentialRequestCandidateStage,
            TossApiCredentialRequestRequirement,
            TossApiCredentialRequestTimingDecision,
            TossApiCredentialRequestTimingResult,
            TossApiCredentialRequestTimingValidationResult,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(is_dataclass(model))
                self.assertTrue(model.__dataclass_params__.frozen)

    def test_timing_policy_is_no_io_and_closed_now(self) -> None:
        policy = build_toss_api_credential_request_timing_policy()

        self.assertEqual(policy.timing_version, "MS-15.03")
        self.assertEqual(
            policy.next_live_stage_candidate,
            "MS-16.00 first read-only Toss API live smoke",
        )
        for flag in (
            "credential_timing_policy_only",
            "explicit_user_approval_required_before_request",
            "separate_secret_entry_required",
            "separate_env_read_approval_required",
            "separate_oauth_approval_required",
            "separate_live_http_approval_required",
            "account_seq_must_remain_blocked",
            "order_scope_must_remain_blocked",
            "account_balance_fills_scope_must_remain_blocked",
            "raw_payload_output_must_remain_blocked",
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
        ):
            self.assertTrue(getattr(policy, flag), flag)
        for flag in (
            "current_stage_requests_credentials",
            "current_stage_reads_credentials",
            "current_stage_uses_credentials",
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

    def test_ms15_02_approval_preflight_is_reused(self) -> None:
        result = run_toss_api_credential_request_timing_preflight_checks()

        self.assertTrue(run_toss_api_readonly_live_smoke_approval_gate().passed)
        self.assertTrue(run_toss_api_readonly_live_smoke_approval_preflight_checks().passed)
        self.assertTrue(result.passed, result.failures)

    def test_candidate_stage_is_symbolic_ms16_candidate_only(self) -> None:
        candidate_stages = build_toss_api_credential_request_candidate_stages()

        self.assertEqual(len(candidate_stages), 1)
        candidate = candidate_stages[0]
        self.assertEqual(
            candidate.stage_label,
            "ms_16_00_first_readonly_toss_api_live_smoke",
        )
        self.assertTrue(candidate.stage_scope.startswith("symbolic_"))
        self.assertTrue(candidate.readonly_market_data_only)
        self.assertTrue(candidate.may_request_toss_credentials_later)
        self.assertTrue(candidate.requires_explicit_user_approval)
        self.assertTrue(candidate.requires_redaction_policy)
        self.assertTrue(candidate.requires_no_raw_payload_output)
        self.assertTrue(candidate.requires_no_db_write)
        self.assertTrue(candidate.requires_no_account_balance_fills)
        self.assertTrue(candidate.requires_readonly_scope)
        self.assertFalse(candidate.may_request_openai_key_later)
        self.assertFalse(candidate.may_request_account_seq_later)
        self.assertFalse(candidate.may_request_order_scope_later)
        self.assertFalse(candidate.live_execution_allowed_in_current_stage)
        self.assertFalse(candidate.credential_request_allowed_in_current_stage)

    def test_requirement_list_is_complete_and_not_satisfied_now(self) -> None:
        requirements = build_toss_api_credential_request_requirements()

        self.assertEqual(
            tuple(requirement.requirement_id for requirement in requirements),
            EXPECTED_REQUIREMENTS,
        )
        for requirement in requirements:
            with self.subTest(requirement=requirement.requirement_id):
                self.assertTrue(requirement.safe_requirement_id.startswith("safe_"))
                self.assertTrue(requirement.required)
                self.assertFalse(requirement.satisfied_now)
                self.assertTrue(requirement.required_before_candidate_stage)

    def test_timing_decision_is_deterministic_and_closed_now(self) -> None:
        first = evaluate_toss_api_credential_request_timing_decision()
        second = evaluate_toss_api_credential_request_timing_decision()

        self.assertEqual(first, second)
        self.assertTrue(first.timing_policy_invocation_allowed)
        self.assertTrue(first.approval_gate_passed)
        self.assertFalse(first.current_stage_credential_request_allowed)
        self.assertFalse(first.current_stage_env_read_allowed)
        self.assertFalse(first.current_stage_oauth_allowed)
        self.assertFalse(first.current_stage_token_issuance_allowed)
        self.assertFalse(first.current_stage_live_http_allowed)
        self.assertFalse(first.current_stage_live_execution_allowed)
        self.assertFalse(first.current_stage_account_seq_allowed)
        self.assertFalse(first.current_stage_order_allowed)
        self.assertFalse(first.current_stage_account_data_allowed)
        self.assertFalse(first.current_stage_balance_allowed)
        self.assertFalse(first.current_stage_fills_allowed)
        self.assertFalse(first.current_stage_openai_key_allowed)
        self.assertFalse(first.current_stage_llm_allowed)
        self.assertTrue(first.ms_16_00_can_request_toss_credentials_after_explicit_approval)
        self.assertFalse(first.ms_16_00_can_request_openai_key)
        self.assertFalse(first.ms_16_00_can_use_account_seq)
        self.assertFalse(first.ms_16_00_can_use_order_scope)

    def test_timing_result_is_deterministic_safe_and_closed(self) -> None:
        first = run_toss_api_credential_request_timing_policy()
        second = run_toss_api_credential_request_timing_policy()

        self.assertEqual(first, second)
        self.assertTrue(first.passed)
        self.assertTrue(first.policy_closed_for_current_stage)
        self.assertEqual(
            first.candidate_stage_label,
            "ms_16_00_first_readonly_toss_api_live_smoke",
        )
        self.assertIn("pure_no_io_timing_policy", first.safe_diagnostics)
        self.assertIn("approval_gate_reused", first.safe_diagnostics)
        self.assert_no_forbidden_safe_output(first)

    def test_validation_result_confirms_timing_contract(self) -> None:
        result = validate_toss_api_credential_request_timing_result()

        self.assertTrue(result.passed, result.failures)
        self.assertIn("credential_timing_policy_only", result.checked_policy_flags)
        self.assertIn(
            "may_request_toss_credentials_later",
            result.checked_candidate_stage_flags,
        )
        self.assertEqual(result.checked_requirement_ids, EXPECTED_REQUIREMENTS)
        self.assertIn(
            "timing_policy_invocation_allowed",
            result.checked_decision_flags,
        )
        self.assertIn("policy_closed_for_current_stage", result.checked_result_flags)
        self.assertIn("symbolic_credential_timing_policy_only", result.diagnostics)

    def test_preflight_result_is_deterministic(self) -> None:
        first = run_toss_api_credential_request_timing_preflight_checks()
        second = run_toss_api_credential_request_timing_preflight_checks()

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
            "authorization_header_value",
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
            "real_secret_value",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def assert_no_forbidden_safe_output(
        self,
        result: TossApiCredentialRequestTimingResult,
    ) -> None:
        rendered_output = " ".join(
            (
                result.safe_message,
                str(result.safe_diagnostics),
                result.next_stage,
                result.candidate_stage_label,
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
