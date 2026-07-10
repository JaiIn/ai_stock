"""Offline tests for the MS-09.02 watchlist data model contract."""

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

from ai_stock.recommendation.candidate_input_preflight import (
    ALLOWED_CANDIDATE_SOURCES,
    FORBIDDEN_CANDIDATE_LABELS,
    FORBIDDEN_CANDIDATE_SOURCES,
    CandidateInput,
)
from ai_stock.recommendation.watchlist_model import (
    FORBIDDEN_WATCHLIST_FIELDS,
    WATCHLIST_STATUSES,
    Watchlist,
    WatchlistItem,
    build_watchlist_policy,
    build_watchlist_summary,
    validate_watchlist,
    validate_watchlist_item,
    watchlist_items_to_candidate_inputs,
)


class WatchlistModelTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_watchlist_policy()
        self.valid_item = WatchlistItem(
            symbol=" 005930 ",
            name="Samsung Electronics",
            market="kospi",
            source="manual_watchlist",
            reason="manual observation candidate",
            tags=(" core ", "", "large-cap"),
            group=" default ",
            priority=10,
            note=" caller supplied only ",
        )
        self.valid_watchlist = Watchlist(
            name=" Local manual list ",
            description="caller supplied watchlist",
            items=(self.valid_item,),
            source_label="manual input",
        )

    def test_default_policy_identity_and_immutability(self) -> None:
        self.assertEqual(self.policy.stage_name, "MS-09.02")
        self.assertEqual(self.policy.mode, "watchlist_data_model")
        with self.assertRaises(FrozenInstanceError):
            self.policy.db_write_required = True

    def test_policy_reuses_candidate_source_and_label_contracts(self) -> None:
        self.assertEqual(self.policy.allowed_sources, ALLOWED_CANDIDATE_SOURCES)
        self.assertEqual(self.policy.forbidden_sources, FORBIDDEN_CANDIDATE_SOURCES)
        self.assertEqual(self.policy.forbidden_labels, FORBIDDEN_CANDIDATE_LABELS)

    def test_valid_watchlist_item_generation_and_validation(self) -> None:
        result = validate_watchlist_item(self.valid_item, self.policy)
        self.assertEqual(result.symbol, "005930")
        self.assertEqual(result.market, "KOSPI")
        self.assertEqual(result.group, "default")
        self.assertEqual(result.note, "caller supplied only")
        self.assertEqual(result.tags, ("core", "large-cap"))
        self.assertEqual(result.validation_status, "valid_candidate")
        self.assertTrue(result.selectable)

    def test_empty_watchlist_processing(self) -> None:
        result = validate_watchlist(Watchlist(name="empty", items=()), self.policy)
        self.assertEqual(result.validation_status, "empty_watchlist")
        self.assertEqual(result.summary.total_items, 0)

    def test_invalid_watchlist_name_processing(self) -> None:
        result = validate_watchlist(
            Watchlist(name="  ", items=(self.valid_item,)),
            self.policy,
        )
        self.assertEqual(result.validation_status, "invalid_watchlist_name")
        self.assertIn("watchlist_name_required", result.rejection_reasons)

    def test_allowed_source_item_is_valid_or_safe_status(self) -> None:
        for source in ALLOWED_CANDIDATE_SOURCES:
            result = validate_watchlist_item(
                WatchlistItem(symbol="005930", source=source),
                self.policy,
            )
            self.assertIn(result.validation_status, self.policy.safe_candidate_statuses)
            self.assertNotEqual(result.validation_status, "unsupported_source")

    def test_forbidden_source_item_is_rejected(self) -> None:
        for source in FORBIDDEN_CANDIDATE_SOURCES:
            result = validate_watchlist_item(
                WatchlistItem(symbol="005930", source=source),
                self.policy,
            )
            self.assertEqual(result.validation_status, "unsupported_source")
            self.assertIn("forbidden_source", result.rejection_reasons)
            self.assertFalse(result.selectable)

    def test_empty_symbol_is_invalid(self) -> None:
        result = validate_watchlist_item(
            WatchlistItem(symbol=" ", source="manual_watchlist"),
            self.policy,
        )
        self.assertEqual(result.validation_status, "invalid_symbol")
        self.assertIn("symbol_required", result.rejection_reasons)

    def test_symbol_trim_processing(self) -> None:
        result = validate_watchlist_item(self.valid_item, self.policy)
        self.assertEqual(result.symbol, "005930")

    def test_duplicate_symbol_processing(self) -> None:
        result = validate_watchlist(
            Watchlist(
                name="duplicates",
                items=(
                    WatchlistItem(symbol="005930", source="manual_watchlist"),
                    WatchlistItem(symbol=" 005930 ", source="test_fixture"),
                ),
            ),
            self.policy,
        )
        self.assertEqual(
            result.validation_status,
            "contains_duplicate_candidates",
        )
        self.assertEqual(result.items[1].validation_status, "duplicate_candidate")
        self.assertEqual(result.summary.duplicate_items, 1)

    def test_disabled_item_processing(self) -> None:
        result = validate_watchlist_item(
            WatchlistItem(
                symbol="005930",
                source="manual_watchlist",
                enabled=False,
            ),
            self.policy,
        )
        self.assertEqual(result.validation_status, "disabled_candidate")
        self.assertFalse(result.selectable)

    def test_default_disabled_watchlist_disables_items(self) -> None:
        result = validate_watchlist(
            Watchlist(
                name="disabled by default",
                default_enabled=False,
                items=(WatchlistItem(symbol="005930", source="manual_watchlist"),),
            ),
            self.policy,
        )
        self.assertEqual(result.validation_status, "contains_disabled_candidates")
        self.assertEqual(result.summary.disabled_items, 1)

    def test_priority_range_validation(self) -> None:
        result = validate_watchlist_item(
            WatchlistItem(
                symbol="005930",
                source="manual_watchlist",
                priority=self.policy.max_priority + 1,
            ),
            self.policy,
        )
        self.assertEqual(result.validation_status, "needs_review")
        self.assertIn("priority_out_of_range", result.rejection_reasons)
        self.assertFalse(result.selectable)

    def test_tags_normalization(self) -> None:
        result = validate_watchlist_item(self.valid_item, self.policy)
        self.assertEqual(result.tags, ("core", "large-cap"))

    def test_insufficient_data_hint_processing(self) -> None:
        result = validate_watchlist(
            Watchlist(
                name="partial",
                items=(
                    WatchlistItem(
                        symbol="005930",
                        source="local_snapshot_summary",
                        data_availability_hint="partial_data",
                    ),
                ),
            ),
            self.policy,
        )
        self.assertEqual(result.validation_status, "needs_review")
        self.assertEqual(result.summary.insufficient_data_items, 1)
        self.assertEqual(result.items[0].validation_status, "insufficient_data")

    def test_watchlist_items_to_candidate_inputs_pure_conversion(self) -> None:
        candidates = watchlist_items_to_candidate_inputs(
            (self.valid_item,),
            source_label="manual source",
        )
        self.assertEqual(
            candidates,
            (
                CandidateInput(
                    symbol=" 005930 ",
                    source="manual_watchlist",
                    name="Samsung Electronics",
                    market="kospi",
                    source_label="manual source",
                    enabled=True,
                    reason="manual observation candidate",
                    tags=(" core ", "", "large-cap"),
                    data_availability_hint="",
                ),
            ),
        )

    def test_forbidden_labels_are_not_generated(self) -> None:
        result = validate_watchlist(self.valid_watchlist, self.policy)
        for forbidden_label in FORBIDDEN_CANDIDATE_LABELS:
            self.assertNotEqual(result.validation_status, forbidden_label)
            for item in result.items:
                self.assertNotEqual(item.validation_status, forbidden_label)

    def test_summary_required_flags_are_all_false(self) -> None:
        summary = build_watchlist_summary(self.valid_watchlist, self.policy)
        self.assertFalse(summary.credential_required)
        self.assertFalse(summary.db_read_required)
        self.assertFalse(summary.db_write_required)
        self.assertFalse(summary.file_read_required)
        self.assertFalse(summary.file_write_required)
        self.assertFalse(summary.toss_api_required)
        self.assertFalse(summary.openai_required)
        self.assertFalse(summary.oauth_required)
        self.assertFalse(summary.account_seq_required)
        self.assertFalse(summary.real_order_required)
        self.assertFalse(summary.scoring_required)
        self.assertFalse(summary.ui_required)

    def test_policy_disables_storage_loader_recommendation_scoring_and_ui(self) -> None:
        self.assertFalse(self.policy.actual_recommendation_allowed)
        self.assertFalse(self.policy.scoring_allowed)
        self.assertFalse(self.policy.watchlist_persistence_allowed)
        self.assertFalse(self.policy.file_loader_allowed)
        self.assertFalse(self.policy.ui_change_allowed)

    def test_forbidden_field_policy_is_documented(self) -> None:
        for forbidden_field in (
            "real_holding_quantity",
            "real_average_buy_price",
            "real_valuation_amount",
            "real_orderable_quantity",
            "real_account_balance",
            "real_fill_information",
            "real_order_id",
            "accountSeq",
            "access_token",
            "authorization_header",
            "api_key",
            "secret_key",
            "recommendation_score",
            "buy_sell_hold_label",
            "target_price",
            "expected_return",
        ):
            self.assertIn(forbidden_field, FORBIDDEN_WATCHLIST_FIELDS)

    def test_watchlist_statuses_are_safe_collection_statuses(self) -> None:
        for expected in (
            "valid_watchlist",
            "empty_watchlist",
            "invalid_watchlist_name",
            "contains_invalid_candidates",
            "contains_duplicate_candidates",
            "contains_disabled_candidates",
            "needs_review",
        ):
            self.assertIn(expected, WATCHLIST_STATUSES)

    def test_same_watchlist_always_returns_same_validation(self) -> None:
        first = validate_watchlist(self.valid_watchlist, self.policy)
        second = validate_watchlist(self.valid_watchlist, self.policy)
        self.assertEqual(first, second)

    def test_module_structure_has_no_io_or_external_dependencies(self) -> None:
        module_path = Path("src/ai_stock/recommendation/watchlist_model.py")
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
                "ai_stock.recommendation.candidate_input_preflight",
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

    def test_module_has_no_forbidden_runtime_imports_or_paths(self) -> None:
        source = Path(
            "src/ai_stock/recommendation/watchlist_model.py"
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
            "os.environ",
            ".env.local",
            "local_snapshot_latest_read_model",
        ):
            self.assertNotIn(forbidden, source)


if __name__ == "__main__":
    unittest.main()
