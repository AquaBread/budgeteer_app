PRAGMA foreign_keys = ON;

-- Single-user table
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  name TEXT,
  email TEXT,
  salary_annual_cents INTEGER NOT NULL DEFAULT 0,
  payday_day INTEGER,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

-- Financial accounts
CREATE TABLE IF NOT EXISTS accounts (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  type TEXT NOT NULL CHECK (type IN ('debit','credit','investment')),
  last4 TEXT
);

-- Net worth
CREATE TABLE IF NOT EXISTS account_balances (
  id INTEGER PRIMARY KEY,
  account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  as_of TEXT NOT NULL, -- 'YYYY-MM-DD'
  balance_cents INTEGER NOT NULL CHECK (balance_cents >= 0),
  UNIQUE(account_id, as_of)
);

-- Categories and category groups
CREATE TABLE IF NOT EXISTS category_groups (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  sort_order INTEGER,
  type TEXT NOT NULL DEFAULT 'expense' CHECK (type IN ('expense','income'))
);

CREATE TABLE IF NOT EXISTS categories (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  group_id INTEGER REFERENCES category_groups(id) ON DELETE SET NULL
);

-- Budgets: per category per month
CREATE TABLE IF NOT EXISTS budgets (
  month TEXT NOT NULL,          -- 'YYYY-MM'
  category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  amount_cents INTEGER NOT NULL
);

-- Recurring rules
CREATE TABLE IF NOT EXISTS recurring (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL,
  account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
  amount_cents INTEGER NOT NULL,
  day_of_month INTEGER NOT NULL CHECK (day_of_month BETWEEN 1 AND 28),
  direction TEXT NOT NULL DEFAULT 'out' CHECK (direction IN ('in','out')),
  active INTEGER NOT NULL DEFAULT 1
);

-- Tags
CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  color TEXT NOT NULL DEFAULT '#64748b'
);

-- Transactions
CREATE TABLE IF NOT EXISTS transactions (
  id INTEGER PRIMARY KEY,
  account_id INTEGER NOT NULL REFERENCES accounts(id) ON DELETE CASCADE,
  date TEXT NOT NULL,           -- 'YYYY-MM-DD'
  description TEXT,
  amount_cents INTEGER NOT NULL,
  category_id INTEGER REFERENCES categories(id) ON DELETE SET NULL,
  recurring_id INTEGER REFERENCES recurring(id) ON DELETE SET NULL,
  created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS transaction_tags (
  transaction_id INTEGER NOT NULL REFERENCES transactions(id) ON DELETE CASCADE,
  tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY (transaction_id, tag_id)
);

-- Indexes for dashboard and filtering performance
CREATE INDEX IF NOT EXISTS idx_txn_date ON transactions(date);
CREATE INDEX IF NOT EXISTS idx_txn_cat ON transactions(category_id);

CREATE UNIQUE INDEX IF NOT EXISTS idx_budget_unique ON budgets(month, category_id);
