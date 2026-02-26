"""Budget calculation functions.

Core formula: remainder = budget - spend + carry
"""

from stockholm import Money


def compute_remainder(
    carry: dict, parsed_budget: dict, parsed_statement: dict
) -> dict:
    """Calculate remainder for each sub-category: budget - spend + carry."""
    remainder = {}
    for category in parsed_budget:
        remainder[category] = {}
        for sub_category in parsed_budget[category]:
            sub_category_budget = parsed_budget[category][sub_category]
            sub_category_spend = (
                parsed_statement
                .get(category, {})
                .get(sub_category, Money(0, "AUD"))
            )
            sub_category_carry = carry[category][sub_category]
            remainder[category][sub_category] = (
                sub_category_budget - sub_category_spend + sub_category_carry
            )
    return remainder


def compute_remaining_spend(carry: dict, parsed_budget: dict) -> dict:
    """Compute available budget including carried amounts."""
    remaining_spend = {}
    for category in parsed_budget:
        remaining_spend[category] = {}
        for sub_category in parsed_budget[category]:
            sub_category_budget = parsed_budget[category][sub_category]
            sub_category_carry = carry[category][sub_category]
            remaining_spend[category][sub_category] = (
                sub_category_budget + sub_category_carry
            )
    return remaining_spend


def compute_next_month_available_budget(
    remainder: dict, parsed_budget: dict
) -> dict:
    """Calculate next month's available budget: budget + remainder."""
    next_month_budget = {}
    for category in parsed_budget:
        next_month_budget[category] = {}
        for sub_category in parsed_budget[category]:
            sub_category_budget = parsed_budget[category][sub_category]
            sub_category_remainder = remainder[category][sub_category]
            next_month_budget[category][sub_category] = (
                sub_category_budget + sub_category_remainder
            )
    return next_month_budget


def compute_carry(prev_remainder: dict | None, parsed_budget: dict) -> dict:
    """Convert previous month's remainder into this month's carry forward."""
    if prev_remainder is None:
        return init_carry(parsed_budget)
    return {
        category: dict(sub_categories)
        for category, sub_categories in prev_remainder.items()
    }


def init_carry(parsed_budget: dict) -> dict:
    """Initialise carry dictionary with zero values for all categories."""
    return {
        category: {
            sub_category: Money(0, "AUD")
            for sub_category in parsed_budget[category]
        }
        for category in parsed_budget
    }
