"""Tests for MS-16.03 live smoke operator runbook rehearsal."""

from dataclasses import is_dataclass, replace
from pathlib import Path
import unittest

from ai_stock.clients import (
    TossApiLiveSmokeOperatorPrerequisite,
    TossApiLiveSmokeOperatorRehearsalDecision,
    TossApiLiveSmokeOperatorRehearsalResult,
    TossApiLiveSmokeOperatorRehearsalValidationResult,
    TossApiLiveSmokeOperatorRunbookPolicy,
    TossApiLiveSmokeOperatorRunbookStep,
    TossApiLiveSmokeRuntimeApprovalChecklist,
    TossApiLiveSmokeStopCondition,
    build_toss_api_live_smoke_operator_prerequisites,
    build_toss_api_live_smoke_operator_runbook_policy,
    build_toss_api_live_smoke_operator_runbook_steps,
    build_toss_api_live_smoke_runtime_approval_checklist,
    build_toss_api_live_smoke_stop_conditions,
    evaluate_toss_api_live_smoke_operator_rehearsal_decision,
    run_toss_api_first_live_smoke_preflight_checks,
    run_toss_api_live_smoke_operator_rehearsal,
    run_toss_api_live_smoke_operator_rehearsal_preflight_checks,
    run_toss_api_live_smoke_result_hardening_preflight_checks,
    run_toss_api_readonly_endpoint_selection,
    run_toss_api_readonly_endpoint_selection_preflight_checks,
    validate_toss_api_live_smoke_operator_rehearsal_result,
)


MODULE_PATH = Path("src/ai_stock/clients/toss_api_live_smoke_operator_runbook.py")
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


