"""Budget file parsing utilities."""

import csv
import re
from datetime import datetime

from stockholm import Money

from budget_planner.parsing.statement import parse_monthly_statement_date


def find_latest_valid_budget(monthly_budgets: list[str], statement: str) -> str:
    """Find the most recent budget file that precedes the given statement date.

    Raises FileNotFoundError if no valid budget is found.
    """
    statement_date = parse_monthly_statement_date(statement)
    latest_valid_budget = None
    for budget in sorted(monthly_budgets):
        monthly_budget_date = parse_monthly_budget_date(budget)
        if monthly_budget_date < statement_date:
            latest_valid_budget = budget
    if latest_valid_budget is None:
        raise FileNotFoundError(
            f"No valid budget found for provided statement: {statement}"
        )
    return latest_valid_budget


def parse_latest_valid_budget(monthly_budgets: list[str], statement: str) -> dict:
    """Parse the latest valid budget CSV into a nested category dictionary.

    Returns a dict of {category: {sub_category: Money}}.
    """
    latest_valid_budget = find_latest_valid_budget(monthly_budgets, statement)
    parsed_budget = {}
    with open(latest_valid_budget) as file:
        reader = csv.reader(file)
        header_row = True

        for row in reader:
            if header_row:
                category_index = row.index("Category")
                sub_category_index = row.index("Sub-Category")
                budget_index = row.index("Budget")
                ignore_index = row.index("Ignore")
                header_row = False
            else:
                category = row[category_index]
                sub_category = row[sub_category_index]
                if category not in parsed_budget:
                    parsed_budget[category] = {}
                if row[ignore_index] != "1":
                    parsed_budget[category][sub_category] = Money(
                        int(row[budget_index]), "AUD"
                    )
    return parsed_budget


def parse_monthly_budget_date(budget: str) -> datetime:
    """Extract date from budget filename (YYYYMMDD format)."""
    monthly_budget_date_str = re.search(r"(\d{8})", budget).group(0)
    return datetime.strptime(monthly_budget_date_str, "%Y%m%d")
