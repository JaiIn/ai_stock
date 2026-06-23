"""Paper-trading domain models.

Every model in this module is explicitly for simulated trading. The module does
not create live orders, connect to a broker, or depend on Toss API clients.
"""

from dataclasses import dataclass, field
from decimal import Decimal
from enum import StrEnum


class PaperOrderSide(StrEnum):
    """Allowed sides for simulated paper orders."""

    BUY = "buy"
    SELL = "sell"


class PaperOrderType(StrEnum):
    """Allowed order types for simulated paper orders."""

    MARKET = "market"
    LIMIT = "limit"


class PaperOrderStatus(StrEnum):
    """Minimal lifecycle states for simulated paper orders."""

    CREATED = "created"
    ACCEPTED = "accepted"
    CANCELLED = "cancelled"
    REJECTED = "rejected"
    FILLED = "filled"


_PAPER_ORDER_TRANSITIONS: dict[PaperOrderStatus, frozenset[PaperOrderStatus]] = {
    PaperOrderStatus.CREATED: frozenset(
        {
            PaperOrderStatus.ACCEPTED,
            PaperOrderStatus.CANCELLED,
            PaperOrderStatus.REJECTED,
        }
    ),
    PaperOrderStatus.ACCEPTED: frozenset(
        {
            PaperOrderStatus.CANCELLED,
            PaperOrderStatus.REJECTED,
            PaperOrderStatus.FILLED,
        }
    ),
    PaperOrderStatus.CANCELLED: frozenset(),
    PaperOrderStatus.REJECTED: frozenset(),
    PaperOrderStatus.FILLED: frozenset(),
}


def _require_positive_decimal(value: Decimal, field_name: str) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be a Decimal.")
    if not value.is_finite() or value <= Decimal("0"):
        raise ValueError(f"{field_name} must be greater than zero.")


def _require_non_negative_decimal(value: Decimal, field_name: str) -> None:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be a Decimal.")
    if not value.is_finite() or value < Decimal("0"):
        raise ValueError(f"{field_name} cannot be negative.")


def _require_text(value: str, field_name: str) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} is required.")


@dataclass(frozen=True, slots=True)
class PaperHolding:
    """Simulated holding for a paper portfolio."""

    stock_code: str
    quantity: Decimal
    average_price: Decimal
    currency: str = "KRW"

    def __post_init__(self) -> None:
        _require_text(self.stock_code, "stock_code")
        _require_positive_decimal(self.quantity, "quantity")
        _require_positive_decimal(self.average_price, "average_price")
        _require_text(self.currency, "currency")


@dataclass(frozen=True, slots=True)
class PaperPortfolio:
    """Simulated portfolio with cash and paper holdings only."""

    paper_portfolio_id: str
    cash_balance: Decimal
    currency: str = "KRW"
    holdings: tuple[PaperHolding, ...] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        _require_text(self.paper_portfolio_id, "paper_portfolio_id")
        _require_non_negative_decimal(self.cash_balance, "cash_balance")
        _require_text(self.currency, "currency")
        if not isinstance(self.holdings, tuple):
            raise TypeError("holdings must be a tuple of PaperHolding values.")
        for holding in self.holdings:
            if not isinstance(holding, PaperHolding):
                raise TypeError("holdings must contain only PaperHolding values.")


@dataclass(frozen=True, slots=True)
class PaperOrder:
    """Simulated paper order request.

    This model is not a broker order request and cannot be sent to a live API.
    """

    paper_order_id: str
    stock_code: str
    side: PaperOrderSide
    order_type: PaperOrderType
    quantity: Decimal
    price: Decimal
    status: PaperOrderStatus = PaperOrderStatus.CREATED
    currency: str = "KRW"
    submitted_at: str | None = None

    def __post_init__(self) -> None:
        _require_text(self.paper_order_id, "paper_order_id")
        _require_text(self.stock_code, "stock_code")
        if not isinstance(self.side, PaperOrderSide):
            raise TypeError("side must be a PaperOrderSide.")
        if not isinstance(self.order_type, PaperOrderType):
            raise TypeError("order_type must be a PaperOrderType.")
        if not isinstance(self.status, PaperOrderStatus):
            raise TypeError("status must be a PaperOrderStatus.")
        _require_positive_decimal(self.quantity, "quantity")
        _require_positive_decimal(self.price, "price")
        _require_text(self.currency, "currency")

    def transition_to(self, next_status: PaperOrderStatus) -> "PaperOrder":
        """Return a new simulated order with a validated status transition."""
        if not isinstance(next_status, PaperOrderStatus):
            raise TypeError("next_status must be a PaperOrderStatus.")
        allowed = _PAPER_ORDER_TRANSITIONS[self.status]
        if next_status not in allowed:
            raise ValueError(
                f"Invalid paper order status transition: "
                f"{self.status.value} -> {next_status.value}."
            )
        return PaperOrder(
            paper_order_id=self.paper_order_id,
            stock_code=self.stock_code,
            side=self.side,
            order_type=self.order_type,
            quantity=self.quantity,
            price=self.price,
            status=next_status,
            currency=self.currency,
            submitted_at=self.submitted_at,
        )


@dataclass(frozen=True, slots=True)
class PaperTrade:
    """Simulated trade generated from a paper order."""

    paper_trade_id: str
    paper_order_id: str
    stock_code: str
    side: PaperOrderSide
    quantity: Decimal
    price: Decimal
    traded_at: str
    currency: str = "KRW"

    def __post_init__(self) -> None:
        _require_text(self.paper_trade_id, "paper_trade_id")
        _require_text(self.paper_order_id, "paper_order_id")
        _require_text(self.stock_code, "stock_code")
        if not isinstance(self.side, PaperOrderSide):
            raise TypeError("side must be a PaperOrderSide.")
        _require_positive_decimal(self.quantity, "quantity")
        _require_positive_decimal(self.price, "price")
        _require_text(self.traded_at, "traded_at")
        _require_text(self.currency, "currency")
