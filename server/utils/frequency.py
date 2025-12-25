"""Frequency calculation utilities for recurring transactions."""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta


def calculate_next_due_date(current_due: date, frequency: str) -> date:
    """
    Calculate the next due date based on frequency.

    Args:
        current_due: The current due date
        frequency: One of 'daily', 'weekly', 'biweekly', 'monthly', 'yearly'

    Returns:
        The next due date

    Raises:
        ValueError: If frequency is not recognized
    """
    if frequency == "daily":
        return current_due + timedelta(days=1)
    elif frequency == "weekly":
        return current_due + timedelta(weeks=1)
    elif frequency == "biweekly":
        return current_due + timedelta(weeks=2)
    elif frequency == "monthly":
        return current_due + relativedelta(months=1)
    elif frequency == "yearly":
        return current_due + relativedelta(years=1)
    else:
        raise ValueError(f"Unknown frequency: {frequency}")


def get_frequency_multiplier_monthly(frequency: str) -> float:
    """
    Get the multiplier to convert a frequency amount to monthly equivalent.

    Args:
        frequency: One of 'daily', 'weekly', 'biweekly', 'monthly', 'yearly'

    Returns:
        Multiplier for monthly calculation
    """
    multipliers = {
        "daily": 30.0,
        "weekly": 4.33,
        "biweekly": 2.17,
        "monthly": 1.0,
        "yearly": 1 / 12,
    }
    return multipliers.get(frequency, 1.0)


VALID_FREQUENCIES = ["daily", "weekly", "biweekly", "monthly", "yearly"]


def is_valid_frequency(frequency: str) -> bool:
    """Check if a frequency string is valid."""
    return frequency in VALID_FREQUENCIES
