#!/usr/bin/env python3
import csv
from datetime import datetime
import glob
import re
from dateutil.relativedelta import relativedelta
from stockholm import Money
from mako.template import Template

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
                normalised_debit = row[debit_index].replace("$", "").replace(",","")
                normalised_credit = row[credit_index].replace("$", "").replace(",","")
                missing_debit = normalised_debit == "" or normalised_debit == "-"
                missing_credit = normalised_credit == "" or normalised_credit == "-"
                category_exists = row[category_index] != "" and row[category_index] != "-"
                sub_category_exists = row[sub_category_index] != "" and row[sub_category_index] != "-"
                credit_with_category = not missing_credit and category_exists and sub_category_exists

                if missing_debit and not credit_with_category:
                    continue

                parsed_debit_amount = None if missing_debit else Money(normalised_debit, "AUD")
                parsed_credit_amount: Money = None if missing_credit else -Money(normalised_credit, "AUD")
                applied_amount = parsed_debit_amount if parsed_debit_amount != None else parsed_credit_amount
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

def prepare_report_rows(parsed_budget: dict, parsed_statement: dict, carry: dict, remainder: dict, remaining_spend: dict, next_month_available: dict) -> list[list[str]]:
    rows = []
    complete_budget_total = Money(0, "AUD")
    complete_spend_total = Money(0, "AUD")
    complete_carry_total = Money(0, "AUD")
    complete_remainder_total = Money(0, "AUD")
    complete_remaining_spend_total = Money(0, "AUD")
    complete_next_month_available_total = Money(0, "AUD")
    for category in parsed_budget:
        category_budget = category_total(parsed_budget, category)
        category_spend = category_total(parsed_statement, category)
        category_carry = category_total(carry, category)
        category_remainder = category_total(remainder, category)
        category_remaining_spend = category_total(remaining_spend, category)
        category_next_month_available = category_total(next_month_available, category)

        complete_budget_total = complete_budget_total + category_budget
        complete_spend_total = complete_spend_total + category_spend
        complete_carry_total = complete_carry_total + category_carry
        complete_remainder_total = complete_remainder_total + category_remainder
        complete_remaining_spend_total = complete_remaining_spend_total + category_remaining_spend
        complete_next_month_available_total = complete_next_month_available_total + category_next_month_available

        category_row = [category, "", "", "", "", "", "", ""]
        rows.append(category_row)

        for sub_category in parsed_budget[category]:
            sub_category_budget = Money(0, "AUD") if sub_category not in parsed_budget[category] else parsed_budget[category][sub_category]
            sub_category_spend: Money = Money(0, "AUD") if category not in parsed_statement or sub_category not in parsed_statement[category] else parsed_statement[category][sub_category]
            sub_category_carry: Money = Money(0, "AUD") if sub_category not in carry[category] else carry[category][sub_category]
            sub_category_remainder: Money = Money(0, "AUD") if sub_category not in remainder[category] else remainder[category][sub_category]
            sub_category_remaining_spend: Money = Money(0, "AUD") if sub_category not in remaining_spend[category] else remaining_spend[category][sub_category]
            sub_category_next_month_available: Money = Money(0, "AUD") if sub_category not in next_month_available[category] else next_month_available[category][sub_category]
            sub_category_row = ["", sub_category, sub_category_budget.amount_as_string(), sub_category_carry.amount_as_string(), sub_category_remaining_spend.amount_as_string(), sub_category_spend.amount_as_string(), sub_category_remainder.amount_as_string(), sub_category_next_month_available.amount_as_string()]
            rows.append(sub_category_row)
        totals_row = ["Total", "", category_budget.amount_as_string(), category_carry.amount_as_string(), category_remaining_spend.amount_as_string(), category_spend.amount_as_string(), category_remainder.amount_as_string(), category_next_month_available.amount_as_string()]
        rows.append(totals_row)
    complete_totals_row = ["Complete Total", "", complete_budget_total.amount_as_string(), complete_carry_total.amount_as_string(), complete_remaining_spend_total.amount_as_string(), complete_spend_total.amount_as_string(), complete_remainder_total.amount_as_string(), complete_next_month_available_total.amount_as_string()]
    rows.append(complete_totals_row)
    return rows

def category_total(parsed_dict: dict, category_name: str) -> Money:
    sum = Money(0, "AUD")
    if category_name not in parsed_dict:
        return sum
    for sub_category in parsed_dict[category_name]:
        sum = sum + parsed_dict[category_name][sub_category]
    return sum

def render_csv(parsed_budget: dict, parsed_statement: dict, carry: dict, remainder: dict, remaining_spend: dict, next_month_available: dict, statement_date: datetime) -> None:
    report_rows = []
    report_rows.append(rows_header.copy())
    for row in prepare_report_rows(parsed_budget, parsed_statement, carry, remainder, remaining_spend, next_month_available):
        report_rows.append(row)
    filename = "report{}.csv".format(statement_date.strftime("%Y%m%d"))
    with open(filename, 'w') as file:
        writer = csv.writer(file)
        for row in report_rows:
            writer.writerow(row)

