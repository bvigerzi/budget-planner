import csv
import json
import math

import tiktoken
from budget_parser import find_latest_valid_budget

MAX_TOKENS: int = 2048
MAX_INPUT_TOKENS: int = int(MAX_TOKENS / 2)

# cl100k_base	gpt-4, gpt-3.5-turbo, text-embedding-ada-002
# p50k_base	Codex models, text-davinci-002, text-davinci-003
# r50k_base (or gpt2)	GPT-3 models like davinci
#
# source: https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb

token_encoder = tiktoken.get_encoding("p50k_base")  # TODO: make this customisable so we can switch models easily


# Assumes budget has the following structure:
# Category, Sub-Category, Budget, Ignore
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


# Assumes statement has the following structure:
# Date, Description, Debit, Credit
def gpt_friendly_statement(statement: str) -> str:
    output = ""
    with open(statement) as file:
        reader = csv.reader(file)
        for row in reader:
            row.pop(0)  # Date
            row.pop()  # Balance --> TODO: this was not balance, but actually credit, double check this
            output = output + ",".join(row) + "\n"
    return output


def gpt_friendly_statement_header(statement: str) -> str:
    friendly_statement = gpt_friendly_statement(statement)
    return friendly_statement.split("\n")[0]


def gpt_friendly_statement_no_header(statement: str) -> str:
    friendly_statement = gpt_friendly_statement(statement)
    return "\n".join(friendly_statement.split("\n")[1:])


def pre_budget_prompt() -> str:
    return "The below is categories and sub-categories for a personal budget."


def pre_statement_prompt() -> str:
    return "Using the categories and sub-categories, categorise the transactions that follow. Give the result in csv " \
           "format. Do not provide any other text"


def longest_row_by_token(statement_rows: list[str]) -> int:
    clean_statement_rows = list(filter(lambda row: len(row) != 0, statement_rows))
    tokenized_rows = list(map(lambda row: token_encoder.encode(row), clean_statement_rows))
    token_count_per_row = list(map(lambda row: len(row), tokenized_rows))
    token_count_per_row.sort()
    return token_count_per_row[-1]


def number_rows_per_prompt(statement_rows: list[str], number_tokens_for_statement: int) -> int:
    longest_row = longest_row_by_token(statement_rows)
    # this is a naive solution to take the longest row by token and use it to determine
    # the number of rows we can fit in a prompt
    # it can be optimised using some maths to compute the average size and compute the standard deviation to determine
    # if we will exceed some margin which would be the largest possible prompt we can have
    # as long as we are within the largest possible prompt, then that is the best fit
    # for MVP, we do not need to perform this optimisation
    return math.floor(number_tokens_for_statement / longest_row)


def prepare_prompts(budget: str, gpt_statement_header: str, statement_rows: list[str],
                    rows_per_prompt: int) -> list[str]:
    full_pre_prompt = pre_budget_prompt() + "\n" + budget + "\n" + pre_statement_prompt() + "\n" + gpt_statement_header
    prompts = []
    for x in range(0, len(statement_rows) - rows_per_prompt, rows_per_prompt):
        full_statement_for_prompt = ""
        for y in range(0, rows_per_prompt):
            full_statement_for_prompt = full_statement_for_prompt + statement_rows[x + y] + "\n"
        prompts.append(full_pre_prompt + "\n" + full_statement_for_prompt)
    return prompts


def categorise_statement(monthly_budgets: list[str], statement_file: str) -> None:
    gpt_budget = gpt_friendly_budget(monthly_budgets, statement_file)
    gpt_statement_header = gpt_friendly_statement_header(statement_file)
    gpt_statement_no_header = gpt_friendly_statement_no_header(statement_file)
    pre_budget_prompt_text = pre_budget_prompt()
    pre_statement_prompt_text = pre_statement_prompt()

    budget_tokens = token_encoder.encode(gpt_budget)
    pre_budget_prompt_text_tokens = token_encoder.encode(pre_budget_prompt_text)
    pre_statement_prompt_text_tokens = token_encoder.encode(pre_statement_prompt_text)
    gpt_statement_header_tokens = token_encoder.encode(gpt_statement_header)
    budget_tokens_count = len(budget_tokens)
    pre_budget_prompt_text_tokens_count = len(pre_budget_prompt_text_tokens)
    pre_statement_prompt_text_tokens_count = len(pre_statement_prompt_text_tokens)
    gpt_statement_header_tokens_count = len(gpt_statement_header_tokens)

    tokens_for_statement = MAX_INPUT_TOKENS - pre_budget_prompt_text_tokens_count - budget_tokens_count - \
                           pre_statement_prompt_text_tokens_count - gpt_statement_header_tokens_count

    statement_rows: list[str] = gpt_statement_no_header.split("\n")
    rows_per_prompt = number_rows_per_prompt(statement_rows, tokens_for_statement)
    prompts = prepare_prompts(gpt_budget, gpt_statement_header, statement_rows, rows_per_prompt)
    # TODO:
    # iterate over prompts, calling openai API completions
    # for each completions response, parse it and start re-building the transactions csv
    print(json.dumps(prompts[0]))
    print(len(prompts))
