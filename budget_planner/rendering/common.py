"""Shared report rendering utilities."""

from stockholm import Money

REPORT_HEADER: list[str] = [
    "Category",
    "Sub-Category",
    "Monthly Allocation (Budget)",
    "Prev. Month Remainder",
    "Avail. Budget",
    "Spend",
    "Remainder",
    "Next Month Avail.",
]


def prepare_report_rows(
    parsed_budget: dict,
    parsed_statement: dict,
    carry: dict,
    remainder: dict,
    remaining_spend: dict,
    next_month_available: dict,
) -> list[list[str]]:
    """Structure all budget data into rows for report generation."""
    rows = []
    complete_budget_total = Money(0, "AUD")
    complete_spend_total = Money(0, "AUD")
    complete_carry_total = Money(0, "AUD")
    complete_remainder_total = Money(0, "AUD")
    complete_remaining_spend_total = Money(0, "AUD")
    complete_next_month_available_total = Money(0, "AUD")

    for category in parsed_budget:
        cat_budget = category_total(parsed_budget, category)
        cat_spend = category_total(parsed_statement, category)
        cat_carry = category_total(carry, category)
        cat_remainder = category_total(remainder, category)
        cat_remaining_spend = category_total(remaining_spend, category)
        cat_next_month = category_total(next_month_available, category)

        complete_budget_total += cat_budget
        complete_spend_total += cat_spend
        complete_carry_total += cat_carry
        complete_remainder_total += cat_remainder
        complete_remaining_spend_total += cat_remaining_spend
        complete_next_month_available_total += cat_next_month

        rows.append([category, "", "", "", "", "", "", ""])

        for sub_category in parsed_budget[category]:
            sub_budget = parsed_budget[category].get(
                sub_category, Money(0, "AUD")
            )
            sub_spend = parsed_statement.get(category, {}).get(
                sub_category, Money(0, "AUD")
            )
            sub_carry = carry[category].get(sub_category, Money(0, "AUD"))
            sub_remainder = remainder[category].get(
                sub_category, Money(0, "AUD")
            )
            sub_remaining_spend = remaining_spend[category].get(
                sub_category, Money(0, "AUD")
            )
            sub_next_month = next_month_available[category].get(
                sub_category, Money(0, "AUD")
            )

            rows.append([
                "",
                sub_category,
                sub_budget.amount_as_string(),
                sub_carry.amount_as_string(),
                sub_remaining_spend.amount_as_string(),
                sub_spend.amount_as_string(),
                sub_remainder.amount_as_string(),
                sub_next_month.amount_as_string(),
            ])

        rows.append([
            "Total",
            "",
            cat_budget.amount_as_string(),
            cat_carry.amount_as_string(),
            cat_remaining_spend.amount_as_string(),
            cat_spend.amount_as_string(),
            cat_remainder.amount_as_string(),
            cat_next_month.amount_as_string(),
        ])

    rows.append([
        "Complete Total",
        "",
        complete_budget_total.amount_as_string(),
        complete_carry_total.amount_as_string(),
        complete_remaining_spend_total.amount_as_string(),
        complete_spend_total.amount_as_string(),
        complete_remainder_total.amount_as_string(),
        complete_next_month_available_total.amount_as_string(),
    ])

    return rows


def category_total(parsed_dict: dict, category_name: str) -> Money:
    """Calculate the total for a category across all sub-categories."""
    total = Money(0, "AUD")
    if category_name not in parsed_dict:
        return total
    for sub_category in parsed_dict[category_name]:
        total += parsed_dict[category_name][sub_category]
    return total
