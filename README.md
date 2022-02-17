# Automated Tools for Planning a Budget

## Background

Effective budget planning involves allocating inflows of cash over a period of time to outflows such as regular bills, expenses and investments while ensuring that you are not spending more than you have. A method to this approach is to estimate how much you would spend in each category while keeping note of how much cash you have left in your budget.

As we know expenses usually come in at different intervals. For example, a rent payment may occur like clockwork each month while expenditure like food occur more frequently and fluctuate in value. An approach to tackling this irregularity in expenses is by specifying the budgeted amount and time period (how often we would see this budgeted expense "come out"). Then, inflows of cash can also be specified by amount earned and over what time period. Finally, total expenditure can be calculated independent of the time period and full allocation of cash influx can be determined.

An important thing to note is that some months may have a negative cash flow (spending more than you earn) but this can be made up by having a positive cash flow (spending less than you earn) in either previous months (borrowing from the past) or future months (borrowing from the future). The goal is to ensure that over a certain period of time you are not continuously going over budget.

The intention of this project is to keep track of cash flows over a time period and have full visibility of where cash is flowing. It is also intended to keep track of the budget and determine if it needs to be adjusted by drawing attention to over and under expenditure.

## Approach

First, the budget is determined using [moneysmart's budget planner](https://moneysmart.gov.au/budgeting/budget-planner) (recommendation: use the excel spreadsheet for ease of use). Here, the inflows and outflows are specified along with their specific time periods. Then we can determine an appropriate time period to review if the budget is on track or if we are overspending / underspending. In this case an expenses statement of one month (e.g. bank statement or credit card statement) can be enhanced (manually for now but could be automated using classification ML) by specifying which budget category a particular purchase is associated with.

### Statement Structure

In our case the monthly expenses statement is in CSV format and has the following structure;

```
Date,Description,Debit,Credit,Balance,Category,Sub-Category
```

The `Category` and `Sub-Category` columns should be manually added and are filled in by categorising each expense on a monthly basis. Since it is a monthly statement a single date row can be used to determine the expense month during automated processing.

### Automated Processing

Firstly, we need to take the budget from the planner above and determine the expense budget per month using the view tool in the planner. This data can be fed into the processor in the following format:

**monthly_budgetYYYYMMDD.csv** (dated to keep track of budget changes -- tool should take latest budget)

```
category,sub-category,budget
```

The tool should then be run monthly to generate a report (format TBD) on monthly expenditure. The intention is that it will use the allocation for each category and subtract the debits from the expenses statement. At the end the remaining budget will either be negative, positive or exactly zero. The remainder should "carry" to the next month. A positive value will be added to the monthly allocation for the particular category, while a negative value will be subtracted from the allocation. For example, consider a category called `Groceries` with the sub-category `Groceries`. If the monthly budget is $500 and the total expenditure for the category in January is $650 then the remainder is -$150. Now in February the same categorisation had an expense of $450. Taking the monthly budget of $500 we subtract the $150 from January and then subtract the $450 from February to arrive at -$100. This -$100 will carry to the month of March.

#### Spending Habit Flags

The tool should be able to determine if you are consistently overspending in a category (e.g. negative for 3 months or more) and flag it in future reports for evaluation. Constant and significant underspending should also be flagged by the system to review manually. Putting your money to work effectively is just as important as ensuring you are not overspending.

### Irregular Expenses

Yearly expenses (e.g. insurance charged annually, other annual subscriptions) will make a monthly budget look bad. For 11 months out of 12 you will be over-budget in these annual expense categories. There should be a system in place to ensure false positive flags are not generated for irregular fixed expenses.
 