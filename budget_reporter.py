#!/usr/bin/env python3
import csv
from datetime import datetime
import glob
import re
from dateutil.relativedelta import relativedelta
from stockholm import Money

monthly_budget_csv_pattern = "./monthly_budget[0-9]*.csv"
expenses_statement_csv_pattern = "./SpendAccount[a-zA-Z0-9-]*[0-9]*-[0-9]*.csv"

monthly_budgets = glob.glob(monthly_budget_csv_pattern)

monthly_expenses = glob.glob(expenses_statement_csv_pattern)

def parse_latest_valid_budget(monthly_budgets, statement):
    statement_date_str = re.search("([0-9]{4}-[0-9]{2})", statement).group(0)
    statement_date = datetime.strptime(statement_date_str, "%Y-%m") + relativedelta(months=1) - relativedelta(days=1)
    latest_valid_budget = None
    for budget in sorted(monthly_budgets):
        monthly_budget_date_str = re.search("([0-9]{8})", budget).group(0)
        monthly_budget_date = datetime.strptime(monthly_budget_date_str, "%Y%m%d")
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

def prepare_report_rows(parsed_budget, parsed_statement): # does not include carry-over yet!
    rows = []
    header_row = ['Category', 'Sub-Category', 'Monthly Allocation (Budget)', 'Carry-Over', 'Spend', 'Remainder']
    rows.append(header_row)
    for category in parsed_statement:
        category_budget = category_total(parsed_budget, category)
        category_spend = category_total(parsed_statement, category)
        category_row = [category, "", "", "", "", ""]
        rows.append(category_row)
        sub_category_dict = parsed_statement[category]
        for sub_category in sub_category_dict:
            # TODO: what about when the sub-category is not in the budget? Could we add it without an associated budget (with a note?)
            sub_category_budget = Money(0, "AUD") if sub_category == "Uncategorised" else parsed_budget[category][sub_category]
            sub_category_spend: Money = parsed_statement[category][sub_category]
            sub_category_row = ["", sub_category, sub_category_budget.amount_as_string(), "", sub_category_spend.amount_as_string(), ""] # TODO: carry-over and remainder
            rows.append(sub_category_row)
        totals_row = ["Total", "", category_budget.amount_as_string(), "", category_spend.amount_as_string(), ""] # TODO: carry-over and remainder
        rows.append(totals_row)
    return rows

def category_total(parsed_dict, category_name): # could be budget or statement -- they have the same structure
    sum = Money(0, "AUD")
    # raises KeyError if the monthly budget does not have a category that is in the statement
    # should be able to handle this when and if categories change over time!
    # ideally old categories should not be removed, only new ones added but that removes some flexibility
    for sub_category in parsed_dict[category_name]:
        sum = sum + parsed_dict[category_name][sub_category]
    return sum

def render_csv(parsed_budget, parsed_statement):
    report_rows = prepare_report_rows(parsed_budget, parsed_statement)
    with open('report.csv', 'w') as file:
        writer = csv.writer(file)
        for row in report_rows:
            writer.writerow(row)

for statement in monthly_expenses:
    parsed_budget = parse_latest_valid_budget(monthly_budgets, statement)
    parsed_statement = parse_monthly_statement(statement)
    # TODO: compute carry-over for each cat/sub-cat
    # TODO: compute remainder for each cat/sub-cat
    render_csv(parsed_budget, parsed_statement)
