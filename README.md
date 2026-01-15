# Budgeteer — Personal Budgeting + Net Worth Dashboard
#### Video Demo: (https://youtu.be/DdmmRbTiZu0)
#### Description:
Budgeteer is a lightweight personal finance web app built with Python (Flask), SQLite, Jinja templates, and Chart.js. The goal is to provide a clean “daily-driver” budgeting workflow: track transactions, set monthly budgets, auto-post recurring items (including income), summarize spending in a dashboard, and track net worth over time using manual account balance snapshots. The app is intentionally simple to deploy and run locally, while still modeling money correctly (income vs. expenses vs. balances) and presenting clear, actionable summaries.

At a high level, Budgeteer supports:
- **Transactions** with required category assignment, supporting both **expenses (−)** and **income (+)**.
- **Monthly budgets** per category, with optional **rollover suggestions** from the previous month.
- **Recurring items** (expenses and income) that automatically post into the current month as transactions.
- **Category groups** (e.g., Housing, Food, Utilities) with explicit **group types** (`expense` vs `income`) to avoid mixing budget/spend logic with income reporting.
- A **Dashboard** that includes totals (income, budget, spent MTD), pro-rata comparisons, daily cap guidance, savings estimates, and charts.
- **Accounts** (debit/credit/investment) plus **Net Worth tracking** using daily balance snapshots, including a net worth chart over time.

## How the app models money (design choices)

**1) All money is stored as integer cents.**
Amounts are stored as `*_cents` integers in the database (e.g., `amount_cents`, `balance_cents`) to avoid floating point rounding errors. Inputs are accepted in dollars (e.g., 12.34), converted to cents, and formatted back into dollars for display.

**2) Transactions use a sign convention for clarity.**
Expenses are stored as negative values; income/refunds are stored as positive values. This makes monthly totals and charts easier and safer to compute using SQL aggregation.

**3) Income is not treated like an expense category.**
Income categories can exist for classification, but “Income” is not budgeted or “spent.” Category groups have a `type` field (`expense` or `income`) so that:
- Expense groups show **Budget / Spent / Remaining**
- Income groups show **Income** only
This avoids misleading “budget vs spent” comparisons for income.

**4) Net worth is snapshot-based (stock), not derived from transactions (flow).**
The app tracks net worth using manual account balance snapshots instead of trying to reconstruct account balances from transactions. This keeps the accounting model simple and accurate without implementing bank reconciliation logic.

## Features and pages

### Dashboard (`/`)
The dashboard summarizes the current month:
- Monthly income (based on posted income transactions)
- Total budget for the month
- Spending month-to-date (expenses only)
- Pro-rata target vs actual spending
- Daily spending cap for the remainder of the month
- Projected savings for the month
- Charts for **Budget vs Spent by Category** and **Budget vs Spent by Expense Group**
- A group-level table that correctly separates expense groups from income groups

### Transactions (`/transactions`)
Users can add a transaction with:
- date, account, direction (expense vs income), amount, category, description
Categories are required to prevent “invisible” spending/income from falling out of analytics and charts. Transactions can be deleted from the list view.

### Budgets (`/budgets`)
Users assign a monthly budget to each category (stored by month key `YYYY-MM`). Budgets include a rollover helper that can suggest next month’s budget based on the previous month’s budget and actual spending.

### Recurring (`/recurring`)
Recurring items can be created for either direction:
- expense (−) or income (+)
Each recurring item includes name, account, category, amount, day of month, and an active toggle. The app automatically creates the matching transaction(s) for the month when appropriate so recurring items show up in the dashboard and transaction lists.

### Category Groups (`/category-groups`)
Users can create and manage category groups, choose a group type (`expense` or `income`), and assign categories to groups. Group type is central to keeping the dashboard summaries intuitive (income groups are summarized as income; expense groups are summarized with budgets/spending).

### Categories (`/categories`)
Categories can be created and deleted. Deletion is protected if a category is in use by required relationships (such as recurring items), preventing accidental data corruption.

### Accounts (`/accounts`)
Accounts support CRUD actions and track a `type`:
- `debit` (checking/savings)
- `credit` (credit card liabilities)
- `investment` (brokerage/retirement assets)

### Net Worth (`/net-worth`)
The net worth page lets users enter balances (positive numbers) per account for a selected “as of” date. The app computes:
- Total assets (debit + investment)
- Total liabilities (credit)
- Net worth (assets − liabilities)
It also graphs net worth over time using saved snapshot history.

## Project files

- `app.py`: Main Flask application. Defines routes for dashboard, transactions, budgets, recurring items, categories, category groups, accounts, and net worth. Contains the SQL queries that compute summaries and chart datasets.
- `db.py`: Database helper(s) used to open a SQLite connection with row access by column name.
- `schema.sql`: SQLite schema defining tables for users, accounts, categories, budgets, transactions, recurring items, category groups, and account balance snapshots for net worth.
- `calculations.py`: Helper functions used for monthly keys and budgeting math (pro-rata targets and daily cap).
- `templates/layout.html`: Base layout template with navigation and global styling hooks.
- `templates/index.html`: Dashboard view with summary cards, charts, and group/category breakdowns.
- `templates/transactions.html`: Transaction entry form and transaction list view with delete actions.
- `templates/budgets.html`: Monthly budgets editor with rollover/suggestion support.
- `templates/recurring.html`: Recurring items creation + list (enable/disable/delete).
- `templates/accounts.html`: Accounts CRUD UI (create/update/delete).
- `templates/settings.html`: User settings (e.g., salary field used earlier in the project).
- `templates/categories.html`: Category creation and deletion.
- `templates/category_groups.html`: Group management + category-to-group assignment UI.
- `templates/net_worth.html`: Net worth snapshot entry + summary + chart.
- `static/styles.css`: App styling.
- `static/chart.js` (or CDN Chart.js): Used by the dashboard and net worth pages to render charts.

## Running the project (local)
1. Install dependencies:
   - `pip install -r requirements.txt`
2. Start the app:
   - `flask run` (or `python app.py`)
3. Open in browser:
   - `http://127.0.0.1:5000/`

## Future improvements
Some enhancements I considered (or may add later) include PDF exports, CSV import, transfers between accounts, and more advanced net worth analytics. I prioritized correctness of financial modeling (income vs expense vs balances) and a clean dashboard experience first, since those are the foundations of a reliable personal finance tool.

## Use of AI Tools
This project was developed primarily by me. I used ChatGPT as a supplemental tool
for debugging, architectural discussion, and design validation, particularly when
working with complex SQL queries, financial logic, and edge cases.

All core logic, structure, and implementation decisions were made by me, and I
verified, adapted, and integrated any suggestions manually.
