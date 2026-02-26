"""Configuration constants for the budget planner."""

from pathlib import Path

MONTHLY_BUDGET_CSV_PATTERN = "monthly_budget[0-9]*.csv"
EXPENSES_STATEMENT_CSV_PATTERN = "SpendAccount[a-zA-Z0-9-]*[0-9]*-[0-9]*.csv"

MONTHLY_BUDGET_DIR = Path(".")
EXPENSES_STATEMENT_PRE_CATEGORISE_DIR = Path("pre-categorise")
EXPENSES_STATEMENT_POST_CATEGORISE_DIR = Path("post-categorise")

# GPT Configuration
MAX_TOKENS = 2048
MAX_INPUT_TOKENS = MAX_TOKENS // 2
GPT_MODEL = "gpt-3.5-turbo"
TOKEN_ENCODING = "cl100k_base"
