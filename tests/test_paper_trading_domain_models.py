"""Safety tests for paper-trading-only domain models."""

import socket
import unittest
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from ai_stock.paper_trading import (
    PaperHolding,
    PaperOrder,
    PaperOrderSide,
    PaperOrderStatus,
    PaperOrderType,
    PaperPortfolio,
    PaperTrade,
)
from ai_stock.risk import PaperTradingSafetyError, assert_paper_trading_only


class PaperTradingDomainModelTests(unittest.TestCase):
    def test_paper_portfolio_rejects_negative_cash_balance(self) -> None:
        with self.assertRaises(ValueError):
            PaperPortfolio(
                paper_portfolio_id="paper-portfolio-1",
                cash_balance=Decimal("-0.01"),
            )

    def test_paper_holding_requires_positive_quantity_and_price(self) -> None:
        with self.assertRaises(ValueError):
            PaperHolding(
                stock_code="005930",
                quantity=Decimal("0"),
                average_price=Decimal("70000"),
            )
        with self.assertRaises(ValueError):
            PaperHolding(
                stock_code="005930",
                quantity=Decimal("1"),
                average_price=Decimal("0"),
            )

    def test_paper_order_requires_decimal_positive_quantity_and_price(self) -> None:
        with self.assertRaises(ValueError):
            PaperOrder(
                paper_order_id="paper-order-1",
                stock_code="005930",
                side=PaperOrderSide.BUY,
                order_type=PaperOrderType.LIMIT,
                quantity=Decimal("-1"),
                price=Decimal("70000"),
            )
        with self.assertRaises(TypeError):
            PaperOrder(
                paper_order_id="paper-order-1",
                stock_code="005930",
                side="buy",  # type: ignore[arg-type]
                order_type=PaperOrderType.LIMIT,
                quantity=Decimal("1"),
                price=Decimal("70000"),
            )

    def test_paper_order_status_transition_rules(self) -> None:
        created = PaperOrder(
            paper_order_id="paper-order-1",
            stock_code="005930",
            side=PaperOrderSide.BUY,
            order_type=PaperOrderType.LIMIT,
            quantity=Decimal("1"),
            price=Decimal("70000"),
        )

        accepted = created.transition_to(PaperOrderStatus.ACCEPTED)
        filled = accepted.transition_to(PaperOrderStatus.FILLED)

        self.assertEqual(accepted.status, PaperOrderStatus.ACCEPTED)
        self.assertEqual(filled.status, PaperOrderStatus.FILLED)
        with self.assertRaises(ValueError):
            filled.transition_to(PaperOrderStatus.CANCELLED)

    def test_paper_trade_requires_simulated_trade_values(self) -> None:
        trade = PaperTrade(
            paper_trade_id="paper-trade-1",
            paper_order_id="paper-order-1",
            stock_code="005930",
            side=PaperOrderSide.SELL,
            quantity=Decimal("2"),
            price=Decimal("71000.50"),
            traded_at="2026-06-23T09:00:00Z",
        )

        self.assertEqual(trade.quantity, Decimal("2"))
        self.assertEqual(trade.price, Decimal("71000.50"))

    def test_safety_guard_allows_only_paper_modes(self) -> None:
        assert_paper_trading_only(mode="paper")
        assert_paper_trading_only(mode="simulated", flags={"dry_run": True})
        with self.assertRaises(PaperTradingSafetyError):
            assert_paper_trading_only(mode="live")
        with self.assertRaises(PaperTradingSafetyError):
            assert_paper_trading_only(flags={"real_order": True})
        with self.assertRaises(PaperTradingSafetyError):
            assert_paper_trading_only(flags={"execution_mode": "production"})

    def test_paper_models_do_not_open_network_sockets(self) -> None:
        with patch.object(
            socket,
            "socket",
            side_effect=AssertionError("network access is forbidden"),
        ):
            portfolio = PaperPortfolio(
                paper_portfolio_id="paper-portfolio-1",
                cash_balance=Decimal("1000000"),
            )
            order = PaperOrder(
                paper_order_id="paper-order-1",
                stock_code="005930",
                side=PaperOrderSide.BUY,
                order_type=PaperOrderType.MARKET,
                quantity=Decimal("1"),
                price=Decimal("70000"),
            )
            self.assertEqual(portfolio.cash_balance, Decimal("1000000"))
            self.assertEqual(order.side, PaperOrderSide.BUY)

    def test_paper_sources_do_not_import_live_trading_dependencies(self) -> None:
        import ai_stock.paper_trading.models as paper_models
        import ai_stock.risk.paper_trading as paper_safety

        source_text = "\n".join(
            [
                Path(paper_models.__file__).read_text(encoding="utf-8"),
                Path(paper_safety.__file__).read_text(encoding="utf-8"),
            ]
        )

        forbidden_terms = (
            "ai_stock.clients",
            "httpx.Client",
            "httpx.AsyncClient",
            "token_provider",
            "request_context",
            ".send(",
            "accountSeq",
            "create_real_order",
            "submit_real_order",
        )
        for term in forbidden_terms:
            self.assertNotIn(term, source_text)


if __name__ == "__main__":
    unittest.main()