class TossApiLiveSmokeOperatorRunbookTests(unittest.TestCase):
    def test_operator_runbook_dataclasses_are_frozen(self) -> None:
        for model in (
            TossApiLiveSmokeOperatorRunbookPolicy,
            TossApiLiveSmokeOperatorPrerequisite,
            TossApiLiveSmokeRuntimeApprovalChecklist,
            TossApiLiveSmokeStopCondition,
            TossApiLiveSmokeOperatorRunbookStep,
            TossApiLiveSmokeOperatorRehearsalDecision,
            TossApiLiveSmokeOperatorRehearsalResult,
            TossApiLiveSmokeOperatorRehearsalValidationResult,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(is_dataclass(model))
                self.assertTrue(model.__dataclass_params__.frozen)

    def test_runbook_policy_is_closed_to_runtime_execution(self) -> None:
        policy = build_toss_api_live_smoke_operator_runbook_policy()

        self.assertEqual(policy.runbook_version, "MS-16.03")
        for flag in (
            "operator_runbook_only",
            "runtime_approval_rehearsal_only",
            "endpoint_must_be_selected_before_live",
            "selected_endpoint_required_for_live",
            "current_endpoint_selection_blocked",
            "redacted_diagnostics_only",
        ):
            self.assertTrue(getattr(policy, flag), flag)
        for flag in (
            "live_http_execution_allowed",
            "credential_request_allowed",
            "credential_value_output_allowed",
            "env_read_allowed",
            "raw_request_output_allowed",
            "raw_response_output_allowed",
            "endpoint_full_url_output_allowed",
            "current_selected_endpoint_available",
            "account_seq_allowed",
            "order_scope_allowed",
            "account_data_allowed",
            "balance_allowed",
            "fills_allowed",
            "oauth_token_issuance_allowed",
            "access_token_required_now",
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

    def test_ms16_preflights_are_reused(self) -> None:
        self.assertTrue(run_toss_api_first_live_smoke_preflight_checks().passed)
        self.assertTrue(
            run_toss_api_live_smoke_result_hardening_preflight_checks().passed
        )
        self.assertTrue(run_toss_api_readonly_endpoint_selection_preflight_checks().passed)

        result = run_toss_api_live_smoke_operator_rehearsal_preflight_checks()

        self.assertTrue(result.passed, result.failures)

    def test_default_rehearsal_is_blocked_without_selected_endpoint(self) -> None:
        selection = run_toss_api_readonly_endpoint_selection()
        result = run_toss_api_live_smoke_operator_rehearsal(selection)

        self.assertTrue(result.passed, result)
        self.assertIsNone(selection.decision.selected_endpoint_id)
        self.assertTrue(selection.decision.selection_blocked)
        self.assertFalse(result.decision.selected_endpoint_available)
        self.assertTrue(result.decision.endpoint_selection_blocked)
        self.assertTrue(result.decision.rehearsal_blocked)
        self.assertIn("selected_endpoint_missing", result.decision.blocking_reasons)
        self.assertIn("endpoint_selection_blocked", result.decision.blocking_reasons)

    def test_runtime_gates_remain_closed(self) -> None:
        decision = evaluate_toss_api_live_smoke_operator_rehearsal_decision()

        self.assertTrue(decision.operator_runbook_invocation_allowed)
        self.assertTrue(decision.runtime_approval_rehearsal_only)
        self.assertTrue(decision.ms_16_00_preflight_passed)
        self.assertTrue(decision.ms_16_01_hardening_passed)
        self.assertTrue(decision.ms_16_02_endpoint_selection_passed)
        for flag in (
            "live_http_execution_allowed_now",
            "credential_request_allowed_now",
            "env_read_allowed_now",
            "oauth_allowed_now",
            "token_issuance_allowed_now",
            "account_seq_allowed_now",
            "order_allowed_now",
            "account_data_allowed_now",
            "balance_allowed_now",
            "fills_allowed_now",
            "openai_key_allowed_now",
            "llm_allowed_now",
            "db_write_allowed_now",
            "streamlit_allowed_now",
            "recommendation_allowed_now",
            "ranking_allowed_now",
            "buy_sell_hold_allowed_now",
            "raw_request_output_allowed",
            "raw_response_output_allowed",
            "endpoint_full_url_output_allowed",
        ):
            self.assertFalse(getattr(decision, flag), flag)

    def test_checklist_prerequisites_stop_conditions_and_steps(self) -> None:
        prerequisites = build_toss_api_live_smoke_operator_prerequisites()
        checklist = build_toss_api_live_smoke_runtime_approval_checklist()
        stop_conditions = build_toss_api_live_smoke_stop_conditions()
        runbook_steps = build_toss_api_live_smoke_operator_runbook_steps()

        credential_prerequisite = next(
            item
            for item in prerequisites
            if item.prerequisite_id == "credential_local_session_only"
        )
        self.assertIn(
            "AI_STOCK_TOSS_API_KEY",
            credential_prerequisite.safe_operator_instruction,
        )
        self.assertIn(
            "AI_STOCK_TOSS_API_SECRET",
            credential_prerequisite.safe_operator_instruction,
        )
        self.assertNotIn(".env", credential_prerequisite.safe_operator_instruction)
        self.assertFalse(checklist.explicit_ms_16_live_http_approval_present)
        self.assertFalse(checklist.confirmed_readonly_endpoint_selected)
        self.assertFalse(checklist.approval_rehearsal_passed)
        triggered = {
            condition.stop_condition_id
            for condition in stop_conditions
            if condition.triggered_now
        }
        self.assertIn("selected_endpoint_missing", triggered)
        self.assertIn("endpoint_selection_blocked", triggered)
        execute_step = next(
            step for step in runbook_steps if step.step_id == "execute_live_http_smoke"
        )
        self.assertFalse(execute_step.allowed_now)
        self.assertNotIn(".env", " ".join(step.safe_instruction for step in runbook_steps))

    def test_safe_diagnostics_do_not_expose_forbidden_terms_url_or_command(self) -> None:
        result = run_toss_api_live_smoke_operator_rehearsal()
        safe_text = " ".join((result.safe_message, *result.safe_diagnostics)).casefold()

        self.assertNotIn("/", safe_text)
        self.assertNotIn("http:", safe_text)
        self.assertNotIn("https:", safe_text)
        self.assertNotIn("command", safe_text)
        for forbidden in FORBIDDEN_SAFE_OUTPUT_TEXT:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden.casefold(), safe_text)

    def test_forbidden_output_validation_blocks_unsafe_safe_diagnostics(self) -> None:
        result = run_toss_api_live_smoke_operator_rehearsal()
        unsafe = replace(
            result,
            safe_diagnostics=(
                *result.safe_diagnostics,
                "authorization bearer synthetic token",
            ),
        )

        validation = validate_toss_api_live_smoke_operator_rehearsal_result(unsafe)

        self.assertFalse(validation.passed)
        self.assertIn("forbidden_safe_output_fragment_exposed", validation.failures)

    def test_execution_command_and_endpoint_path_are_blocked_by_validation(self) -> None:
        result = run_toss_api_live_smoke_operator_rehearsal()

        command_result = replace(
            result,
            safe_diagnostics=(*result.safe_diagnostics, "execution_command=run"),
        )
        path_result = replace(
            result,
            safe_diagnostics=(*result.safe_diagnostics, "endpoint_path=/unsafe"),
        )

        self.assertIn(
            "execution_command_exposed",
            validate_toss_api_live_smoke_operator_rehearsal_result(
                command_result
            ).failures,
        )
        self.assertIn(
            "endpoint_full_url_or_path_exposed",
            validate_toss_api_live_smoke_operator_rehearsal_result(path_result).failures,
        )

    def test_rehearsal_decision_and_result_are_deterministic(self) -> None:
        self.assertEqual(
            evaluate_toss_api_live_smoke_operator_rehearsal_decision(),
            evaluate_toss_api_live_smoke_operator_rehearsal_decision(),
        )
        self.assertEqual(
            run_toss_api_live_smoke_operator_rehearsal(),
            run_toss_api_live_smoke_operator_rehearsal(),
        )

    def test_source_has_no_forbidden_io_or_runtime_imports(self) -> None:
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
