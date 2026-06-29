"""Dry-run plan for a future live read-only snapshot ingestion smoke.

This module evaluates endpoint metadata only. It does not construct clients,
load settings, read environment files, create a database connection, or send
network requests.
"""

from dataclasses import dataclass

from ai_stock.risk import LiveApiSafetyDecision, LiveApiSafetyGate, TossEndpointMetadata

STOCK_SYMBOL = "005930"
EXCHANGE_RATE_PAIR = "USD/KRW"
CANDLE_INTERVAL = "1d"
CANDLE_COUNT = 1
CANDLE_ADJUSTED = True


@dataclass(frozen=True, slots=True)
class PlannedReadOnlyEndpoint:
    """Non-sensitive endpoint metadata and fixed query for the future smoke."""

    method: str
    path: str
    endpoint_category: str
    query: tuple[tuple[str, str], ...]
    requires_auth: bool = True
    requires_account_seq: bool = False
    is_read_only: bool = True

    def metadata(self) -> TossEndpointMetadata:
        """Convert the plan entry to Safety Gate metadata."""

        return TossEndpointMetadata(
            method=self.method,
            path=self.path,
            endpoint_category=self.endpoint_category,
            requires_auth=self.requires_auth,
            requires_account_seq=self.requires_account_seq,
        )


@dataclass(frozen=True, slots=True)
class LiveReadOnlySnapshotIngestionPreflightPlan:
    """Immutable dry-run contract for a separately approved future stage."""

    symbol: str
    exchange_rate_pair: str
    candle_interval: str
    candle_count: int
    candle_adjusted: bool
    candle_before_used: bool
    stock_warnings_included: bool
    stock_warnings_deferred: bool
    storage_mode: str
    storage_connection_target: str
    actual_db_file_created: bool
    expected_oauth_token_endpoint_calls: int
    expected_business_api_calls: int
    expected_total_network_calls: int
    allowed_business_endpoints: tuple[PlannedReadOnlyEndpoint, ...]
    denied_endpoints: tuple[str, ...]
    requires_account_seq: bool
    account_seq_used: bool
    real_order_related_call_allowed: bool
    safety_gate_preflight_passed: bool
    safety_gate_decisions: tuple[LiveApiSafetyDecision, ...]
    actual_network_call_performed: bool
    oauth_token_endpoint_called: bool
    actual_storage_performed: bool
    env_file_read: bool


_ALLOWED_BUSINESS_ENDPOINTS = (
    PlannedReadOnlyEndpoint(
        method="GET",
        path="/api/v1/stocks",
        endpoint_category="stock_info",
        query=(("symbols", STOCK_SYMBOL),),
    ),
    PlannedReadOnlyEndpoint(
        method="GET",
        path="/api/v1/prices",
        endpoint_category="market_data",
        query=(("symbols", STOCK_SYMBOL),),
    ),
    PlannedReadOnlyEndpoint(
        method="GET",
        path="/api/v1/candles",
        endpoint_category="market_data",
        query=(
            ("symbol", STOCK_SYMBOL),
            ("interval", CANDLE_INTERVAL),
            ("count", str(CANDLE_COUNT)),
            ("adjusted", "true"),
        ),
    ),
    PlannedReadOnlyEndpoint(
        method="GET",
        path="/api/v1/exchange-rate",
        endpoint_category="market_info",
        query=(("baseCurrency", "USD"), ("quoteCurrency", "KRW")),
    ),
)

_DENIED_ENDPOINTS = (
    "GET /api/v1/stocks/{symbol}/warnings",
    "POST /api/v1/orders",
    "GET /api/v1/orders",
    "GET /api/v1/accounts",
    "GET /api/v1/assets",
    "GET /api/v1/balance",
    "GET /api/v1/fills",
    "PATCH /api/v1/prices",
)

_DENIED_METADATA = (
    TossEndpointMetadata(
        method="POST",
        path="/api/v1/orders",
        endpoint_category="order",
        requires_auth=True,
        requires_account_seq=False,
    ),
    TossEndpointMetadata(
        method="GET",
        path="/api/v1/orders",
        endpoint_category="order",
        requires_auth=True,
        requires_account_seq=True,
    ),
    TossEndpointMetadata(
        method="GET",
        path="/api/v1/assets",
        endpoint_category="asset",
        requires_auth=True,
        requires_account_seq=True,
    ),
    TossEndpointMetadata(
        method="GET",
        path="/api/v1/balance",
        endpoint_category="account",
        requires_auth=True,
        requires_account_seq=True,
    ),
    TossEndpointMetadata(
        method="GET",
        path="/api/v1/fills",
        endpoint_category="account",
        requires_auth=True,
        requires_account_seq=True,
    ),
    TossEndpointMetadata(
        method="PATCH",
        path="/api/v1/prices",
        endpoint_category="mutation",
        requires_auth=True,
        requires_account_seq=False,
    ),
)


def build_live_readonly_snapshot_ingestion_preflight(
    safety_gate: LiveApiSafetyGate | None = None,
) -> LiveReadOnlySnapshotIngestionPreflightPlan:
    """Build and validate the dry-run plan without external or storage I/O."""

    gate = safety_gate or LiveApiSafetyGate()
    allowed_decisions = tuple(
        gate.evaluate(
            endpoint.metadata(),
            live_api_enabled=True,
            real_order_allowed=False,
            dry_run_only=True,
            send_requested=False,
        )
        for endpoint in _ALLOWED_BUSINESS_ENDPOINTS
    )
    if not all(
        decision.allowed
        and decision.is_read_only
        and decision.requires_auth
        and not decision.requires_account_seq
        and decision.dry_run_only
        for decision in allowed_decisions
    ):
        raise ValueError("Read-only snapshot endpoint preflight was rejected.")

    denied_decisions = tuple(
        gate.evaluate(
            metadata,
            live_api_enabled=True,
            real_order_allowed=False,
            dry_run_only=True,
            send_requested=False,
        )
        for metadata in _DENIED_METADATA
    )
    if any(decision.allowed for decision in denied_decisions):
        raise ValueError("Unsafe endpoint metadata passed the preflight gate.")

    return LiveReadOnlySnapshotIngestionPreflightPlan(
        symbol=STOCK_SYMBOL,
        exchange_rate_pair=EXCHANGE_RATE_PAIR,
        candle_interval=CANDLE_INTERVAL,
        candle_count=CANDLE_COUNT,
        candle_adjusted=CANDLE_ADJUSTED,
        candle_before_used=False,
        stock_warnings_included=False,
        stock_warnings_deferred=True,
        storage_mode="in_memory_sqlite",
        storage_connection_target=":memory:",
        actual_db_file_created=False,
        expected_oauth_token_endpoint_calls=1,
        expected_business_api_calls=len(_ALLOWED_BUSINESS_ENDPOINTS),
        expected_total_network_calls=1 + len(_ALLOWED_BUSINESS_ENDPOINTS),
        allowed_business_endpoints=_ALLOWED_BUSINESS_ENDPOINTS,
        denied_endpoints=_DENIED_ENDPOINTS,
        requires_account_seq=False,
        account_seq_used=False,
        real_order_related_call_allowed=False,
        safety_gate_preflight_passed=True,
        safety_gate_decisions=allowed_decisions,
        actual_network_call_performed=False,
        oauth_token_endpoint_called=False,
        actual_storage_performed=False,
        env_file_read=False,
    )
