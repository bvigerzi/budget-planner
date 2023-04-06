import csv
from datetime import datetime
from stockholm import Money
from mako.template import Template

rows_header: list[str] = ['Category', 'Sub-Category', 'Monthly Allocation (Budget)', 'Prev. Month Remainder',
                          'Avail. Budget', 'Spend', 'Remainder', 'Next Month Avail.']


def prepare_report_rows(parsed_budget: dict, parsed_statement: dict, carry: dict, remainder: dict,
                        remaining_spend: dict, next_month_available: dict) -> list[list[str]]:
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
            sub_category_budget = Money(0, "AUD") if sub_category not in parsed_budget[category] else \
                parsed_budget[category][sub_category]
            sub_category_spend: Money = Money(0, "AUD") if category not in parsed_statement or sub_category not in \
                                                           parsed_statement[category] else parsed_statement[category][
                sub_category]
            sub_category_carry: Money = Money(0, "AUD") if sub_category not in carry[category] else carry[category][
                sub_category]
            sub_category_remainder: Money = Money(0, "AUD") if sub_category not in remainder[category] else \
                remainder[category][sub_category]
            sub_category_remaining_spend: Money = Money(0, "AUD") if sub_category not in remaining_spend[category] else \
                remaining_spend[category][sub_category]
            sub_category_next_month_available: Money = Money(0, "AUD") if sub_category not in next_month_available[
                category] else next_month_available[category][sub_category]
            sub_category_row = ["", sub_category, sub_category_budget.amount_as_string(),
                                sub_category_carry.amount_as_string(), sub_category_remaining_spend.amount_as_string(),
                                sub_category_spend.amount_as_string(), sub_category_remainder.amount_as_string(),
                                sub_category_next_month_available.amount_as_string()]
            rows.append(sub_category_row)
        totals_row = ["Total", "", category_budget.amount_as_string(), category_carry.amount_as_string(),
                      category_remaining_spend.amount_as_string(), category_spend.amount_as_string(),
                      category_remainder.amount_as_string(), category_next_month_available.amount_as_string()]
        rows.append(totals_row)
    complete_totals_row = ["Complete Total", "", complete_budget_total.amount_as_string(),
                           complete_carry_total.amount_as_string(), complete_remaining_spend_total.amount_as_string(),
                           complete_spend_total.amount_as_string(), complete_remainder_total.amount_as_string(),
                           complete_next_month_available_total.amount_as_string()]
    rows.append(complete_totals_row)
    return rows


def category_total(parsed_dict: dict, category_name: str) -> Money:
    total = Money(0, "AUD")
    if category_name not in parsed_dict:
        return total
    for sub_category in parsed_dict[category_name]:
        total = total + parsed_dict[category_name][sub_category]
    return total


def render_csv(parsed_budget: dict, parsed_statement: dict, carry: dict, remainder: dict, remaining_spend: dict,
               next_month_available: dict, statement_date: datetime) -> None:
    report_rows = [rows_header.copy()]
    for row in prepare_report_rows(parsed_budget, parsed_statement, carry, remainder, remaining_spend,
                                   next_month_available):
        report_rows.append(row)
    filename = "report{}.csv".format(statement_date.strftime("%Y%m%d"))
    with open(filename, 'w') as file:
        writer = csv.writer(file)
        for row in report_rows:
            writer.writerow(row)


def render_html(parsed_budget: dict, parsed_statement: dict, carry: dict, remainder: dict, remaining_spend: dict,
                next_month_available: dict, statement_date: datetime) -> None:
    report_rows = prepare_report_rows(parsed_budget, parsed_statement, carry, remainder, remaining_spend,
                                      next_month_available)
    header = "Budget Spend " + statement_date.strftime("%B %Y")
    filename = "report{}.html".format(statement_date.strftime("%Y%m%d"))
    rendered_template = Template(filename='report_template.mako').render(rows=report_rows, header=header,
                                                                         rows_header=rows_header)
    with open(filename, 'w') as file:
        file.write(rendered_template)