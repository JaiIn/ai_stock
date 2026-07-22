"""Tests for the MS-15.00 read-only live smoke planning gate."""

from dataclasses import fields, is_dataclass
import ast
from pathlib import Path
import re
import unittest

from ai_stock.clients import (
    TossApiReadOnlyLiveSmokeAllowlist,
    TossApiReadOnlyLiveSmokeBlocklist,
    TossApiReadOnlyLiveSmokeExecutionGate,
    TossApiReadOnlyLiveSmokePlan,
    TossApiReadOnlyLiveSmokePlanningPolicy,
    TossApiReadOnlyLiveSmokePlanningValidationResult,
    TossApiReadOnlyLiveSmokePrerequisite,
    TossApiReadOnlyLiveSmokeTarget,
    build_toss_api_external_capability_flags,
    build_toss_api_readonly_live_smoke_allowlist,
    build_toss_api_readonly_live_smoke_blocklist,
    build_toss_api_readonly_live_smoke_execution_gate,
    build_toss_api_readonly_live_smoke_plan,
    build_toss_api_readonly_live_smoke_planning_policy,
    build_toss_api_readonly_live_smoke_prerequisites,
    build_toss_api_readonly_live_smoke_targets,
    run_toss_api_client_contract_preflight_checks,
    run_toss_api_config_guardrail_preflight_checks,
    run_toss_api_fake_transport_preflight_checks,
    run_toss_api_live_readiness_preflight_checks,
    run_toss_api_no_secret_dry_run,
    run_toss_api_readonly_live_smoke_planning_preflight_checks,
    validate_toss_api_readonly_live_smoke_plan,
)


