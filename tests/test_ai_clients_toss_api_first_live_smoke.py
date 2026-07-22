"""Tests for the MS-16.00 first read-only Toss API live smoke gate."""

from dataclasses import is_dataclass
from pathlib import Path
import unittest

from ai_stock.clients import (
    TossApiFirstLiveSmokeCredentialPresence,
    TossApiFirstLiveSmokeDecision,
    TossApiFirstLiveSmokeEndpointCandidate,
    TossApiFirstLiveSmokeHttpResult,
    TossApiFirstLiveSmokePolicy,
    TossApiFirstLiveSmokeRequestPlan,
    TossApiFirstLiveSmokeResult,
    TossApiFirstLiveSmokeRuntimeApproval,
    TossApiFirstLiveSmokeValidationResult,
    build_toss_api_first_live_smoke_endpoint_candidates,
    build_toss_api_first_live_smoke_policy,
    build_toss_api_first_live_smoke_request_plan,
    build_toss_api_first_live_smoke_runtime_approval,
    read_toss_api_first_live_smoke_credential_presence,
    run_toss_api_credential_request_timing_preflight_checks,
    run_toss_api_first_live_smoke,
    run_toss_api_first_live_smoke_preflight_checks,
    validate_toss_api_first_live_smoke_result,
)


MODULE_PATH = Path("src/ai_stock/clients/toss_api_first_live_smoke.py")
ALLOWED_ENV_NAMES = (
    "AI_STOCK_TOSS_API_KEY",
    "AI_STOCK_TOSS_API_SECRET",
)
FORBIDDEN_SAFE_DIAGNOSTIC_TEXT = (
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


class TossApiFirstLiveSmokeTests(unittest.TestCase):
    def test_first_live_smoke_dataclasses_are_frozen(self) -> None:
        for model in (
            TossApiFirstLiveSmokePolicy,
            TossApiFirstLiveSmokeCredentialPresence,
            TossApiFirstLiveSmokeEndpointCandidate,
            TossApiFirstLiveSmokeRuntimeApproval,
            TossApiFirstLiveSmokeRequestPlan,
            TossApiFirstLiveSmokeHttpResult,
            TossApiFirstLiveSmokeDecision,
            TossApiFirstLiveSmokeResult,
            TossApiFirstLiveSmokeValidationResult,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(is_dataclass(model))
                self.assertTrue(model.__dataclass_params__.frozen)

    def test_policy_allows_only_gated_readonly_market_data_smoke(self) -> None:
        policy = build_toss_api_first_live_smoke_policy()

        self.assertEqual(policy.smoke_version, "MS-16.00")
        self.assertTrue(policy.first_live_smoke_only)
        self.assertTrue(policy.readonly_market_data_only)
        self.assertTrue(policy.credential_request_allowed_in_this_stage)
        self.assertTrue(policy.process_env_read_allowed_for_allowed_names_only)
        self.assertTrue(policy.redacted_diagnostics_only)
        self.assertTrue(policy.live_http_allowed_only_when_runtime_approved)
        for flag in (
            "credential_value_output_allowed",
            "credential_commit_allowed",
            "env_file_read_allowed",
            "oauth_token_issuance_allowed",
            "access_token_required",
            "authorization_bearer_output_allowed",
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
            "raw_request_output_allowed",
            "raw_response_output_allowed",
            "default_runtime_approved",
        ):
            self.assertFalse(getattr(policy, flag), flag)

    def test_credential_presence_exposes_names_and_booleans_only(self) -> None:
        missing = read_toss_api_first_live_smoke_credential_presence(environ={})
        present = read_toss_api_first_live_smoke_credential_presence(
            environ={
                "AI_STOCK_TOSS_API_KEY": "local-placeholder-key",
                "AI_STOCK_TOSS_API_SECRET": "local-placeholder-secret",
            }
        )

        self.assertEqual(missing.required_env_names, ALLOWED_ENV_NAMES)
        self.assertFalse(missing.api_key_present)
        self.assertFalse(missing.api_secret_present)
        self.assertFalse(missing.all_required_credentials_present)
        self.assertEqual(
            missing.missing_env_names_redacted,
            ("missing_required_name_redacted", "missing_required_name_redacted"),
        )
        self.assertTrue(present.api_key_present)
        self.assertTrue(present.api_secret_present)
        self.assertTrue(present.all_required_credentials_present)
        self.assertNotIn("local-placeholder-key", repr(present))
        self.assertNotIn("local-placeholder-secret", repr(present))

    def test_default_run_is_blocked_dry_run_without_live_http(self) -> None:
        result = run_toss_api_first_live_smoke(
            credential_presence=read_toss_api_first_live_smoke_credential_presence(
                environ={}
            )
        )

        self.assertTrue(result.passed)
        self.assertTrue(result.blocked)
        self.assertFalse(result.http_result.attempted)
        self.assertFalse(result.decision.live_http_attempted)
        self.assertIn("runtime_approval_missing", result.decision.blocking_reasons)
        self.assertIn(
            "required_credential_presence_missing",
            result.decision.blocking_reasons,
        )
        self.assertIn("endpoint_not_confirmed", result.decision.blocking_reasons)

    def test_missing_runtime_approval_prevents_executor_call(self) -> None:
        calls: list[TossApiFirstLiveSmokeRequestPlan] = []
        result = run_toss_api_first_live_smoke(
            credential_presence=_present_credentials(),
            endpoint_candidate=_confirmed_readonly_endpoint(),
            executor=lambda plan: calls.append(plan) or _safe_http_result(),
        )

        self.assertEqual(calls, [])
        self.assertTrue(result.blocked)
        self.assertFalse(result.decision.live_http_attempted)
        self.assertIn("runtime_approval_missing", result.decision.blocking_reasons)

    def test_missing_credentials_prevents_executor_call(self) -> None:
        calls: list[TossApiFirstLiveSmokeRequestPlan] = []
        result = run_toss_api_first_live_smoke(
            credential_presence=read_toss_api_first_live_smoke_credential_presence(
                environ={}
            ),
            endpoint_candidate=_confirmed_readonly_endpoint(),
            runtime_approval=_full_runtime_approval(),
            executor=lambda plan: calls.append(plan) or _safe_http_result(),
        )

        self.assertEqual(calls, [])
        self.assertTrue(result.blocked)
        self.assertIn(
            "required_credential_presence_missing",
            result.decision.blocking_reasons,
        )

    def test_unconfirmed_endpoint_prevents_executor_call(self) -> None:
        calls: list[TossApiFirstLiveSmokeRequestPlan] = []
        result = run_toss_api_first_live_smoke(
            credential_presence=_present_credentials(),
            runtime_approval=_full_runtime_approval(),
            executor=lambda plan: calls.append(plan) or _safe_http_result(),
        )

        self.assertEqual(calls, [])
        self.assertTrue(result.blocked)
        self.assertIn("endpoint_not_confirmed", result.decision.blocking_reasons)

    def test_fake_executor_attempted_case_is_redacted_and_readonly(self) -> None:
        calls: list[TossApiFirstLiveSmokeRequestPlan] = []

        def fake_executor(
            plan: TossApiFirstLiveSmokeRequestPlan,
        ) -> TossApiFirstLiveSmokeHttpResult:
            calls.append(plan)
            return _safe_http_result()

        result = run_toss_api_first_live_smoke(
            credential_presence=_present_credentials(),
            endpoint_candidate=_confirmed_readonly_endpoint(),
            runtime_approval=_full_runtime_approval(),
            executor=fake_executor,
        )

        self.assertEqual(len(calls), 1)
        self.assertTrue(result.passed)
        self.assertFalse(result.blocked)
        self.assertTrue(result.http_result.attempted)
        self.assertEqual(result.http_result.status_code, 200)
        self.assertEqual(result.http_result.response_shape_summary, ("object_shape",))
        self.assertTrue(result.decision.live_http_attempted)
        self.assertTrue(result.decision.readonly_scope_confirmed)
        self.assertFalse(result.decision.account_seq_used)
        self.assertFalse(result.decision.order_scope_used)
        self.assertFalse(result.decision.account_balance_fills_scope_used)
        self.assertFalse(result.decision.raw_request_output)
        self.assertFalse(result.decision.raw_response_output)
        self.assertTrue(result.decision.credentials_redacted)
        self.assertTrue(result.decision.result_safe_to_report)
        self.assertFalse(result.decision.openai_key_used)
        self.assertFalse(result.decision.llm_used)
        self.assertFalse(result.decision.db_written)
        self.assertFalse(result.decision.streamlit_used)
        self.assertFalse(result.decision.recommendation_generated)
        self.assertFalse(result.decision.ranking_generated)
        self.assertFalse(result.decision.buy_sell_hold_generated)

    def test_request_plan_is_redacted(self) -> None:
        plan = build_toss_api_first_live_smoke_request_plan(
            _present_credentials(),
            _confirmed_readonly_endpoint(),
        )

        self.assertEqual(plan.method, "GET")
        self.assertTrue(plan.readonly)
        self.assertTrue(plan.market_data_only)
        self.assertTrue(plan.credential_attached)
        self.assertTrue(plan.headers_redacted)
        self.assertTrue(plan.body_redacted)
        self.assertFalse(plan.raw_request_output_allowed)

    def test_preflight_reuses_ms15_03_timing_gate(self) -> None:
        self.assertTrue(run_toss_api_credential_request_timing_preflight_checks().passed)

        result = run_toss_api_first_live_smoke_preflight_checks()

        self.assertTrue(result.passed, result.failures)
        self.assertIn("first_readonly_live_smoke", "_".join(result.diagnostics))

    def test_validation_blocks_forbidden_safe_diagnostics(self) -> None:
        result = run_toss_api_first_live_smoke(
            credential_presence=_present_credentials(),
            endpoint_candidate=_confirmed_readonly_endpoint(),
            runtime_approval=_full_runtime_approval(),
            executor=lambda _plan: TossApiFirstLiveSmokeHttpResult(
                attempted=True,
                status_code=200,
                success=True,
                error_category=None,
                response_shape_summary=("raw_response",),
                elapsed_ms=1,
                redacted_diagnostics=("authorization",),
            ),
        )

        validation = validate_toss_api_first_live_smoke_result(result)

        self.assertFalse(validation.passed)

    def test_safe_diagnostics_do_not_expose_forbidden_text(self) -> None:
        result = run_toss_api_first_live_smoke(
            credential_presence=_present_credentials(),
            endpoint_candidate=_confirmed_readonly_endpoint(),
            runtime_approval=_full_runtime_approval(),
            executor=lambda _plan: _safe_http_result(),
        )
        diagnostic_text = " ".join(
            (
                *result.safe_diagnostics,
                *result.http_result.redacted_diagnostics,
                *result.http_result.response_shape_summary,
                result.decision.safe_message,
            )
        ).casefold()

        for forbidden in FORBIDDEN_SAFE_DIAGNOSTIC_TEXT:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden.casefold(), diagnostic_text)

    def test_source_has_only_allowed_runtime_dependencies(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")

        for forbidden in (
            "import requests",
            "import httpx",
            "import aiohttp",
            "from dotenv",
            "import dotenv",
            "os.getenv",
            "sqlite3",
            "import streamlit",
            "import openai",
            "read_text(",
            "write_text(",
            ".env.local",
            ".env.example",
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)
        self.assertEqual(source.count("os.environ.get"), 1)
        self.assertIn("urllib.request", source)

    def test_endpoint_candidates_default_to_blocked_until_confirmed(self) -> None:
        candidates = build_toss_api_first_live_smoke_endpoint_candidates()

        self.assertEqual(len(candidates), 1)
        candidate = candidates[0]
        self.assertTrue(candidate.readonly)
        self.assertTrue(candidate.market_data_only)
        self.assertFalse(candidate.requires_account_seq)
        self.assertFalse(candidate.requires_order_scope)
        self.assertFalse(candidate.requires_account_balance_fills)
        self.assertFalse(candidate.allows_raw_payload_output)
        self.assertFalse(candidate.endpoint_confirmed)
        self.assertFalse(candidate.live_http_executable_without_oauth)


def _present_credentials() -> TossApiFirstLiveSmokeCredentialPresence:
    return read_toss_api_first_live_smoke_credential_presence(
        environ={
            "AI_STOCK_TOSS_API_KEY": "local-placeholder-key",
            "AI_STOCK_TOSS_API_SECRET": "local-placeholder-secret",
        }
    )


def _confirmed_readonly_endpoint() -> TossApiFirstLiveSmokeEndpointCandidate:
    return TossApiFirstLiveSmokeEndpointCandidate(
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
    )


def _full_runtime_approval() -> TossApiFirstLiveSmokeRuntimeApproval:
    return build_toss_api_first_live_smoke_runtime_approval(
        explicit_user_approved_ms_16_00=True,
        runtime_live_http_approved=True,
        credential_request_approved=True,
        readonly_scope_confirmed=True,
        raw_output_block_confirmed=True,
        no_account_scope_confirmed=True,
        no_order_scope_confirmed=True,
    )


def _safe_http_result() -> TossApiFirstLiveSmokeHttpResult:
    return TossApiFirstLiveSmokeHttpResult(
        attempted=True,
        status_code=200,
        success=True,
        error_category=None,
        response_shape_summary=("object_shape",),
        elapsed_ms=1,
        redacted_diagnostics=("shape_only",),
    )


if __name__ == "__main__":
    unittest.main()
