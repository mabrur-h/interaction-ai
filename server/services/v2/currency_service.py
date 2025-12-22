"""Currency service for multi-currency support."""

from datetime import date
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Tuple

from server.repositories.exchange_rates import ExchangeRateRepository


# Supported currencies with their symbols
SUPPORTED_CURRENCIES = {
    "UZS": {"symbol": "so'm", "decimals": 0},
    "USD": {"symbol": "$", "decimals": 2},
    "EUR": {"symbol": "€", "decimals": 2},
    "RUB": {"symbol": "₽", "decimals": 2},
    "GBP": {"symbol": "£", "decimals": 2},
}

# Default rates (fallback when no rate in DB)
DEFAULT_RATES = {
    ("USD", "UZS"): Decimal("12600"),
    ("EUR", "UZS"): Decimal("13200"),
    ("RUB", "UZS"): Decimal("126"),
    ("GBP", "UZS"): Decimal("15800"),
}


class CurrencyService:
    """Service for currency conversion and formatting."""

    def __init__(self, exchange_rate_repo: ExchangeRateRepository):
        """Initialize with exchange rate repository.

        Args:
            exchange_rate_repo: Repository for exchange rates
        """
        self.exchange_rate_repo = exchange_rate_repo

    async def convert(
        self,
        amount: int,
        from_currency: str,
        to_currency: str,
        rate_date: Optional[date] = None,
    ) -> Tuple[int, Optional[Decimal]]:
        """Convert amount between currencies.

        Args:
            amount: Amount in cents/smallest unit
            from_currency: Source currency code
            to_currency: Target currency code
            rate_date: Date for exchange rate (defaults to today)

        Returns:
            Tuple of (converted_amount, exchange_rate_used)
        """
        if from_currency == to_currency:
            return amount, Decimal("1.0")

        rate = await self.get_rate(from_currency, to_currency, rate_date)
        if rate is None:
            # Use default rate if available
            rate = self._get_default_rate(from_currency, to_currency)
            if rate is None:
                raise ValueError(
                    f"No exchange rate found for {from_currency} -> {to_currency}"
                )

        converted = Decimal(str(amount)) * rate
        return int(converted.quantize(Decimal("1"), rounding=ROUND_HALF_UP)), rate

    async def get_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate_date: Optional[date] = None,
    ) -> Optional[Decimal]:
        """Get exchange rate for currency pair.

        Args:
            from_currency: Source currency code
            to_currency: Target currency code
            rate_date: Date for the rate

        Returns:
            Exchange rate or None if not found
        """
        if from_currency == to_currency:
            return Decimal("1.0")

        return await self.exchange_rate_repo.get_rate(
            from_currency, to_currency, rate_date
        )

    def _get_default_rate(
        self,
        from_currency: str,
        to_currency: str,
    ) -> Optional[Decimal]:
        """Get default/fallback rate for currency pair."""
        # Direct lookup
        if (from_currency, to_currency) in DEFAULT_RATES:
            return DEFAULT_RATES[(from_currency, to_currency)]

        # Inverse lookup
        if (to_currency, from_currency) in DEFAULT_RATES:
            rate = DEFAULT_RATES[(to_currency, from_currency)]
            return Decimal("1") / rate if rate != 0 else None

        return None

    def format_amount(
        self,
        amount: int,
        currency: str,
        include_symbol: bool = True,
    ) -> str:
        """Format amount for display.

        Args:
            amount: Amount in cents/smallest unit
            currency: Currency code
            include_symbol: Whether to include currency symbol

        Returns:
            Formatted string
        """
        currency_info = SUPPORTED_CURRENCIES.get(
            currency, {"symbol": currency, "decimals": 2}
        )
        decimals = currency_info["decimals"]

        if decimals == 0:
            # No decimal places (like UZS)
            formatted = f"{amount:,}"
        else:
            # With decimal places
            divisor = 10 ** decimals
            whole = amount // divisor
            fraction = amount % divisor
            formatted = f"{whole:,}.{fraction:0{decimals}d}"

        if include_symbol:
            symbol = currency_info["symbol"]
            # Symbol placement varies by currency
            if currency in ("USD", "GBP"):
                return f"{symbol}{formatted}"
            else:
                return f"{formatted} {symbol}"

        return formatted

    async def set_rate(
        self,
        from_currency: str,
        to_currency: str,
        rate: Decimal,
        rate_date: Optional[date] = None,
        bidirectional: bool = True,
    ) -> None:
        """Set exchange rate.

        Args:
            from_currency: Source currency
            to_currency: Target currency
            rate: Exchange rate
            rate_date: Date for the rate
            bidirectional: If True, also sets inverse rate
        """
        if bidirectional:
            await self.exchange_rate_repo.set_rate_bidirectional(
                from_currency, to_currency, rate, rate_date
            )
        else:
            await self.exchange_rate_repo.set_rate(
                from_currency, to_currency, rate, rate_date
            )

    @staticmethod
    def is_supported(currency: str) -> bool:
        """Check if currency is supported."""
        return currency in SUPPORTED_CURRENCIES

    @staticmethod
    def get_supported_currencies() -> list:
        """Get list of supported currency codes."""
        return list(SUPPORTED_CURRENCIES.keys())
