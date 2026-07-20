"""Offline tests for the MS-13.00 observation-list UI preflight."""

from dataclasses import FrozenInstanceError, fields
from types import FunctionType
import unittest

import ai_stock.recommendation.observation_list_ui_preflight as ui_preflight
from ai_stock.recommendation.observation_list_ui_preflight import (
    ALLOWED_OBSERVATION_LIST_BADGE_LABELS,
    ALLOWED_OBSERVATION_LIST_COLUMN_KEYS,
    ALLOWED_OBSERVATION_LIST_VIEW_MODES,
    FORBIDDEN_OBSERVATION_LIST_BADGE_LABELS,
    FORBIDDEN_OBSERVATION_LIST_COLUMN_KEYS,
    FORBIDDEN_OBSERVATION_LIST_UI_OUTPUT_KEYWORDS,
    OBSERVATION_LIST_UI_REQUIRED_DISCLAIMER_LABELS,
    OBSERVATION_LIST_UI_REQUIRED_FALSE_FLAGS,
    ObservationListUIPreflightPolicy,
    ObservationListUIRow,
    ObservationListUIValidationResult,
    build_observation_list_ui_preflight_policy,
    build_observation_list_ui_row_from_item,
    build_observation_list_ui_rows_from_all_fixtures,
    build_observation_list_ui_rows_from_items,
    summarize_observation_list_ui_rows,
    validate_observation_list_ui_row,
    validate_observation_list_ui_rows,
)
from ai_stock.recommendation.recommendation_list_preflight import (
    ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES,
    FORBIDDEN_RECOMMENDATION_LIST_ACTION_LABELS,
    FORBIDDEN_RECOMMENDATION_LIST_RANKING_LABELS,
    FORBIDDEN_RECOMMENDATION_LIST_RECOMMENDATION_LABELS,
    build_recommendation_list_items_from_all_fixtures,
)


class ObservationListUIPreflightTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.policy = build_observation_list_ui_preflight_policy()
        cls.items = build_recommendation_list_items_from_all_fixtures()
        cls.rows = build_observation_list_ui_rows_from_all_fixtures(cls.policy)

    def test_observation_list_ui_preflight_policy_generation(self) -> None:
        self.assertIsInstance(self.policy, ObservationListUIPreflightPolicy)
        self.assertEqual(self.policy.preflight_version, "MS-13.00")
        self.assertEqual(
            self.policy.preflight_scope,
            "observation_list_ui_preflight_shape_only",
        )
        self.assertEqual(
            self.policy.allowed_view_modes,
            ALLOWED_OBSERVATION_LIST_VIEW_MODES,
        )
        self.assertEqual(
            self.policy.allowed_column_keys,
            ALLOWED_OBSERVATION_LIST_COLUMN_KEYS,
        )
        self.assertFalse(self.policy.streamlit_required)
        self.assertFalse(self.policy.ui_integration_required)
        with self.assertRaises(FrozenInstanceError):
            self.policy.streamlit_required = True

    def test_allowed_and_forbidden_column_keys(self) -> None:
        self.assertIn("status_badge", self.policy.allowed_column_keys)
        self.assertIn("score_snapshot_label", self.policy.allowed_column_keys)
        self.assertIn("guardrail_flags", self.policy.allowed_column_keys)
        for forbidden in (
            "button",
            "callback",
            "session_state",
            "api_refresh",
            "oauth_login",
            "credential_input",
            "accountSeq_input",
            "rank",
            "ranking",
            "ranking_position",
            "priority",
            "order",
            "recommendation",
            "action",
        ):
            self.assertIn(forbidden, self.policy.forbidden_column_keys)
            self.assertNotIn(forbidden, self.policy.allowed_column_keys)
        self.assertEqual(
            self.policy.forbidden_column_keys,
            FORBIDDEN_OBSERVATION_LIST_COLUMN_KEYS,
        )

    def test_allowed_and_forbidden_badge_labels(self) -> None:
        self.assertEqual(
            self.policy.allowed_badge_labels,
            ALLOWED_OBSERVATION_LIST_BADGE_LABELS,
        )
        self.assertEqual(
            self.policy.forbidden_badge_labels,
            FORBIDDEN_OBSERVATION_LIST_BADGE_LABELS,
        )
        for allowed in (
            "review_ready",
            "review_needed",
            "quality_blocked",
            "sanitized_input",
            "empty_input",
        ):
            self.assertIn(allowed, self.policy.allowed_badge_labels)
        for forbidden in ("buy", "sell", "hold", "ranking", "action"):
            self.assertIn(forbidden, self.policy.forbidden_badge_labels)
            self.assertNotIn(forbidden, self.policy.allowed_badge_labels)

    def test_ui_row_model_creation_from_item(self) -> None:
        row = build_observation_list_ui_row_from_item(self.items[0], self.policy)
        field_names = tuple(field.name for field in fields(ObservationListUIRow))

        self.assertIsInstance(row, ObservationListUIRow)
        self.assertEqual(field_names, self.policy.allowed_column_keys)
        self.assertEqual(row.item_status, "item_ready_for_review")
        self.assertEqual(row.status_badge, "review_ready")
        self.assertIn("observation_only_preflight", row.disclaimer_labels)
        with self.assertRaises(FrozenInstanceError):
            row.status_badge = "changed"

    def test_rows_created_from_items_and_all_fixtures(self) -> None:
        rows_from_items = build_observation_list_ui_rows_from_items(
            self.items,
            self.policy,
        )

        self.assertEqual(rows_from_items, self.rows)
        self.assertEqual(len(self.rows), 11)
        self.assertEqual(
            tuple(row.item_status for row in self.rows),
            tuple(item.item_status for item in self.items),
        )

    def test_deterministic_output(self) -> None:
        self.assertEqual(
            build_observation_list_ui_rows_from_all_fixtures(self.policy),
            build_observation_list_ui_rows_from_all_fixtures(self.policy),
        )
        self.assertEqual(
            build_observation_list_ui_rows_from_items(self.items, self.policy),
            build_observation_list_ui_rows_from_items(self.items, self.policy),
        )

    def test_row_validation_passes(self) -> None:
        validations = validate_observation_list_ui_rows(self.rows, self.policy)

        self.assertTrue(all(validation.valid for validation in validations))
        self.assertTrue(
            all(isinstance(validation, ObservationListUIValidationResult) for validation in validations)
        )
        for validation in validations:
            self.assertEqual(validation.rejection_reasons, ())
            self.assertFalse(validation.forbidden_ui_control_present)

    def test_summary_is_deterministic(self) -> None:
        first = summarize_observation_list_ui_rows(self.rows)
        second = summarize_observation_list_ui_rows(self.rows)

        self.assertEqual(first, second)
        self.assertEqual(first.total_rows, 11)
        self.assertEqual(first.ready_rows, 4)
        self.assertEqual(first.needs_review_rows, 7)
        self.assertIn("no_streamlit_rendering", first.diagnostics)

    def test_status_badge_is_not_trade_directive(self) -> None:
        forbidden = (
            *FORBIDDEN_RECOMMENDATION_LIST_ACTION_LABELS,
            "buy",
            "sell",
            "hold",
            "strong_buy",
            "must_buy",
            "must_sell",
        )

        for row in self.rows:
            self.assertNotIn(row.status_badge, forbidden)
            self.assertIn(row.status_badge, self.policy.allowed_badge_labels)

    def test_score_snapshot_label_is_not_directive_output(self) -> None:
        for row in self.rows:
            self.assertIn("quality_preflight_score:", row.score_snapshot_label)
            for forbidden in ("recommendation", "ranking", "action"):
                self.assertNotIn(forbidden, row.score_snapshot_label)
            self.assertFalse(
                validate_observation_list_ui_row(
                    row,
                    self.policy,
                ).score_snapshot_label_directive_present
            )

    def test_display_bucket_is_not_ranking_priority_or_order(self) -> None:
        for row in self.rows:
            self.assertNotIn("rank", row.display_bucket)
            self.assertNotIn("priority", row.display_bucket)
            self.assertNotIn("order", row.display_bucket)
            self.assertFalse(
                validate_observation_list_ui_row(
                    row,
                    self.policy,
                ).display_bucket_ranking_present
            )

    def test_usability_label_is_not_ranking_flag(self) -> None:
        for row in self.rows:
            self.assertIn(row.usability_label, ("future_list_ready", "future_list_review_only"))
            self.assertNotIn("rank", row.usability_label)
            self.assertNotIn("priority", row.usability_label)
            self.assertNotIn("order", row.usability_label)
            self.assertFalse(
                validate_observation_list_ui_row(
                    row,
                    self.policy,
                ).usability_label_ranking_present
            )

    def test_forbidden_output_field_is_not_copied_to_ui_row(self) -> None:
        rendered = repr(self.rows)

        for keyword in FORBIDDEN_OBSERVATION_LIST_UI_OUTPUT_KEYWORDS:
            self.assertNotIn(keyword, rendered)
        for forbidden in (
            "accountSeq",
            "access_token",
            "authorization",
            "bearer",
            "api_key",
            "secret_key",
            "raw_response",
            "raw_request",
            "db_row",
            "file_path",
            ".env.local",
        ):
            self.assertNotIn(forbidden, rendered)

    def test_required_flags_all_false(self) -> None:
        for row in self.rows:
            self.assertEqual(
                row.guardrail_flags,
                tuple(
                    f"{flag}=false"
                    for flag in OBSERVATION_LIST_UI_REQUIRED_FALSE_FLAGS
                ),
            )
            self.assertFalse(any(flag.endswith("=true") for flag in row.guardrail_flags))
        self.assertFalse(
            build_observation_list_ui_preflight_policy().recommendation_required
        )
        self.assertFalse(build_observation_list_ui_preflight_policy().ranking_required)
        self.assertFalse(
            build_observation_list_ui_preflight_policy().ui_integration_required
        )

    def test_disclaimer_labels_keep_observation_only_meaning(self) -> None:
        for row in self.rows:
            self.assertEqual(
                row.disclaimer_labels,
                OBSERVATION_LIST_UI_REQUIRED_DISCLAIMER_LABELS,
            )
            self.assertIn("observation_only_preflight", row.disclaimer_labels)
            self.assertIn("not_trade_directive", row.disclaimer_labels)

    def test_allowed_item_statuses_only(self) -> None:
        produced_statuses = tuple(row.item_status for row in self.rows)

        self.assertTrue(
            set(produced_statuses).issubset(ALLOWED_RECOMMENDATION_LIST_ITEM_STATUSES)
        )
        for forbidden in (
            *FORBIDDEN_RECOMMENDATION_LIST_ACTION_LABELS,
            *FORBIDDEN_RECOMMENDATION_LIST_RECOMMENDATION_LABELS,
            *FORBIDDEN_RECOMMENDATION_LIST_RANKING_LABELS,
            "ranking_position",
            "priority",
            "order",
        ):
            self.assertNotIn(forbidden, produced_statuses)

    def test_no_streamlit_or_ui_control_runtime_imports(self) -> None:
        runtime_modules = {
            getattr(value, "__module__", "") for value in vars(ui_preflight).values()
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

    def test_no_file_network_env_db_access_calls(self) -> None:
        called_names = _ui_preflight_module_code_names()

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

    def test_no_streamlit_controls_or_forbidden_paths_are_referenced(self) -> None:
        constants = _ui_preflight_module_constants()
        module_symbols = {
            str(part).casefold() for part in (*vars(ui_preflight), *constants)
        }

        for forbidden in (
            "import streamlit",
            "st.button",
            "session_state",
            "app/streamlit_app.py",
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

    def test_no_forbidden_action_status_output_is_generated(self) -> None:
        produced_values = tuple(row.item_status for row in self.rows) + tuple(
            row.status_badge for row in self.rows
        )

        for forbidden_label in (
            *FORBIDDEN_RECOMMENDATION_LIST_ACTION_LABELS,
            *FORBIDDEN_RECOMMENDATION_LIST_RECOMMENDATION_LABELS,
            *FORBIDDEN_RECOMMENDATION_LIST_RANKING_LABELS,
            "ranking_position",
            "priority",
            "order",
        ):
            self.assertNotIn(forbidden_label, produced_values)


def _ui_preflight_module_code_names() -> set[str]:
    names: set[str] = set()
    for value in vars(ui_preflight).values():
        if isinstance(value, FunctionType):
            names.update(value.__code__.co_names)
    return names


def _ui_preflight_module_constants() -> tuple[object, ...]:
    constants: list[object] = []
    for value in vars(ui_preflight).values():
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
