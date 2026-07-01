"""Read-only latest snapshot model backed by the local SQLite database."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path
import sqlite3
from typing import Any

STAGE = "MS-06.11"
PHASE = "local_snapshot_latest_read_model"
PLANNED_DB_RELATIVE_PATH = "data/local/ai_stock.sqlite3"
DEFAULT_SYMBOL = "005930"
DEFAULT_BASE_CURRENCY = "USD"
DEFAULT_QUOTE_CURRENCY = "KRW"
DEFAULT_CANDLE_INTERVAL = "1d"


@dataclass(frozen=True, slots=True)
class StockSummary:
    symbol: str
    display_name: str
    market: str | None
    currency: str | None
    observed_at: str


@dataclass(frozen=True, slots=True)
class LatestPriceSummary:
    price: Decimal
    timestamp: str
    currency: str | None


@dataclass(frozen=True, slots=True)
class LatestCandleSummary:
    interval: str
    timestamp: str
    open: Decimal
    high: Decimal
    low: Decimal
    close: Decimal
    volume: Decimal
    currency: str | None
    ohlcv_present: bool


@dataclass(frozen=True, slots=True)
class LatestExchangeRateSummary:
    base_currency: str
    quote_currency: str
    exchange_rate: Decimal
    timestamp: str | None


@dataclass(frozen=True, slots=True)
class SourceCounts:
    stocks: int = 0
    price_snapshots: int = 0
    candles: int = 0
    exchange_rates: int = 0


@dataclass(frozen=True, slots=True)
class CompletenessFlags:
    stock_info_present: bool = False
    price_snapshot_present: bool = False
    candle_present: bool = False
    exchange_rate_present: bool = False
    all_components_present: bool = False


@dataclass(frozen=True, slots=True)
class LocalSnapshotLatestReadModel:
    success: bool
    stage: str
    phase: str
    planned_db_relative_path: str
    db_file_exists: bool
    db_open_mode: str
    db_write_allowed_this_stage: bool
    actual_db_file_modified_this_stage: bool
    api_call_allowed_this_stage: bool
    oauth_token_endpoint_allowed_this_stage: bool
    env_file_read_allowed_this_stage: bool
    credential_required_this_stage: bool
    account_seq_allowed: bool
    real_order_related_call_allowed: bool
    stock_warnings_included: bool
    stock_warnings_deferred: bool
    symbol: str
    exchange_rate_pair: str
    candle_interval: str
    stock: StockSummary | None
    latest_price: LatestPriceSummary | None
    latest_candle: LatestCandleSummary | None
    latest_exchange_rate: LatestExchangeRateSummary | None
    source_counts: SourceCounts
    completeness: CompletenessFlags
    safe_error_type: str | None
    safe_error_message: str | None

    def safe_dict(self) -> dict[str, object]:
        """Return JSON-safe structured data without raw rows or secret fields."""

        return _json_safe(asdict(self))


def build_local_snapshot_latest_read_model(
    database_path: str | Path = PLANNED_DB_RELATIVE_PATH,
    *,
    symbol: str = DEFAULT_SYMBOL,
    base_currency: str = DEFAULT_BASE_CURRENCY,
    quote_currency: str = DEFAULT_QUOTE_CURRENCY,
    candle_interval: str = DEFAULT_CANDLE_INTERVAL,
) -> LocalSnapshotLatestReadModel:
    """Build a latest snapshot model using aggregate and single-row SELECTs only."""

    path = Path(database_path)
    before = _file_metadata(path)
    if before is None:
        return _failure(
            symbol=symbol,
            base_currency=base_currency,
            quote_currency=quote_currency,
            candle_interval=candle_interval,
            db_file_exists=False,
            modified=False,
            error_type="database_not_found",
            error_message="The local snapshot database file does not exist.",
        )

    try:
        connection = _open_readonly(path)
        try:
            counts = _source_counts(
                connection,
                symbol=symbol,
                base_currency=base_currency,
                quote_currency=quote_currency,
                candle_interval=candle_interval,
            )
            stock = _latest_stock(connection, symbol)
            price = _latest_price(connection, symbol)
            candle = _latest_candle(connection, symbol, candle_interval)
            exchange_rate = _latest_exchange_rate(
                connection,
                base_currency,
                quote_currency,
            )
        finally:
            connection.close()
    except (sqlite3.Error, InvalidOperation, TypeError, ValueError):
        after = _file_metadata(path)
        return _failure(
            symbol=symbol,
            base_currency=base_currency,
            quote_currency=quote_currency,
            candle_interval=candle_interval,
            db_file_exists=True,
            modified=after != before,
            error_type="database_read_failed",
            error_message="The latest snapshot read model failed safely.",
        )

    after = _file_metadata(path)
    modified = after != before
    if stock is None:
        return _failure(
            symbol=symbol,
            base_currency=base_currency,
            quote_currency=quote_currency,
            candle_interval=candle_interval,
            db_file_exists=True,
            modified=modified,
            error_type="symbol_not_found",
            error_message="The requested stock symbol was not found.",
            counts=counts,
            price=price,
            candle=candle,
            exchange_rate=exchange_rate,
        )
    if modified:
        return _failure(
            symbol=symbol,
            base_currency=base_currency,
            quote_currency=quote_currency,
            candle_interval=candle_interval,
            db_file_exists=True,
            modified=True,
            error_type="database_modified_during_read",
            error_message="The database metadata changed during the read-only query.",
            counts=counts,
            stock=stock,
            price=price,
            candle=candle,
            exchange_rate=exchange_rate,
        )

    completeness = _completeness(stock, price, candle, exchange_rate)
    return _model(
        success=True,
        symbol=symbol,
        base_currency=base_currency,
        quote_currency=quote_currency,
        candle_interval=candle_interval,
        db_file_exists=True,
        modified=False,
        stock=stock,
        price=price,
        candle=candle,
        exchange_rate=exchange_rate,
        counts=counts,
        completeness=completeness,
        error_type=None,
        error_message=None,
    )


def _open_readonly(path: Path) -> sqlite3.Connection:
    uri = f"{path.resolve().as_uri()}?mode=ro"
    connection = sqlite3.connect(uri, uri=True)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA query_only = ON")
    return connection


def _source_counts(
    connection: sqlite3.Connection,
    *,
    symbol: str,
    base_currency: str,
    quote_currency: str,
    candle_interval: str,
) -> SourceCounts:
    return SourceCounts(
        stocks=_scalar(
            connection,
            "SELECT COUNT(*) FROM stocks WHERE symbol = ?",
            (symbol,),
        ),
        price_snapshots=_scalar(
            connection,
            "SELECT COUNT(*) FROM price_snapshots WHERE symbol = ?",
            (symbol,),
        ),
        candles=_scalar(
            connection,
            "SELECT COUNT(*) FROM candles WHERE symbol = ? AND interval = ?",
            (symbol, candle_interval),
        ),
        exchange_rates=_scalar(
            connection,
            "SELECT COUNT(*) FROM exchange_rates "
            "WHERE base_currency = ? AND quote_currency = ?",
            (base_currency, quote_currency),
        ),
    )


def _latest_stock(
    connection: sqlite3.Connection,
    symbol: str,
) -> StockSummary | None:
    row = connection.execute(
        """
        SELECT symbol, name, market, currency, updated_at
        FROM stocks
        WHERE symbol = ?
        LIMIT 1
        """,
        (symbol,),
    ).fetchone()
    if row is None:
        return None
    return StockSummary(
        symbol=row["symbol"],
        display_name=row["name"],
        market=row["market"],
        currency=row["currency"],
        observed_at=row["updated_at"],
    )


def _latest_price(
    connection: sqlite3.Connection,
    symbol: str,
) -> LatestPriceSummary | None:
    row = connection.execute(
        """
        SELECT timestamp, price, currency
        FROM price_snapshots
        WHERE symbol = ?
        ORDER BY timestamp DESC, id DESC
        LIMIT 1
        """,
        (symbol,),
    ).fetchone()
    if row is None:
        return None
    return LatestPriceSummary(
        price=_decimal(row["price"]),
        timestamp=row["timestamp"],
        currency=row["currency"],
    )


def _latest_candle(
    connection: sqlite3.Connection,
    symbol: str,
    interval: str,
) -> LatestCandleSummary | None:
    row = connection.execute(
        """
        SELECT interval, timestamp, open, high, low, close, volume, currency
        FROM candles
        WHERE symbol = ? AND interval = ?
        ORDER BY timestamp DESC, id DESC
        LIMIT 1
        """,
        (symbol, interval),
    ).fetchone()
    if row is None:
        return None
    values = (
        _decimal(row["open"]),
        _decimal(row["high"]),
        _decimal(row["low"]),
        _decimal(row["close"]),
        _decimal(row["volume"]),
    )
    return LatestCandleSummary(
        interval=row["interval"],
        timestamp=row["timestamp"],
        open=values[0],
        high=values[1],
        low=values[2],
        close=values[3],
        volume=values[4],
        currency=row["currency"],
        ohlcv_present=all(value.is_finite() for value in values),
    )


def _latest_exchange_rate(
    connection: sqlite3.Connection,
    base_currency: str,
    quote_currency: str,
) -> LatestExchangeRateSummary | None:
    row = connection.execute(
        """
        SELECT base_currency, quote_currency, exchange_rate, date_time
        FROM exchange_rates
        WHERE base_currency = ? AND quote_currency = ?
        ORDER BY date_time DESC, id DESC
        LIMIT 1
        """,
        (base_currency, quote_currency),
    ).fetchone()
    if row is None:
        return None
    return LatestExchangeRateSummary(
        base_currency=row["base_currency"],
        quote_currency=row["quote_currency"],
        exchange_rate=_decimal(row["exchange_rate"]),
        timestamp=row["date_time"],
    )


def _scalar(
    connection: sqlite3.Connection,
    statement: str,
    parameters: tuple[str, ...],
) -> int:
    row = connection.execute(statement, parameters).fetchone()
    return int(row[0])


def _decimal(value: object) -> Decimal:
    parsed = Decimal(str(value))
    if not parsed.is_finite():
        raise ValueError("Snapshot numeric values must be finite.")
    return parsed


def _file_metadata(path: Path) -> tuple[int, int] | None:
    if not path.is_file():
        return None
    stat = path.stat()
    return stat.st_size, stat.st_mtime_ns


def _completeness(
    stock: StockSummary | None,
    price: LatestPriceSummary | None,
    candle: LatestCandleSummary | None,
    exchange_rate: LatestExchangeRateSummary | None,
) -> CompletenessFlags:
    flags = (
        stock is not None,
        price is not None,
        candle is not None,
        exchange_rate is not None,
    )
    return CompletenessFlags(
        stock_info_present=flags[0],
        price_snapshot_present=flags[1],
        candle_present=flags[2],
        exchange_rate_present=flags[3],
        all_components_present=all(flags),
    )


def _failure(
    *,
    symbol: str,
    base_currency: str,
    quote_currency: str,
    candle_interval: str,
    db_file_exists: bool,
    modified: bool,
    error_type: str,
    error_message: str,
    counts: SourceCounts = SourceCounts(),
    stock: StockSummary | None = None,
    price: LatestPriceSummary | None = None,
    candle: LatestCandleSummary | None = None,
    exchange_rate: LatestExchangeRateSummary | None = None,
) -> LocalSnapshotLatestReadModel:
    return _model(
        success=False,
        symbol=symbol,
        base_currency=base_currency,
        quote_currency=quote_currency,
        candle_interval=candle_interval,
        db_file_exists=db_file_exists,
        modified=modified,
        stock=stock,
        price=price,
        candle=candle,
        exchange_rate=exchange_rate,
        counts=counts,
        completeness=_completeness(stock, price, candle, exchange_rate),
        error_type=error_type,
        error_message=error_message,
    )


def _model(
    *,
    success: bool,
    symbol: str,
    base_currency: str,
    quote_currency: str,
    candle_interval: str,
    db_file_exists: bool,
    modified: bool,
    stock: StockSummary | None,
    price: LatestPriceSummary | None,
    candle: LatestCandleSummary | None,
    exchange_rate: LatestExchangeRateSummary | None,
    counts: SourceCounts,
    completeness: CompletenessFlags,
    error_type: str | None,
    error_message: str | None,
) -> LocalSnapshotLatestReadModel:
    return LocalSnapshotLatestReadModel(
        success=success,
        stage=STAGE,
        phase=PHASE,
        planned_db_relative_path=PLANNED_DB_RELATIVE_PATH,
        db_file_exists=db_file_exists,
        db_open_mode="readonly",
        db_write_allowed_this_stage=False,
        actual_db_file_modified_this_stage=modified,
        api_call_allowed_this_stage=False,
        oauth_token_endpoint_allowed_this_stage=False,
        env_file_read_allowed_this_stage=False,
        credential_required_this_stage=False,
        account_seq_allowed=False,
        real_order_related_call_allowed=False,
        stock_warnings_included=False,
        stock_warnings_deferred=True,
        symbol=symbol,
        exchange_rate_pair=f"{base_currency}/{quote_currency}",
        candle_interval=candle_interval,
        stock=stock,
        latest_price=price,
        latest_candle=candle,
        latest_exchange_rate=exchange_rate,
        source_counts=counts,
        completeness=completeness,
        safe_error_type=error_type,
        safe_error_message=error_message,
    )


def _json_safe(value: Any) -> Any:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, dict):
        return {key: _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    return value
