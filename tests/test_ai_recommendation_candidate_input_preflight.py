"""Offline tests for the MS-09.01 candidate input contract preflight."""

import ast
from dataclasses import FrozenInstanceError
from pathlib import Path
import unittest

from ai_stock.recommendation.candidate_input_preflight import (
    ALLOWED_CANDIDATE_SOURCES,
    FORBIDDEN_CANDIDATE_LABELS,
    FORBIDDEN_CANDIDATE_SOURCES,
    SAFE_CANDIDATE_STATUSES,
    CandidateInput,
    build_candidate_input_preflight_policy,
    build_candidate_input_preflight_summary,
    validate_candidate_batch,
    validate_candidate_input,
)


class CandidateInputPreflightTests(unittest.TestCase):
    def setUp(self) -> None:
        self.policy = build_candidate_input_preflight_policy()

    def test_default_policy_identity_and_immutability(self) -> None:
        self.assertEqual(self.policy.stage_name, "MS-09.01")
        self.assertEqual(
            self.policy.mode,
            "candidate_input_contract_preflight",
        )
        with self.assertRaises(FrozenInstanceError):
            self.policy.db_write_required = True

    def test_allowed_sources_are_valid_or_safe_status(self) -> None:
        for source in ALLOWED_CANDIDATE_SOURCES:
            result = validate_candidate_input(
                CandidateInput(symbol="005930", source=source),
                self.policy,
            )
            self.assertIn(result.validation_status, SAFE_CANDIDATE_STATUSES)
            self.assertNotEqual(result.validation_status, "unsupported_source")

    def test_forbidden_sources_are_rejected(self) -> None:
        for source in FORBIDDEN_CANDIDATE_SOURCES:
            result = validate_candidate_input(
                CandidateInput(symbol="005930", source=source),
                self.policy,
            )
            self.assertEqual(result.validation_status, "unsupported_source")
            self.assertIn("forbidden_source", result.rejection_reasons)
            self.assertFalse(result.selectable)

    def test_empty_symbol_is_invalid_symbol(self) -> None:
        result = validate_candidate_input(
            CandidateInput(symbol="  ", source="dashboard_selector"),
            self.policy,
        )
        self.assertEqual(result.validation_status, "invalid_symbol")
        self.assertIn("symbol_required", result.rejection_reasons)
        self.assertFalse(result.selectable)

    def test_symbol_is_trimmed(self) -> None:
        result = validate_candidate_input(
            CandidateInput(symbol=" 005930 ", source="dashboard_selector"),
            self.policy,
        )
        self.assertEqual(result.symbol, "005930")
        self.assertEqual(result.validation_status, "valid_candidate")

    def test_too_long_symbol_is_rejected(self) -> None:
        result = validate_candidate_input(
            CandidateInput(
                symbol="A" * (self.policy.max_symbol_length + 1),
                source="manual_watchlist",
            ),
            self.policy,
        )
        self.assertEqual(result.validation_status, "invalid_symbol")
        self.assertFalse(result.selectable)

    def test_unknown_market_becomes_unknown_safe_status(self) -> None:
        result = validate_candidate_input(
            CandidateInput(
                symbol="MSFT",
                source="manual_watchlist",
                market="unexpected_market",
            ),
            self.policy,
        )
        self.assertEqual(result.market, "UNKNOWN")
        self.assertEqual(result.validation_status, "valid_candidate")

    def test_disabled_candidate_is_safe_disabled_status(self) -> None:
        result = validate_candidate_input(
            CandidateInput(
                symbol="005930",
                source="manual_watchlist",
                enabled=False,
            ),
            self.policy,
        )
        self.assertEqual(result.validation_status, "disabled_candidate")
        self.assertIn("candidate_disabled", result.rejection_reasons)
        self.assertFalse(result.selectable)

    def test_insufficient_data_hint_is_safe_status(self) -> None:
        result = validate_candidate_input(
            CandidateInput(
                symbol="005930",
                source="local_snapshot_summary",
                data_availability_hint="insufficient_data",
            ),
            self.policy,
        )
        self.assertEqual(result.validation_status, "insufficient_data")
        self.assertFalse(result.selectable)

    def test_needs_review_hint_is_safe_status(self) -> None:
        result = validate_candidate_input(
            CandidateInput(
                symbol="005930",
                source="local_snapshot_summary",
                data_availability_hint="needs_data_review",
            ),
            self.policy,
        )
        self.assertEqual(result.validation_status, "needs_review")
        self.assertFalse(result.selectable)

    def test_duplicate_policy_marks_later_duplicate_without_storage(self) -> None:
        results = validate_candidate_batch(
            (
                CandidateInput(symbol="005930", source="manual_watchlist"),
                CandidateInput(symbol=" 005930 ", source="test_fixture"),
            ),
            self.policy,
        )
        self.assertEqual(results[0].validation_status, "valid_candidate")
        self.assertEqual(results[1].validation_status, "duplicate_candidate")
        self.assertIn("duplicate_symbol", results[1].rejection_reasons)
        self.assertEqual(
            self.policy.duplicate_handling_policy,
            "mark_duplicate_candidate_without_persistence",
        )

    def test_forbidden_labels_are_not_generated(self) -> None:
        summary = build_candidate_input_preflight_summary(
            (
                CandidateInput(symbol="005930", source="dashboard_selector"),
                CandidateInput(symbol="", source="dashboard_selector"),
                CandidateInput(
                    symbol="AAPL",
                    source="real_account_holdings",
                ),
            ),
            self.policy,
        )
        for forbidden_label in FORBIDDEN_CANDIDATE_LABELS:
            for candidate in summary.candidates:
                self.assertNotEqual(candidate.validation_status, forbidden_label)

    def test_summary_required_flags_are_all_false(self) -> None:
        summary = build_candidate_input_preflight_summary(
            (CandidateInput(symbol="005930", source="dashboard_selector"),),
            self.policy,
        )
        self.assertFalse(summary.credential_required)
        self.assertFalse(summary.db_read_required)
        self.assertFalse(summary.db_write_required)
        self.assertFalse(summary.toss_api_required)
        self.assertFalse(summary.openai_required)
        self.assertFalse(summary.oauth_required)
        self.assertFalse(summary.account_seq_required)
        self.assertFalse(summary.real_order_required)

    def test_summary_counts_are_deterministic_and_safe(self) -> None:
        candidates = (
            CandidateInput(symbol="005930", source="dashboard_selector"),
            CandidateInput(symbol="", source="dashboard_selector"),
            CandidateInput(
                symbol="MSFT",
                source="local_snapshot_summary",
                data_availability_hint="insufficient_data",
            ),
            CandidateInput(symbol="AAPL", source="credential_based_source"),
            CandidateInput(symbol="005930", source="manual_watchlist"),
        )
        first = build_candidate_input_preflight_summary(candidates, self.policy)
        second = build_candidate_input_preflight_summary(candidates, self.policy)
        self.assertEqual(first, second)
        self.assertEqual(first.total_candidates, 5)
        self.assertEqual(first.valid_candidates, 1)
        self.assertEqual(first.rejected_candidates, 3)
        self.assertEqual(first.insufficient_data_candidates, 1)
        self.assertEqual(first.forbidden_source_candidates, 1)
        self.assertEqual(first.duplicate_candidates, 1)

    def test_policy_disables_recommendation_scoring_ui_and_storage(self) -> None:
        self.assertFalse(self.policy.actual_recommendation_allowed)
        self.assertFalse(self.policy.scoring_allowed)
        self.assertFalse(self.policy.watchlist_write_allowed)
        self.assertFalse(self.policy.ui_change_allowed)

    def test_module_structure_has_no_io_or_external_dependencies(self) -> None:
        module_path = Path(
            "src/ai_stock/recommendation/candidate_input_preflight.py"
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

        self.assertEqual(imported_modules, {"dataclasses", "enum"})
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
            "src/ai_stock/recommendation/candidate_input_preflight.py"
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

    def _summary_strings(self, summary) -> str:
        values: list[str] = [
            summary.stage_name,
            summary.mode,
        ]
        for candidate in summary.candidates:
            values.extend(
                (
                    candidate.symbol,
                    candidate.name,
                    candidate.market,
                    candidate.source,
                    candidate.source_label,
                    candidate.reason,
                    candidate.data_availability_hint,
                    candidate.validation_status,
                    *candidate.tags,
                    *candidate.rejection_reasons,
                )
            )
        return "\n".join(values).casefold()


if __name__ == "__main__":
    unittest.main()
