"""Tests for MS-16.04 confirmed endpoint evidence update."""

from dataclasses import is_dataclass, replace
from pathlib import Path
import unittest

from ai_stock.clients import (
    TossApiConfirmedEndpointEvidenceCandidate,
    TossApiConfirmedEndpointEvidenceDecision,
    TossApiConfirmedEndpointEvidencePolicy,
    TossApiConfirmedEndpointEvidenceResult,
    TossApiConfirmedEndpointEvidenceSource,
    TossApiConfirmedEndpointEvidenceValidationResult,
    build_toss_api_confirmed_endpoint_evidence_candidates,
    build_toss_api_confirmed_endpoint_evidence_policy,
    build_toss_api_confirmed_endpoint_evidence_sources,
    evaluate_toss_api_confirmed_endpoint_evidence_decision,
    run_toss_api_confirmed_endpoint_evidence_preflight_checks,
    run_toss_api_confirmed_endpoint_evidence_update,
    run_toss_api_first_live_smoke_preflight_checks,
    run_toss_api_live_smoke_operator_rehearsal_preflight_checks,
    run_toss_api_live_smoke_result_hardening_preflight_checks,
    run_toss_api_readonly_endpoint_selection_preflight_checks,
    validate_toss_api_confirmed_endpoint_evidence_result,
)


MODULE_PATH = Path("src/ai_stock/clients/toss_api_confirmed_endpoint_evidence.py")
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


