"""Offline tests for the MS-08.03 recommendation explanation UI preflight."""

import ast
from dataclasses import FrozenInstanceError, replace
from pathlib import Path
import unittest

from ai_stock.recommendation.explanation_ui_preflight import (
    FORBIDDEN_EXPLANATION_SECTIONS,
    SAFE_EXPLANATION_SECTIONS,
    RecommendationExplanationSection,
    RecommendationExplanationSectionName,
    build_default_recommendation_explanation_ui_policy,
    build_recommendation_explanation_view_model,
    validate_recommendation_explanation_ui_policy,
    validate_recommendation_explanation_view_model,
)
from ai_stock.recommendation.mock_policy_model import (
    FORBIDDEN_MOCK_LABELS,
    MockRecommendationInput,
    build_default_mock_recommendation_policy,
    build_mock_recommendation_result,
)
from ai_stock.recommendation.safety_preflight import (
    ALLOWED_EXPLANATION_LANGUAGE,
    FORBIDDEN_RECOMMENDATION_LANGUAGE,
    REQUIRED_DISCLAIMERS,
)


class RecommendationExplanationUIPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_default_recommendation_explanation_ui_policy()
        self.mock_policy = build_default_mock_recommendation_policy()
        self.mock_result = build_mock_recommendation_result(
            MockRecommendationInput(
                symbol="005930",
                has_stock_info=True,
                has_price_snapshot=True,
                has_candle=True,
                has_exchange_rate=True,
                observation_notes=("caller prepared note",),
            ),
            self.mock_policy,
        )
        self.view_model = build_recommendation_explanation_view_model(
            self.mock_result,
            self.policy,
        )

    def test_default_policy_identity_and_immutability(self) -> None:
        self.assertEqual(self.policy.stage_name, "MS-08.03")
        self.assertEqual(
            self.policy.mode,
            "recommendation_explanation_ui_preflight",
        )
        with self.assertRaises(FrozenInstanceError):
            self.policy.real_recommendation_allowed = True

    def test_default_ui_preflight_policy_has_safe_values(self) -> None:
        self.assertFalse(self.policy.streamlit_ui_change_allowed)
        self.assertTrue(self.policy.ui_contract_only)
        self.assertTrue(self.policy.mock_result_display_allowed_future_stage)
        self.assertFalse(self.policy.real_trade_allowed)

    def test_recommendation_advice_and_directives_are_disabled(self) -> None:
        self.assertFalse(self.policy.real_recommendation_allowed)
        self.assertFalse(self.policy.investment_advice_allowed)
        self.assertFalse(self.policy.buy_sell_hold_directive_allowed)

    def test_llm_api_openai_and_toss_credentials_are_disabled(self) -> None:
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

    def test_db_write_is_disabled(self) -> None:
        self.assertFalse(self.policy.db_write_allowed)

    def test_safe_sections_only_are_defined(self) -> None:
        self.assertEqual(self.policy.safe_sections, SAFE_EXPLANATION_SECTIONS)
        self.assertEqual(
            self.policy.forbidden_sections,
            FORBIDDEN_EXPLANATION_SECTIONS,
        )
        self.assertFalse(
            set(self.policy.safe_sections) & set(self.policy.forbidden_sections)
        )
        for expected in (
            "summary",
            "observation",
            "risk_review",
            "data_completeness",
            "disclaimer",
            "diagnostics",
            "next_checks",
        ):
            self.assertIn(expected, self.policy.safe_sections)

    def test_forbidden_sections_are_not_in_default_view_model(self) -> None:
        section_names = tuple(section.name for section in self.view_model.safe_sections)
        for forbidden_section in FORBIDDEN_EXPLANATION_SECTIONS:
            self.assertNotIn(forbidden_section, section_names)

    def test_mock_result_view_model_preserves_safe_label(self) -> None:
        self.assertIn(self.view_model.label, self.policy.allowed_labels)
        self.assertEqual(self.view_model.label, self.mock_result.label)

    def test_required_disclaimers_are_in_view_model(self) -> None:
        self.assertEqual(self.view_model.disclaimers, REQUIRED_DISCLAIMERS)
        disclaimer_section = next(
            section
            for section in self.view_model.safe_sections
            if section.name == RecommendationExplanationSectionName.DISCLAIMER.value
        )
        self.assertEqual(disclaimer_section.lines, REQUIRED_DISCLAIMERS)

    def test_forbidden_recommendation_language_is_not_in_view_model(self) -> None:
        combined = "\n".join(self._view_model_strings(self.view_model))
        for phrase in FORBIDDEN_RECOMMENDATION_LANGUAGE:
            self.assertNotIn(phrase, combined)

    def test_view_model_action_and_sensitive_controls_are_disabled(self) -> None:
        self.assertFalse(self.view_model.action_allowed)
        self.assertFalse(self.view_model.is_investment_advice)
        self.assertFalse(self.view_model.real_trade_allowed)
        self.assertFalse(self.view_model.order_button_allowed)
        self.assertFalse(self.view_model.credential_input_allowed)
        self.assertFalse(self.view_model.account_seq_input_allowed)
        self.assertFalse(self.view_model.live_refresh_allowed)
        self.assertFalse(self.view_model.oauth_allowed)

    def test_same_mock_result_always_builds_same_view_model(self) -> None:
        first = build_recommendation_explanation_view_model(
            self.mock_result,
            self.policy,
        )
        second = build_recommendation_explanation_view_model(
            self.mock_result,
            self.policy,
        )
        self.assertEqual(first, second)

    def test_validation_passes_for_default_policy_and_view_model(self) -> None:
        policy_validation = validate_recommendation_explanation_ui_policy(
            self.policy,
        )
        view_validation = validate_recommendation_explanation_view_model(
            self.view_model,
            self.policy,
        )
        self.assertTrue(policy_validation.passed)
        self.assertEqual(policy_validation.violations, ())
        self.assertTrue(view_validation.passed)
        self.assertEqual(view_validation.violations, ())

    def test_forbidden_section_fails_validation(self) -> None:
        unsafe_section = RecommendationExplanationSection(
            name="order_ticket",
            heading="Unsafe",
            lines=("must not display",),
        )
        unsafe_view_model = replace(
            self.view_model,
            safe_sections=self.view_model.safe_sections + (unsafe_section,),
        )
        validation = validate_recommendation_explanation_view_model(
            unsafe_view_model,
            self.policy,
        )
        self.assertFalse(validation.passed)
        self.assertIn(
            "view_model_contains_forbidden_section",
            validation.violations,
        )

    def test_buy_sell_hold_labels_fail_validation(self) -> None:
        for forbidden_label in FORBIDDEN_MOCK_LABELS:
            unsafe_view_model = replace(
                self.view_model,
                label=forbidden_label,
            )
            validation = validate_recommendation_explanation_view_model(
                unsafe_view_model,
                self.policy,
            )
            self.assertFalse(validation.passed)
            self.assertIn(
                "view_model_label_is_forbidden_directive",
                validation.violations,
            )

    def test_sensitive_true_flags_fail_validation(self) -> None:
        for field_name in (
            "order_button_allowed",
            "credential_input_allowed",
            "account_seq_input_allowed",
            "live_refresh_allowed",
            "oauth_allowed",
        ):
            unsafe_view_model = replace(
                self.view_model,
                **{field_name: True},
            )
            validation = validate_recommendation_explanation_view_model(
                unsafe_view_model,
                self.policy,
            )
            self.assertFalse(validation.passed)
            self.assertIn(
                f"{field_name}_must_be_false",
                validation.violations,
            )

    def test_action_advice_and_real_trade_true_fail_validation(self) -> None:
        for field_name in (
            "action_allowed",
            "is_investment_advice",
            "real_trade_allowed",
        ):
            unsafe_view_model = replace(
                self.view_model,
                **{field_name: True},
            )
            validation = validate_recommendation_explanation_view_model(
                unsafe_view_model,
                self.policy,
            )
            self.assertFalse(validation.passed)
            self.assertIn(
                f"{field_name}_must_be_false",
                validation.violations,
            )

    def test_missing_disclaimer_fails_validation(self) -> None:
        unsafe_view_model = replace(
            self.view_model,
            disclaimers=self.view_model.disclaimers[:-1],
        )
        validation = validate_recommendation_explanation_view_model(
            unsafe_view_model,
            self.policy,
        )
        self.assertFalse(validation.passed)
        self.assertIn(
            "view_model_must_include_all_required_disclaimers",
            validation.violations,
        )

    def test_forbidden_language_fails_validation(self) -> None:
        unsafe_section = RecommendationExplanationSection(
            name=RecommendationExplanationSectionName.OBSERVATION.value,
            heading="Observation",
            lines=(
                (
                    f"{ALLOWED_EXPLANATION_LANGUAGE[0]}: "
                    f"{FORBIDDEN_RECOMMENDATION_LANGUAGE[0]}"
                ),
            ),
        )
        safe_sections = tuple(
            unsafe_section
            if section.name == RecommendationExplanationSectionName.OBSERVATION.value
            else section
            for section in self.view_model.safe_sections
        )
        unsafe_view_model = replace(
            self.view_model,
            safe_sections=safe_sections,
        )
        validation = validate_recommendation_explanation_view_model(
            unsafe_view_model,
            self.policy,
        )
        self.assertFalse(validation.passed)
        self.assertIn(
            "view_model_contains_forbidden_recommendation_language",
            validation.violations,
        )

    def test_view_model_strings_have_no_directive_words(self) -> None:
        combined = "\n".join(self._view_model_strings(self.view_model)).casefold()
        for forbidden_word in ("buy", "sell", "hold"):
            self.assertNotIn(forbidden_word, combined)

    def test_module_structure_has_no_io_or_external_dependencies(self) -> None:
        module_path = Path(
            "src/ai_stock/recommendation/explanation_ui_preflight.py"
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
                "ai_stock.recommendation.mock_policy_model",
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
            "src/ai_stock/recommendation/explanation_ui_preflight.py"
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

    def _view_model_strings(
        self,
        view_model,
    ) -> tuple[str, ...]:
        section_strings: list[str] = []
        for section in view_model.safe_sections:
            section_strings.append(section.name)
            section_strings.append(section.heading)
            section_strings.extend(section.lines)
        return (
            view_model.title,
            view_model.stage_name,
            view_model.label,
            *view_model.safe_summary,
            *section_strings,
            *view_model.disclaimers,
            *view_model.diagnostics,
        )


if __name__ == "__main__":
    unittest.main()
