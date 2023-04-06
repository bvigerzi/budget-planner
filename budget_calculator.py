from stockholm import Money


def compute_remainder(carry: dict, parsed_budget: dict, parsed_statement: dict) -> dict:
    remainder = {}
    for category in parsed_budget:
        remainder[category] = {}
        for sub_category in parsed_budget[category]:
            sub_category_budget = parsed_budget[category][sub_category]
            sub_category_spend = Money(0, "AUD") if category not in parsed_statement or sub_category not in \
                                                    parsed_statement[category] else parsed_statement[category][
                sub_category]
            sub_category_carry = carry[category][sub_category]
            remainder[category][sub_category] = sub_category_budget - sub_category_spend + sub_category_carry
    return remainder


def compute_remaining_spend(carry: dict, parsed_budget: dict) -> dict:
    remaining_spend = {}
    for category in parsed_budget:
        remaining_spend[category] = {}
        for sub_category in parsed_budget[category]:
            sub_category_budget = parsed_budget[category][sub_category]
            sub_category_carry = carry[category][sub_category]
            remaining_spend[category][sub_category] = sub_category_budget + sub_category_carry
    return remaining_spend


def compute_next_month_available_budget(remainder: dict, parsed_budget: dict) -> dict:
    next_month_budget = {}
    for category in parsed_budget:
        next_month_budget[category] = {}
        for sub_category in parsed_budget[category]:
            sub_category_budget = parsed_budget[category][sub_category]
            sub_category_remainder = remainder[category][sub_category]
            next_month_budget[category][sub_category] = sub_category_budget + sub_category_remainder
    return next_month_budget


def compute_carry(prev_remainder: dict, parsed_budget: dict) -> dict:
    if prev_remainder is None:
        return init_carry(parsed_budget)
    carry = {}
    for category in prev_remainder:
        carry[category] = {}
        for sub_category in prev_remainder[category]:
            carry[category][sub_category] = prev_remainder[category][sub_category]
    return carry


def init_carry(parsed_budget: dict) -> dict:
    carry = {}
    for category in parsed_budget:
        carry[category] = {}
        for sub_category in parsed_budget[category]:
            carry[category][sub_category] = Money(0, "AUD")
    return carry
