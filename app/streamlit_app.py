"""Minimal read-only local snapshot dashboard.

The full interactive UI is intentionally deferred to later Micro Stages.
"""

from streamlit import (
    caption,
    columns,
    error,
    expander,
    info,
    set_page_config,
    subheader,
    success,
    text_input,
    title,
    warning,
    write,
)

from ai_stock.recommendation.explanation_ui_preflight import (
    RecommendationExplanationViewModel,
    build_default_recommendation_explanation_ui_policy,
    build_recommendation_explanation_view_model,
    validate_recommendation_explanation_view_model,
)
from ai_stock.recommendation.mock_policy_model import (
    MockRecommendationInput,
    build_default_mock_recommendation_policy,
    build_mock_recommendation_result,
    validate_mock_recommendation_result,
)
from ai_stock.ui.readonly_snapshot_dashboard import (
    DASHBOARD_TITLE,
    DEFAULT_BASE_CURRENCY,
    DEFAULT_QUOTE_CURRENCY,
    DEFAULT_SYMBOL,
    ReadonlySnapshotDashboardView,
    build_readonly_snapshot_dashboard,
)


def _render_status(level: str, message: str) -> None:
    renderers = {
        "success": success,
        "warning": warning,
        "error": error,
    }
    renderers.get(level, info)(message)


def _render_optional_section(
    heading: str,
    values: dict[str, object] | None,
) -> None:
    with expander(heading, expanded=True):
        if values is None:
            info("No local snapshot is available for this section.")
            return
        for label, value in values.items():
            write(f"**{label.replace('_', ' ').title()}:** {value}")


def _build_mock_recommendation_input(
    view: ReadonlySnapshotDashboardView,
) -> MockRecommendationInput:
    completeness_flags = tuple(
        f"{name}_missing"
        for name, complete in view.completeness.items()
        if name != "all_components_present" and not complete
    )
    observation_notes = (
        "local_readonly_dashboard_summary",
        f"status_level={view.status_level}",
        f"stock_warnings_deferred={view.stock_warnings_deferred}",
    )
    return MockRecommendationInput(
        symbol=view.symbol,
        has_stock_info=view.stock_info is not None,
        has_price_snapshot=view.price_snapshot is not None,
        has_candle=view.candle is not None,
        has_exchange_rate=view.exchange_rate is not None,
        completeness_flags=completeness_flags,
        risk_flags=(),
        observation_notes=observation_notes,
    )


def _build_recommendation_explanation_view_model(
    view: ReadonlySnapshotDashboardView,
) -> RecommendationExplanationViewModel | None:
    mock_policy = build_default_mock_recommendation_policy()
    mock_result = build_mock_recommendation_result(
        _build_mock_recommendation_input(view),
        mock_policy,
    )
    mock_validation = validate_mock_recommendation_result(
        mock_result,
        mock_policy,
    )
    if not mock_validation.passed:
        return None

    ui_policy = build_default_recommendation_explanation_ui_policy()
    view_model = build_recommendation_explanation_view_model(
        mock_result,
        ui_policy,
    )
    ui_validation = validate_recommendation_explanation_view_model(
        view_model,
        ui_policy,
    )
    if not ui_validation.passed:
        return None
    return view_model


def _render_recommendation_explanation_panel(
    view: ReadonlySnapshotDashboardView,
) -> None:
    view_model = _build_recommendation_explanation_view_model(view)

    subheader("Mock Recommendation Explanation")
    caption("mock-only / observation-only / not investment advice")
    info(
        "mock-only | observation-only | not investment advice | "
        "no real recommendation | no order execution | no account access | "
        "no live API access | no credential required"
    )

    if view_model is None:
        warning(
            "The mock-only explanation panel is unavailable because safe "
            "ViewModel validation did not pass."
        )
        return

    summary_columns = columns(3)
    summary_columns[0].metric("Stage", view_model.stage_name)
    summary_columns[1].metric("Label", view_model.label)
    summary_columns[2].metric("Action allowed", "False")

    with expander("Safe summary", expanded=True):
        for line in view_model.safe_summary:
            write(line)

    for section in view_model.safe_sections:
        if section.name == "summary":
            continue
        with expander(section.heading, expanded=False):
            for line in section.lines:
                write(line)


def main() -> None:
    set_page_config(
        page_title="Local Snapshot Dashboard",
        page_icon="📊",
        layout="wide",
    )

    title(DASHBOARD_TITLE)
    caption("Local SQLite snapshot summary · read-only")

    subheader("Local read-only selection")
    selector_columns = columns(3)
    with selector_columns[0]:
        selected_symbol = text_input("Symbol", value=DEFAULT_SYMBOL)
    with selector_columns[1]:
        selected_base_currency = text_input(
            "Base currency",
            value=DEFAULT_BASE_CURRENCY,
            max_chars=3,
        )
    with selector_columns[2]:
        selected_quote_currency = text_input(
            "Quote currency",
            value=DEFAULT_QUOTE_CURRENCY,
            max_chars=3,
        )

    view = build_readonly_snapshot_dashboard(
        symbol=selected_symbol,
        base_currency=selected_base_currency,
        quote_currency=selected_quote_currency,
    )

    _render_status(view.status_level, view.status_message)

    _render_recommendation_explanation_panel(view)

    subheader("Data source")
    source_columns = columns(4)
    source_columns[0].metric("Source", view.data_source)
    source_columns[1].metric("Symbol", view.symbol)
    source_columns[2].metric("Exchange pair", view.exchange_pair)
    source_columns[3].metric("DB mode", view.db_open_mode)
    caption(f"Database: {view.database_path}")

    _render_optional_section("Latest stock information", view.stock_info)
    _render_optional_section("Latest price snapshot", view.price_snapshot)
    _render_optional_section("Latest candle", view.candle)
    _render_optional_section("Latest exchange rate", view.exchange_rate)

    subheader("Completeness")
    completeness_columns = columns(len(view.completeness))
    for column, (name, complete) in zip(
        completeness_columns,
        view.completeness.items(),
        strict=True,
    ):
        column.metric(name.replace("_", " ").title(), "Yes" if complete else "No")

    subheader("Source counts")
    count_columns = columns(len(view.source_counts))
    for column, (name, count) in zip(
        count_columns,
        view.source_counts.items(),
        strict=True,
    ):
        column.metric(name.replace("_", " ").title(), count)

    subheader("Read-only diagnostics")
    diagnostics = {
        "Database exists": view.db_file_exists,
        "Database size (bytes)": view.db_file_size_bytes,
        "Database modified time (UTC)": view.db_file_modified_time_utc,
        "Database modified by this view": (
            view.actual_db_file_modified_this_stage
        ),
        "Warnings deferred": view.stock_warnings_deferred,
    }
    for label, value in diagnostics.items():
        write(f"**{label}:** {value}")


if __name__ == "__main__":
    main()
