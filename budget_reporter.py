#!/usr/bin/env python3
import csv
from datetime import datetime
import glob
import re
from dateutil.relativedelta import relativedelta
from stockholm import Money
from mako.template import Template


def parse_latest_valid_budget(monthly_budgets, statement):
    statement_date = parse_monthly_statement_date(statement)
    latest_valid_budget = None
    for budget in sorted(monthly_budgets):
        monthly_budget_date = parse_monthly_budget_date(budget)
        if monthly_budget_date < statement_date:
            latest_valid_budget = budget
        if latest_valid_budget is None:
            raise Exception("No valid budget found for provided statement: {}!".format(statement))
    parsed_budget = {}
    with open(budget) as file:
        reader = csv.reader(file)
        header_row = True
        
        for row in reader:
            if header_row:
                category_index = row.index("Category")
                sub_category_index = row.index("Sub-Category")
                budget_index = row.index("Budget")
                header_row = False
            else:
                category = row[category_index]
                sub_category = row[sub_category_index]
                if category not in parsed_budget:
                    parsed_budget[category] = {}
                parsed_budget[category][sub_category] = Money(int(row[budget_index]), "AUD")
    return parsed_budget

def parse_monthly_statement(statement):
    parsed_statement = {}
    with open(statement) as file:
        reader = csv.reader(file)
        header_row = True

        for row in reader:
            if header_row:
                debit_index = row.index("Debit")
                category_index = row.index("Category")
                sub_category_index = row.index("Sub-Category")
                header_row = False
            else:
                normalised_debit = row[debit_index].replace("$", "").replace(",","")
                if normalised_debit == "" or normalised_debit == "-":
                    continue
                parsed_debit_amount = Money(normalised_debit, "AUD")
                category_name = "Uncategorised" if row[category_index] == "" or row[category_index] == "-" else row[category_index]
                sub_category_name = "Uncategorised" if row[sub_category_index] == "" or row[sub_category_index] == "-" else row[sub_category_index]
                if category_name not in parsed_statement:
                    parsed_statement[category_name] = {}
                    parsed_statement[category_name][sub_category_name] = parsed_debit_amount
                elif sub_category_name not in parsed_statement[category_name]:
                    parsed_statement[category_name][sub_category_name] = parsed_debit_amount
                else:
                    current_total = parsed_statement[category_name][sub_category_name]
                    parsed_statement[category_name][sub_category_name] = current_total + parsed_debit_amount
    return parsed_statement

def prepare_report_rows(parsed_budget, parsed_statement, carry, remainder):
    rows = []
    for category in parsed_budget:
        category_budget = category_total(parsed_budget, category)
        category_spend = category_total(parsed_statement, category)
        category_carry = category_total(carry, category)
        category_remainder = category_total(remainder, category)
        category_row = [category, "", "", "", "", ""]
        rows.append(category_row)
        for sub_category in parsed_budget[category]:
            sub_category_budget = Money(0, "AUD") if sub_category not in parsed_budget[category] else parsed_budget[category][sub_category]
            sub_category_spend: Money = Money(0, "AUD") if category not in parsed_statement or sub_category not in parsed_statement[category] else parsed_statement[category][sub_category]
            sub_category_carry: Money = Money(0, "AUD") if sub_category not in carry[category] else carry[category][sub_category]
            sub_category_remainder: Money = Money(0, "AUD") if sub_category not in remainder[category] else remainder[category][sub_category]
            sub_category_row = ["", sub_category, sub_category_budget.amount_as_string(), sub_category_carry.amount_as_string(), sub_category_spend.amount_as_string(), sub_category_remainder.amount_as_string()]
            rows.append(sub_category_row)
        totals_row = ["Total", "", category_budget.amount_as_string(), category_carry.amount_as_string(), category_spend.amount_as_string(), category_remainder.amount_as_string()]
        rows.append(totals_row)
    return rows

