"""Tests for MS-16.02 confirmed read-only endpoint selection."""

from dataclasses import is_dataclass, replace
from pathlib import Path
import unittest

from ai_stock.clients import (
    TossApiReadOnlyEndpointCandidate,
    TossApiReadOnlyEndpointEvidence,
    TossApiReadOnlyEndpointSelectionDecision,
    TossApiReadOnlyEndpointSelectionPolicy,
    TossApiReadOnlyEndpointSelectionResult,
    TossApiReadOnlyEndpointSelectionValidationResult,
    build_toss_api_readonly_endpoint_candidates,
    build_toss_api_readonly_endpoint_evidence,
    build_toss_api_readonly_endpoint_selection_policy,
    evaluate_toss_api_readonly_endpoint_selection_decision,
    run_toss_api_first_live_smoke_preflight_checks,
    run_toss_api_live_smoke_result_hardening_preflight_checks,
    run_toss_api_readonly_endpoint_selection,
    run_toss_api_readonly_endpoint_selection_preflight_checks,
    validate_toss_api_readonly_endpoint_selection_result,
)


MODULE_PATH = Path("src/ai_stock/clients/toss_api_readonly_endpoint_selection.py")
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


class TossApiReadOnlyEndpointSelectionTests(unittest.TestCase):
    def test_selection_dataclasses_are_frozen(self) -> None:
        for model in (
            TossApiReadOnlyEndpointSelectionPolicy,
            TossApiReadOnlyEndpointEvidence,
            TossApiReadOnlyEndpointCandidate,
            TossApiReadOnlyEndpointSelectionDecision,
            TossApiReadOnlyEndpointSelectionResult,
            TossApiReadOnlyEndpointSelectionValidationResult,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(is_dataclass(model))
                self.assertTrue(model.__dataclass_params__.frozen)

    def test_selection_policy_is_closed_to_live_runtime(self) -> None:
        policy = build_toss_api_readonly_endpoint_selection_policy()

        self.assertEqual(policy.selection_version, "MS-16.02")
        for flag in (
            "endpoint_selection_only",
            "endpoint_must_be_confirmed",
            "readonly_required",
            "market_data_or_public_required",
            "redacted_diagnostics_only",
        ):
            self.assertTrue(getattr(policy, flag), flag)
        for flag in (
            "live_http_execution_allowed",
            "credential_request_allowed",
            "credential_value_output_allowed",
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

    def test_ms16_preflights_are_reused(self) -> None:
        self.assertTrue(run_toss_api_first_live_smoke_preflight_checks().passed)
        self.assertTrue(
            run_toss_api_live_smoke_result_hardening_preflight_checks().passed
        )

        result = run_toss_api_readonly_endpoint_selection_preflight_checks()

        self.assertTrue(result.passed, result.failures)

    def test_default_candidate_is_unconfirmed_and_selection_blocked(self) -> None:
        result = run_toss_api_readonly_endpoint_selection()

        self.assertTrue(result.passed, result)
        self.assertEqual(len(result.candidates), 1)
        self.assertFalse(result.candidates[0].endpoint_confirmed)
        self.assertTrue(result.decision.endpoint_selection_invocation_allowed)
        self.assertTrue(result.decision.ms_16_00_preflight_passed)
        self.assertTrue(result.decision.ms_16_01_hardening_passed)
        self.assertIsNone(result.decision.selected_endpoint_id)
        self.assertIsNone(result.decision.selected_endpoint_label)
        self.assertFalse(result.decision.selected_endpoint_confirmed)
        self.assertTrue(result.decision.selection_blocked)
        self.assertEqual(result.decision.blocking_reasons, ("candidate_ineligible",))

    def test_confirmed_readonly_market_data_candidate_can_be_selected(self) -> None:
        candidate = _confirmed_candidate()
        result = run_toss_api_readonly_endpoint_selection((candidate,))

        self.assertTrue(result.passed, result)
        self.assertFalse(result.decision.selection_blocked)
        self.assertEqual(
            result.decision.selected_endpoint_id,
            "symbolic_confirmed_readonly_market_data_candidate",
        )
        self.assertEqual(
            result.decision.selected_endpoint_label,
            "confirmed_readonly_market_data_candidate",
        )
        self.assertTrue(result.decision.selected_endpoint_confirmed)
        self.assertTrue(candidate.readonly)
        self.assertTrue(candidate.market_data_only)
        self.assertTrue(candidate.public_or_market_data)
        self.assertFalse(candidate.requires_account_seq)
        self.assertFalse(candidate.requires_order_scope)
        self.assertFalse(candidate.requires_account_balance_fills)
        self.assertFalse(candidate.requires_oauth_token)
        self.assertFalse(candidate.allows_raw_payload_output)

    def test_required_scopes_and_oauth_candidates_are_rejected(self) -> None:
        cases = (
            replace(_confirmed_candidate(), requires_account_seq=True),
            replace(_confirmed_candidate(), requires_order_scope=True),
            replace(_confirmed_candidate(), requires_account_balance_fills=True),
            replace(_confirmed_candidate(), requires_oauth_token=True),
            replace(_confirmed_candidate(), allows_raw_payload_output=True),
        )

        for candidate in cases:
            with self.subTest(candidate=candidate):
                result = run_toss_api_readonly_endpoint_selection((candidate,))
                self.assertTrue(result.passed, result)
                self.assertTrue(result.decision.selection_blocked)
                self.assertIsNone(result.decision.selected_endpoint_id)
                self.assertFalse(result.decision.selected_endpoint_confirmed)

    def test_decision_always_keeps_runtime_gates_closed(self) -> None:
        decision = evaluate_toss_api_readonly_endpoint_selection_decision(
            (_confirmed_candidate(),)
        )

        self.assertFalse(decision.live_http_execution_allowed_now)
        self.assertFalse(decision.credential_request_allowed_now)
        self.assertFalse(decision.oauth_allowed_now)
        self.assertFalse(decision.token_issuance_allowed_now)
        self.assertFalse(decision.account_seq_allowed_now)
        self.assertFalse(decision.order_allowed_now)
        self.assertFalse(decision.account_data_allowed_now)
        self.assertFalse(decision.balance_allowed_now)
        self.assertFalse(decision.fills_allowed_now)
        self.assertFalse(decision.openai_key_allowed_now)
        self.assertFalse(decision.llm_allowed_now)
        self.assertFalse(decision.db_write_allowed_now)
        self.assertFalse(decision.streamlit_allowed_now)
        self.assertFalse(decision.recommendation_allowed_now)
        self.assertFalse(decision.ranking_allowed_now)
        self.assertFalse(decision.buy_sell_hold_allowed_now)
        self.assertFalse(decision.raw_request_output_allowed)
        self.assertFalse(decision.raw_response_output_allowed)
        self.assertFalse(decision.endpoint_full_url_output_allowed)

    def test_safe_diagnostics_do_not_expose_forbidden_terms_or_full_url(self) -> None:
        result = run_toss_api_readonly_endpoint_selection((_confirmed_candidate(),))
        safe_text = " ".join(
            (
                result.safe_message,
                *result.safe_diagnostics,
                result.decision.selected_endpoint_id or "",
                result.decision.selected_endpoint_label or "",
            )
        ).casefold()

        self.assertNotIn("/", safe_text)
        self.assertNotIn("http:", safe_text)
        self.assertNotIn("https:", safe_text)
        for forbidden in FORBIDDEN_SAFE_OUTPUT_TEXT:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden.casefold(), safe_text)

    def test_forbidden_output_validation_blocks_unsafe_safe_diagnostics(self) -> None:
        result = run_toss_api_readonly_endpoint_selection()
        unsafe = replace(
            result,
            safe_diagnostics=(
                *result.safe_diagnostics,
                "authorization bearer synthetic token",
            ),
        )

        validation = validate_toss_api_readonly_endpoint_selection_result(unsafe)

        self.assertFalse(validation.passed)
        self.assertIn("forbidden_safe_output_fragment_exposed", validation.failures)

    def test_endpoint_full_url_output_is_blocked_by_validation(self) -> None:
        result = run_toss_api_readonly_endpoint_selection()
        unsafe = replace(
            result,
            safe_diagnostics=(*result.safe_diagnostics, "endpoint_path=/unsafe"),
        )

        validation = validate_toss_api_readonly_endpoint_selection_result(unsafe)

        self.assertFalse(validation.passed)
        self.assertIn("endpoint_full_url_or_path_exposed", validation.failures)

    def test_selection_result_and_decision_are_deterministic(self) -> None:
        candidates = (_confirmed_candidate(),)

        self.assertEqual(
            evaluate_toss_api_readonly_endpoint_selection_decision(candidates),
            evaluate_toss_api_readonly_endpoint_selection_decision(candidates),
        )
        self.assertEqual(
            run_toss_api_readonly_endpoint_selection(candidates),
            run_toss_api_readonly_endpoint_selection(candidates),
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


def _confirmed_evidence() -> TossApiReadOnlyEndpointEvidence:
    return build_toss_api_readonly_endpoint_evidence(
        evidence_id="confirmed_readonly_market_data_evidence",
        source_label="project_symbolic_contract_reference",
        readonly_confirmed=True,
        market_data_or_public_confirmed=True,
        account_seq_not_required_confirmed=True,
        order_scope_not_required_confirmed=True,
        account_balance_fills_not_required_confirmed=True,
        oauth_not_required_for_smoke_confirmed=True,
        raw_output_block_confirmed=True,
        confidence_label="confirmed_symbolic_contract",
    )


def _confirmed_candidate() -> TossApiReadOnlyEndpointCandidate:
    return build_toss_api_readonly_endpoint_candidates(_confirmed_evidence())[0].__class__(
        endpoint_id="symbolic_confirmed_readonly_market_data_candidate",
        endpoint_label="confirmed_readonly_market_data_candidate",
        endpoint_scope="readonly_market_data_public_symbolic",
        readonly=True,
        market_data_only=True,
        public_or_market_data=True,
        requires_account_seq=False,
        requires_order_scope=False,
        requires_account_balance_fills=False,
        requires_oauth_token=False,
        live_http_executable_without_oauth=True,
        endpoint_confirmed=True,
        allows_raw_payload_output=False,
        evidence=_confirmed_evidence(),
    )


if __name__ == "__main__":
    unittest.main()
