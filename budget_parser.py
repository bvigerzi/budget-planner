import csv
import re
from dateutil.relativedelta import relativedelta
from stockholm import Money
from datetime import datetime


def find_latest_valid_budget(monthly_budgets: list[str], statement: str) -> str:
    statement_date = parse_monthly_statement_date(statement)
    latest_valid_budget = None
    for budget in sorted(monthly_budgets):
        monthly_budget_date = parse_monthly_budget_date(budget)
        if monthly_budget_date < statement_date:
            latest_valid_budget = budget
    if latest_valid_budget is None:
        raise Exception("No valid budget found for provided statement: {}!".format(statement))
    return latest_valid_budget


def parse_latest_valid_budget(monthly_budgets: list[str], statement: str) -> dict:
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
                    parsed_budget[category][sub_category] = Money(int(row[budget_index]), "AUD")
    return parsed_budget


def parse_monthly_statement(statement: str) -> dict:
    parsed_statement = {}
    with open(statement) as file:
        reader = csv.reader(file)
        header_row = True

        for row in reader:
            if header_row:
                debit_index = row.index("Debit")
                credit_index = row.index("Credit")
                category_index = row.index("Category")
                sub_category_index = row.index("Sub-Category")
                header_row = False
            else:
                normalised_debit = row[debit_index].replace("$", "").replace(",", "")
                normalised_credit = row[credit_index].replace("$", "").replace(",", "")
                missing_debit = normalised_debit == "" or normalised_debit == "-"
                missing_credit = normalised_credit == "" or normalised_credit == "-"
                category_exists = row[category_index] != "" and row[category_index] != "-"
                sub_category_exists = row[sub_category_index] != "" and row[sub_category_index] != "-"
                credit_with_category = not missing_credit and category_exists and sub_category_exists

                if missing_debit and not credit_with_category:
                    continue

                parsed_debit_amount = None if missing_debit else Money(normalised_debit, "AUD")
                parsed_credit_amount: Money = None if missing_credit else -Money(normalised_credit, "AUD")
                applied_amount = parsed_debit_amount if parsed_debit_amount is not None else parsed_credit_amount
                category_name = "Uncategorised" if not category_exists else row[category_index]
                sub_category_name = "Uncategorised" if not sub_category_exists else row[sub_category_index]

                if category_name not in parsed_statement:
                    parsed_statement[category_name] = {}
                    parsed_statement[category_name][sub_category_name] = applied_amount
                elif sub_category_name not in parsed_statement[category_name]:
                    parsed_statement[category_name][sub_category_name] = applied_amount
                else:
                    current_total: Money = parsed_statement[category_name][sub_category_name]
                    parsed_statement[category_name][sub_category_name] = current_total + applied_amount

    return parsed_statement


def parse_monthly_statement_date(statement: str) -> datetime:
    statement_date_str = re.search("([0-9]{4}-[0-9]{2})", statement).group(0)
    return datetime.strptime(statement_date_str, "%Y-%m") + relativedelta(months=1) - relativedelta(days=1)


def parse_monthly_budget_date(budget: str) -> datetime:
    monthly_budget_date_str = re.search("([0-9]{8})", budget).group(0)
    return datetime.strptime(monthly_budget_date_str, "%Y%m%d")