import csv
import math

import tiktoken
from more_itertools import divide
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
            row.pop()  # Balance
            output = output + ",".join(row) + "\n"
    return output


def pre_prompt() -> str:
    return """
        categorise this statement
    """  # TODO: improve this


def categorise_statement(gpt_budget: str, gpt_statement: str) -> None:
    pre_prompt_text = pre_prompt()
    budget_tokens = token_encoder.encode(gpt_budget)
    statement_tokens = token_encoder.encode(gpt_statement)
    pre_prompt_tokens = token_encoder.encode(pre_prompt_text)
    budget_tokens_count = len(budget_tokens)
    statement_tokens_count = len(statement_tokens)
    pre_prompt_tokens_count = len(pre_prompt_tokens)
    tokens_for_statement = MAX_INPUT_TOKENS - pre_prompt_tokens_count - budget_tokens_count
    split_statement_by = math.ceil(statement_tokens_count / tokens_for_statement)
    print("divide statement by {}".format(split_statement_by))
    statement_split = list(map(lambda iterator: ''.join(iterator), list(divide(split_statement_by, gpt_statement))))
    print(statement_split)
    # Requirements:
    # 1. need the header for each sub_statement -> extract it from gpt_statement and prepend on each iteration
    # 2. this will change the calculations slightly
    # 3. also need to re-think calculations because we should split exactly on newlines rather than by tokens
    # 4. this is necessary because we cannot have a partial row sent to GPT

    # split gpt_statement by split_statement_by and iterate over the substrings
    # for each substring_statement:
    # prompt = pre_prompt_text + gpt_budget + substring_statement
    # query openai API completions, parse response
    # hold onto response, it will form the partial categorised transactions
    return
