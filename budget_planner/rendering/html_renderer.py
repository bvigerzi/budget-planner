"""HTML report renderer using Mako templates."""

from datetime import datetime
from pathlib import Path

from mako.template import Template

from budget_planner.rendering.common import REPORT_HEADER, prepare_report_rows

TEMPLATE_PATH = Path(__file__).parent.parent / "templates" / "report.mako"


def render_html(
    parsed_budget: dict,
    parsed_statement: dict,
    carry: dict,
    remainder: dict,
    remaining_spend: dict,
    next_month_available: dict,
    statement_date: datetime,
) -> None:
    """Generate an HTML report using the Mako template."""
    report_rows = prepare_report_rows(
        parsed_budget,
        parsed_statement,
        carry,
        remainder,
        remaining_spend,
        next_month_available,
    )
    header = f"Budget Spend {statement_date.strftime('%B %Y')}"
    filename = f"report{statement_date.strftime('%Y%m%d')}.html"
    rendered_template = Template(filename=str(TEMPLATE_PATH)).render(
        rows=report_rows, header=header, rows_header=REPORT_HEADER
    )
    with open(filename, "w") as file:
        file.write(rendered_template)
