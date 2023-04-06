#!/usr/bin/env python3
import glob

from calculator import compute_carry, compute_remainder, compute_remaining_spend, \
    compute_next_month_available_budget
from parser import parse_latest_valid_budget, parse_monthly_statement, parse_monthly_statement_date
from renderer import render_csv, render_html
from gpt_categoriser import gpt_friendly_budget

if __name__ == "__main__":
    monthly_budget_csv_pattern: str = "./monthly_budget[0-9]*.csv"
    expenses_statement_csv_pattern: str = "./SpendAccount[a-zA-Z0-9-]*[0-9]*-[0-9]*.csv"
    monthly_budgets: list[str] = glob.glob(monthly_budget_csv_pattern)
    monthly_expenses: list[str] = glob.glob(expenses_statement_csv_pattern)
    carry = None
    remainder = None

    for statement in monthly_expenses:
        parsed_budget = parse_latest_valid_budget(monthly_budgets, statement)
        print(gpt_friendly_budget(monthly_budgets, statement))
        parsed_statement = parse_monthly_statement(statement)
        statement_date = parse_monthly_statement_date(statement)
        carry = compute_carry(remainder, parsed_budget)
        remainder = compute_remainder(carry, parsed_budget, parsed_statement)
        remaining_spend = compute_remaining_spend(carry, parsed_budget)
        next_month_available = compute_next_month_available_budget(remainder, parsed_budget)
        render_csv(parsed_budget, parsed_statement, carry, remainder, remaining_spend, next_month_available,
                   statement_date)
        render_html(parsed_budget, parsed_statement, carry, remainder, remaining_spend, next_month_available,
                    statement_date)
