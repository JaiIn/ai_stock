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

from ai_stock.ui.readonly_snapshot_dashboard import (
    DASHBOARD_TITLE,
    DEFAULT_BASE_CURRENCY,
    DEFAULT_QUOTE_CURRENCY,
    DEFAULT_SYMBOL,
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
