"""Offline tests for the MS-09.03 manual/local watchlist source adapter."""

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

from ai_stock.recommendation.candidate_input_preflight import (
    CandidateInput,
    FORBIDDEN_CANDIDATE_LABELS,
)
from ai_stock.recommendation.watchlist_model import WatchlistItem
from ai_stock.recommendation.watchlist_source import (
    ALLOWED_MANUAL_WATCHLIST_SOURCE_TYPES,
    FORBIDDEN_MANUAL_WATCHLIST_SOURCE_TYPES,
    FORBIDDEN_WATCHLIST_SOURCE_FIELDS,
    ManualWatchlistSourceType,
    WatchlistSourceConfig,
    build_local_static_watchlist_source,
    build_manual_watchlist_from_items,
    build_manual_watchlist_from_symbols,
    build_manual_watchlist_source_policy,
    build_watchlist_source_result,
    normalize_manual_symbol_record,
    validate_watchlist_source_config,
)


class WatchlistSourceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_manual_watchlist_source_policy()

    def test_default_policy_identity_and_immutability(self) -> None:
        self.assertEqual(self.policy.stage_name, "MS-09.03")
        self.assertEqual(self.policy.mode, "manual_local_watchlist_source")
        with self.assertRaises(FrozenInstanceError):
            self.policy.db_write_required = True

    def test_allowed_source_types_are_documented(self) -> None:
        self.assertEqual(
            ALLOWED_MANUAL_WATCHLIST_SOURCE_TYPES,
            (
                "manual_symbols",
                "manual_watchlist_items",
                "local_static_candidates",
                "test_fixture_source",
            ),
        )

    def test_forbidden_source_types_are_rejected(self) -> None:
        for source_type in FORBIDDEN_MANUAL_WATCHLIST_SOURCE_TYPES:
            result = validate_watchlist_source_config(
                WatchlistSourceConfig(
                    source_type=source_type,
                    raw_items=("005930",),
                ),
                self.policy,
            )
            self.assertFalse(result.valid)
            self.assertEqual(
                result.validation_status,
                "unsupported_source_type",
            )
            self.assertIn("forbidden_source_type", result.rejection_reasons)

    def test_file_database_api_credential_account_sources_are_rejected(self) -> None:
        for source_type in (
            "file_path",
            "database_table",
            "sqlite_query",
            "toss_api_endpoint",
            "credential_based_source",
            "accountSeq_source",
        ):
            result = build_watchlist_source_result(
                WatchlistSourceConfig(
                    source_type=source_type,
                    raw_items=("005930",),
                ),
                self.policy,
            )
            self.assertIn("forbidden_source_type", result.rejection_reasons)
            self.assertEqual(result.summary.total_items, 0)

    def test_manual_symbol_list_converts_to_watchlist(self) -> None:
        watchlist = build_manual_watchlist_from_symbols(
            (" 005930 ", "MSFT"),
            source_label=" caller source ",
            watchlist_name=" Manual Symbols ",
            default_market="kospi",
            default_tags=(" local ", "manual"),
            default_group=" core ",
            default_reason=" caller supplied ",
        )
        self.assertEqual(watchlist.name, " Manual Symbols ")
        self.assertEqual(watchlist.source_label, " caller source ")
        self.assertEqual(len(watchlist.items), 2)
        self.assertEqual(watchlist.items[0].symbol, "005930")
        self.assertEqual(watchlist.items[0].market, "kospi")
        self.assertEqual(watchlist.items[0].source, "manual_watchlist")
        self.assertEqual(watchlist.items[0].tags, ("local", "manual"))
        self.assertEqual(watchlist.items[0].group, "core")
        self.assertEqual(watchlist.items[0].reason, "caller supplied")

    def test_manual_symbol_list_converts_to_candidate_inputs(self) -> None:
        result = build_watchlist_source_result(
            WatchlistSourceConfig(
                source_type=ManualWatchlistSourceType.MANUAL_SYMBOLS.value,
                source_label="manual symbols",
                raw_items=("005930",),
            ),
            self.policy,
        )
        self.assertEqual(
            result.candidate_inputs,
            (
                CandidateInput(
                    symbol="005930",
                    source="manual_watchlist",
                    market="unknown",
                    source_label="manual symbols",
                    enabled=True,
                ),
            ),
        )

    def test_manual_item_dict_converts_to_watchlist(self) -> None:
        watchlist = build_manual_watchlist_from_items(
            (
                {
                    "symbol": " AAPL ",
                    "name": " Apple ",
                    "market": "nasdaq",
                    "tags": (" tech ", ""),
                    "group": " US ",
                    "reason": " caller supplied ",
                    "priority": "7",
                    "note": " observe only ",
                },
            ),
            source_label="manual dict",
        )
        item = watchlist.items[0]
        self.assertEqual(
            item,
            WatchlistItem(
                symbol="AAPL",
                name="Apple",
                market="nasdaq",
                source="manual_watchlist",
                enabled=True,
                reason="caller supplied",
                tags=("tech",),
                group="US",
                priority=7,
                note="observe only",
            ),
        )

    def test_defaults_apply_to_item_dictionaries(self) -> None:
        result = build_watchlist_source_result(
            WatchlistSourceConfig(
                source_type="manual_watchlist_items",
                source_label="manual dict",
                default_market="kosdaq",
                default_tags=("growth",),
                default_group="screen-a",
                default_reason="manual review",
                raw_items=({"symbol": "035720"},),
            ),
            self.policy,
        )
        item = result.watchlist.items[0]
        self.assertEqual(item.market, "kosdaq")
        self.assertEqual(item.tags, ("growth",))
        self.assertEqual(item.group, "screen-a")
        self.assertEqual(item.reason, "manual review")

    def test_empty_symbol_is_rejected(self) -> None:
        result = build_watchlist_source_result(
            WatchlistSourceConfig(
                source_type="manual_symbols",
                raw_items=(" ",),
            ),
            self.policy,
        )
        self.assertEqual(result.validation.items[0].validation_status, "invalid_symbol")
        self.assertIn("symbol_required", result.validation.items[0].rejection_reasons)

    def test_symbol_trim_processing(self) -> None:
        item = normalize_manual_symbol_record(
            " 005930 ",
            WatchlistSourceConfig(source_type="manual_symbols"),
        )
        self.assertEqual(item.symbol, "005930")

    def test_duplicate_symbol_processing(self) -> None:
        result = build_watchlist_source_result(
            WatchlistSourceConfig(
                source_type="manual_symbols",
                raw_items=("005930", " 005930 "),
            ),
            self.policy,
        )
        self.assertEqual(
            result.validation.validation_status,
            "contains_duplicate_candidates",
        )
        self.assertEqual(result.summary.duplicate_items, 1)
        self.assertEqual(
            result.validation.items[1].validation_status,
            "duplicate_candidate",
        )

    def test_disabled_item_processing(self) -> None:
        result = build_watchlist_source_result(
            WatchlistSourceConfig(
                source_type="manual_watchlist_items",
                raw_items=({"symbol": "005930", "enabled": "false"},),
            ),
            self.policy,
        )
        self.assertEqual(
            result.validation.items[0].validation_status,
            "disabled_candidate",
        )
        self.assertFalse(result.validation.items[0].selectable)

    def test_forbidden_candidate_source_rejects_item(self) -> None:
        result = build_watchlist_source_result(
            WatchlistSourceConfig(
                source_type="manual_watchlist_items",
                raw_items=(
                    {
                        "symbol": "005930",
                        "source": "real_account_holdings",
                    },
                ),
            ),
            self.policy,
        )
        self.assertEqual(
            result.validation.items[0].validation_status,
            "unsupported_source",
        )
        self.assertIn(
            "forbidden_source",
            result.validation.items[0].rejection_reasons,
        )

    def test_forbidden_field_detection(self) -> None:
        result = build_watchlist_source_result(
            WatchlistSourceConfig(
                source_type="manual_watchlist_items",
                raw_items=(
                    {
                        "symbol": "005930",
                        "accountSeq": "redacted-not-output",
                        "target_price": "redacted-not-output",
                    },
                ),
            ),
            self.policy,
        )
        self.assertIn("forbidden_field:accountSeq", result.rejection_reasons)
        self.assertIn("forbidden_field:target_price", result.rejection_reasons)
        self.assertIn(
            "forbidden_field_detected:accountSeq",
            result.diagnostics,
        )

    def test_forbidden_fields_are_not_in_output_model(self) -> None:
        result = build_watchlist_source_result(
            WatchlistSourceConfig(
                source_type="manual_watchlist_items",
                raw_items=(
                    {
                        "symbol": "005930",
                        "api_key": "redacted-not-output",
                        "balance": "redacted-not-output",
                        "score": "redacted-not-output",
                    },
                ),
            ),
            self.policy,
        )
        output = repr(result.watchlist.items) + repr(result.candidate_inputs)
        self.assertNotIn("redacted-not-output", output)
        self.assertNotIn("api_key=", output)
        self.assertNotIn("balance=", output)
        self.assertNotIn("score=", output)

    def test_forbidden_labels_are_not_generated_as_action_labels(self) -> None:
        result = build_watchlist_source_result(
            WatchlistSourceConfig(
                source_type="manual_symbols",
                raw_items=("005930", "MSFT"),
            ),
            self.policy,
        )
        produced_statuses = (
            result.validation.validation_status,
            *(item.validation_status for item in result.validation.items),
        )
        for forbidden_label in FORBIDDEN_CANDIDATE_LABELS:
            self.assertNotIn(forbidden_label, produced_statuses)

    def test_local_static_source_uses_local_snapshot_candidate_source(self) -> None:
        result = build_local_static_watchlist_source(
            WatchlistSourceConfig(
                source_type="manual_symbols",
                raw_items=({"symbol": "MSFT"},),
            ),
            self.policy,
        )
        self.assertEqual(result.source_type, "local_static_candidates")
        self.assertEqual(result.watchlist.items[0].source, "local_snapshot_summary")

    def test_insufficient_data_hint_processing(self) -> None:
        result = build_watchlist_source_result(
            WatchlistSourceConfig(
                source_type="manual_watchlist_items",
                raw_items=(
                    {
                        "symbol": "005930",
                        "data_availability_hint": "partial_data",
                    },
                ),
            ),
            self.policy,
        )
        self.assertEqual(result.validation.validation_status, "needs_review")
        self.assertEqual(result.summary.insufficient_data_items, 1)

    def test_result_required_flags_are_all_false(self) -> None:
        result = build_watchlist_source_result(
            WatchlistSourceConfig(
                source_type="manual_symbols",
                raw_items=("005930",),
            ),
            self.policy,
        )
        self.assertFalse(result.credential_required)
        self.assertFalse(result.db_read_required)
        self.assertFalse(result.db_write_required)
        self.assertFalse(result.file_read_required)
        self.assertFalse(result.file_write_required)
        self.assertFalse(result.toss_api_required)
        self.assertFalse(result.openai_required)
        self.assertFalse(result.oauth_required)
        self.assertFalse(result.account_seq_required)
        self.assertFalse(result.real_order_required)
        self.assertFalse(result.scoring_required)
        self.assertFalse(result.ui_required)

    def test_policy_disables_storage_loader_recommendation_scoring_and_ui(self) -> None:
        self.assertFalse(self.policy.actual_recommendation_allowed)
        self.assertFalse(self.policy.scoring_allowed)
        self.assertFalse(self.policy.watchlist_persistence_allowed)
        self.assertFalse(self.policy.file_loader_allowed)
        self.assertFalse(self.policy.ui_change_allowed)

    def test_forbidden_field_policy_is_documented(self) -> None:
        for forbidden_field in (
            "accountSeq",
            "access_token",
            "authorization",
            "api_key",
            "secret_key",
            "client_secret",
            "holdings",
            "balance",
            "fills",
            "order",
            "order_id",
            "avg_buy_price",
            "quantity",
            "target_price",
            "expected_return",
            "score",
            "buy",
            "sell",
            "hold",
        ):
            self.assertIn(forbidden_field, FORBIDDEN_WATCHLIST_SOURCE_FIELDS)

    def test_same_input_always_returns_same_output(self) -> None:
        config = WatchlistSourceConfig(
            source_type="manual_watchlist_items",
            default_tags=("manual",),
            raw_items=(
                {"symbol": "005930", "priority": 3},
                {"symbol": "005930", "priority": 4},
            ),
        )
        first = build_watchlist_source_result(config, self.policy)
        second = build_watchlist_source_result(config, self.policy)
        self.assertEqual(first, second)

    def test_module_structure_has_no_io_or_external_dependencies(self) -> None:
        module_path = Path("src/ai_stock/recommendation/watchlist_source.py")
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
                "collections.abc",
                "dataclasses",
                "enum",
                "ai_stock.recommendation.candidate_input_preflight",
                "ai_stock.recommendation.watchlist_model",
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
            "src/ai_stock/recommendation/watchlist_source.py"
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
