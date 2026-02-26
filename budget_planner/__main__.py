"""Entry point for the budget planner report generator."""

import glob
import logging
from pathlib import Path

from budget_planner.calculator import (
    compute_carry,
    compute_next_month_available_budget,
    compute_remainder,
    compute_remaining_spend,
)
from budget_planner.categoriser import categorise_statement
from budget_planner.config import (
    EXPENSES_STATEMENT_CSV_PATTERN,
    EXPENSES_STATEMENT_POST_CATEGORISE_DIR,
    EXPENSES_STATEMENT_PRE_CATEGORISE_DIR,
    MONTHLY_BUDGET_CSV_PATTERN,
    MONTHLY_BUDGET_DIR,
)
from budget_planner.parsing import (
    parse_latest_valid_budget,
    parse_monthly_statement,
    parse_monthly_statement_date,
)
from budget_planner.rendering import render_csv, render_html

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


def main() -> None:
    """Generate budget reports from expense statements."""
    monthly_budgets = glob.glob(
        str(MONTHLY_BUDGET_DIR / MONTHLY_BUDGET_CSV_PATTERN)
    )

    uncategorised_monthly_expenses = glob.glob(
        str(EXPENSES_STATEMENT_PRE_CATEGORISE_DIR / EXPENSES_STATEMENT_CSV_PATTERN)
    )
    categorised_monthly_expenses = glob.glob(
        str(EXPENSES_STATEMENT_POST_CATEGORISE_DIR / EXPENSES_STATEMENT_CSV_PATTERN)
    )

    categorised_filenames = {
        Path(path).name for path in categorised_monthly_expenses
    }

    for statement in uncategorised_monthly_expenses:
        if Path(statement).name not in categorised_filenames:
            logger.info("Categorising statement: %s", statement)
            categorise_statement(monthly_budgets, statement)

    carry = None
    remainder = None

    for statement in categorised_monthly_expenses:
        logger.info("Processing statement: %s", statement)

        parsed_budget = parse_latest_valid_budget(monthly_budgets, statement)
        parsed_statement = parse_monthly_statement(statement)
        statement_date = parse_monthly_statement_date(statement)

        carry = compute_carry(remainder, parsed_budget)
        remainder = compute_remainder(carry, parsed_budget, parsed_statement)
        remaining_spend = compute_remaining_spend(carry, parsed_budget)
        next_month_available = compute_next_month_available_budget(
            remainder, parsed_budget
        )

        render_csv(
            parsed_budget,
            parsed_statement,
            carry,
            remainder,
            remaining_spend,
            next_month_available,
            statement_date,
        )
        render_html(
            parsed_budget,
            parsed_statement,
            carry,
            remainder,
            remaining_spend,
            next_month_available,
            statement_date,
        )
        logger.info(
            "Generated reports for %s", statement_date.strftime("%B %Y")
        )


if __name__ == "__main__":
    main()
