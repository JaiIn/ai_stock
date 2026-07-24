"""Tests for MS-16.05a live smoke auth/execution bridge."""

from dataclasses import is_dataclass, replace
from pathlib import Path
import unittest

from ai_stock.clients import (
    TossApiLiveSmokeAuthRealignment,
    TossApiLiveSmokeExecutionBridgeDecision,
    TossApiLiveSmokeExecutionBridgePolicy,
    TossApiLiveSmokeExecutionBridgeResult,
    TossApiLiveSmokeExecutionBridgeValidationResult,
    TossApiLiveSmokeExecutionGuard,
    TossApiLiveSmokeExecutionPlan,
    build_toss_api_live_smoke_auth_realignment,
    build_toss_api_live_smoke_execution_bridge_policy,
    build_toss_api_live_smoke_execution_guard,
    build_toss_api_live_smoke_execution_plan,
    evaluate_toss_api_live_smoke_execution_bridge_decision,
    run_toss_api_confirmed_endpoint_evidence_update,
    run_toss_api_live_smoke_execution_bridge,
    run_toss_api_live_smoke_execution_bridge_preflight_checks,
    validate_toss_api_live_smoke_execution_bridge_result,
)


MODULE_PATH = Path("src/ai_stock/clients/toss_api_live_smoke_execution_bridge.py")
SELECTED_ENDPOINT_ID = "confirmed_prices_single_symbol_readonly_market_data"
SELECTED_ENDPOINT_LABEL = "Prices single-symbol read-only market data"
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
    "accountseq",
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
    "strong_buy",
    "recommendation",
    "ranking_position",
    "target_price",
    "expected_return",
    "profit_probability",
    "must_buy",
    "must_sell",
)


