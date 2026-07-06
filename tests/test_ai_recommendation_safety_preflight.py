"""Offline tests for the MS-08.01 recommendation safety contract."""

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

from ai_stock.recommendation.safety_preflight import (
    ALLOWED_EXPLANATION_LANGUAGE,
    FORBIDDEN_RECOMMENDATION_LANGUAGE,
    REQUIRED_DISCLAIMERS,
    build_default_recommendation_safety_preflight_policy,
    summarize_recommendation_safety_preflight,
    validate_recommendation_safety_preflight_policy,
)


class RecommendationSafetyPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_default_recommendation_safety_preflight_policy()

    def test_policy_identity_and_immutability(self) -> None:
        self.assertEqual(self.policy.stage_name, "MS-08.01")
        self.assertEqual(self.policy.mode, "safety_preflight")
        with self.assertRaises(FrozenInstanceError):
            self.policy.real_recommendation_allowed = True

    def test_real_and_mock_recommendations_are_disabled(self) -> None:
        self.assertFalse(self.policy.real_recommendation_allowed)
        self.assertFalse(self.policy.mock_recommendation_allowed)
        self.assertFalse(self.policy.real_trade_allowed)

    def test_llm_external_ai_and_credentials_are_disabled(self) -> None:
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

    def test_database_write_and_streamlit_ui_change_are_disabled(self) -> None:
        self.assertFalse(self.policy.db_write_allowed)
        self.assertFalse(self.policy.streamlit_ui_change_allowed)

    def test_required_disclaimers_match_safety_contract(self) -> None:
        self.assertEqual(self.policy.required_disclaimers, REQUIRED_DISCLAIMERS)
        for message in (
            "이 기능은 투자 조언이 아닙니다.",
            "실제 매수/매도/보유 지시가 아닙니다.",
            "실거래 전 별도 판단이 필요합니다.",
            "모델/룰 기반 출력은 오류가 있을 수 있습니다.",
            "손실 가능성이 있습니다.",
            "이 프로젝트는 local-only 실험 도구입니다.",
        ):
            self.assertIn(message, self.policy.required_disclaimers)

    def test_forbidden_recommendation_language_matches_contract(self) -> None:
        self.assertEqual(
            self.policy.forbidden_recommendation_language,
            FORBIDDEN_RECOMMENDATION_LANGUAGE,
        )
        for phrase in ("지금 사라", "확정 수익", "원금 보장", "자동 주문"):
            self.assertIn(
                phrase,
                self.policy.forbidden_recommendation_language,
            )

    def test_allowed_explanation_language_matches_contract(self) -> None:
        self.assertEqual(
            self.policy.allowed_explanation_language,
            ALLOWED_EXPLANATION_LANGUAGE,
        )
        for phrase in (
            "관찰 포인트",
            "리스크 요인",
            "모의 판단",
            "투자 조언 아님",
        ):
            self.assertIn(phrase, self.policy.allowed_explanation_language)

    def test_next_stage_is_mock_only_and_explanation_focused(self) -> None:
        plan = self.policy.next_stage_plan
        self.assertEqual(plan.stage_name, "MS-08.02")
        self.assertTrue(plan.mock_only_input)
        self.assertTrue(plan.local_snapshot_read_model_dto_allowed)
        self.assertTrue(plan.rule_based_placeholder_allowed)
        self.assertTrue(plan.deterministic_placeholder_allowed)
        self.assertTrue(plan.explanation_focused)
        self.assertFalse(plan.live_api_refresh_allowed)
        self.assertFalse(plan.real_ai_llm_call_allowed)
        self.assertFalse(plan.investment_advice_allowed)
        self.assertFalse(plan.real_order_allowed)
        self.assertFalse(plan.direct_buy_sell_instruction_allowed)

    def test_validation_passes_for_default_policy(self) -> None:
        result = validate_recommendation_safety_preflight_policy(self.policy)
        self.assertTrue(result.passed)
        self.assertEqual(result.violations, ())
        self.assertEqual(result.stage_name, "MS-08.01")
        self.assertEqual(result.mode, "safety_preflight")

    def test_summary_is_deterministic_and_contains_no_recommendation(self) -> None:
        first = summarize_recommendation_safety_preflight(self.policy)
        second = summarize_recommendation_safety_preflight(self.policy)
        self.assertEqual(first, second)
        self.assertIn("real_recommendation_allowed=False", first)
        self.assertIn("next_stage=MS-08.02", first)

    def test_module_structure_has_no_io_or_external_imports(self) -> None:
        module_path = Path(
            "src/ai_stock/recommendation/safety_preflight.py"
        )
        tree = ast.parse(module_path.read_text(encoding="utf-8"))
        imported_roots: set[str] = set()
        called_names: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported_roots.update(
                    alias.name.partition(".")[0] for alias in node.names
                )
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported_roots.add(node.module.partition(".")[0])
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    called_names.add(node.func.id)
                elif isinstance(node.func, ast.Attribute):
                    called_names.add(node.func.attr)

        self.assertEqual(imported_roots, {"dataclasses"})
        for forbidden_call in (
            "open",
            "read_text",
            "read_bytes",
            "write_text",
            "write_bytes",
            "connect",
            "getenv",
            "environ",
            "request",
            "get",
            "post",
        ):
            self.assertNotIn(forbidden_call, called_names)

    def test_module_has_no_streamlit_client_llm_or_datetime_dependency(self) -> None:
        source = Path(
            "src/ai_stock/recommendation/safety_preflight.py"
        ).read_text(encoding="utf-8").casefold()
        for forbidden in (
            "import streamlit",
            "ai_stock.clients",
            "ai_stock.storage",
            "sqlite3",
            "httpx",
            "requests",
            "import openai",
            "dotenv",
            "datetime",
            "os.environ",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
