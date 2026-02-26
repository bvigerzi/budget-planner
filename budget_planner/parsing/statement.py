"""Statement file parsing utilities."""

import csv
import re
from datetime import datetime

from dateutil.relativedelta import relativedelta
from stockholm import Money


def parse_monthly_statement(statement: str) -> dict:
    """Parse a monthly expense statement CSV into a nested category dictionary.

    Returns a dict of {category: {sub_category: Money}} with aggregated amounts.
    """
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
                missing_debit = normalised_debit in ("", "-")
                missing_credit = normalised_credit in ("", "-")
                category_exists = row[category_index] not in ("", "-")
                sub_category_exists = row[sub_category_index] not in ("", "-")
                credit_with_category = (
                    not missing_credit and category_exists and sub_category_exists
                )

                if missing_debit and not credit_with_category:
                    continue

                parsed_debit_amount = (
                    None if missing_debit else Money(normalised_debit, "AUD")
                )
                parsed_credit_amount = (
                    None if missing_credit else -Money(normalised_credit, "AUD")
                )
                applied_amount = (
                    parsed_debit_amount
                    if parsed_debit_amount is not None
                    else parsed_credit_amount
                )
                category_name = (
                    "Uncategorised" if not category_exists else row[category_index]
                )
                sub_category_name = (
                    "Uncategorised"
                    if not sub_category_exists
                    else row[sub_category_index]
                )

                if category_name not in parsed_statement:
                    parsed_statement[category_name] = {}
                    parsed_statement[category_name][sub_category_name] = applied_amount
                elif sub_category_name not in parsed_statement[category_name]:
                    parsed_statement[category_name][sub_category_name] = applied_amount
                else:
                    current_total: Money = parsed_statement[category_name][
                        sub_category_name
                    ]
                    parsed_statement[category_name][sub_category_name] = (
                        current_total + applied_amount
                    )

    return parsed_statement


def parse_monthly_statement_date(statement: str) -> datetime:
    """Extract date from statement filename (YYYY-MM format).

    Returns the last day of the statement month.
    """
    statement_date_str = re.search(r"(\d{4}-\d{2})", statement).group(0)
    return (
        datetime.strptime(statement_date_str, "%Y-%m")
        + relativedelta(months=1)
        - relativedelta(days=1)
    )