MODULE_PATH = Path("src/ai_stock/clients/toss_api_live_smoke_plan.py")
EXPECTED_TARGET_IDS = (
    "symbolic_market_data_readonly_smoke",
    "symbolic_rate_limit_handling_smoke",
    "symbolic_redaction_probe_smoke",
)
EXPECTED_ALLOWLIST = (
    "symbolic_readonly_market_data_target",
    "planning_documentation_only",
    "safe_redacted_summary_only",
    "explicit_future_approval_required",
)
EXPECTED_BLOCKLIST = (
    "live_execution_now",
    "secret_request_now",
    "oauth_now",
    "token_issuance_now",
    "account_seq_now",
    "order_or_account_data_now",
    "db_or_file_io_now",
    "streamlit_or_llm_now",
    "recommendation_or_ranking_now",
)
EXPECTED_PREREQUISITES = (
    "ms1400_contract_preflight_passed",
    "ms1401_fake_transport_preflight_passed",
    "ms1402_config_guardrail_preflight_passed",
    "ms1403_live_readiness_preflight_passed",
    "ms1403_no_secret_dry_run_passed",
    "explicit_live_stage_approval_not_present",
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


class TossApiReadOnlyLiveSmokePlanTests(unittest.TestCase):
    def test_planning_dataclasses_are_frozen_shapes(self) -> None:
        for model in (
            TossApiReadOnlyLiveSmokePlanningPolicy,
            TossApiReadOnlyLiveSmokeTarget,
            TossApiReadOnlyLiveSmokeAllowlist,
            TossApiReadOnlyLiveSmokeBlocklist,
            TossApiReadOnlyLiveSmokePrerequisite,
            TossApiReadOnlyLiveSmokeExecutionGate,
            TossApiReadOnlyLiveSmokePlan,
            TossApiReadOnlyLiveSmokePlanningValidationResult,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(is_dataclass(model))
                self.assertTrue(model.__dataclass_params__.frozen)

    def test_planning_policy_is_no_io_and_closed_now(self) -> None:
        policy = build_toss_api_readonly_live_smoke_planning_policy()

        self.assertEqual(policy.planning_version, "MS-15.00")
        for flag in (
            "planning_only",
            "uses_contract_preflight",
            "uses_fake_transport_preflight",
            "uses_config_guardrail_preflight",
            "uses_live_readiness_preflight",
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
            "live_http_ready",
            "oauth_ready",
            "account_seq_required_now",
            "order_required_now",
            "streamlit_required",
            "http_smoke_required",
        ):
            self.assertFalse(getattr(policy, flag), flag)

    def test_ms14_preflight_layers_are_reused(self) -> None:
        plan = build_toss_api_readonly_live_smoke_plan()

        self.assertEqual(plan.contract_preflight, run_toss_api_client_contract_preflight_checks())
        self.assertEqual(
            plan.fake_transport_preflight,
            run_toss_api_fake_transport_preflight_checks(),
        )
        self.assertEqual(
            plan.config_guardrail_preflight,
            run_toss_api_config_guardrail_preflight_checks(),
        )
        self.assertEqual(
            plan.live_readiness_preflight,
            run_toss_api_live_readiness_preflight_checks(),
        )
        self.assertEqual(plan.no_secret_dry_run, run_toss_api_no_secret_dry_run())

    def test_targets_are_symbolic_readonly_and_planning_only(self) -> None:
        targets = build_toss_api_readonly_live_smoke_targets()

        self.assertEqual(tuple(target.target_id for target in targets), EXPECTED_TARGET_IDS)
        for target in targets:
            with self.subTest(target=target.target_id):
                self.assertTrue(target.target_id.startswith("symbolic_"))
                self.assertTrue(target.readonly)
                self.assertTrue(target.market_data_only)
                self.assertFalse(target.account_data_allowed)
                self.assertFalse(target.order_data_allowed)
                self.assertFalse(target.balance_data_allowed)
                self.assertFalse(target.fills_data_allowed)
                self.assertFalse(target.actual_url_defined)
                self.assertFalse(target.actual_endpoint_path_defined)
                self.assertFalse(target.live_call_allowed_now)
                self.assertTrue(target.planning_only)

    def test_allowlist_blocklist_and_prerequisites(self) -> None:
        allowlist = build_toss_api_readonly_live_smoke_allowlist()
        blocklist = build_toss_api_readonly_live_smoke_blocklist()
        prerequisites = build_toss_api_readonly_live_smoke_prerequisites()

        self.assertEqual(allowlist.allowed_items, EXPECTED_ALLOWLIST)
        self.assertEqual(allowlist.allowed_target_ids, EXPECTED_TARGET_IDS)
        self.assertTrue(allowlist.readonly_only)
        self.assertTrue(allowlist.market_data_only)
        self.assertTrue(allowlist.planning_only)
        self.assertTrue(allowlist.redacted_output_only)

        self.assertEqual(blocklist.blocked_items, EXPECTED_BLOCKLIST)
        self.assertTrue(blocklist.block_live_execution_now)
        self.assertTrue(blocklist.block_credential_request_now)
        self.assertTrue(blocklist.block_oauth_now)
        self.assertTrue(blocklist.block_token_issuance_now)
        self.assertTrue(blocklist.block_account_seq_now)
        self.assertTrue(blocklist.block_order_account_balance_fills_now)
        self.assertTrue(blocklist.block_db_and_file_io_now)
        self.assertTrue(blocklist.block_streamlit_and_llm_now)
        self.assertTrue(blocklist.block_recommendation_ranking_action_now)

        self.assertEqual(
            tuple(prerequisite.prerequisite_id for prerequisite in prerequisites),
            EXPECTED_PREREQUISITES,
        )
        self.assertTrue(all(prerequisite.passed for prerequisite in prerequisites))

    def test_execution_gate_is_deterministic_and_closed(self) -> None:
        prerequisites = build_toss_api_readonly_live_smoke_prerequisites()
        first = build_toss_api_readonly_live_smoke_execution_gate(prerequisites)
        second = build_toss_api_readonly_live_smoke_execution_gate(prerequisites)

        self.assertEqual(first, second)
        self.assertTrue(first.planning_passed)
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
        self.assertTrue(first.explicit_approval_required)

    def test_plan_and_preflight_are_deterministic_and_safe(self) -> None:
        first_plan = build_toss_api_readonly_live_smoke_plan()
        second_plan = build_toss_api_readonly_live_smoke_plan()
        first_preflight = run_toss_api_readonly_live_smoke_planning_preflight_checks()
        second_preflight = run_toss_api_readonly_live_smoke_planning_preflight_checks()

        self.assertEqual(first_plan, second_plan)
        self.assertEqual(first_preflight, second_preflight)
        self.assertTrue(first_preflight.passed, first_preflight.failures)
        self.assertIn("symbolic_readonly_targets_only", first_preflight.diagnostics)
        self.assertIn("live_execution_blocked_now", first_preflight.diagnostics)
        self.assert_no_forbidden_safe_output(first_plan)

    def test_validation_result_confirms_planning_gate(self) -> None:
        result = validate_toss_api_readonly_live_smoke_plan()

        self.assertTrue(result.passed, result.failures)
        self.assertEqual(result.checked_target_ids, EXPECTED_TARGET_IDS)
        self.assertEqual(result.checked_allowlist_items, EXPECTED_ALLOWLIST)
        self.assertEqual(result.checked_blocklist_items, EXPECTED_BLOCKLIST)
        self.assertEqual(result.checked_prerequisites, EXPECTED_PREREQUISITES)
        self.assertIn("planning_passed", result.checked_gate_flags)

    def test_external_capability_flags_remain_false(self) -> None:
        flags = build_toss_api_external_capability_flags()

        self.assertTrue(fields(type(flags)))
        self.assertFalse(any(flags.__dict__.values()))

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
        ):
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden, source)

    def assert_no_forbidden_safe_output(
        self,
        plan: TossApiReadOnlyLiveSmokePlan,
    ) -> None:
        rendered_output = " ".join(
            (
                str(plan.safe_summary),
                str(plan.execution_gate.blocking_reasons),
                str(plan.execution_gate.prerequisite_summary),
            )
        ).casefold()
        output_tokens = set(re.findall(r"[a-z0-9_.]+", rendered_output))
        for forbidden in FORBIDDEN_SAFE_OUTPUT_TEXT:
            with self.subTest(forbidden=forbidden):
                self.assertNotIn(forbidden.casefold(), output_tokens)


if __name__ == "__main__":
    unittest.main()
