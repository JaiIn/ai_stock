"""Simulated execution service for paper trading only.

This module uses explicit simulated execution prices supplied by the caller. It
does not fetch market prices, send broker requests, or persist execution data.
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
    PaperTrade,
)
from ai_stock.paper_trading.validation import (
    PaperOrderValidationError,
    PaperOrderValidationService,
)
from ai_stock.risk import assert_paper_trading_only


class PaperExecutionError(ValueError):
    """Raised when a simulated paper execution cannot be completed."""


@dataclass(frozen=True, slots=True)
class PaperExecutionResult:
    """Immutable result of a simulated paper execution."""

    updated_portfolio: PaperPortfolio
    updated_order: PaperOrder
    trade: PaperTrade
    cash_delta: Decimal
    holding_delta: Decimal


class PaperSimulatedExecutionService:
    """Execute validated paper orders against simulated cash and holdings."""

    def __init__(
        self,
        validator: PaperOrderValidationService | None = None,
    ) -> None:
        self._validator = validator or PaperOrderValidationService()

    def execute(
        self,
        portfolio: PaperPortfolio,
        order: PaperOrder,
        *,
        simulated_execution_price: Decimal,
        executed_at: str,
        mode: str = "paper",
        flags: Mapping[str, Any] | None = None,
    ) -> PaperExecutionResult:
        """Return simulated execution results without mutating input objects."""
        assert_paper_trading_only(mode=mode, flags=flags)
        self._require_positive_decimal(
            simulated_execution_price,
            "simulated_execution_price",
        )
        self._require_text(executed_at, "executed_at")

        validation_order = self._order_with_execution_price(
            order,
            simulated_execution_price,
        )
        try:
            self._validator.require_valid(
                portfolio,
                validation_order,
                mode=mode,
                flags=flags,
            )
        except PaperOrderValidationError as exc:
            raise PaperExecutionError(str(exc)) from exc

        if order.side is PaperOrderSide.BUY:
            return self._execute_buy(
                portfolio,
                order,
                simulated_execution_price=simulated_execution_price,
                executed_at=executed_at,
            )
        if order.side is PaperOrderSide.SELL:
            return self._execute_sell(
                portfolio,
                order,
                simulated_execution_price=simulated_execution_price,
                executed_at=executed_at,
            )
        raise PaperExecutionError("Unsupported paper order side.")

    def _execute_buy(
        self,
        portfolio: PaperPortfolio,
        order: PaperOrder,
        *,
        simulated_execution_price: Decimal,
        executed_at: str,
    ) -> PaperExecutionResult:
        amount = order.quantity * simulated_execution_price
        updated_portfolio = PaperPortfolio(
            paper_portfolio_id=portfolio.paper_portfolio_id,
            cash_balance=portfolio.cash_balance - amount,
            currency=portfolio.currency,
            holdings=self._upsert_buy_holding(
                portfolio.holdings,
                order,
                simulated_execution_price,
            ),
        )
        return self._build_result(
            updated_portfolio,
            order,
            simulated_execution_price=simulated_execution_price,
            executed_at=executed_at,
            cash_delta=-amount,
            holding_delta=order.quantity,
        )

    def _execute_sell(
        self,
        portfolio: PaperPortfolio,
        order: PaperOrder,
        *,
        simulated_execution_price: Decimal,
        executed_at: str,
    ) -> PaperExecutionResult:
        amount = order.quantity * simulated_execution_price
        updated_portfolio = PaperPortfolio(
            paper_portfolio_id=portfolio.paper_portfolio_id,
            cash_balance=portfolio.cash_balance + amount,
            currency=portfolio.currency,
            holdings=self._decrease_sell_holding(portfolio.holdings, order),
        )
        return self._build_result(
            updated_portfolio,
            order,
            simulated_execution_price=simulated_execution_price,
            executed_at=executed_at,
            cash_delta=amount,
            holding_delta=-order.quantity,
        )

    def _build_result(
        self,
        updated_portfolio: PaperPortfolio,
        order: PaperOrder,
        *,
        simulated_execution_price: Decimal,
        executed_at: str,
        cash_delta: Decimal,
        holding_delta: Decimal,
    ) -> PaperExecutionResult:
        updated_order = self._mark_order_filled(order)
        trade = PaperTrade(
            paper_trade_id=f"paper-trade-{order.paper_order_id}",
            paper_order_id=order.paper_order_id,
            stock_code=order.stock_code,
            side=order.side,
            quantity=order.quantity,
            price=simulated_execution_price,
            traded_at=executed_at,
            currency=order.currency,
        )
        return PaperExecutionResult(
            updated_portfolio=updated_portfolio,
            updated_order=updated_order,
            trade=trade,
            cash_delta=cash_delta,
            holding_delta=holding_delta,
        )

    def _upsert_buy_holding(
        self,
        holdings: tuple[PaperHolding, ...],
        order: PaperOrder,
        simulated_execution_price: Decimal,
    ) -> tuple[PaperHolding, ...]:
        updated: list[PaperHolding] = []
        matched = False
        for holding in holdings:
            if holding.stock_code != order.stock_code:
                updated.append(holding)
                continue
            matched = True
            new_quantity = holding.quantity + order.quantity
            old_value = holding.quantity * holding.average_price
            new_value = order.quantity * simulated_execution_price
            updated.append(
                PaperHolding(
                    stock_code=holding.stock_code,
                    quantity=new_quantity,
                    average_price=(old_value + new_value) / new_quantity,
                    currency=holding.currency,
                )
            )
        if not matched:
            updated.append(
                PaperHolding(
                    stock_code=order.stock_code,
                    quantity=order.quantity,
                    average_price=simulated_execution_price,
                    currency=order.currency,
                )
            )
        return tuple(updated)

    def _decrease_sell_holding(
        self,
        holdings: tuple[PaperHolding, ...],
        order: PaperOrder,
    ) -> tuple[PaperHolding, ...]:
        updated: list[PaperHolding] = []
        for holding in holdings:
            if holding.stock_code != order.stock_code:
                updated.append(holding)
                continue
            remaining_quantity = holding.quantity - order.quantity
            if remaining_quantity > Decimal("0"):
                updated.append(
                    PaperHolding(
                        stock_code=holding.stock_code,
                        quantity=remaining_quantity,
                        average_price=holding.average_price,
                        currency=holding.currency,
                    )
                )
        return tuple(updated)

    def _order_with_execution_price(
        self,
        order: PaperOrder,
        simulated_execution_price: Decimal,
    ) -> PaperOrder:
        return PaperOrder(
            paper_order_id=order.paper_order_id,
            stock_code=order.stock_code,
            side=order.side,
            order_type=order.order_type,
            quantity=order.quantity,
            price=simulated_execution_price,
            status=order.status,
            currency=order.currency,
            submitted_at=order.submitted_at,
        )

    def _mark_order_filled(self, order: PaperOrder) -> PaperOrder:
        if order.status is PaperOrderStatus.CREATED:
            accepted_order = order.transition_to(PaperOrderStatus.ACCEPTED)
            return accepted_order.transition_to(PaperOrderStatus.FILLED)
        raise PaperExecutionError("Only CREATED paper orders can be executed.")

    def _require_positive_decimal(self, value: Decimal, field_name: str) -> None:
        if not isinstance(value, Decimal):
            raise TypeError(f"{field_name} must be a Decimal.")
        if not value.is_finite() or value <= Decimal("0"):
            raise PaperExecutionError(f"{field_name} must be greater than zero.")

    def _require_text(self, value: str, field_name: str) -> None:
        if not isinstance(value, str) or not value.strip():
            raise PaperExecutionError(f"{field_name} is required.")


__all__ = [
    "PaperExecutionError",
    "PaperExecutionResult",
    "PaperSimulatedExecutionService",
]
