"""Tests for paper-only simulated execution service."""

from decimal import Decimal
import inspect
import socket
from unittest.mock import patch

import pytest

from ai_stock.paper_trading import (
    PaperExecutionError,
    PaperHolding,
    PaperOrder,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType,
    PaperPortfolio,
    PaperSimulatedExecutionService,
)
from ai_stock.paper_trading import execution as execution_module
from ai_stock.risk import PaperTradingSafetyError


def _portfolio() -> PaperPortfolio:
    return PaperPortfolio(
        paper_portfolio_id="paper-portfolio-1",
        cash_balance=Decimal("100000"),
        holdings=(
            PaperHolding(
                stock_code="005930",
                quantity=Decimal("5"),
                average_price=Decimal("60000"),
            ),
        ),
    )


def _order(
    *,
    side: PaperOrderSide,
    stock_code: str = "005930",
    quantity: Decimal = Decimal("1"),
    price: Decimal = Decimal("50000"),
    status: PaperOrderStatus = PaperOrderStatus.CREATED,
) -> PaperOrder:
    return PaperOrder(
        paper_order_id=f"paper-order-{stock_code}-{side.value}",
        stock_code=stock_code,
        side=side,
        order_type=PaperOrderType.LIMIT,
        quantity=quantity,
        price=price,
        status=status,
    )


def test_paper_buy_execution_creates_new_holding_without_mutating_inputs() -> None:
    service = PaperSimulatedExecutionService()
    portfolio = _portfolio()
    order = _order(
        side=PaperOrderSide.BUY,
        stock_code="000660",
        quantity=Decimal("2"),
        price=Decimal("40000"),
    )

    result = service.execute(
        portfolio,
        order,
        simulated_execution_price=Decimal("45000"),
        executed_at="2026-06-23T09:00:00+09:00",
    )

    assert result.updated_portfolio.cash_balance == Decimal("10000")
    new_holding = next(
        holding
        for holding in result.updated_portfolio.holdings
        if holding.stock_code == "000660"
    )
    assert new_holding.quantity == Decimal("2")
    assert new_holding.average_price == Decimal("45000")
    assert result.updated_order.status is PaperOrderStatus.FILLED
    assert result.trade.paper_order_id == order.paper_order_id
    assert result.trade.price == Decimal("45000")
    assert result.cash_delta == Decimal("-90000")
    assert result.holding_delta == Decimal("2")
    assert portfolio.cash_balance == Decimal("100000")
    assert order.status is PaperOrderStatus.CREATED


def test_paper_buy_execution_updates_existing_average_price() -> None:
    service = PaperSimulatedExecutionService()

    result = service.execute(
        _portfolio(),
        _order(side=PaperOrderSide.BUY, quantity=Decimal("1")),
        simulated_execution_price=Decimal("70000"),
        executed_at="2026-06-23T09:01:00+09:00",
    )

    holding = next(
        holding
        for holding in result.updated_portfolio.holdings
        if holding.stock_code == "005930"
    )
    expected_average = (
        Decimal("5") * Decimal("60000") + Decimal("1") * Decimal("70000")
    ) / Decimal("6")
    assert holding.quantity == Decimal("6")
    assert holding.average_price == expected_average
    assert result.updated_portfolio.cash_balance == Decimal("30000")


def test_paper_sell_execution_reduces_holding_and_adds_cash() -> None:
    service = PaperSimulatedExecutionService()

    result = service.execute(
        _portfolio(),
        _order(side=PaperOrderSide.SELL, quantity=Decimal("2")),
        simulated_execution_price=Decimal("70000"),
        executed_at="2026-06-23T09:02:00+09:00",
    )

    holding = next(
        holding
        for holding in result.updated_portfolio.holdings
        if holding.stock_code == "005930"
    )
    assert result.updated_portfolio.cash_balance == Decimal("240000")
    assert holding.quantity == Decimal("3")
    assert holding.average_price == Decimal("60000")
    assert result.updated_order.status is PaperOrderStatus.FILLED
    assert result.trade.side is PaperOrderSide.SELL
    assert result.cash_delta == Decimal("140000")
    assert result.holding_delta == Decimal("-2")


