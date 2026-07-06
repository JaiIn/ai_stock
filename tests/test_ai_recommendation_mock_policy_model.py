"""Offline tests for the MS-08.02 mock-only recommendation policy model."""

import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import unittest

from ai_stock.recommendation.mock_policy_model import (
    ALLOWED_MOCK_LABELS,
    FORBIDDEN_MOCK_LABELS,
    MockRecommendationInput,
    MockRecommendationLabel,
    build_default_mock_recommendation_policy,
    build_mock_recommendation_result,
    validate_mock_recommendation_policy,
    validate_mock_recommendation_result,
)
from ai_stock.recommendation.safety_preflight import (
    ALLOWED_EXPLANATION_LANGUAGE,
    FORBIDDEN_RECOMMENDATION_LANGUAGE,
    REQUIRED_DISCLAIMERS,
)


class MockRecommendationPolicyModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_default_mock_recommendation_policy()
        self.complete_input = MockRecommendationInput(
            symbol="005930",
            has_stock_info=True,
            has_price_snapshot=True,
            has_candle=True,
            has_exchange_rate=True,
            observation_notes=("caller note one",),
        )

    def test_default_policy_identity_and_immutability(self) -> None:
        self.assertEqual(self.policy.stage_name, "MS-08.02")
        self.assertEqual(self.policy.mode, "mock_only_policy_model")
        self.assertTrue(self.policy.mock_policy_model_allowed)
        with self.assertRaises(FrozenInstanceError):
            self.policy.real_recommendation_allowed = True

    def test_recommendation_advice_and_directives_are_disabled(self) -> None:
        self.assertFalse(self.policy.real_recommendation_allowed)
        self.assertFalse(self.policy.investment_advice_allowed)
        self.assertFalse(self.policy.buy_sell_hold_directive_allowed)
        self.assertFalse(self.policy.real_trade_allowed)

    def test_llm_external_api_and_credentials_are_disabled(self) -> None:
        self.assertFalse(self.policy.llm_call_allowed)
        self.assertFalse(self.policy.external_ai_api_allowed)
        self.assertFalse(self.policy.openai_api_key_required)
        self.assertFalse(self.policy.toss_api_key_required)
        self.assertFalse(self.policy.toss_secret_key_required)

    def test_oauth_live_account_order_and_account_seq_are_disabled(self) -> None:
        self.assertFalse(self.policy.oauth_allowed)
        self.assertFalse(self.policy.live_market_api_allowed)
        self.assertFalse(self.policy.account_api_allowed)
        self.assertFalse(self.policy.order_api_allowed)
        self.assertFalse(self.policy.account_seq_required)

    def test_db_write_and_streamlit_change_are_disabled(self) -> None:
        self.assertFalse(self.policy.db_write_allowed)
        self.assertFalse(self.policy.streamlit_ui_change_allowed)

    def test_policy_reuses_safety_preflight_contracts(self) -> None:
        self.assertEqual(self.policy.required_disclaimers, REQUIRED_DISCLAIMERS)
        self.assertEqual(
            self.policy.forbidden_recommendation_language,
            FORBIDDEN_RECOMMENDATION_LANGUAGE,
        )
        self.assertEqual(
            self.policy.allowed_explanation_language,
            ALLOWED_EXPLANATION_LANGUAGE,
        )
        self.assertEqual(self.policy.allowed_labels, ALLOWED_MOCK_LABELS)
        self.assertEqual(self.policy.forbidden_labels, FORBIDDEN_MOCK_LABELS)

    def test_incomplete_input_returns_insufficient_data(self) -> None:
        recommendation_input = replace(
            self.complete_input,
            has_candle=False,
            completeness_flags=("missing_candle",),
        )
        result = build_mock_recommendation_result(
            recommendation_input,
            self.policy,
        )
        self.assertEqual(
            result.label,
            MockRecommendationLabel.INSUFFICIENT_DATA.value,
        )
        self.assertTrue(
            validate_mock_recommendation_result(result, self.policy).passed
        )

    def test_risk_flags_return_risk_review(self) -> None:
        recommendation_input = replace(
            self.complete_input,
            risk_flags=("volatility_review",),
        )
        result = build_mock_recommendation_result(
            recommendation_input,
            self.policy,
        )
        self.assertEqual(
            result.label,
            MockRecommendationLabel.RISK_REVIEW.value,
        )
        self.assertTrue(
            validate_mock_recommendation_result(result, self.policy).passed
        )

    def test_complete_neutral_input_returns_observation_only(self) -> None:
        result = build_mock_recommendation_result(
            self.complete_input,
            self.policy,
        )
        self.assertEqual(
            result.label,
            MockRecommendationLabel.OBSERVATION_ONLY.value,
        )
        self.assertTrue(
            validate_mock_recommendation_result(result, self.policy).passed
        )

    def test_same_input_always_returns_same_output(self) -> None:
        first = build_mock_recommendation_result(
            self.complete_input,
            self.policy,
        )
        second = build_mock_recommendation_result(
            self.complete_input,
            self.policy,
        )
        self.assertEqual(first, second)

    def test_result_contains_disclaimers_and_safe_explanations(self) -> None:
        result = build_mock_recommendation_result(
            self.complete_input,
            self.policy,
        )
        self.assertEqual(result.required_disclaimers, REQUIRED_DISCLAIMERS)
        self.assertFalse(result.is_investment_advice)
        self.assertFalse(result.action_allowed)
        self.assertFalse(result.real_trade_allowed)
        for explanation in result.explanations:
            self.assertTrue(
                any(
                    explanation.startswith(f"{phrase}:")
                    for phrase in ALLOWED_EXPLANATION_LANGUAGE
                )
            )
        combined = "\n".join(
            (
                result.label,
                *result.explanations,
                *result.required_disclaimers,
            )
        )
        for phrase in FORBIDDEN_RECOMMENDATION_LANGUAGE:
            self.assertNotIn(phrase, combined)

    def test_default_policy_and_result_validation_pass(self) -> None:
        policy_validation = validate_mock_recommendation_policy(self.policy)
        result = build_mock_recommendation_result(
            self.complete_input,
            self.policy,
        )
        result_validation = validate_mock_recommendation_result(
            result,
            self.policy,
        )
        self.assertTrue(policy_validation.passed)
        self.assertEqual(policy_validation.violations, ())
        self.assertTrue(result_validation.passed)
        self.assertEqual(result_validation.violations, ())

    def test_unsafe_policy_flags_fail_validation(self) -> None:
        for field_name in (
            "llm_call_allowed",
            "external_ai_api_allowed",
            "oauth_allowed",
            "live_market_api_allowed",
            "account_api_allowed",
            "order_api_allowed",
            "db_write_allowed",
        ):
            unsafe_policy = replace(self.policy, **{field_name: True})
            validation = validate_mock_recommendation_policy(unsafe_policy)
            self.assertFalse(validation.passed)
            self.assertIn(
                f"{field_name}_must_be_false",
                validation.violations,
            )

    def test_forbidden_directive_labels_fail_validation(self) -> None:
        safe_result = build_mock_recommendation_result(
            self.complete_input,
            self.policy,
        )
        for forbidden_label in FORBIDDEN_MOCK_LABELS:
            invalid_result = replace(safe_result, label=forbidden_label)
            validation = validate_mock_recommendation_result(
                invalid_result,
                self.policy,
            )
            self.assertFalse(validation.passed)
            self.assertIn(
                "result_label_is_forbidden_directive",
                validation.violations,
            )

    def test_action_advice_and_trade_true_fail_validation(self) -> None:
        safe_result = build_mock_recommendation_result(
            self.complete_input,
            self.policy,
        )
        for field_name in (
            "action_allowed",
            "is_investment_advice",
            "real_trade_allowed",
        ):
            invalid_result = replace(safe_result, **{field_name: True})
            validation = validate_mock_recommendation_result(
                invalid_result,
                self.policy,
            )
            self.assertFalse(validation.passed)
            self.assertIn(
                f"{field_name}_must_be_false",
                validation.violations,
            )

    def test_forbidden_language_fails_validation(self) -> None:
        safe_result = build_mock_recommendation_result(
            self.complete_input,
            self.policy,
        )
        invalid_result = replace(
            safe_result,
            explanations=(
                (
                    "관찰 포인트: "
                    f"{FORBIDDEN_RECOMMENDATION_LANGUAGE[0]}"
                ),
            ),
        )
        validation = validate_mock_recommendation_result(
            invalid_result,
            self.policy,
        )
        self.assertFalse(validation.passed)
        self.assertIn(
            "result_contains_forbidden_recommendation_language",
            validation.violations,
        )

    def test_invalid_input_fails_closed_without_echoing_input(self) -> None:
        recommendation_input = replace(
            self.complete_input,
            symbol="",
            observation_notes=(FORBIDDEN_RECOMMENDATION_LANGUAGE[0],),
        )
        result = build_mock_recommendation_result(
            recommendation_input,
            self.policy,
        )
        self.assertEqual(
            result.label,
            MockRecommendationLabel.NOT_EVALUATED.value,
        )
        self.assertEqual(result.symbol, "invalid_input")
        self.assertNotIn(
            FORBIDDEN_RECOMMENDATION_LANGUAGE[0],
            "\n".join(result.explanations),
        )
        self.assertTrue(
            validate_mock_recommendation_result(result, self.policy).passed
        )

    def test_module_structure_has_no_io_or_external_dependencies(self) -> None:
        module_path = Path(
            "src/ai_stock/recommendation/mock_policy_model.py"
        )
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        imported_modules: set[str] = set()
        called_names: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_modules.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_modules.add(node.module)
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_names.add(node.func.attr)

        self.assertEqual(
            imported_modules,
            {
                "dataclasses",
                "enum",
                "ai_stock.recommendation.safety_preflight",
            },
        )
        for forbidden_call in (
            "open",
            "read_text",
            "read_bytes",
            "write_text",
            "write_bytes",
            "connect",
            "getenv",
            "request",
            "get",
            "post",
            "now",
            "random",
        ):
            self.assertNotIn(forbidden_call, called_names)

    def test_module_has_no_forbidden_runtime_imports(self) -> None:
        source = Path(
            "src/ai_stock/recommendation/mock_policy_model.py"
        ).read_text(encoding="utf-8").casefold()
        for forbidden in (
            "import streamlit",
            "ai_stock.clients",
            "ai_stock.storage",
            "ai_stock.paper_trading",
            "sqlite3",
            "sqlalchemy",
            "httpx",
            "requests",
            "import openai",
            "dotenv",
            "datetime",
            "os.environ",
            "local_snapshot_latest_read_model",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
