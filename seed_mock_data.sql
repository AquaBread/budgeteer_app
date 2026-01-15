-- ChatGPT generated the mock data for demo purposes

PRAGMA foreign_keys = ON;

BEGIN;

-- -------------------------
-- DEV RESET (delete children first)
-- -------------------------
DELETE FROM transaction_tags;
DELETE FROM tags;

DELETE FROM transactions;
DELETE FROM recurring;
DELETE FROM budgets;
DELETE FROM categories;
DELETE FROM category_groups;
DELETE FROM accounts;
DELETE FROM users;

-- -------------------------
-- User (single-row app)
-- Annual salary: $72,000.00
-- -------------------------
INSERT INTO users (id, name, email, salary_annual_cents, payday_day)
VALUES (1, 'Mock User', 'mock@example.com', 7200000, NULL);

-- -------------------------
-- Accounts
-- NOTE: types must match your schema CHECK constraint
-- -------------------------
INSERT INTO accounts (id, name, type, last4) VALUES
(1, 'Checking',   'debit',      '1234'),
(2, 'Savings',    'debit',      '5678'),
(3, 'Visa Card',  'credit',     '4242'),
(4, 'Brokerage',  'investment', '0001');

-- -------------------------
-- Category Groups
-- IMPORTANT: includes "type" (expense/income) to support group summaries
-- -------------------------
INSERT INTO category_groups (id, name, type, sort_order) VALUES
(1, 'Income',     'income',  1),
(2, 'Housing',    'expense', 2),
(3, 'Utilities',  'expense', 3),
(4, 'Food',       'expense', 4),
(5, 'Transport',  'expense', 5),
(6, 'Health',     'expense', 6),
(7, 'Lifestyle',  'expense', 7),
(8, 'Finance',    'expense', 8);

-- -------------------------
-- Categories
-- -------------------------
INSERT INTO categories (id, name, group_id) VALUES
(1,  'Paycheck',            1),

(10, 'Rent',                2),

(20, 'Electric',            3),
(21, 'Water',               3),
(22, 'Internet',            3),
(23, 'Phone',               3),

(30, 'Groceries',           4),
(31, 'Dining Out',          4),

(40, 'Gas',                 5),
(41, 'Car Maintenance',     5),

(50, 'Gym',                 6),

(60, 'Subscriptions',       7),
(61, 'Entertainment',       7),

(70, 'Insurance',           8),
(71, 'Emergency Fund',      8),
(72, 'Credit Card Payment', 8);

-- -------------------------
-- Budgets for multiple months (so range views look real)
-- -------------------------

-- 2025-10
INSERT INTO budgets (month, category_id, amount_cents) VALUES
('2025-10', 10, 160000),
('2025-10', 20, 12000), ('2025-10', 21, 6000), ('2025-10', 22, 7000), ('2025-10', 23, 8000),
('2025-10', 30, 45000), ('2025-10', 31, 18000),
('2025-10', 40, 14000), ('2025-10', 41, 9000),
('2025-10', 50, 3000),
('2025-10', 60, 2500), ('2025-10', 61, 8000),
('2025-10', 70, 12000),
('2025-10', 71, 40000),
('2025-10', 72, 90000);

-- 2025-11
INSERT INTO budgets (month, category_id, amount_cents) VALUES
('2025-11', 10, 160000),
('2025-11', 20, 12000), ('2025-11', 21, 6000), ('2025-11', 22, 7000), ('2025-11', 23, 8000),
('2025-11', 30, 48000), ('2025-11', 31, 20000),
('2025-11', 40, 15000), ('2025-11', 41, 10000),
('2025-11', 50, 3000),
('2025-11', 60, 2500), ('2025-11', 61, 9000),
('2025-11', 70, 12000),
('2025-11', 71, 50000),
('2025-11', 72, 100000);

