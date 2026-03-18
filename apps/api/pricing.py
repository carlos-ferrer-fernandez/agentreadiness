"""
Dynamic pricing based on documentation size.

Price = max(min_price, round_up_to_nice(estimated_api_cost * multiplier))

The idea: the bigger the documentation, the more API work is needed to produce
the report, so the price scales with the actual effort. Minimum price is kept
low (€49) to be an impulse buy for small docs sites.
"""

import math
from config import get_settings


def _round_to_nice_price(raw: float) -> int:
    """Round up to the nearest 'nice' price ending in 9."""
    # Examples: 49, 79, 99, 129, 149, 199, 249, 299, 349, 399, 449, 499
    ceiled = math.ceil(raw)
    # Round up to next number ending in 9
    remainder = ceiled % 10
    if remainder <= 9:
        nice = ceiled + (9 - remainder)
    return nice


def calculate_report_price(page_count: int) -> int:
    """
    Calculate the report price in EUR based on the number of pages analysed.

    Returns an integer price in EUR (e.g. 49, 79, 149).
    """
    settings = get_settings()

    estimated_api_cost = (
        settings.pricing_base_cost
        + settings.pricing_per_page_cost * page_count
    )

    raw_price = estimated_api_cost * settings.pricing_margin_multiplier

    nice_price = _round_to_nice_price(raw_price)

    # Clamp between min and max
    return max(settings.pricing_min_eur, min(nice_price, settings.pricing_max_eur))


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
