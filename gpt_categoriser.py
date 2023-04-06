import csv

from budget_parser import find_latest_valid_budget


def gpt_friendly_budget(monthly_budgets: list[str], statement: str) -> str:
    budget = find_latest_valid_budget(monthly_budgets, statement)
    output = ""
    with open(budget) as file:
        reader = csv.reader(file)
        header_row = True
        for row in reader:
            if header_row:
                ignore_index = row.index("Ignore")
                header_row = False
                row.pop()  # Ignore
                row.pop()  # Budget
                output = output + ",".join(row) + "\n"
            else:
                if row[ignore_index] == "1":
                    continue
                else:
                    row.pop()  # Ignore
                    row.pop()  # Budget
                    output = output + ",".join(row) + "\n"
    return output


def gpt_friendly_statement(statement: str) -> str:
    output = ""
    with open(statement) as file:
        reader = csv.reader(file)
        for row in reader:
            row.pop(0)  # Date
            row.pop()  # Balance
            output = output + ",".join(row) + "\n"
    return output