def test_paper_sell_execution_removes_zero_quantity_holding() -> None:
    service = PaperSimulatedExecutionService()

    result = service.execute(
        _portfolio(),
        _order(side=PaperOrderSide.SELL, quantity=Decimal("5")),
        simulated_execution_price=Decimal("70000"),
        executed_at="2026-06-23T09:03:00+09:00",
    )

    assert all(
        holding.stock_code != "005930"
        for holding in result.updated_portfolio.holdings
    )
    assert result.updated_portfolio.cash_balance == Decimal("450000")


def test_paper_buy_execution_rejects_insufficient_cash() -> None:
    service = PaperSimulatedExecutionService()

    with pytest.raises(PaperExecutionError, match="Insufficient simulated cash"):
        service.execute(
            _portfolio(),
            _order(side=PaperOrderSide.BUY, quantity=Decimal("3")),
            simulated_execution_price=Decimal("50000"),
            executed_at="2026-06-23T09:04:00+09:00",
        )


def test_paper_sell_execution_rejects_insufficient_holding() -> None:
    service = PaperSimulatedExecutionService()

    with pytest.raises(
        PaperExecutionError,
        match="Insufficient simulated holding quantity",
    ):
        service.execute(
            _portfolio(),
            _order(side=PaperOrderSide.SELL, quantity=Decimal("6")),
            simulated_execution_price=Decimal("70000"),
            executed_at="2026-06-23T09:05:00+09:00",
        )


def test_paper_execution_rejects_terminal_order_status() -> None:
    service = PaperSimulatedExecutionService()

    with pytest.raises(PaperExecutionError, match="Only CREATED paper orders"):
        service.execute(
            _portfolio(),
            _order(side=PaperOrderSide.BUY, status=PaperOrderStatus.FILLED),
            simulated_execution_price=Decimal("50000"),
            executed_at="2026-06-23T09:06:00+09:00",
        )


def test_paper_execution_rejects_non_positive_execution_price() -> None:
    service = PaperSimulatedExecutionService()

    with pytest.raises(PaperExecutionError, match="greater than zero"):
        service.execute(
            _portfolio(),
            _order(side=PaperOrderSide.BUY),
            simulated_execution_price=Decimal("0"),
            executed_at="2026-06-23T09:07:00+09:00",
        )


def test_paper_execution_rejects_live_flag() -> None:
    service = PaperSimulatedExecutionService()

    with pytest.raises(PaperTradingSafetyError):
        service.execute(
            _portfolio(),
            _order(side=PaperOrderSide.BUY),
            simulated_execution_price=Decimal("50000"),
            executed_at="2026-06-23T09:08:00+09:00",
            flags={"real_order": True},
        )


def test_paper_execution_does_not_use_network_socket() -> None:
    service = PaperSimulatedExecutionService()

    with patch.object(socket, "socket", side_effect=AssertionError("network")):
        result = service.execute(
            _portfolio(),
            _order(side=PaperOrderSide.SELL, quantity=Decimal("1")),
            simulated_execution_price=Decimal("70000"),
            executed_at="2026-06-23T09:09:00+09:00",
        )

    assert result.updated_order.status is PaperOrderStatus.FILLED


def test_paper_execution_source_avoids_external_trading_dependencies() -> None:
    source = inspect.getsource(execution_module)
    forbidden_terms = (
        "ai_stock.clients",
        "token_provider",
        "request_context",
        "httpx",
        ".send(",
        "OAuth",
        "Toss",
        "accountSeq",
        "account_seq",
        "access_token",
        "client_secret",
        "api_key",
        "sqlite3",
        "sqlalchemy",
    )

    for forbidden_term in forbidden_terms:
        assert forbidden_term not in source