def category_total(parsed_dict, category_name):
    sum = Money(0, "AUD")
    if category_name not in parsed_dict:
        return sum
    for sub_category in parsed_dict[category_name]:
        sum = sum + parsed_dict[category_name][sub_category]
    return sum

def render_csv(parsed_budget, parsed_statement, carry, remainder, statement_date: datetime):
    report_rows = []
    report_rows.append(rows_header.copy())
    for row in prepare_report_rows(parsed_budget, parsed_statement, carry, remainder):
        report_rows.append(row)
    filename = "report{}.csv".format(statement_date.strftime("%Y%m%d"))
    with open(filename, 'w') as file:
        writer = csv.writer(file)
        for row in report_rows:
            writer.writerow(row)

def render_html(parsed_budget, parsed_statement, carry, remainder, statement_date: datetime):
    report_rows = prepare_report_rows(parsed_budget, parsed_statement, carry, remainder)
    header = "Budget Spend " + statement_date.strftime("%B %Y")
    filename = "report{}.html".format(statement_date.strftime("%Y%m%d"))
    rendered_template = Template(filename='report_template.mako').render(rows=report_rows, header=header, rows_header=rows_header)
    with open(filename, 'w') as file:
        file.write(rendered_template)
    

def compute_remainder(carry, parsed_budget, parsed_statement):
    remainder = {}
    for category in parsed_budget:
        remainder[category] = {}
        for sub_category in parsed_budget[category]:
            sub_category_budget = parsed_budget[category][sub_category]
            sub_category_spend = Money(0, "AUD") if category not in parsed_statement or sub_category not in parsed_statement[category] else parsed_statement[category][sub_category]
            sub_category_carry = carry[category][sub_category]
            remainder[category][sub_category] = sub_category_budget - sub_category_spend + sub_category_carry
    return remainder

def compute_carry(prev_remainder, parsed_budget):
    if prev_remainder == None:
        return init_carry(parsed_budget)
    carry = {}
    for category in prev_remainder:
        carry[category] = {}
        for sub_category in prev_remainder[category]:
            carry[category][sub_category] = prev_remainder[category][sub_category]

def init_carry(parsed_budget):
    carry = {}
    for category in parsed_budget:
        carry[category] = {}
        for sub_category in parsed_budget[category]:
            carry[category][sub_category] = Money(0, "AUD")
    return carry   

def parse_monthly_statement_date(statement):
    statement_date_str = re.search("([0-9]{4}-[0-9]{2})", statement).group(0)
    return datetime.strptime(statement_date_str, "%Y-%m") + relativedelta(months=1) - relativedelta(days=1)

def parse_monthly_budget_date(budget):
    monthly_budget_date_str = re.search("([0-9]{8})", budget).group(0)
    return datetime.strptime(monthly_budget_date_str, "%Y%m%d")

monthly_budget_csv_pattern = "./monthly_budget[0-9]*.csv"
expenses_statement_csv_pattern = "./SpendAccount[a-zA-Z0-9-]*[0-9]*-[0-9]*.csv"

monthly_budgets = glob.glob(monthly_budget_csv_pattern)

monthly_expenses = glob.glob(expenses_statement_csv_pattern)

rows_header = ['Category', 'Sub-Category', 'Monthly Allocation (Budget)', 'Prev. Month Remainder', 'Spend', 'Remainder']

carry = None
remainder = None
for statement in monthly_expenses:
    parsed_budget = parse_latest_valid_budget(monthly_budgets, statement)
    parsed_statement = parse_monthly_statement(statement)
    statement_date = parse_monthly_statement_date(statement)
    carry = compute_carry(remainder, parsed_budget)
    remainder = compute_remainder(carry, parsed_budget, parsed_statement)
    render_csv(parsed_budget, parsed_statement, carry, remainder, statement_date)
    render_html(parsed_budget, parsed_statement, carry, remainder, statement_date)
