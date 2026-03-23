"""
Flat pricing for documentation optimization.

One price for everyone: €84 ($99 USD). No tiers, no complexity.
One-time payment. No subscription. No recurring fees.
"""

from config import get_settings


def calculate_report_price(page_count: int) -> int:
    """
    Return the flat price in EUR.

    We keep page_count as a parameter for API compatibility,
    but the price is always the same: €84 ($99 USD).
    """
    settings = get_settings()
    return settings.pricing_min_eur  # €84 flat


def get_price_breakdown(page_count: int) -> dict:
    """Return a price breakdown for API responses.

    Note: We intentionally don't expose cost structure or margin.
    The customer sees page count and final price — that's it.
    """
    price = calculate_report_price(page_count)

    return {
        "page_count": page_count,
        "price_eur": price,
    }
