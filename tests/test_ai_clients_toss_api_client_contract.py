"""Tests for the MS-14.00 Toss API client contract preflight."""

from dataclasses import fields, is_dataclass
import ast
from pathlib import Path
import unittest

from ai_stock.clients import (
    TossApiClientContractPolicy,
    TossApiCredentialNamePolicy,
    TossApiEndpointContract,
    TossApiErrorContract,
    TossApiExternalCapabilityFlags,
    TossApiRedactionPolicy,
    TossApiRequestContract,
    TossApiResponseContract,
    build_symbolic_toss_api_endpoint_contracts,
    build_toss_api_client_contract_policy,
    build_toss_api_credential_name_policy,
    build_toss_api_error_contracts,
    build_toss_api_external_capability_flags,
    build_toss_api_redaction_policy,
    build_toss_api_request_contract,
    build_toss_api_response_contract,
    redact_mapping,
    redact_sensitive_value,
    run_toss_api_client_contract_preflight_checks,
    validate_no_sensitive_output,
    validate_toss_api_client_contract_policy,
    validate_toss_api_endpoint_contract,
    validate_toss_api_request_contract,
    validate_toss_api_response_contract,
)


MODULE_PATH = Path("src/ai_stock/clients/toss_api_client_contract.py")


class TossApiClientContractPreflightTests(unittest.TestCase):
    def test_contract_dataclasses_are_frozen_shapes(self) -> None:
        for model in (
            TossApiClientContractPolicy,
            TossApiCredentialNamePolicy,
            TossApiEndpointContract,
            TossApiRequestContract,
            TossApiResponseContract,
            TossApiErrorContract,
            TossApiRedactionPolicy,
            TossApiExternalCapabilityFlags,
        ):
            with self.subTest(model=model.__name__):
                self.assertTrue(is_dataclass(model))
                self.assertTrue(model.__dataclass_params__.frozen)

    def test_policy_creation_has_required_no_io_flags(self) -> None:
        policy = build_toss_api_client_contract_policy()

        self.assertEqual(policy.contract_version, "MS-14.00")
        self.assertEqual(
            policy.contract_scope,
            "pure_no_io_toss_api_client_contract_preflight",
        )
        for flag in (
            "no_network",
            "no_oauth",
            "no_credentials",
            "no_account_seq",
            "no_orders",
            "no_account_assets",
            "no_balance",
            "no_fills",
            "no_db",
            "no_file_io",
            "no_streamlit",
            "no_llm",
            "no_recommendation",
            "no_ranking",
        ):
            self.assertTrue(getattr(policy, flag), flag)

    def test_credential_name_policy_has_no_values_or_loaders(self) -> None:
        credential_policy = build_toss_api_credential_name_policy()

        self.assertFalse(credential_policy.required_now)
        self.assertFalse(credential_policy.read_from_env_now)
        self.assertFalse(credential_policy.read_from_file_now)
        self.assertFalse(credential_policy.print_allowed)
        self.assertFalse(credential_policy.raw_value_allowed)
        self.assertTrue(credential_policy.mask_required)
        self.assertTrue(
            all(name.endswith("_name") for name in credential_policy.credential_field_names)
        )

    def test_external_capability_flags_are_all_false(self) -> None:
        flags = build_toss_api_external_capability_flags()

        self.assertTrue(fields(TossApiExternalCapabilityFlags))
        self.assertFalse(any(flags.__dict__.values()))
        self.assertFalse(flags.live_http_ready)
        self.assertFalse(flags.oauth_ready)
        self.assertFalse(flags.credential_required_now)
        self.assertFalse(flags.account_seq_required_now)
        self.assertFalse(flags.order_required_now)
        self.assertFalse(flags.db_required_now)
        self.assertFalse(flags.streamlit_required)
        self.assertFalse(flags.http_smoke_required)

    def test_endpoint_contracts_are_symbolic_only(self) -> None:
        endpoints = build_symbolic_toss_api_endpoint_contracts()
        policy = build_toss_api_client_contract_policy()

        self.assertGreaterEqual(len(endpoints), 2)
        for endpoint in endpoints:
            with self.subTest(endpoint=endpoint.endpoint_id):
                self.assertIn(endpoint.endpoint_kind, policy.allowed_endpoint_kinds)
                self.assertTrue(endpoint.symbolic_only)
                self.assertTrue(endpoint.allowed)
                self.assertFalse(endpoint.live_http_ready)
                self.assertFalse(endpoint.fake_transport_ready)
                self.assertFalse(endpoint.oauth_ready)
                self.assertFalse(endpoint.account_seq_required_now)
                self.assertFalse(endpoint.order_required_now)
                rendered = repr(endpoint)
                self.assertNotIn("http://", rendered)
                self.assertNotIn("https://", rendered)
                self.assertNotIn("/oauth", rendered)
                self.assertNotIn("/order", rendered)
                self.assertNotIn("/account", rendered)

    def test_request_contract_is_dry_run_only(self) -> None:
        request_contract = build_toss_api_request_contract()

        self.assertEqual(request_contract.method, "SYMBOLIC_METHOD")
        self.assertTrue(request_contract.redaction_required)
        self.assertTrue(request_contract.dry_run_only)
        self.assertFalse(request_contract.live_call_allowed)
        self.assertNotIn("authorization", request_contract.header_shape)
        self.assertNotIn("accountSeq", request_contract.query_shape)
        self.assertNotIn("order_id", request_contract.body_shape)

    def test_response_contract_blocks_raw_payloads(self) -> None:
        response_contract = build_toss_api_response_contract()

        self.assertFalse(response_contract.raw_payload_allowed)
        self.assertIn("raw_payload_blocked", response_contract.diagnostics)
        self.assertNotIn("raw_response", response_contract.redacted_body_preview)
        self.assertNotIn("access_token", response_contract.redacted_body_preview)
        self.assertNotIn("accountSeq", response_contract.redacted_body_preview)

    def test_error_contract_kinds_are_complete_and_safe(self) -> None:
        error_contracts = build_toss_api_error_contracts()
        error_kinds = {contract.error_kind for contract in error_contracts}

        self.assertEqual(
            error_kinds,
            {
                "configuration_missing",
                "credential_unavailable",
                "oauth_not_allowed",
                "network_not_allowed",
                "endpoint_not_allowed",
                "account_seq_not_allowed",
                "order_not_allowed",
                "account_asset_not_allowed",
                "raw_payload_blocked",
                "redaction_failed",
                "unknown_contract_error",
            },
        )
        self.assertTrue(all(contract.safe_to_display for contract in error_contracts))
        self.assertFalse(any(contract.raw_payload_allowed for contract in error_contracts))

    def test_redaction_policy_and_helpers_do_not_return_sensitive_values(self) -> None:
        policy = build_toss_api_redaction_policy()

        for field_name in (
            "access_token",
            "authorization",
            "api_key",
            "secret_key",
            "accountSeq",
            "raw_response",
            ".env.local",
        ):
            with self.subTest(field_name=field_name):
                result = redact_sensitive_value(
                    field_name,
                    "do-not-return-this-value",
                    policy,
                )
                self.assertEqual(result.value, policy.redaction_placeholder)
                self.assertTrue(result.redacted)
                self.assertNotIn("do-not-return-this-value", repr(result))

        redacted = redact_mapping(
            {
                "access_token": "token-value",
                "accountSeq": "account-seq-value",
                "symbolic_status": "ok",
            },
            policy,
        )
        self.assertEqual(redacted["access_token"], policy.redaction_placeholder)
        self.assertEqual(redacted["accountSeq"], policy.redaction_placeholder)
        self.assertEqual(redacted["symbolic_status"], "ok")

    def test_validate_no_sensitive_output_detects_unredacted_sensitive_fields(
        self,
    ) -> None:
        policy = build_toss_api_redaction_policy()
        valid_result = validate_no_sensitive_output(
            {"access_token": policy.redaction_placeholder},
            policy,
        )
        invalid_result = validate_no_sensitive_output(
            {"access_token": "visible-token-value"},
            policy,
        )

        self.assertTrue(valid_result.passed)
        self.assertFalse(invalid_result.passed)
        self.assertIn("sensitive_field_exposed:access_token", invalid_result.failures)

    def test_validation_helpers_pass_for_default_contract(self) -> None:
        policy = build_toss_api_client_contract_policy()
        endpoints = build_symbolic_toss_api_endpoint_contracts()
        endpoint_results = tuple(
            validate_toss_api_endpoint_contract(endpoint, policy)
            for endpoint in endpoints
        )
        request_result = validate_toss_api_request_contract(
            build_toss_api_request_contract(), policy
        )
        response_result = validate_toss_api_response_contract(
            build_toss_api_response_contract(), policy
        )
        policy_result = validate_toss_api_client_contract_policy(policy)
        runner_result = run_toss_api_client_contract_preflight_checks()

        self.assertTrue(all(result.passed for result in endpoint_results))
        self.assertTrue(request_result.passed)
        self.assertTrue(response_result.passed)
        self.assertTrue(policy_result.passed)
        self.assertTrue(runner_result.passed)
        self.assertEqual(runner_result.failures, ())

    def test_validation_helpers_fail_on_forbidden_contract_shapes(self) -> None:
        endpoint_result = validate_toss_api_endpoint_contract(
            TossApiEndpointContract(
                endpoint_id="forbidden_oauth_contract",
                endpoint_kind="oauth_token",
                description="forbidden symbolic probe",
                symbolic_only=False,
                allowed=False,
                live_http_ready=True,
                fake_transport_ready=False,
                oauth_ready=True,
                account_seq_required_now=True,
                order_required_now=True,
            )
        )
        request_result = validate_toss_api_request_contract(
            TossApiRequestContract(
                method="SYMBOLIC_METHOD",
                endpoint_kind="contract_only_endpoint_id",
                query_shape=("accountSeq",),
                body_shape=("order_id",),
                header_shape=("authorization",),
                timeout_policy="shape_only",
                retry_policy="shape_only",
                idempotency_policy="shape_only",
                redaction_required=False,
                dry_run_only=False,
                live_call_allowed=True,
            )
        )
        response_result = validate_toss_api_response_contract(
            TossApiResponseContract(
                normalized_status="contract_shape_only",
                status_code_shape="symbolic_status_code",
                response_kind="normalized_contract_response",
                normalized_body_shape=("redacted_body_preview",),
                error_shape=("error_kind", "safe_message"),
                redacted_body_preview={"access_token": "visible-token"},
                diagnostics=(),
                raw_payload_allowed=True,
            )
        )

        self.assertFalse(endpoint_result.passed)
        self.assertFalse(request_result.passed)
        self.assertFalse(response_result.passed)

    def test_contract_module_has_no_forbidden_imports_or_runtime_access(self) -> None:
        source = MODULE_PATH.read_text(encoding="utf-8")
        tree = ast.parse(source)

        imported_modules = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)

        for forbidden_module in (
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
        ):
            self.assertNotIn(forbidden_module, imported_modules)

        forbidden_calls_or_attributes = (
            "os.environ",
            "os.getenv",
            "Path(",
            "open(",
            "read_text(",
            "read_bytes(",
            "write_text(",
            "write_bytes(",
            "connect(",
            "send(",
            ".get(",
            ".post(",
            ".request(",
            "Bearer ",
        )
        for forbidden in forbidden_calls_or_attributes:
            self.assertNotIn(forbidden, source)

    def test_no_recommendation_ranking_action_or_trade_contract_output(self) -> None:
        runner_result = run_toss_api_client_contract_preflight_checks()
        rendered = repr(runner_result).casefold()

        for forbidden in (
            "buy_signal",
            "sell_signal",
            "hold_signal",
            "target_price_value",
            "expected_return_value",
            "profit_probability_value",
            "ranking_position_value",
            "recommendation_result",
            "trade_action",
        ):
            self.assertNotIn(forbidden, rendered)


if __name__ == "__main__":
    unittest.main()
