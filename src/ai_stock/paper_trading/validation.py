"""Paper-order validation service for simulated trading only.

The validator reads PaperPortfolio and PaperOrder values and returns a
validation result. It does not mutate portfolio cash/holdings, execute fills,
create broker requests, or depend on live trading clients.
"""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ai_stock.paper_trading.models import (
    PaperHolding,
    PaperOrder,
    PaperOrderSide,
    PaperOrderStatus,
    PaperPortfolio,
)
from ai_stock.risk import assert_paper_trading_only


class PaperOrderValidationError(ValueError):
    """Raised when a simulated paper order is not valid for the portfolio."""


@dataclass(frozen=True, slots=True)
class PaperOrderValidationResult:
    """Read-only result for simulated paper-order validation."""

    is_valid: bool
    reason: str | None = None
    required_cash: Decimal = Decimal("0")
    available_cash: Decimal = Decimal("0")
    requested_quantity: Decimal = Decimal("0")
    available_quantity: Decimal = Decimal("0")


class PaperOrderValidationService:
    """Validate paper orders against a simulated paper portfolio."""

    def validate(
        self,
        portfolio: PaperPortfolio,
        order: PaperOrder,
        *,
        mode: str = "paper",
        flags: Mapping[str, Any] | None = None,
    ) -> PaperOrderValidationResult:
        """Validate without changing cash, holdings, status, or external state."""
        assert_paper_trading_only(mode=mode, flags=flags)
        self._require_created_order(order)
        if order.side is PaperOrderSide.BUY:
            return self._validate_buy(portfolio, order)
        if order.side is PaperOrderSide.SELL:
            return self._validate_sell(portfolio, order)
        raise PaperOrderValidationError("Unsupported paper order side.")

    def require_valid(
        self,
        portfolio: PaperPortfolio,
        order: PaperOrder,
        *,
        mode: str = "paper",
        flags: Mapping[str, Any] | None = None,
    ) -> PaperOrderValidationResult:
        """Return validation result or raise for invalid simulated paper orders."""
        result = self.validate(portfolio, order, mode=mode, flags=flags)
        if not result.is_valid:
            raise PaperOrderValidationError(result.reason or "Invalid paper order.")
        return result

    def _require_created_order(self, order: PaperOrder) -> None:
        if order.status is not PaperOrderStatus.CREATED:
            raise PaperOrderValidationError(
                "Only CREATED paper orders can be validated."
            )

    def _validate_buy(
        self,
        portfolio: PaperPortfolio,
        order: PaperOrder,
    ) -> PaperOrderValidationResult:
        required_cash = order.quantity * order.price
        available_cash = portfolio.cash_balance
        if required_cash > available_cash:
            return PaperOrderValidationResult(
                is_valid=False,
                reason="Insufficient simulated cash for paper buy order.",
                required_cash=required_cash,
                available_cash=available_cash,
                requested_quantity=order.quantity,
            )
        return PaperOrderValidationResult(
            is_valid=True,
            required_cash=required_cash,
            available_cash=available_cash,
            requested_quantity=order.quantity,
        )

    def _validate_sell(
        self,
        portfolio: PaperPortfolio,
        order: PaperOrder,
    ) -> PaperOrderValidationResult:
        holding = self._find_holding(portfolio, order.stock_code)
        if holding is None:
            return PaperOrderValidationResult(
                is_valid=False,
                reason="No simulated holding exists for paper sell order.",
                requested_quantity=order.quantity,
            )
        if order.quantity > holding.quantity:
            return PaperOrderValidationResult(
                is_valid=False,
                reason="Insufficient simulated holding quantity for paper sell order.",
                requested_quantity=order.quantity,
                available_quantity=holding.quantity,
            )
        return PaperOrderValidationResult(
            is_valid=True,
            requested_quantity=order.quantity,
            available_quantity=holding.quantity,
        )

    def _find_holding(
        self,
        portfolio: PaperPortfolio,
        stock_code: str,
    ) -> PaperHolding | None:
        for holding in portfolio.holdings:
            if holding.stock_code == stock_code:
                return holding
        return None