def render_html(parsed_budget: dict, parsed_statement: dict, carry: dict, remainder: dict, remaining_spend: dict, next_month_available: dict, statement_date: datetime) -> None:
    report_rows = prepare_report_rows(parsed_budget, parsed_statement, carry, remainder, remaining_spend, next_month_available)
    header = "Budget Spend " + statement_date.strftime("%B %Y")
    filename = "report{}.html".format(statement_date.strftime("%Y%m%d"))
    rendered_template = Template(filename='report_template.mako').render(rows=report_rows, header=header, rows_header=rows_header)
    with open(filename, 'w') as file:
        file.write(rendered_template)
    

def compute_remainder(carry: dict, parsed_budget: dict, parsed_statement: dict) -> dict:
    remainder = {}
    for category in parsed_budget:
        remainder[category] = {}
        for sub_category in parsed_budget[category]:
            sub_category_budget = parsed_budget[category][sub_category]
            sub_category_spend = Money(0, "AUD") if category not in parsed_statement or sub_category not in parsed_statement[category] else parsed_statement[category][sub_category]
            sub_category_carry = carry[category][sub_category]
            remainder[category][sub_category] = sub_category_budget - sub_category_spend + sub_category_carry
    return remainder

def compute_remaining_spend(carry: dict, parsed_budget: dict) -> dict:
    remaining_spend = {}
    for category in parsed_budget:
        remaining_spend[category] = {}
        for sub_category in parsed_budget[category]:
            sub_category_budget = parsed_budget[category][sub_category]
            sub_category_carry = carry[category][sub_category]
            remaining_spend[category][sub_category] = sub_category_budget + sub_category_carry
    return remaining_spend

def compute_next_month_available_budget(remainder: dict, parsed_budget: dict) -> dict:
    next_month_budget = {}
    for category in parsed_budget:
        next_month_budget[category] = {}
        for sub_category in parsed_budget[category]:
            sub_category_budget = parsed_budget[category][sub_category]
            sub_category_remainder = remainder[category][sub_category]
            next_month_budget[category][sub_category] = sub_category_budget + sub_category_remainder
    return next_month_budget

def compute_carry(prev_remainder: dict, parsed_budget: dict) -> dict:
    if prev_remainder == None:
        return init_carry(parsed_budget)
    carry = {}
    for category in prev_remainder:
        carry[category] = {}
        for sub_category in prev_remainder[category]:
            carry[category][sub_category] = prev_remainder[category][sub_category]
    return carry

def init_carry(parsed_budget: dict) -> dict:
    carry = {}
    for category in parsed_budget:
        carry[category] = {}
        for sub_category in parsed_budget[category]:
            carry[category][sub_category] = Money(0, "AUD")
    return carry   

def parse_monthly_statement_date(statement: str) -> datetime:
    statement_date_str = re.search("([0-9]{4}-[0-9]{2})", statement).group(0)
    return datetime.strptime(statement_date_str, "%Y-%m") + relativedelta(months=1) - relativedelta(days=1)

def parse_monthly_budget_date(budget: str) -> datetime:
    monthly_budget_date_str = re.search("([0-9]{8})", budget).group(0)
    return datetime.strptime(monthly_budget_date_str, "%Y%m%d")

monthly_budget_csv_pattern: str = "./monthly_budget[0-9]*.csv"
expenses_statement_csv_pattern: str = "./SpendAccount[a-zA-Z0-9-]*[0-9]*-[0-9]*.csv"

monthly_budgets: list[str] = glob.glob(monthly_budget_csv_pattern)

monthly_expenses: list[str] = glob.glob(expenses_statement_csv_pattern)

rows_header: list[str] = ['Category', 'Sub-Category', 'Monthly Allocation (Budget)', 'Prev. Month Remainder', 'Avail. Budget', 'Spend', 'Remainder', 'Next Month Avail.']

carry = None
remainder = None
for statement in monthly_expenses:
    parsed_budget = parse_latest_valid_budget(monthly_budgets, statement)
    print(parsed_budget)
    parsed_statement = parse_monthly_statement(statement)
    statement_date = parse_monthly_statement_date(statement)
    carry = compute_carry(remainder, parsed_budget)
    remainder = compute_remainder(carry, parsed_budget, parsed_statement)
    remaining_spend = compute_remaining_spend(carry, parsed_budget)
    next_month_available = compute_next_month_available_budget(remainder, parsed_budget)
    render_csv(parsed_budget, parsed_statement, carry, remainder, remaining_spend, next_month_available, statement_date)
    render_html(parsed_budget, parsed_statement, carry, remainder, remaining_spend, next_month_available, statement_date)
