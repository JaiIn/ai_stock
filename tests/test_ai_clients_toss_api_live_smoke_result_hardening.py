"""Tests for MS-16.01 read-only live smoke result hardening."""

from dataclasses import is_dataclass, replace
from pathlib import Path
import unittest

from ai_stock.clients import (
    TossApiFirstLiveSmokeCredentialPresence,
    TossApiFirstLiveSmokeEndpointCandidate,
    TossApiFirstLiveSmokeHttpResult,
    TossApiLiveSmokeRedactionProbe,
    TossApiLiveSmokeResultHardeningDecision,
    TossApiLiveSmokeResultHardeningPolicy,
    TossApiLiveSmokeResultHardeningResult,
    TossApiLiveSmokeResultHardeningValidationResult,
    TossApiLiveSmokeSafeErrorSummary,
    TossApiLiveSmokeSafeHttpSummary,
    build_toss_api_first_live_smoke_runtime_approval,
    build_toss_api_live_smoke_redaction_probe,
    build_toss_api_live_smoke_result_hardening_policy,
    build_toss_api_live_smoke_safe_error_summary,
    build_toss_api_live_smoke_safe_http_summary,
    evaluate_toss_api_live_smoke_result_hardening_decision,
    run_toss_api_first_live_smoke,
    run_toss_api_first_live_smoke_preflight_checks,
    run_toss_api_live_smoke_result_hardening,
    run_toss_api_live_smoke_result_hardening_preflight_checks,
    validate_toss_api_live_smoke_result_hardening_result,
)


MODULE_PATH = Path("src/ai_stock/clients/toss_api_live_smoke_result_hardening.py")
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