class TossApiConfirmedEndpointEvidenceTests(unittest.TestCase):
    def test_evidence_dataclasses_are_frozen(self) -> None:
        for model in (
            TossApiConfirmedEndpointEvidencePolicy,
            TossApiConfirmedEndpointEvidenceSource,
            TossApiConfirmedEndpointEvidenceCandidate,
            TossApiConfirmedEndpointEvidenceDecision,
            TossApiConfirmedEndpointEvidenceResult,
            TossApiConfirmedEndpointEvidenceValidationResult,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(is_dataclass(model))
                self.assertTrue(model.__dataclass_params__.frozen)

    def test_policy_is_closed_to_runtime_execution(self) -> None:
        policy = build_toss_api_confirmed_endpoint_evidence_policy()

        self.assertEqual(policy.evidence_version, "MS-16.04")
        for flag in (
            "endpoint_evidence_update_only",
            "endpoint_must_be_confirmed",
            "readonly_required",
            "public_or_market_data_required",
            "redacted_diagnostics_only",
        ):
            self.assertTrue(getattr(policy, flag), flag)
        for flag in (
            "live_http_execution_allowed",
            "credential_request_allowed",
            "credential_presence_check_allowed",
            "credential_value_output_allowed",
            "env_read_allowed",
            "raw_request_output_allowed",
            "raw_response_output_allowed",
            "endpoint_full_url_output_allowed",
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

    def test_evidence_source_and_candidate_are_symbolic_and_confirmed(self) -> None:
        sources = build_toss_api_confirmed_endpoint_evidence_sources()
        candidates = build_toss_api_confirmed_endpoint_evidence_candidates(sources)

        self.assertEqual(len(sources), 1)
        self.assertTrue(sources[0].source_available)
        self.assertTrue(sources[0].official_reference_confirmed)
        self.assertTrue(sources[0].project_reference_confirmed)
        self.assertTrue(sources[0].readonly_confirmed)
        self.assertTrue(sources[0].public_or_market_data_confirmed)
        self.assertTrue(sources[0].account_seq_not_required_confirmed)
        self.assertTrue(sources[0].order_scope_not_required_confirmed)
        self.assertTrue(sources[0].account_balance_fills_not_required_confirmed)
        self.assertTrue(sources[0].oauth_token_not_required_confirmed)
        self.assertTrue(sources[0].raw_output_block_confirmed)
        self.assertEqual(len(candidates), 1)
        self.assertTrue(candidates[0].endpoint_confirmed)
        self.assertTrue(candidates[0].readonly)
        self.assertTrue(candidates[0].public_or_market_data)
        self.assertFalse(candidates[0].requires_account_seq)
        self.assertFalse(candidates[0].requires_order_scope)
        self.assertFalse(candidates[0].requires_account_balance_fills)
        self.assertFalse(candidates[0].requires_oauth_token)
        self.assertFalse(candidates[0].allows_raw_payload_output)

    def test_ms16_preflights_are_reused(self) -> None:
        self.assertTrue(run_toss_api_first_live_smoke_preflight_checks().passed)
        self.assertTrue(
            run_toss_api_live_smoke_result_hardening_preflight_checks().passed
        )
        self.assertTrue(run_toss_api_readonly_endpoint_selection_preflight_checks().passed)
        self.assertTrue(
            run_toss_api_live_smoke_operator_rehearsal_preflight_checks().passed
        )

        result = run_toss_api_confirmed_endpoint_evidence_preflight_checks()

        self.assertTrue(result.passed, result.failures)

    def test_default_confirmed_candidate_is_selected(self) -> None:
        result = run_toss_api_confirmed_endpoint_evidence_update()

        self.assertTrue(result.passed, result)
        self.assertFalse(result.decision.selection_blocked)
        self.assertEqual(
            result.decision.selected_endpoint_id,
            "confirmed_prices_single_symbol_readonly_market_data",
        )
        self.assertEqual(
            result.decision.selected_endpoint_label,
            "Prices single-symbol read-only market data",
        )
        self.assertTrue(result.decision.selected_endpoint_confirmed)
        self.assertTrue(result.decision.selected_endpoint_readonly)
        self.assertTrue(result.decision.selected_endpoint_public_or_market_data)
        self.assertFalse(result.decision.selected_endpoint_requires_account_seq)
        self.assertFalse(result.decision.selected_endpoint_requires_order_scope)
        self.assertFalse(
            result.decision.selected_endpoint_requires_account_balance_fills
        )
        self.assertFalse(result.decision.selected_endpoint_requires_oauth_token)
        self.assertFalse(
            result.decision.selected_endpoint_allows_raw_payload_output
        )
        self.assertEqual(result.decision.blocking_reasons, ())
        self.assertEqual(
            result.next_stage,
            "MS-16.05 first actual read-only live HTTP smoke",
        )

    def test_evidence_missing_blocks_selection(self) -> None:
        candidate = replace(_confirmed_candidate(), evidence_sources=())

        result = run_toss_api_confirmed_endpoint_evidence_update((candidate,))

        self.assertTrue(result.passed, result)
        self.assertTrue(result.decision.selection_blocked)
        self.assertIsNone(result.decision.selected_endpoint_id)
        self.assertIn(
            "confirmed_endpoint_evidence_missing",
            result.decision.blocking_reasons,
        )

    def test_ineligible_candidates_are_rejected(self) -> None:
        cases = (
            replace(_confirmed_candidate(), requires_account_seq=True),
            replace(_confirmed_candidate(), requires_order_scope=True),
            replace(_confirmed_candidate(), requires_account_balance_fills=True),
            replace(_confirmed_candidate(), requires_oauth_token=True),
            replace(_confirmed_candidate(), allows_raw_payload_output=True),
            replace(_confirmed_candidate(), endpoint_confirmed=False),
        )

        for candidate in cases:
            with self.subTest(candidate=candidate):
                result = run_toss_api_confirmed_endpoint_evidence_update((candidate,))
                self.assertTrue(result.passed, result)
                self.assertTrue(result.decision.selection_blocked)
                self.assertIsNone(result.decision.selected_endpoint_id)
                self.assertIn("candidate_ineligible", result.decision.blocking_reasons)

    def test_runtime_gates_remain_closed(self) -> None:
        decision = evaluate_toss_api_confirmed_endpoint_evidence_decision()

        self.assertTrue(decision.endpoint_evidence_invocation_allowed)
        self.assertTrue(decision.endpoint_evidence_update_only)
        self.assertTrue(decision.ms_16_00_preflight_passed)
        self.assertTrue(decision.ms_16_01_hardening_passed)
        self.assertTrue(decision.ms_16_02_endpoint_selection_passed)
        self.assertTrue(decision.ms_16_03_operator_rehearsal_passed)
        for flag in (
            "live_http_execution_allowed_now",
            "credential_request_allowed_now",
            "credential_presence_check_allowed_now",
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

    def test_safe_diagnostics_do_not_expose_forbidden_terms_url_or_command(self) -> None:
        result = run_toss_api_confirmed_endpoint_evidence_update()
        safe_text = " ".join((result.safe_message, *result.safe_diagnostics)).casefold()

        self.assertNotIn("/", safe_text)
        self.assertNotIn("http:", safe_text)
        self.assertNotIn("https:", safe_text)
        self.assertNotIn("command", safe_text)
        for forbidden in FORBIDDEN_SAFE_OUTPUT_TEXT:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden.casefold(), safe_text)

    def test_forbidden_output_validation_blocks_unsafe_safe_diagnostics(self) -> None:
        result = run_toss_api_confirmed_endpoint_evidence_update()
        unsafe = replace(
            result,
            safe_diagnostics=(
                *result.safe_diagnostics,
                "authorization bearer synthetic token",
            ),
        )

        validation = validate_toss_api_confirmed_endpoint_evidence_result(unsafe)

        self.assertFalse(validation.passed)
        self.assertIn("forbidden_safe_output_fragment_exposed", validation.failures)

    def test_endpoint_full_url_and_command_are_blocked_by_validation(self) -> None:
        result = run_toss_api_confirmed_endpoint_evidence_update()
        path_result = replace(
            result,
            safe_diagnostics=(*result.safe_diagnostics, "endpoint_path=/unsafe"),
        )
        command_result = replace(
            result,
            safe_diagnostics=(*result.safe_diagnostics, "execution_command=run"),
        )

        self.assertIn(
            "endpoint_full_url_or_path_exposed",
            validate_toss_api_confirmed_endpoint_evidence_result(path_result).failures,
        )
        self.assertIn(
            "execution_command_exposed",
            validate_toss_api_confirmed_endpoint_evidence_result(
                command_result
            ).failures,
        )

    def test_evidence_result_is_deterministic(self) -> None:
        self.assertEqual(
            evaluate_toss_api_confirmed_endpoint_evidence_decision(),
            evaluate_toss_api_confirmed_endpoint_evidence_decision(),
        )
        self.assertEqual(
            run_toss_api_confirmed_endpoint_evidence_update(),
            run_toss_api_confirmed_endpoint_evidence_update(),
        )

    def test_source_has_no_forbidden_io_runtime_or_cli_imports(self) -> None:
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


def _confirmed_candidate() -> TossApiConfirmedEndpointEvidenceCandidate:
    return build_toss_api_confirmed_endpoint_evidence_candidates(
        build_toss_api_confirmed_endpoint_evidence_sources()
    )[0]


if __name__ == "__main__":
    unittest.main()
