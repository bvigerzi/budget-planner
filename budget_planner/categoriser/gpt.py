"""GPT-powered transaction categorisation.

Uses the OpenAI API to automatically categorise bank transactions
against budget categories and sub-categories.
"""

import csv
import functools
import logging
import math
import statistics
from itertools import chain
from pathlib import Path

import openai
import tiktoken

from budget_planner.config import (
    EXPENSES_STATEMENT_POST_CATEGORISE_DIR,
    EXPENSES_STATEMENT_PRE_CATEGORISE_DIR,
    GPT_MODEL,
    MAX_INPUT_TOKENS,
    TOKEN_ENCODING,
)
from budget_planner.parsing.budget import find_latest_valid_budget

logger = logging.getLogger(__name__)

token_encoder = tiktoken.get_encoding(TOKEN_ENCODING)

PRE_BUDGET_PROMPT = (
    "The below is categories and sub-categories for a personal budget.\n"
)

PRE_STATEMENT_PROMPT = (
    "Using the categories and sub-categories, categorise the transactions that "
    "follow. Give the result in csv format as: "
    "Description,Debit,Credit,Category,Sub-Category. Do not provide any other "
    "text. Output the transactions in the order received.\n"
)


def gpt_friendly_budget(monthly_budgets: list[str], statement: str) -> str:
    """Format budget for GPT consumption, removing Budget and Ignore columns."""
    budget = find_latest_valid_budget(monthly_budgets, statement)
    return gpt_friendly_budget_parse(budget)


@functools.lru_cache()
def gpt_friendly_budget_parse(budget: str) -> str:
    """Parse budget CSV and format for GPT, cached for repeated calls."""
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
                output += ",".join(row) + "\n"
            else:
                if row[ignore_index] == "1":
                    continue
                row.pop()  # Ignore
                row.pop()  # Budget
                output += ",".join(row) + "\n"
    return output


@functools.lru_cache()
def gpt_friendly_statement(statement: str) -> str:
    """Format expense statement for GPT, removing Date and Balance columns."""
    output = ""
    with open(statement) as file:
        reader = csv.reader(file)
        for row in reader:
            row.pop(0)  # Date
            row.pop()  # Balance
            output += ",".join(row) + "\n"
    return output


def gpt_friendly_statement_header(statement: str) -> str:
    """Extract CSV header from GPT-formatted statement."""
    friendly_statement = gpt_friendly_statement(statement)
    return friendly_statement.split("\n")[0]


def gpt_friendly_statement_no_header(statement: str) -> str:
    """Return GPT-formatted statement without header row."""
    friendly_statement = gpt_friendly_statement(statement)
    return "\n".join(friendly_statement.split("\n")[1:])


def longest_row_by_token(statement_rows: list[str]) -> int:
    """Find the row with the most tokens."""
    token_count_per_row = tokens_by_row(statement_rows)
    token_count_per_row.sort()
    return token_count_per_row[-1]


def tokens_by_row(statement_rows: list[str]) -> list[int]:
    """Calculate token count per row, excluding empty rows."""
    clean_rows = [row for row in statement_rows if len(row) != 0]
    return [len(token_encoder.encode(row)) for row in clean_rows]


def number_rows_per_prompt(
    statement_rows: list[str], number_tokens_for_statement: int
) -> int:
    """Calculate optimal number of rows per API request based on token limits.

    Uses median token count as rows are approximately the same length.
    """
    tokens_rows = tokens_by_row(statement_rows)
    median_row_token_count = statistics.median(tokens_rows)
    return math.floor(number_tokens_for_statement / median_row_token_count)


def prepare_prompts(
    budget: str,
    gpt_statement_header: str,
    statement_rows: list[str],
    rows_per_prompt: int,
) -> list[str]:
    """Batch statement rows into multiple prompts respecting token limits."""
    full_pre_prompt = (
        f"{PRE_BUDGET_PROMPT}\n{budget}\n{PRE_STATEMENT_PROMPT}\n"
        f"{gpt_statement_header}"
    )
    prompts = []
    copy_statement_rows = statement_rows.copy()
    for _ in range(0, len(statement_rows) - rows_per_prompt, rows_per_prompt):
        full_statement_for_prompt = ""
        for _ in range(rows_per_prompt):
            full_statement_for_prompt += copy_statement_rows.pop(0) + "\n"
        prompts.append(f"{full_pre_prompt}\n{full_statement_for_prompt}")
    final_statement = ""
    for _ in range(len(copy_statement_rows)):
        final_statement += copy_statement_rows.pop(0) + "\n"
    if final_statement:
        prompts.append(f"{full_pre_prompt}\n{final_statement}")
    return prompts


def rebuild_categorised_statement(
    categorised_rows: list[list[str]], statement_file: str
) -> None:
    """Write categorised results back to CSV with Category and Sub-Category columns."""
    rebuilt_csv = []
    with open(statement_file) as file:
        reader = csv.reader(file)
        row_count = 0
        for row in reader:
            if row_count == 0:
                row.extend(["Category", "Sub-Category"])
            else:
                categorised_row: list[str] = categorised_rows[row_count - 1]
                category_columns = categorised_row[-2:]
                row.extend(category_columns)
            rebuilt_csv.append(row)
            row_count += 1
        logger.info("CSV rows: %d", row_count)

    logger.debug("Rebuilt CSV: %s", rebuilt_csv)
    file_name = Path(statement_file).name
    categorised_file_path = EXPENSES_STATEMENT_POST_CATEGORISE_DIR / file_name
    with open(categorised_file_path, "w") as file:
        writer = csv.writer(file)
        writer.writerows(rebuilt_csv)


def categorise_statement(
    monthly_budgets: list[str], statement_file: str
) -> None:
    """Categorise all transactions in a statement via GPT."""
    gpt_budget = gpt_friendly_budget(monthly_budgets, statement_file)
    gpt_header = gpt_friendly_statement_header(statement_file)
    gpt_no_header = gpt_friendly_statement_no_header(statement_file)

    budget_tokens_count = len(token_encoder.encode(gpt_budget))
    pre_budget_tokens_count = len(token_encoder.encode(PRE_BUDGET_PROMPT))
    pre_statement_tokens_count = len(token_encoder.encode(PRE_STATEMENT_PROMPT))
    header_tokens_count = len(token_encoder.encode(gpt_header))

    tokens_for_statement = (
        MAX_INPUT_TOKENS
        - pre_budget_tokens_count
        - budget_tokens_count
        - pre_statement_tokens_count
        - header_tokens_count
    )

    statement_rows: list[str] = gpt_no_header.split("\n")
    rows_per = number_rows_per_prompt(statement_rows, tokens_for_statement)
    prompts = prepare_prompts(gpt_budget, gpt_header, statement_rows, rows_per)

    all_categorised_rows = list(openai_completions_generator(prompts))
    logger.debug("All categorised rows: %s", all_categorised_rows)
    all_rows_flattened = list(chain.from_iterable(all_categorised_rows))
    logger.info("Total categorised rows: %d", len(all_rows_flattened))

    rebuild_categorised_statement(all_rows_flattened, statement_file)


def openai_completions_generator(prompts: list[str]) -> list[list[str]]:
    """Call OpenAI Chat Completions API for each prompt and parse responses."""
    client = openai.OpenAI()
    for prompt in prompts:
        logger.debug("Sending prompt to OpenAI:\n%s", prompt)
        response = client.chat.completions.create(
            model=GPT_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=MAX_INPUT_TOKENS,
        )
        response_text = response.choices[0].message.content
        logger.debug("OpenAI response: %s", response_text)
        yield [row.split(",") for row in response_text.split("\n")]