-- 2025-12 (your “showcase” month)
INSERT INTO budgets (month, category_id, amount_cents) VALUES
('2025-12', 10, 160000),
('2025-12', 20, 12000), ('2025-12', 21, 6000), ('2025-12', 22, 7000), ('2025-12', 23, 8000),
('2025-12', 30, 50000), ('2025-12', 31, 20000),
('2025-12', 40, 15000), ('2025-12', 41, 10000),
('2025-12', 50, 3000),
('2025-12', 60, 2500), ('2025-12', 61, 8000),
('2025-12', 70, 12000),
('2025-12', 71, 60000),
('2025-12', 72, 120000);

-- -------------------------
-- Tags (color is user-picked)
-- -------------------------
INSERT INTO tags (id, name, color) VALUES
(1, 'H-E-B',   '#2e7d32'),
(2, 'family',  '#6a1b9a'),
(3, 'fun',     '#ef6c00'),
(4, 'job',     '#1565c0'),
(5, 'travel',  '#00838f');

-- -------------------------
-- Recurring (include direction!)
-- day_of_month must be 1..28
-- -------------------------
INSERT INTO recurring (id, name, account_id, category_id, amount_cents, day_of_month, direction, active) VALUES
-- Income
(1, 'Paycheck',         1,  1, 300000,  1, 'in',  1),
(2, 'Paycheck',         1,  1, 300000, 15, 'in',  1),

-- Expenses
(10, 'Rent',            1, 10, 160000,  1, 'out', 1),
(11, 'Electric Bill',   1, 20,  12000, 10, 'out', 1),
(12, 'Water Bill',      1, 21,   6000, 12, 'out', 1),
(13, 'Internet',        1, 22,   7000, 15, 'out', 1),
(14, 'Phone',           1, 23,   8000, 16, 'out', 1),
(15, 'Gym Membership',  1, 50,   3000,  5, 'out', 1),
(16, 'Streaming Bundle',3, 60,   2500,  7, 'out', 1),
(17, 'Car Insurance',   1, 70,  12000, 20, 'out', 1);

-- -------------------------
-- Transactions: multi-month data so trends look real
-- (recurring_id NULL is fine; your app may auto-generate recurring too)
-- -------------------------

-- ===== 2025-10 =====
INSERT INTO transactions (account_id, date, description, amount_cents, category_id, recurring_id) VALUES
(1, '2025-10-01', 'Paycheck', 300000, 1, NULL),
(1, '2025-10-15', 'Paycheck', 300000, 1, NULL),

(1, '2025-10-01', 'Rent', -160000, 10, NULL),
(1, '2025-10-10', 'Electric', -11850, 20, NULL),
(1, '2025-10-12', 'Water', -5800, 21, NULL),
(1, '2025-10-15', 'Internet', -7000, 22, NULL),
(1, '2025-10-16', 'Phone', -8000, 23, NULL),

(3, '2025-10-04', 'HEB Groceries', -12450, 30, NULL),
(3, '2025-10-09', 'Costco Groceries', -18320, 30, NULL),
(3, '2025-10-19', 'Dinner', -4200, 31, NULL),

(3, '2025-10-07', 'Gas', -4025, 40, NULL),
(1, '2025-10-21', 'Oil Change', -6500, 41, NULL),

(1, '2025-10-05', 'Gym', -3000, 50, NULL),
(3, '2025-10-07', 'Streaming Bundle', -2500, 60, NULL),
(3, '2025-10-24', 'Movie', -1560, 61, NULL),

(1, '2025-10-20', 'Car Insurance', -12000, 70, NULL),
(1, '2025-10-25', 'Emergency Fund', -40000, 71, NULL),
(1, '2025-10-26', 'Visa Payment', -90000, 72, NULL);

-- ===== 2025-11 =====
INSERT INTO transactions (account_id, date, description, amount_cents, category_id, recurring_id) VALUES
(1, '2025-11-01', 'Paycheck', 300000, 1, NULL),
(1, '2025-11-15', 'Paycheck', 300000, 1, NULL),

