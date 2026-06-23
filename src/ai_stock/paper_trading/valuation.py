"""Paper portfolio valuation from caller-supplied simulated prices only."""

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from typing import Any

from ai_stock.paper_trading.models import PaperHolding, PaperPortfolio
from ai_stock.risk import assert_paper_trading_only


class PaperPortfolioValuationError(ValueError):
    """Raised when a simulated paper portfolio cannot be valued safely."""


@dataclass(frozen=True, slots=True)
class PaperHoldingValuation:
    """Valuation details for one simulated paper holding."""

    stock_code: str
    quantity: Decimal
    average_price: Decimal
    current_price: Decimal
    market_value: Decimal
    cost_basis: Decimal
    unrealized_pnl: Decimal
    unrealized_pnl_rate: Decimal | None
    currency: str = "KRW"


@dataclass(frozen=True, slots=True)
class PaperPortfolioValuationResult:
    """Valuation summary for a simulated paper portfolio."""

    paper_portfolio_id: str
    cash_balance: Decimal
    holding_valuations: tuple[PaperHoldingValuation, ...]
    total_holdings_value: Decimal
    total_portfolio_value: Decimal
    total_cost_basis: Decimal
    total_unrealized_pnl: Decimal
    total_unrealized_pnl_rate: Decimal | None
    currency: str = "KRW"


class PaperPortfolioValuationService:
    """Value a paper portfolio using explicit simulated current prices."""

    def value_portfolio(
        self,
        portfolio: PaperPortfolio,
        simulated_current_prices: Mapping[str, Decimal],
        *,
        mode: str = "paper",
        flags: Mapping[str, Any] | None = None,
    ) -> PaperPortfolioValuationResult:
        """Return valuation results without mutating portfolio or holdings."""
        assert_paper_trading_only(mode=mode, flags=flags)
        if not isinstance(simulated_current_prices, Mapping):
            raise TypeError("simulated_current_prices must be a mapping.")

        holding_valuations = tuple(
            self._value_holding(holding, simulated_current_prices)
            for holding in portfolio.holdings
        )
        total_holdings_value = sum(
            (valuation.market_value for valuation in holding_valuations),
            Decimal("0"),
        )
        total_cost_basis = sum(
            (valuation.cost_basis for valuation in holding_valuations),
            Decimal("0"),
        )
        total_unrealized_pnl = sum(
            (valuation.unrealized_pnl for valuation in holding_valuations),
            Decimal("0"),
        )
        return PaperPortfolioValuationResult(
            paper_portfolio_id=portfolio.paper_portfolio_id,
            cash_balance=portfolio.cash_balance,
            holding_valuations=holding_valuations,
            total_holdings_value=total_holdings_value,
            total_portfolio_value=portfolio.cash_balance + total_holdings_value,
            total_cost_basis=total_cost_basis,
            total_unrealized_pnl=total_unrealized_pnl,
            total_unrealized_pnl_rate=self._safe_rate(
                total_unrealized_pnl,
                total_cost_basis,
            ),
            currency=portfolio.currency,
        )

    def _value_holding(
        self,
        holding: PaperHolding,
        simulated_current_prices: Mapping[str, Decimal],
    ) -> PaperHoldingValuation:
        current_price = self._get_current_price(
            holding.stock_code,
            simulated_current_prices,
        )
        market_value = holding.quantity * current_price
        cost_basis = holding.quantity * holding.average_price
        unrealized_pnl = market_value - cost_basis
        return PaperHoldingValuation(
            stock_code=holding.stock_code,
            quantity=holding.quantity,
            average_price=holding.average_price,
            current_price=current_price,
            market_value=market_value,
            cost_basis=cost_basis,
            unrealized_pnl=unrealized_pnl,
            unrealized_pnl_rate=self._safe_rate(unrealized_pnl, cost_basis),
            currency=holding.currency,
        )

    def _get_current_price(
        self,
        stock_code: str,
        simulated_current_prices: Mapping[str, Decimal],
    ) -> Decimal:
        if stock_code not in simulated_current_prices:
            raise PaperPortfolioValuationError(
                f"Missing simulated current price for paper holding: {stock_code}."
            )
        current_price = simulated_current_prices[stock_code]
        self._require_positive_decimal(current_price, "current_price")
        return current_price

    def _safe_rate(
        self,
        numerator: Decimal,
        denominator: Decimal,
    ) -> Decimal | None:
        if denominator <= Decimal("0"):
            return None
        return numerator / denominator

    def _require_positive_decimal(self, value: Decimal, field_name: str) -> None:
        if not isinstance(value, Decimal):
            raise TypeError(f"{field_name} must be a Decimal.")
        if not value.is_finite() or value <= Decimal("0"):
            raise PaperPortfolioValuationError(f"{field_name} must be greater than zero.")


__all__ = [
    "PaperHoldingValuation",
    "PaperPortfolioValuationError",
    "PaperPortfolioValuationResult",
    "PaperPortfolioValuationService",
]
