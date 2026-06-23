"""Tests for paper-only portfolio valuation service."""

from decimal import Decimal
import inspect
import socket
from unittest.mock import patch

import pytest

from ai_stock.paper_trading import (
    PaperHolding,
    PaperPortfolio,
    PaperPortfolioValuationError,
    PaperPortfolioValuationService,
)
from ai_stock.paper_trading import valuation as valuation_module
from ai_stock.risk import PaperTradingSafetyError


def _portfolio(
    holdings: tuple[PaperHolding, ...],
    cash_balance: Decimal = Decimal("100000"),
) -> PaperPortfolio:
    return PaperPortfolio(
        paper_portfolio_id="paper-portfolio-valuation",
        cash_balance=cash_balance,
        holdings=holdings,
    )


def test_cash_only_paper_portfolio_valuation() -> None:
    service = PaperPortfolioValuationService()
    portfolio = _portfolio(holdings=(), cash_balance=Decimal("123000"))

    result = service.value_portfolio(portfolio, {"UNUSED": Decimal("1")})

    assert result.cash_balance == Decimal("123000")
    assert result.holding_valuations == ()
    assert result.total_holdings_value == Decimal("0")
    assert result.total_portfolio_value == Decimal("123000")
    assert result.total_cost_basis == Decimal("0")
    assert result.total_unrealized_pnl == Decimal("0")
    assert result.total_unrealized_pnl_rate is None


def test_single_paper_holding_valuation_positive_pnl() -> None:
    service = PaperPortfolioValuationService()
    portfolio = _portfolio(
        holdings=(
            PaperHolding(
                stock_code="005930",
                quantity=Decimal("2"),
                average_price=Decimal("60000"),
            ),
        ),
        cash_balance=Decimal("10000"),
    )

    result = service.value_portfolio(
        portfolio,
        {"005930": Decimal("72000")},
    )

    valuation = result.holding_valuations[0]
    assert valuation.market_value == Decimal("144000")
    assert valuation.cost_basis == Decimal("120000")
    assert valuation.unrealized_pnl == Decimal("24000")
    assert valuation.unrealized_pnl_rate == Decimal("24000") / Decimal("120000")
    assert result.total_holdings_value == Decimal("144000")
    assert result.total_portfolio_value == Decimal("154000")
    assert result.total_cost_basis == Decimal("120000")
    assert result.total_unrealized_pnl == Decimal("24000")


def test_multiple_paper_holding_valuation_with_positive_and_negative_pnl() -> None:
    service = PaperPortfolioValuationService()
    portfolio = _portfolio(
        holdings=(
            PaperHolding(
                stock_code="005930",
                quantity=Decimal("2"),
                average_price=Decimal("60000"),
            ),
            PaperHolding(
                stock_code="000660",
                quantity=Decimal("3"),
                average_price=Decimal("150000"),
            ),
        ),
        cash_balance=Decimal("50000"),
    )

    result = service.value_portfolio(
        portfolio,
        {
            "005930": Decimal("72000"),
            "000660": Decimal("140000"),
            "EXTRA": Decimal("999"),
        },
    )

    valuations = {item.stock_code: item for item in result.holding_valuations}
    assert valuations["005930"].unrealized_pnl == Decimal("24000")
    assert valuations["000660"].unrealized_pnl == Decimal("-30000")
    assert result.total_holdings_value == Decimal("564000")
    assert result.total_portfolio_value == Decimal("614000")
    assert result.total_cost_basis == Decimal("570000")
    assert result.total_unrealized_pnl == Decimal("-6000")
    assert result.total_unrealized_pnl_rate == Decimal("-6000") / Decimal("570000")


def test_paper_valuation_rejects_missing_price() -> None:
    service = PaperPortfolioValuationService()
    portfolio = _portfolio(
        holdings=(
            PaperHolding(
                stock_code="005930",
                quantity=Decimal("1"),
                average_price=Decimal("60000"),
            ),
        )
    )

    with pytest.raises(PaperPortfolioValuationError, match="Missing simulated"):
        service.value_portfolio(portfolio, {})


@pytest.mark.parametrize("bad_price", [Decimal("0"), Decimal("-1")])
def test_paper_valuation_rejects_non_positive_price(bad_price: Decimal) -> None:
    service = PaperPortfolioValuationService()
    portfolio = _portfolio(
        holdings=(
            PaperHolding(
                stock_code="005930",
                quantity=Decimal("1"),
                average_price=Decimal("60000"),
            ),
        )
    )

    with pytest.raises(PaperPortfolioValuationError, match="greater than zero"):
        service.value_portfolio(portfolio, {"005930": bad_price})


def test_paper_valuation_rejects_live_flag() -> None:
    service = PaperPortfolioValuationService()
    portfolio = _portfolio(holdings=())

    with pytest.raises(PaperTradingSafetyError):
        service.value_portfolio(
            portfolio,
            {},
            flags={"live_order": True},
        )


def test_paper_valuation_does_not_mutate_portfolio_or_holding() -> None:
    service = PaperPortfolioValuationService()
    holding = PaperHolding(
        stock_code="005930",
        quantity=Decimal("2"),
        average_price=Decimal("60000"),
    )
    portfolio = _portfolio(holdings=(holding,))

    result = service.value_portfolio(portfolio, {"005930": Decimal("72000")})

    assert portfolio.cash_balance == Decimal("100000")
    assert portfolio.holdings == (holding,)
    assert holding.quantity == Decimal("2")
    assert holding.average_price == Decimal("60000")
    assert result.holding_valuations[0].market_value == Decimal("144000")


def test_paper_valuation_does_not_use_network_socket() -> None:
    service = PaperPortfolioValuationService()
    portfolio = _portfolio(holdings=())

    with patch.object(socket, "socket", side_effect=AssertionError("network")):
        result = service.value_portfolio(portfolio, {})

    assert result.total_portfolio_value == Decimal("100000")


def test_paper_valuation_source_avoids_external_dependencies() -> None:
    source = inspect.getsource(valuation_module)
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