(1, '2025-11-01', 'Rent', -160000, 10, NULL),
(1, '2025-11-10', 'Electric', -12110, 20, NULL),
(1, '2025-11-12', 'Water', -6100, 21, NULL),
(1, '2025-11-15', 'Internet', -7000, 22, NULL),
(1, '2025-11-16', 'Phone', -8000, 23, NULL),

(3, '2025-11-03', 'HEB Groceries', -14520, 30, NULL),
(3, '2025-11-14', 'Walmart Groceries', -9120, 30, NULL),
(3, '2025-11-20', 'Dining Out', -5600, 31, NULL),

(3, '2025-11-07', 'Gas', -3890, 40, NULL),
(1, '2025-11-22', 'Tire Patch', -3500, 41, NULL),

(1, '2025-11-05', 'Gym', -3000, 50, NULL),
(3, '2025-11-07', 'Streaming Bundle', -2500, 60, NULL),
(3, '2025-11-26', 'Bowling', -2800, 61, NULL),

(1, '2025-11-20', 'Car Insurance', -12000, 70, NULL),
(1, '2025-11-25', 'Emergency Fund', -50000, 71, NULL),
(1, '2025-11-27', 'Visa Payment', -100000, 72, NULL);

-- ===== 2025-12 (showcase month) =====
INSERT INTO transactions (account_id, date, description, amount_cents, category_id, recurring_id) VALUES
(3, '2025-12-04', 'HEB Groceries', -8450, 30, NULL),
(3, '2025-12-08', 'Costco Groceries', -6235, 30, NULL),
(3, '2025-12-14', 'Walmart Groceries', -4120, 30, NULL),
(3, '2025-12-22', 'HEB Groceries', -9535, 30, NULL),

(3, '2025-12-06', 'Tacos', -1845, 31, NULL),
(3, '2025-12-11', 'Coffee', -650, 31, NULL),
(3, '2025-12-18', 'Dinner', -4250, 31, NULL),

(3, '2025-12-21', 'Movie', -1560, 61, NULL),
(3, '2025-12-24', 'Bowling', -2800, 61, NULL),

(3, '2025-12-07', 'Gas', -4025, 40, NULL),
(3, '2025-12-17', 'Gas', -3890, 40, NULL),
(1, '2025-12-19', 'Oil Change', -6500, 41, NULL),

(1, '2025-12-25', 'Emergency Fund', -60000, 71, NULL),
(1, '2025-12-26', 'Visa Payment', -120000, 72, NULL);

-- -------------------------
-- Tag assignments (transaction_tags)
-- We attach tags by selecting transaction IDs we just inserted
-- -------------------------

-- H-E-B tag on all HEB groceries (all months)
INSERT INTO transaction_tags (transaction_id, tag_id)
SELECT id, 1
FROM transactions
WHERE description LIKE 'HEB Groceries%';

-- family tag on some entertainment
INSERT INTO transaction_tags (transaction_id, tag_id)
SELECT id, 2
FROM transactions
WHERE description IN ('Movie', 'Bowling');

-- fun tag on dining out + entertainment
INSERT INTO transaction_tags (transaction_id, tag_id)
SELECT id, 3
FROM transactions
WHERE category_id IN (31, 61);

-- job tag on paychecks (optional but fun for analytics)
INSERT INTO transaction_tags (transaction_id, tag_id)
SELECT id, 4
FROM transactions
WHERE category_id = 1;

-- -------------------------
-- Net Worth Snapshot
-- -------------------------

INSERT INTO account_balances (account_id, as_of, balance_cents) VALUES
-- Assets
(1, '2025-12-30', 120000),   -- Checking: $1,200
(2, '2025-12-30', 450000),   -- Savings:  $4,500
(4, '2025-12-30', 800000),   -- Brokerage: $8,000

-- Liabilities
(3, '2025-12-30', 230000);   -- Visa Card: $2,300

COMMIT;
