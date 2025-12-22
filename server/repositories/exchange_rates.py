"""Exchange rate repository for currency conversion."""

from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from server.database.models import ExchangeRate
from server.repositories.base import BaseRepository


class ExchangeRateRepository(BaseRepository[ExchangeRate]):
    """Repository for ExchangeRate operations (shared, not user-scoped)."""

    model = ExchangeRate

    async def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate_date: Optional[date] = None,
    ) -> Optional[Decimal]:
        """Get exchange rate for a currency pair.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            rate_date: Date for the rate (defaults to today)

        Returns:
            Exchange rate or None if not found
        """
        if from_currency == to_currency:
            return Decimal("1.0")

        rate_date = rate_date or date.today()

        # Try exact date first
        query = select(ExchangeRate.rate).where(
            ExchangeRate.from_currency == from_currency,
            ExchangeRate.to_currency == to_currency,
            ExchangeRate.date == rate_date,
        )
        result = await self.session.execute(query)
        rate = result.scalar_one_or_none()

        if rate:
            return Decimal(str(rate))

        # Fall back to most recent rate
        query = (
            select(ExchangeRate.rate)
            .where(
                ExchangeRate.from_currency == from_currency,
                ExchangeRate.to_currency == to_currency,
                ExchangeRate.date <= rate_date,
            )
            .order_by(ExchangeRate.date.desc())
            .limit(1)
        )
        result = await self.session.execute(query)
        rate = result.scalar_one_or_none()

        return Decimal(str(rate)) if rate else None

    async def set_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate: Decimal,
        rate_date: Optional[date] = None,
    ) -> ExchangeRate:
        """Set or update an exchange rate.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            rate: The exchange rate
            rate_date: Date for the rate (defaults to today)

        Returns:
            The created or updated exchange rate
        """
        rate_date = rate_date or date.today()

        # Check if exists
        query = select(ExchangeRate).where(
            ExchangeRate.from_currency == from_currency,
            ExchangeRate.to_currency == to_currency,
            ExchangeRate.date == rate_date,
        )
        result = await self.session.execute(query)
        existing = result.scalar_one_or_none()

        if existing:
            return await self.update(existing.id, rate=rate)

        return await self.create(
            from_currency=from_currency,
            to_currency=to_currency,
            rate=rate,
            date=rate_date,
        )

    async def set_rate_bidirectional(
        self,
        currency_a: str,
        currency_b: str,
        rate_a_to_b: Decimal,
        rate_date: Optional[date] = None,
    ) -> None:
        """Set exchange rate in both directions.

        Args:
            currency_a: First currency
            currency_b: Second currency
            rate_a_to_b: Rate from A to B
            rate_date: Date for the rate
        """
        rate_date = rate_date or date.today()

        # A -> B
        await self.set_rate(currency_a, currency_b, rate_a_to_b, rate_date)

        # B -> A (inverse)
        if rate_a_to_b != 0:
            rate_b_to_a = Decimal("1") / rate_a_to_b
            await self.set_rate(currency_b, currency_a, rate_b_to_a, rate_date)
