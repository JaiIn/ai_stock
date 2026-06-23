"""Tests for simulated paper-order validation service."""

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
    PaperOrderValidationError,
    PaperOrderValidationService,
    PaperPortfolio,
)
from ai_stock.risk import PaperTradingSafetyError


class PaperOrderValidationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = PaperOrderValidationService()
        self.portfolio = PaperPortfolio(
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

    def _paper_order(
        self,
        *,
        side: PaperOrderSide,
        quantity: Decimal,
        price: Decimal,
        stock_code: str = "005930",
        status: PaperOrderStatus = PaperOrderStatus.CREATED,
    ) -> PaperOrder:
        return PaperOrder(
            paper_order_id="paper-order-1",
            stock_code=stock_code,
            side=side,
            order_type=PaperOrderType.LIMIT,
            quantity=quantity,
            price=price,
            status=status,
        )

    def test_paper_buy_order_is_valid_when_cash_is_sufficient(self) -> None:
        order = self._paper_order(
            side=PaperOrderSide.BUY,
            quantity=Decimal("1"),
            price=Decimal("70000"),
        )

        result = self.validator.validate(self.portfolio, order)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.required_cash, Decimal("70000"))
        self.assertEqual(result.available_cash, Decimal("100000"))

    def test_paper_buy_order_is_rejected_when_cash_is_insufficient(self) -> None:
        order = self._paper_order(
            side=PaperOrderSide.BUY,
            quantity=Decimal("2"),
            price=Decimal("70000"),
        )

        result = self.validator.validate(self.portfolio, order)

        self.assertFalse(result.is_valid)
        self.assertIn("cash", result.reason or "")
        with self.assertRaises(PaperOrderValidationError):
            self.validator.require_valid(self.portfolio, order)

    def test_paper_sell_order_is_valid_when_holding_is_sufficient(self) -> None:
        order = self._paper_order(
            side=PaperOrderSide.SELL,
            quantity=Decimal("3"),
            price=Decimal("70000"),
        )

        result = self.validator.validate(self.portfolio, order)

        self.assertTrue(result.is_valid)
        self.assertEqual(result.requested_quantity, Decimal("3"))
        self.assertEqual(result.available_quantity, Decimal("5"))

    def test_paper_sell_order_is_rejected_when_holding_is_missing(self) -> None:
        order = self._paper_order(
            side=PaperOrderSide.SELL,
            quantity=Decimal("1"),
            price=Decimal("70000"),
            stock_code="000000",
        )

        result = self.validator.validate(self.portfolio, order)

        self.assertFalse(result.is_valid)
        self.assertIn("holding", result.reason or "")

    def test_paper_sell_order_is_rejected_when_quantity_exceeds_holding(self) -> None:
        order = self._paper_order(
            side=PaperOrderSide.SELL,
            quantity=Decimal("6"),
            price=Decimal("70000"),
        )

        result = self.validator.validate(self.portfolio, order)

        self.assertFalse(result.is_valid)
        self.assertEqual(result.available_quantity, Decimal("5"))

    def test_terminal_status_order_is_rejected(self) -> None:
        order = self._paper_order(
            side=PaperOrderSide.BUY,
            quantity=Decimal("1"),
            price=Decimal("70000"),
            status=PaperOrderStatus.FILLED,
        )

        with self.assertRaises(PaperOrderValidationError):
            self.validator.validate(self.portfolio, order)

    def test_live_flags_are_rejected_by_paper_safety_guard(self) -> None:
        order = self._paper_order(
            side=PaperOrderSide.BUY,
            quantity=Decimal("1"),
            price=Decimal("70000"),
        )

        with self.assertRaises(PaperTradingSafetyError):
            self.validator.validate(self.portfolio, order, mode="live")
        with self.assertRaises(PaperTradingSafetyError):
            self.validator.validate(
                self.portfolio,
                order,
                flags={"real_order": True},
            )

    def test_validation_does_not_mutate_portfolio_or_order(self) -> None:
        original_portfolio = self.portfolio
        order = self._paper_order(
            side=PaperOrderSide.BUY,
            quantity=Decimal("1"),
            price=Decimal("70000"),
        )

        self.validator.validate(self.portfolio, order)

        self.assertEqual(self.portfolio, original_portfolio)
        self.assertEqual(order.status, PaperOrderStatus.CREATED)
        self.assertEqual(self.portfolio.cash_balance, Decimal("100000"))
        self.assertEqual(self.portfolio.holdings[0].quantity, Decimal("5"))

    def test_validation_does_not_open_network_sockets(self) -> None:
        order = self._paper_order(
            side=PaperOrderSide.BUY,
            quantity=Decimal("1"),
            price=Decimal("70000"),
        )

        with patch.object(
            socket,
            "socket",
            side_effect=AssertionError("network access is forbidden"),
        ):
            result = self.validator.validate(self.portfolio, order)

        self.assertTrue(result.is_valid)

    def test_validation_source_has_no_live_or_storage_dependencies(self) -> None:
        import ai_stock.paper_trading.validation as validation

        source_text = Path(validation.__file__).read_text(encoding="utf-8")

        forbidden_terms = (
            "ai_stock.clients",
            "httpx",
            "token_provider",
            "request_context",
            ".send(",
            "accountSeq",
            "access_token",
            "client_secret",
            "api_key",
            "sqlite3",
            "sqlalchemy",
            "create_real_order",
            "submit_real_order",
            "fill_engine",
            "performance",
        )
        for term in forbidden_terms:
            self.assertNotIn(term, source_text)


if __name__ == "__main__":
    unittest.main()