class TossApiLiveSmokeExecutionBridgeTests(unittest.TestCase):
    def test_bridge_dataclasses_are_frozen(self) -> None:
        for model in (
            TossApiLiveSmokeExecutionBridgePolicy,
            TossApiLiveSmokeAuthRealignment,
            TossApiLiveSmokeExecutionPlan,
            TossApiLiveSmokeExecutionGuard,
            TossApiLiveSmokeExecutionBridgeDecision,
            TossApiLiveSmokeExecutionBridgeResult,
            TossApiLiveSmokeExecutionBridgeValidationResult,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(is_dataclass(model))
                self.assertTrue(model.__dataclass_params__.frozen)

    def test_policy_is_execution_bridge_only(self) -> None:
        policy = build_toss_api_live_smoke_execution_bridge_policy()

        self.assertEqual(policy.bridge_version, "MS-16.05a")
        self.assertTrue(policy.execution_bridge_only)
        self.assertTrue(policy.auth_realignment_only)
        self.assertTrue(policy.redacted_diagnostics_only)
        for flag in (
            "actual_live_http_allowed",
            "oauth_token_request_allowed_now",
            "readonly_business_request_allowed_now",
            "credential_request_allowed",
            "credential_presence_check_allowed",
            "env_read_allowed",
            "credential_value_output_allowed",
            "access_token_output_allowed",
            "authorization_bearer_output_allowed",
            "raw_request_output_allowed",
            "raw_response_output_allowed",
            "endpoint_full_url_output_allowed",
            "account_seq_allowed",
            "order_scope_allowed",
            "account_data_allowed",
            "balance_allowed",
            "fills_allowed",
            "retry_loop_allowed",
            "db_read_allowed",
            "db_write_allowed",
            "streamlit_allowed",
            "openai_key_allowed",
            "llm_allowed",
            "recommendation_allowed",
            "ranking_allowed",
            "buy_sell_hold_allowed",
        ):
            self.assertFalse(getattr(policy, flag), flag)

    def test_auth_realignment_supersedes_ms_16_04_oauth_assumption(self) -> None:
        realignment = build_toss_api_live_smoke_auth_realignment()

        self.assertEqual(realignment.selected_endpoint_id, SELECTED_ENDPOINT_ID)
        self.assertEqual(realignment.selected_endpoint_label, SELECTED_ENDPOINT_LABEL)
        self.assertFalse(realignment.previous_oauth_required_assumption)
        self.assertTrue(realignment.corrected_oauth_required)
        self.assertTrue(realignment.corrected_access_token_required)
        self.assertTrue(realignment.corrected_authorization_bearer_required)
        self.assertFalse(realignment.account_seq_required)
        self.assertFalse(realignment.order_scope_required)
        self.assertFalse(realignment.account_balance_fills_required)
        self.assertTrue(realignment.supersedes_ms_16_04_oauth_assumption)

    def test_selected_endpoint_and_selection_state_are_preserved(self) -> None:
        evidence_result = run_toss_api_confirmed_endpoint_evidence_update()
        bridge_result = run_toss_api_live_smoke_execution_bridge()

        self.assertFalse(evidence_result.decision.selection_blocked)
        self.assertEqual(evidence_result.decision.selected_endpoint_id, SELECTED_ENDPOINT_ID)
        self.assertEqual(
            bridge_result.auth_realignment.selected_endpoint_id,
            evidence_result.decision.selected_endpoint_id,
        )
        self.assertEqual(
            bridge_result.execution_plan.selected_endpoint_label,
            SELECTED_ENDPOINT_LABEL,
        )

    def test_execution_plan_models_two_future_calls_without_retry(self) -> None:
        plan = build_toss_api_live_smoke_execution_plan()

        self.assertEqual(plan.selected_endpoint_id, SELECTED_ENDPOINT_ID)
        self.assertEqual(plan.operation_kind, "getPrices")
        self.assertEqual(plan.planned_network_call_count, 2)
        self.assertEqual(plan.planned_oauth_call_count, 1)
        self.assertEqual(plan.planned_readonly_business_call_count, 1)
        self.assertEqual(plan.planned_retry_count, 0)
        self.assertEqual(
            plan.credential_source_policy,
            "local_session_env_only_for_future_stage",
        )
        self.assertEqual(
            plan.token_storage_policy,
            "memory_only_no_raw_output_for_future_stage",
        )
        self.assertTrue(plan.ready_for_ms_16_05b)
        for flag in (
            "authorization_header_output_allowed",
            "access_token_output_allowed",
            "raw_request_output_allowed",
            "raw_response_output_allowed",
            "endpoint_full_url_output_allowed",
            "account_seq_used",
            "order_scope_used",
            "account_balance_fills_scope_used",
        ):
            self.assertFalse(getattr(plan, flag), flag)

    def test_execution_guard_blocks_sensitive_and_trading_scope(self) -> None:
        guard = build_toss_api_live_smoke_execution_guard()

        for flag, value in guard.__dict__.items():
            with self.subTest(flag=flag):
                self.assertTrue(value)

    def test_decision_keeps_current_stage_non_executing(self) -> None:
        decision = evaluate_toss_api_live_smoke_execution_bridge_decision()

        self.assertTrue(decision.execution_bridge_invocation_allowed)
        self.assertTrue(decision.execution_bridge_only)
        self.assertEqual(decision.selected_endpoint_id, SELECTED_ENDPOINT_ID)
        self.assertTrue(decision.selected_endpoint_ready)
        self.assertTrue(decision.oauth_requirement_realigned)
        self.assertEqual(decision.future_ms_16_05b_network_call_count, 2)
        self.assertEqual(decision.future_ms_16_05b_oauth_call_count, 1)
        self.assertEqual(decision.future_ms_16_05b_readonly_business_call_count, 1)
        self.assertEqual(decision.future_ms_16_05b_retry_count, 0)
        self.assertTrue(decision.ready_for_ms_16_05b)
        for flag in (
            "actual_live_http_attempted",
            "oauth_token_request_attempted",
            "readonly_business_request_attempted",
            "credential_request_performed",
            "credential_presence_check_performed",
            "env_read_performed",
            "live_http_execution_allowed_now",
            "credential_request_allowed_now",
            "credential_presence_check_allowed_now",
            "env_read_allowed_now",
            "oauth_token_issuance_allowed_now",
            "access_token_output_allowed",
            "authorization_bearer_output_allowed",
            "raw_request_output_allowed",
            "raw_response_output_allowed",
            "endpoint_full_url_output_allowed",
            "account_seq_allowed_now",
            "order_allowed_now",
            "account_data_allowed_now",
            "balance_allowed_now",
            "fills_allowed_now",
            "db_write_allowed_now",
            "streamlit_allowed_now",
            "openai_key_allowed_now",
            "llm_allowed_now",
            "recommendation_allowed_now",
            "ranking_allowed_now",
            "buy_sell_hold_allowed_now",
        ):
            self.assertFalse(getattr(decision, flag), flag)

    def test_preflight_reuses_ms16_chain_and_passes(self) -> None:
        result = run_toss_api_live_smoke_execution_bridge_preflight_checks()

        self.assertTrue(result.passed, result.failures)

    def test_safe_diagnostics_are_allowlisted_and_redacted(self) -> None:
        result = run_toss_api_live_smoke_execution_bridge()
        safe_text = " ".join((result.safe_message, *result.safe_diagnostics)).casefold()

        self.assertIn("selected_endpoint_id=", safe_text)
        self.assertIn("selected_endpoint_label=", safe_text)
        self.assertIn("oauth_required=true", safe_text)
        self.assertIn("access_required=true", safe_text)
        self.assertIn("planned_network_call_count=2", safe_text)
        self.assertIn("planned_oauth_call_count=1", safe_text)
        self.assertIn("planned_readonly_business_call_count=1", safe_text)
        self.assertIn("retry_count=0", safe_text)
        self.assertIn("ready_for_ms_16_05b=true", safe_text)
        self.assertIn("redaction_applied=true", safe_text)
        self.assertNotIn("/", safe_text)
        self.assertNotIn("http:", safe_text)
        self.assertNotIn("https:", safe_text)
        for forbidden in FORBIDDEN_SAFE_OUTPUT_TEXT:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden.casefold(), safe_text)

    def test_forbidden_output_validation_blocks_unsafe_diagnostics(self) -> None:
        result = run_toss_api_live_smoke_execution_bridge()
        unsafe = replace(
            result,
            safe_diagnostics=(
                *result.safe_diagnostics,
                "authorization bearer synthetic token",
            ),
        )

        validation = validate_toss_api_live_smoke_execution_bridge_result(unsafe)

        self.assertFalse(validation.passed)
        self.assertIn("forbidden_safe_output_fragment_exposed", validation.failures)

    def test_endpoint_full_url_and_raw_path_are_blocked(self) -> None:
        result = run_toss_api_live_smoke_execution_bridge()
        unsafe = replace(
            result,
            safe_diagnostics=(*result.safe_diagnostics, "endpoint_path=/unsafe"),
        )

        validation = validate_toss_api_live_smoke_execution_bridge_result(unsafe)

        self.assertFalse(validation.passed)
        self.assertIn("endpoint_full_url_or_path_exposed", validation.failures)

    def test_bridge_result_is_deterministic(self) -> None:
        self.assertEqual(
            evaluate_toss_api_live_smoke_execution_bridge_decision(),
            evaluate_toss_api_live_smoke_execution_bridge_decision(),
        )
        self.assertEqual(
            run_toss_api_live_smoke_execution_bridge(),
            run_toss_api_live_smoke_execution_bridge(),
        )

    def test_source_has_no_io_network_env_cli_or_ui_imports(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")

        for forbidden in (
            "import requests",
            "import httpx",
            "import aiohttp",
            "urllib.request",
            "import socket",
            "os.environ",
            "os.getenv",
            "from dotenv",
            "import dotenv",
            "import subprocess",
            "import argparse",
            "import click",
            "import typer",
            "read_text(",
            "write_text(",
            "open(",
            "import streamlit",
            "import openai",
            "sqlite3",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
