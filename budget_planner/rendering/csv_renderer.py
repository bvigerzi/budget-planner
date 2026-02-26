"""CSV report renderer."""

import csv
from datetime import datetime

from budget_planner.rendering.common import REPORT_HEADER, prepare_report_rows


def render_csv(
    parsed_budget: dict,
    parsed_statement: dict,
    carry: dict,
    remainder: dict,
    remaining_spend: dict,
    next_month_available: dict,
    statement_date: datetime,
) -> None:
    """Generate a CSV report file."""
    report_rows = [REPORT_HEADER.copy()]
    report_rows.extend(
        prepare_report_rows(
            parsed_budget,
            parsed_statement,
            carry,
            remainder,
            remaining_spend,
            next_month_available,
        )
    )
    filename = f"report{statement_date.strftime('%Y%m%d')}.csv"
    with open(filename, "w") as file:
        writer = csv.writer(file)
        writer.writerows(report_rows)
