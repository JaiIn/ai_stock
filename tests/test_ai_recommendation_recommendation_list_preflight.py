"""Offline tests for the MS-12.00 recommendation list preflight contract."""

from dataclasses import FrozenInstanceError, fields
from types import FunctionType
import unittest

import ai_stock.recommendation.recommendation_list_preflight as list_preflight
from ai_stock.recommendation.recommendation_list_preflight import (
    ALLOWED_RECOMMENDATION_LIST_INPUT_SOURCES,
    ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES,
    FORBIDDEN_RECOMMENDATION_LIST_INPUT_SOURCES,
    FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_KEYWORDS,
    RecommendationListItemStatus,
    RecommendationListPreflightItem,
    RecommendationListPreflightPolicy,
    build_recommendation_list_input_from_scoring_result,
    build_recommendation_list_item_from_scoring_result,
    build_recommendation_list_items_from_all_fixtures,
    build_recommendation_list_items_from_scoring_fixture_matrix,
    build_recommendation_list_items_from_scoring_results,
    build_recommendation_list_preflight_policy,
    summarize_recommendation_list_preflight_items,
    validate_recommendation_list_preflight_item,
    validate_recommendation_list_preflight_items,
)
from ai_stock.recommendation.scoring_fixture_hardening import (
    run_scoring_fixture_hardening_checks,
)
from ai_stock.recommendation.scoring_fixtures import (
    build_all_scoring_fixtures,
    evaluate_all_scoring_fixtures,
)
from ai_stock.recommendation.scoring_preflight import (
    FORBIDDEN_SCORING_ACTION_LABELS,
    FORBIDDEN_SCORING_RECOMMENDATION_LABELS,
    SCORE_SCALE,
    ScoreComponent,
    ScoringPreflightResult,
    ScoringPreflightSummaryFlags,
    score_extracted_feature_sets_from_all_fixtures,
)


class RecommendationListPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_recommendation_list_preflight_policy()

    def test_recommendation_list_preflight_policy_generation(self) -> None:
        self.assertIsInstance(self.policy, RecommendationListPreflightPolicy)
        self.assertEqual(self.policy.preflight_version, "MS-12.00")
        self.assertEqual(
            self.policy.preflight_scope,
            "recommendation_list_model_shape_preflight",
        )
        self.assertIn(
            "in_memory_scoring_result",
            self.policy.allowed_input_sources,
        )
        self.assertFalse(self.policy.recommendation_required)
        self.assertFalse(self.policy.ranking_required)
        self.assertFalse(self.policy.ui_required)
        with self.assertRaises(FrozenInstanceError):
            self.policy.ui_required = True

    def test_allowed_and_forbidden_input_sources(self) -> None:
        self.assertEqual(
            self.policy.allowed_input_sources,
            ALLOWED_RECOMMENDATION_LIST_INPUT_SOURCES,
        )
        self.assertIn("file_path", FORBIDDEN_RECOMMENDATION_LIST_INPUT_SOURCES)
        self.assertIn("database", FORBIDDEN_RECOMMENDATION_LIST_INPUT_SOURCES)
        self.assertIn("accountSeq", FORBIDDEN_RECOMMENDATION_LIST_INPUT_SOURCES)
        self.assertIn("toss_api", FORBIDDEN_RECOMMENDATION_LIST_INPUT_SOURCES)

    def test_allowed_and_forbidden_item_statuses(self) -> None:
        self.assertEqual(
            self.policy.allowed_item_statuses,
            ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES,
        )
        for forbidden in (
            "buy",
            "sell",
            "hold",
            "strong_buy",
            "rank",
            "ranking",
            "recommendation",
            "target_price",
            "expected_return",
            "profit_probability",
            "must_buy",
            "must_sell",
        ):
            self.assertNotIn(forbidden, self.policy.allowed_item_statuses)

    def test_scoring_result_to_list_input(self) -> None:
        scoring_result = _ready_scoring_result()
        list_input = build_recommendation_list_input_from_scoring_result(
            scoring_result
        )

        self.assertEqual(list_input.symbol, "005930")
        self.assertEqual(list_input.scoring_status, "score_ready")
        self.assertEqual(list_input.total_score, SCORE_SCALE)
        self.assertTrue(list_input.usable_for_future_ranking)

    def test_scoring_result_to_list_item(self) -> None:
        scoring_result = _ready_scoring_result()
        item = build_recommendation_list_item_from_scoring_result(
            scoring_result,
            self.policy,
        )

        self.assertIsInstance(item, RecommendationListPreflightItem)
        self.assertEqual(item.item_status, "item_ready_for_review")
        self.assertEqual(item.display_bucket, "review_ready")
        self.assertEqual(item.score_snapshot, SCORE_SCALE)
        self.assertTrue(item.usable_for_future_list)
        self.assertTrue(
            validate_recommendation_list_preflight_item(item, self.policy).valid
        )

    def test_scoring_results_to_list_items(self) -> None:
        scoring_results = (
            _ready_scoring_result(),
            _status_scoring_result("score_missing_data"),
        )
        items = build_recommendation_list_items_from_scoring_results(
            scoring_results,
            self.policy,
        )

        self.assertEqual(len(items), 2)
        self.assertEqual(items[0].item_status, "item_ready_for_review")
        self.assertEqual(items[1].item_status, "item_missing_data")

    def test_all_fixtures_based_list_items(self) -> None:
        items = build_recommendation_list_items_from_all_fixtures(self.policy)
        summary = summarize_recommendation_list_preflight_items(items)

        self.assertEqual(len(items), 11)
        self.assertEqual(summary.total_items, 11)
        self.assertEqual(summary.ready_for_review_items, 4)
        self.assertEqual(summary.needs_review_items, 7)
        self.assertEqual(summary.usable_for_future_list_items, 4)
        self.assertTrue(
            all(
                validation.valid
                for validation in validate_recommendation_list_preflight_items(
                    items,
                    self.policy,
                )
            )
        )

    def test_fixture_matrix_reuse_is_deterministic(self) -> None:
        self.assertEqual(
            build_recommendation_list_items_from_scoring_fixture_matrix(),
            build_recommendation_list_items_from_scoring_fixture_matrix(),
        )
        self.assertEqual(
            summarize_recommendation_list_preflight_items(
                build_recommendation_list_items_from_all_fixtures(self.policy)
            ),
            summarize_recommendation_list_preflight_items(
                build_recommendation_list_items_from_all_fixtures(self.policy)
            ),
        )

    def test_score_ready_maps_to_item_ready_for_review(self) -> None:
        item = build_recommendation_list_item_from_scoring_result(
            _ready_scoring_result(),
            self.policy,
        )

        self.assertEqual(
            item.item_status,
            RecommendationListItemStatus.ITEM_READY_FOR_REVIEW.value,
        )
        self.assertTrue(item.usable_for_future_list)

    def test_score_needs_review_maps_to_item_needs_review(self) -> None:
        item = build_recommendation_list_item_from_scoring_result(
            _status_scoring_result("score_needs_review", needs_review=True),
            self.policy,
        )

        self.assertEqual(
            item.item_status,
            RecommendationListItemStatus.ITEM_NEEDS_REVIEW.value,
        )
        self.assertFalse(item.usable_for_future_list)

    def test_blocked_status_mappings(self) -> None:
        mapping = {
            "score_duplicate_candidate": "item_duplicate_candidate",
            "score_disabled_candidate": "item_disabled_candidate",
            "score_missing_data": "item_missing_data",
            "score_invalid_candidate": "item_invalid_candidate",
            "score_forbidden_field_sanitized": (
                "item_forbidden_field_sanitized"
            ),
            "score_empty_input": "item_empty_input",
            "score_blocked_quality": "item_blocked_quality",
        }

        for scoring_status, expected_item_status in mapping.items():
            item = build_recommendation_list_item_from_scoring_result(
                _status_scoring_result(scoring_status, needs_review=True),
                self.policy,
            )
            self.assertEqual(item.item_status, expected_item_status)
            self.assertFalse(item.usable_for_future_list)

    def test_score_snapshot_is_not_directive_output(self) -> None:
        item = build_recommendation_list_item_from_scoring_result(
            _ready_scoring_result(),
            self.policy,
        )

        self.assertEqual(item.score_snapshot, SCORE_SCALE)
        self.assertIn("score_snapshot_quality_preflight_only", item.warnings)
        self.assertNotIn("recommendation", item.item_status)
        self.assertNotIn("ranking", item.item_status)
        self.assertNotIn("action", item.item_status)

    def test_display_bucket_is_review_group_not_ranking(self) -> None:
        item = build_recommendation_list_item_from_scoring_result(
            _ready_scoring_result(),
            self.policy,
        )

        self.assertEqual(item.display_bucket, "review_ready")
        self.assertIn("display_bucket_review_group_only", item.warnings)
        self.assertNotIn("rank", item.display_bucket)
        self.assertNotIn("priority", item.display_bucket)

    def test_usable_for_future_list_is_not_ranking_flag(self) -> None:
        item = build_recommendation_list_item_from_scoring_result(
            _ready_scoring_result(),
            self.policy,
        )

        self.assertTrue(item.usable_for_future_list)
        self.assertFalse(hasattr(item, "ranking_position"))
        self.assertFalse(hasattr(item, "rank"))

    def test_forbidden_action_status_is_not_generated(self) -> None:
        items = build_recommendation_list_items_from_all_fixtures(self.policy)
        produced_values: list[str] = []
        for item in items:
            produced_values.append(item.item_status)
            produced_values.append(item.display_bucket)
            produced_values.extend(item.component_names)

        for forbidden_label in (
            *FORBIDDEN_SCORING_ACTION_LABELS,
            *FORBIDDEN_SCORING_RECOMMENDATION_LABELS,
            "ranking_position",
            "priority",
        ):
            self.assertNotIn(forbidden_label, produced_values)

    def test_forbidden_output_field_is_not_copied_to_item_model(self) -> None:
        rendered = repr(
            build_recommendation_list_items_from_all_fixtures(self.policy)
        )

        for keyword in FORBIDDEN_RECOMMENDATION_LIST_OUTPUT_KEYWORDS:
            self.assertNotIn(keyword, rendered)

    def test_required_flags_are_all_false(self) -> None:
        items = build_recommendation_list_items_from_all_fixtures(self.policy)

        for item in items:
            for field in fields(item.summary_flags):
                self.assertFalse(getattr(item.summary_flags, field.name))
        summary = summarize_recommendation_list_preflight_items(items)
        self.assertFalse(summary.recommendation_required)
        self.assertFalse(summary.ranking_required)
        self.assertFalse(summary.ui_required)

    def test_contract_reuse_paths_are_available(self) -> None:
        self.assertTrue(run_scoring_fixture_hardening_checks().passed)
        self.assertTrue(
            all(
                evaluation.passed
                for evaluation in evaluate_all_scoring_fixtures()
            )
        )
        self.assertEqual(len(build_all_scoring_fixtures()), 8)
        self.assertEqual(
            len(
                [
                    result
                    for group in score_extracted_feature_sets_from_all_fixtures()
                    for result in group
                ]
            ),
            11,
        )

    def test_validation_rejects_forbidden_item_shape(self) -> None:
        item = build_recommendation_list_item_from_scoring_result(
            _ready_scoring_result(),
            self.policy,
        )
        forbidden_item = RecommendationListPreflightItem(
            symbol=item.symbol,
            market=item.market,
            item_status="buy",
            display_bucket=item.display_bucket,
            score_snapshot=item.score_snapshot,
            score_scale=item.score_scale,
            component_names=item.component_names,
            needs_review=item.needs_review,
            usable_for_future_list=item.usable_for_future_list,
            blocked_reasons=item.blocked_reasons,
            warnings=item.warnings,
            diagnostics=item.diagnostics,
            summary_flags=item.summary_flags,
        )
        validation = validate_recommendation_list_preflight_item(
            forbidden_item,
            self.policy,
        )

        self.assertFalse(validation.valid)
        self.assertIn("item_status_not_allowed", validation.rejection_reasons)
        self.assertIn("forbidden_action_label_present", validation.rejection_reasons)

    def test_module_structure_has_no_io_or_external_dependencies(self) -> None:
        runtime_modules = {
            getattr(value, "__module__", "")
            for value in vars(list_preflight).values()
        }
        for forbidden_module in (
            "streamlit",
            "sqlite3",
            "sqlalchemy",
            "httpx",
            "requests",
            "openai",
            "dotenv",
            "os",
            "pathlib",
            "socket",
            "subprocess",
        ):
            self.assertNotIn(forbidden_module, runtime_modules)

        called_names = _module_code_names()
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

    def test_module_has_no_forbidden_runtime_imports_or_paths(self) -> None:
        module_symbols = {
            str(part).casefold()
            for part in (*vars(list_preflight), *_module_constants())
        }
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
            "os.environ",
            ".env.local=",
            "local_snapshot_latest_read_model",
        ):
            self.assertNotIn(forbidden, module_symbols)

    def test_existing_contract_modules_are_not_referenced_as_paths(self) -> None:
        constants = _module_constants()

        self.assertNotIn("app/streamlit_app.py", constants)
        self.assertNotIn("scoring_preflight.py", constants)
        self.assertNotIn("scoring_fixtures.py", constants)
        self.assertNotIn("scoring_fixture_hardening.py", constants)
        self.assertNotIn("scoring.py", constants)
        self.assertNotIn("feature_quality.py", constants)
        self.assertNotIn("feature_quality_fixtures.py", constants)
        self.assertNotIn("feature_extraction_preflight.py", constants)
        self.assertNotIn("feature_extraction_fixtures.py", constants)


