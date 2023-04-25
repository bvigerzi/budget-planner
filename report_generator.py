#!/usr/bin/env python3
import glob

from calculator import compute_carry, compute_remainder, compute_remaining_spend, \
    compute_next_month_available_budget
from budget_parser import parse_latest_valid_budget, parse_monthly_statement, parse_monthly_statement_date
from renderer import render_csv, render_html
from gpt_categoriser import categorise_statement
from file_paths import MONTHLY_BUDGET_DIR, MONTHLY_BUDGET_CSV_PATTERN, EXPENSES_STATEMENT_PRE_CATEGORISE_DIR, \
    EXPENSES_STATEMENT_POST_CATEGORISE_DIR, EXPENSES_STATEMENT_CSV_PATTERN

if __name__ == "__main__":
    monthly_budgets: list[str] = glob.glob(MONTHLY_BUDGET_DIR + MONTHLY_BUDGET_CSV_PATTERN)

    uncategorised_monthly_expenses: list[str] = glob.glob(
        "{0}{1}".format(EXPENSES_STATEMENT_PRE_CATEGORISE_DIR, EXPENSES_STATEMENT_CSV_PATTERN))
    categorised_monthly_expenses: list[str] = glob.glob(
        "{0}{1}".format(EXPENSES_STATEMENT_POST_CATEGORISE_DIR, EXPENSES_STATEMENT_CSV_PATTERN))

    carry = None
    remainder = None

    categorised_statement_files = list(
        map(lambda categorised_statement: categorised_statement[len(EXPENSES_STATEMENT_POST_CATEGORISE_DIR):],
            categorised_monthly_expenses))

    for statement in uncategorised_monthly_expenses:
        uncategorised_statement = statement[len(EXPENSES_STATEMENT_PRE_CATEGORISE_DIR):]
        if uncategorised_statement not in categorised_statement_files:
            categorise_statement(monthly_budgets, statement)

# TODO: wait for async operations -- writing file has IO delay which needs to be factored in

    for statement in categorised_monthly_expenses:
        # Parse budget and expenses step
        parsed_budget = parse_latest_valid_budget(monthly_budgets, statement)
        parsed_statement = parse_monthly_statement(statement)
        statement_date = parse_monthly_statement_date(statement)
        # Compute spend step
        carry = compute_carry(remainder, parsed_budget)
        remainder = compute_remainder(carry, parsed_budget, parsed_statement)
        remaining_spend = compute_remaining_spend(carry, parsed_budget)
        next_month_available = compute_next_month_available_budget(remainder, parsed_budget)
        # Render report step
        render_csv(parsed_budget, parsed_statement, carry, remainder, remaining_spend, next_month_available,
                   statement_date)
        render_html(parsed_budget, parsed_statement, carry, remainder, remaining_spend, next_month_available,
                    statement_date)
