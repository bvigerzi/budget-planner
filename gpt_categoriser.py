import csv
import json
import math
import functools
import statistics

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
    return gpt_friendly_budget_parse(budget)


@functools.lru_cache()
def gpt_friendly_budget_parse(budget: str) -> str:
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
@functools.lru_cache()
def gpt_friendly_statement(statement: str) -> str:
    output = ""
    with open(statement) as file:
        reader = csv.reader(file)
        for row in reader:
            row.pop(0)  # Date
            row.pop()  # Balance
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
    token_count_per_row = tokens_by_row(statement_rows)
    token_count_per_row.sort()
    return token_count_per_row[-1]


def tokens_by_row(statement_rows: list[str]) -> list[int]:
    clean_statement_rows = list(filter(lambda row: len(row) != 0, statement_rows))
    tokenized_rows = list(map(lambda row: token_encoder.encode(row), clean_statement_rows))
    token_count_per_row = list(map(lambda row: len(row), tokenized_rows))
    return token_count_per_row


def number_rows_per_prompt(statement_rows: list[str], number_tokens_for_statement: int) -> int:
    tokens_rows = tokens_by_row(statement_rows)
    median_row_token_count = statistics.median(tokens_rows)
    # this is a pretty good solution, because the standard deviation is likely to be quite low
    # (i.e. rows are approximately the same length)
    # it could be further optimised to make use of the tokens per request
    # this is because the pre-prompt and budget is sent in each request, which burns tokens unnecessarily
    # also, because we are sending that each time, and we only get back the transactions, the actual token count
    # per request could be something like, REQUEST_TOKENS = PRE_TRANSACTIONS_TOKENS + TRANSACTIONS_TOKENS
    # RESPONSE_TOKENS = TRANSACTIONS_TOKENS + some_buffer (to allow for categories and sub-categories)
    # MAX_TOKENS = REQUEST_TOKENS + RESPONSE_TOKENS
    # or, MAX_TOKENS = PRE_TRANSACTIONS_TOKENS + 2*TRANSACTIONS_TOKENS + some_buffer
    return math.floor(number_tokens_for_statement / median_row_token_count)


def prepare_prompts(budget: str, gpt_statement_header: str, statement_rows: list[str],
                    rows_per_prompt: int) -> list[str]:
    full_pre_prompt = pre_budget_prompt() + "\n" + budget + "\n" + pre_statement_prompt() + "\n" + gpt_statement_header
    prompts = []
    copy_statement_rows = statement_rows.copy()
    for _ in range(0, len(statement_rows) - rows_per_prompt, rows_per_prompt):
        full_statement_for_prompt = ""
        for _ in range(0, rows_per_prompt):
            full_statement_for_prompt = full_statement_for_prompt + copy_statement_rows.pop(0) + "\n"
        prompts.append(full_pre_prompt + "\n" + full_statement_for_prompt)
    final_statement = ""
    for _ in range(0, len(copy_statement_rows)):
        final_statement = final_statement + copy_statement_rows.pop(0) + "\n"
    if final_statement != "":
        prompts.append(full_pre_prompt + "\n" + final_statement)
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
    # ideally, just collect the completions responses in a list and re-build the transactions csv piece by piece
    # (i.e. iterate over the original transactions file, and for each iteration grab a list item returned from
    # completions API
    # attach the categories and subcategories onto the transaction csv row and get ready to print it out
    # to a new CSV file at the end

    # for development, before calling the API, just work with a sample response to see if we can do the work after
    # getting the API response
    print(len(prompts))
    print(json.dumps(prompts[0]))
    print("tokens:" + str(len(token_encoder.encode(prompts[0]))))
    print(json.dumps(prompts[1]))
    print("tokens:" + str(len(token_encoder.encode(prompts[1]))))