def _ready_scoring_result() -> ScoringPreflightResult:
    return ScoringPreflightResult(
        symbol="005930",
        market="KR",
        scoring_status="score_ready",
        score_components=(
            ScoreComponent(
                component_name="data_completeness",
                component_score=SCORE_SCALE,
                component_scale=SCORE_SCALE,
                source_feature_names=("symbol", "market"),
                component_status="component_ready",
                warnings=(),
                diagnostics=("quality_ok",),
            ),
        ),
        total_score=SCORE_SCALE,
        score_scale=SCORE_SCALE,
        score_warnings=("quality_preflight_score_only", "no_trade_directive"),
        diagnostics=("deterministic_in_memory_score_shape",),
        needs_review=False,
        usable_for_future_ranking=True,
        blocked_reasons=(),
        summary_flags=ScoringPreflightSummaryFlags(),
    )


def _status_scoring_result(
    scoring_status: str,
    needs_review: bool = True,
) -> ScoringPreflightResult:
    return ScoringPreflightResult(
        symbol="SAFE",
        market="KR",
        scoring_status=scoring_status,
        score_components=(
            ScoreComponent(
                component_name="review_penalty",
                component_score=0 if needs_review else SCORE_SCALE,
                component_scale=SCORE_SCALE,
                source_feature_names=("symbol",),
                component_status=(
                    "component_needs_review" if needs_review else "component_ready"
                ),
                warnings=("needs_review",) if needs_review else (),
                diagnostics=(scoring_status,),
            ),
        ),
        total_score=20 if needs_review else SCORE_SCALE,
        score_scale=SCORE_SCALE,
        score_warnings=("quality_preflight_score_only", "no_trade_directive"),
        diagnostics=("deterministic_in_memory_score_shape", scoring_status),
        needs_review=needs_review,
        usable_for_future_ranking=False,
        blocked_reasons=(f"blocked_by:{scoring_status}",),
        summary_flags=ScoringPreflightSummaryFlags(),
    )


def _module_code_names() -> set[str]:
    names: set[str] = set()
    for value in vars(list_preflight).values():
        if isinstance(value, FunctionType):
            names.update(value.__code__.co_names)
    return names


def _module_constants() -> tuple[object, ...]:
    constants: list[object] = []
    for value in vars(list_preflight).values():
        if isinstance(value, FunctionType):
            constants.extend(_flatten_code_constants(value.__code__.co_consts))
    return tuple(constants)


def _flatten_code_constants(values: tuple[object, ...]) -> tuple[object, ...]:
    flattened: list[object] = []
    for value in values:
        if isinstance(value, tuple):
            flattened.extend(_flatten_code_constants(value))
        else:
            flattened.append(value)
    return tuple(flattened)


if __name__ == "__main__":
    unittest.main()
