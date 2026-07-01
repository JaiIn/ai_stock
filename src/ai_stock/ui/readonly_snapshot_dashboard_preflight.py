"""Immutable no-I/O preflight for the read-only snapshot dashboard."""

from dataclasses import dataclass

STAGE = "MS-07.01"
PHASE = "readonly_streamlit_snapshot_dashboard_preflight"
PLANNED_DEFAULT_DB_RELATIVE_PATH = "data/local/ai_stock.sqlite3"
PLANNED_DEFAULT_SYMBOL = "005930"
PLANNED_DEFAULT_EXCHANGE_PAIR = "USD/KRW"
DATA_SOURCE = "local_snapshot_latest_read_model"

PLANNED_SECTIONS = (
    "data_health_summary",
    "selected_symbol_summary",
    "latest_stock_info_summary",
    "latest_price_snapshot_summary",
    "latest_candle_summary",
    "latest_exchange_rate_summary",
    "completeness_flags",
    "source_counts",
    "safety_status",
    "last_db_audit_metadata",
)

SAFE_DISPLAY_FIELDS = (
    "symbol",
    "stock_display_name",
    "market_or_exchange",
    "latest_price_safe_values",
    "latest_candle_ohlcv_safe_values",
    "usd_krw_exchange_rate_safe_values",
    "timestamp_strings",
    "source_counts",
    "completeness_flags",
    "read_only_status",
    "db_file_safe_metadata",
)

ALLOWED_ACTIONS = (
    "refresh_local_db_read_only_view",
    "select_symbol_from_safe_local_options",
    "show_latest_snapshot_summary",
    "show_completeness_flags",
    "show_safe_diagnostics",
)

FORBIDDEN_ACTIONS = (
    "refresh_from_live_api",
    "issue_oauth_token",
    "read_env_local",
    "write_database",
    "run_database_migration",
    "initialize_schema",
    "query_order_asset_account_balance_fill",
    "submit_order",
    "cancel_order",
    "modify_order",
    "generate_ai_recommendation",
    "show_final_buy_sell_hold_recommendation",
    "value_portfolio_from_real_account",
    "show_automatic_order_button",
    "show_real_order_button",
)

FORBIDDEN_SENSITIVE_FIELDS = (
    "full_database_row",
    "raw_response_body",
    "credential",
    "access_token",
    "authorization_header",
    "account_seq",
    "real_order_account_asset_balance_fill_data",
)


@dataclass(frozen=True, slots=True)
class ReadonlySnapshotDashboardPreflight:
    stage: str
    phase: str
    dashboard_type: str
    planned_default_db_relative_path: str
    planned_default_symbol: str
    planned_default_exchange_pair: str
    data_source: str
    ui_read_only: bool
    db_open_mode_planned: str
    db_write_allowed_this_stage: bool
    actual_db_file_modified_this_stage: bool
    api_call_allowed_this_stage: bool
    oauth_token_endpoint_allowed_this_stage: bool
    env_file_read_allowed_this_stage: bool
    credential_required_this_stage: bool
    account_seq_allowed: bool
    real_order_related_call_allowed: bool
    ai_recommendation_allowed_this_stage: bool
    streamlit_full_ui_allowed_this_stage: bool
    stock_warnings_included: bool
    stock_warnings_deferred: bool
    planned_sections: tuple[str, ...]
    safe_display_fields: tuple[str, ...]
    allowed_actions: tuple[str, ...]
    forbidden_actions: tuple[str, ...]
    forbidden_sensitive_fields: tuple[str, ...]


def build_readonly_snapshot_dashboard_preflight(
) -> ReadonlySnapshotDashboardPreflight:
    """Return the fixed no-I/O policy for the future dashboard stage."""

    return ReadonlySnapshotDashboardPreflight(
        stage=STAGE,
        phase=PHASE,
        dashboard_type="streamlit",
        planned_default_db_relative_path=PLANNED_DEFAULT_DB_RELATIVE_PATH,
        planned_default_symbol=PLANNED_DEFAULT_SYMBOL,
        planned_default_exchange_pair=PLANNED_DEFAULT_EXCHANGE_PAIR,
        data_source=DATA_SOURCE,
        ui_read_only=True,
        db_open_mode_planned="readonly",
        db_write_allowed_this_stage=False,
        actual_db_file_modified_this_stage=False,
        api_call_allowed_this_stage=False,
        oauth_token_endpoint_allowed_this_stage=False,
        env_file_read_allowed_this_stage=False,
        credential_required_this_stage=False,
        account_seq_allowed=False,
        real_order_related_call_allowed=False,
        ai_recommendation_allowed_this_stage=False,
        streamlit_full_ui_allowed_this_stage=False,
        stock_warnings_included=False,
        stock_warnings_deferred=True,
        planned_sections=PLANNED_SECTIONS,
        safe_display_fields=SAFE_DISPLAY_FIELDS,
        allowed_actions=ALLOWED_ACTIONS,
        forbidden_actions=FORBIDDEN_ACTIONS,
        forbidden_sensitive_fields=FORBIDDEN_SENSITIVE_FIELDS,
    )