class TossApiLiveSmokeResultHardeningTests(unittest.TestCase):
    def test_hardening_dataclasses_are_frozen(self) -> None:
        for model in (
            TossApiLiveSmokeResultHardeningPolicy,
            TossApiLiveSmokeSafeHttpSummary,
            TossApiLiveSmokeSafeErrorSummary,
            TossApiLiveSmokeRedactionProbe,
            TossApiLiveSmokeResultHardeningDecision,
            TossApiLiveSmokeResultHardeningResult,
            TossApiLiveSmokeResultHardeningValidationResult,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(is_dataclass(model))
                self.assertTrue(model.__dataclass_params__.frozen)

    def test_hardening_policy_is_closed_to_live_runtime(self) -> None:
        policy = build_toss_api_live_smoke_result_hardening_policy()

        self.assertEqual(policy.hardening_version, "MS-16.01")
        for flag in (
            "result_hardening_only",
            "redacted_diagnostics_only",
            "status_code_allowed",
            "elapsed_ms_allowed",
            "response_shape_summary_allowed",
            "error_category_allowed",
        ):
            self.assertTrue(getattr(policy, flag), flag)
        for flag in (
            "live_http_execution_allowed",
            "credential_request_allowed",
            "credential_value_output_allowed",
            "raw_request_output_allowed",
            "raw_response_output_allowed",
            "authorization_header_output_allowed",
            "token_output_allowed",
            "account_seq_allowed",
            "order_scope_allowed",
            "account_data_allowed",
            "balance_allowed",
            "fills_allowed",
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

    def test_ms16_00_preflight_is_reused(self) -> None:
        self.assertTrue(run_toss_api_first_live_smoke_preflight_checks().passed)

        result = run_toss_api_live_smoke_result_hardening_preflight_checks()

        self.assertTrue(result.passed, result.failures)

    def test_safe_http_summary_allows_only_summary_fields(self) -> None:
        first_smoke = _attempted_first_smoke_result()
        summary = build_toss_api_live_smoke_safe_http_summary(first_smoke)

        self.assertTrue(summary.attempted)
        self.assertEqual(summary.status_code, 204)
        self.assertTrue(summary.success)
        self.assertEqual(summary.error_category, None)
        self.assertEqual(summary.response_shape_summary, ("object_shape",))
        self.assertEqual(summary.elapsed_ms, 7)
        self.assertEqual(summary.diagnostics_kind, "redacted_result_diagnostics")
        self.assertTrue(summary.redaction_applied)

    def test_safe_error_summary_is_symbolic(self) -> None:
        summary = build_toss_api_live_smoke_safe_error_summary()

        self.assertIsInstance(summary.error_category, str)
        self.assertEqual(summary.safe_error_code, "safe_blocked_or_summarized_error")
        self.assertFalse(summary.retryable)
        self.assertEqual(summary.operator_action, "review_redacted_summary_only")
        self.assertEqual(summary.redacted_message, "sensitive_detail_redacted")

    def test_redaction_probe_uses_safe_labels_only(self) -> None:
        probe = build_toss_api_live_smoke_redaction_probe()

        self.assertEqual(probe.synthetic_input_count, 40)
        self.assertEqual(len(probe.sanitized_probe_labels), probe.synthetic_input_count)
        self.assertFalse(probe.synthetic_values_returned)
        self.assertTrue(probe.validation_failure_expected_for_raw_probe)
        self.assertTrue(probe.validation_failure_observed_for_raw_probe)
        for label in probe.sanitized_probe_labels:
            self.assertTrue(label.startswith("safe_probe_label_"))

    def test_hardening_decision_is_deterministic_and_closed(self) -> None:
        first = evaluate_toss_api_live_smoke_result_hardening_decision()
        second = evaluate_toss_api_live_smoke_result_hardening_decision()

        self.assertEqual(first, second)
        self.assertTrue(first.hardening_invocation_allowed)
        self.assertTrue(first.ms_16_00_preflight_passed)
        self.assertFalse(first.live_http_execution_allowed)
        self.assertFalse(first.credential_request_allowed)
        self.assertFalse(first.raw_request_output_allowed)
        self.assertFalse(first.raw_response_output_allowed)
        self.assertTrue(first.credentials_redacted)
        self.assertTrue(first.safe_http_summary_allowed)
        self.assertTrue(first.safe_error_summary_allowed)
        self.assertTrue(first.redaction_probe_passed)
        self.assertFalse(first.account_seq_used)
        self.assertFalse(first.order_scope_used)
        self.assertFalse(first.account_balance_fills_scope_used)
        self.assertFalse(first.openai_key_used)
        self.assertFalse(first.llm_used)
        self.assertFalse(first.db_written)
        self.assertFalse(first.streamlit_used)
        self.assertFalse(first.recommendation_generated)
        self.assertFalse(first.ranking_generated)
        self.assertFalse(first.buy_sell_hold_generated)

    def test_hardening_result_is_deterministic_and_safe(self) -> None:
        first = run_toss_api_live_smoke_result_hardening()
        second = run_toss_api_live_smoke_result_hardening()

        self.assertEqual(first, second)
        self.assertTrue(first.passed)
        self.assertFalse(first.decision.live_http_execution_allowed)
        self.assertFalse(first.decision.credential_request_allowed)
        self.assertTrue(first.decision.credentials_redacted)
        self.assertTrue(first.decision.redaction_probe_passed)
        self.assertEqual(
            validate_toss_api_live_smoke_result_hardening_result(first).failures,
            (),
        )

    def test_raw_request_and_raw_response_are_blocked_by_validation(self) -> None:
        result = run_toss_api_live_smoke_result_hardening()
        unsafe = replace(
            result,
            safe_http_summary=replace(
                result.safe_http_summary,
                response_shape_summary=("raw_request", "raw_response"),
            ),
        )

        validation = validate_toss_api_live_smoke_result_hardening_result(unsafe)

        self.assertFalse(validation.passed)
        self.assertIn("forbidden_safe_output_fragment_exposed", validation.failures)

    def test_synthetic_forbidden_token_fails_validation(self) -> None:
        result = run_toss_api_live_smoke_result_hardening()
        unsafe = replace(
            result,
            safe_error_summary=replace(
                result.safe_error_summary,
                redacted_message="authorization bearer synthetic token",
            ),
        )

        validation = validate_toss_api_live_smoke_result_hardening_result(unsafe)

        self.assertFalse(validation.passed)
        self.assertIn("forbidden_safe_output_fragment_exposed", validation.failures)

    def test_safe_diagnostics_do_not_expose_sensitive_terms(self) -> None:
        result = run_toss_api_live_smoke_result_hardening()
        safe_text = " ".join(
            (
                *result.safe_diagnostics,
                result.safe_http_summary.diagnostics_kind,
                *(result.safe_http_summary.response_shape_summary),
                result.safe_http_summary.error_category or "",
                result.safe_error_summary.error_category or "",
                result.safe_error_summary.safe_error_code,
                result.safe_error_summary.operator_action,
                result.safe_error_summary.redacted_message,
                result.redaction_probe.probe_id,
                *(result.redaction_probe.sanitized_probe_labels),
            )
        ).casefold()

        for forbidden in FORBIDDEN_SAFE_OUTPUT_TEXT:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden.casefold(), safe_text)

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
        self.assertIn("SYNTHETIC_FORBIDDEN_PROBE_INPUTS", source)


def _attempted_first_smoke_result():
    return run_toss_api_first_live_smoke(
        credential_presence=TossApiFirstLiveSmokeCredentialPresence(
            required_env_names=("AI_STOCK_TOSS_API_KEY", "AI_STOCK_TOSS_API_SECRET"),
            api_key_present=True,
            api_secret_present=True,
            all_required_credentials_present=True,
            credential_values_loaded_but_never_exposed=True,
            missing_env_names_redacted=(),
        ),
        endpoint_candidate=TossApiFirstLiveSmokeEndpointCandidate(
            endpoint_id="symbolic_confirmed_readonly_market_data_smoke",
            endpoint_scope="readonly_market_data_public_candidate",
            readonly=True,
            market_data_only=True,
            requires_account_seq=False,
            requires_order_scope=False,
            requires_account_balance_fills=False,
            allows_raw_payload_output=False,
            endpoint_confirmed=True,
            live_http_executable_without_oauth=True,
        ),
        runtime_approval=build_toss_api_first_live_smoke_runtime_approval(
            explicit_user_approved_ms_16_00=True,
            runtime_live_http_approved=True,
            credential_request_approved=True,
            readonly_scope_confirmed=True,
            raw_output_block_confirmed=True,
            no_account_scope_confirmed=True,
            no_order_scope_confirmed=True,
        ),
        executor=lambda _plan: TossApiFirstLiveSmokeHttpResult(
            attempted=True,
            status_code=204,
            success=True,
            error_category=None,
            response_shape_summary=("object_shape",),
            elapsed_ms=7,
            redacted_diagnostics=("shape_only",),
        ),
    )


if __name__ == "__main__":
    unittest.main()
