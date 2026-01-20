from calculations import month_key, pro_rata, daily_cap
from calendar import monthrange
from datetime import date
from db import get_db
from flask import Flask, render_template, request, redirect, url_for, flash
import re
import sqlite3

app = Flask(__name__)
app.secret_key = "dev"

# DB bootstrapping
with get_db() as db:
    db.executescript(open("schema.sql").read())
    db.execute("INSERT OR IGNORE INTO users(id, name) VALUES (1, 'You')")

    # Seed starter categories if DB is empty
    cur = db.execute("SELECT COUNT(*) c FROM categories")
    if cur.fetchone()["c"] == 0:
        db.executemany(
            "INSERT INTO categories(name) VALUES (?)",
            [
                (x,)
                for x in [
                    "Rent/Mortgage",
                    "Utilities",
                    "Groceries",
                    "Dining",
                    "Transport",
                    "Health",
                    "Subscriptions",
                    "Entertainment",
                    "Misc",
                ]
            ],
        )

    # Seed one debit account if none
    cur = db.execute("SELECT COUNT(*) c FROM accounts")
    if cur.fetchone()["c"] == 0:
        db.execute("INSERT INTO accounts(name, type) VALUES ('My Debit', 'debit')")

# Ensures recurring expenses up to today exists as transactions for this month.
# Uses calendar.monthrange to tie day_of_month to last day of month.
# Python docs: https://docs.python.org/3/library/calendar.html#calendar.monthrange
def apply_recurring_for_month(db, today: date) -> None:
    year, month = today.year, today.month
    days_in_month = monthrange(year, month)[1]

    recs = db.execute(
        """
        SELECT id, name, account_id, category_id, amount_cents, day_of_month, direction
        FROM recurring
        WHERE active = 1
        """
    ).fetchall()

    for r in recs:
        # Tie day_of_month to last day of month
        d = min(r["day_of_month"], days_in_month)

        # Only create if that day is <= today
        if d > today.day:
            continue

        dt_str = f"{year:04d}-{month:02d}-{d:02d}"

        # Check if we already created a transaction for this recurring item on that date
        exists = db.execute(
            """
            SELECT 1 FROM transactions
            WHERE recurring_id = ? AND date = ?
            """,
            (r["id"], dt_str),
        ).fetchone()

        if exists:
            continue

        # Convert stored amount into signed transaction amount
        direction = r["direction"]
        amt = abs(r["amount_cents"])
        if direction == "in":
            amt = amt
        else:
            amt = -amt

        db.execute(
            """
            INSERT INTO transactions (account_id, date, description, amount_cents, category_id, recurring_id)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (
                r["account_id"],
                dt_str,
                r["name"],
                amt,
                r["category_id"],
                r["id"],
            ),
        )

# Date helpers for multi-month dashboards
def add_months(y, m, delta):
    m2 = m + delta
    y2 = y + (m2 - 1) // 12
    m2 = (m2 - 1) % 12 + 1
    return y2, m2

def month_key_from_ym(y, m):
    return f"{y:04d}-{m:02d}"

def prev_month_key(mkey: str) -> str:
    """
    Given 'YYYY-MM' return the previous month
    """
    year, mon = map(int, mkey.split('-'))
    if mon == 1:
        return f"{year - 1:04d}-12"
    else:
        return f"{year:04d}-{mon - 1:02d}"

def month_seq(start_mkey: str, end_mkey: str):
    '''
    Inclusive list of YYYY-MM between start and end
    '''
    y1, m1 = map(int, start_mkey.split("-"))
    y2, m2 = map(int, end_mkey.split("-"))

    out = []
    y, m = y1, m1
    while (y < y2) or (y == y2 and m <= m2):
        out.append(f"{y:04d}-{m:02d}")
        y, m = add_months(y, m, 1)

    return out

# Dashboard page
@app.route("/")
def index():
    today = date.today()
    mkey = month_key(today)

    # Range selector for multi-month dashboard
    range_key = request.args.get("range", "1")  # "1", "3", "6", "ytd"
    year, month = today.year, today.month

    # Compute range start month key
    if range_key == "3":
        start_y, start_m = add_months(year, month, -2)
        start_mkey = month_key_from_ym(start_y, start_m)
    elif range_key == "6":
        start_y, start_m = add_months(year, month, -5)
        start_mkey = month_key_from_ym(start_y, start_m)
    elif range_key == "ytd":
        start_mkey = f"{year:04d}-01"
    else:
        start_mkey = mkey

    months = month_seq(start_mkey, mkey)

    # User salary
    with get_db() as db:
        user = db.execute("SELECT salary_annual_cents FROM users WHERE id=1").fetchone()
        salary_annual = user["salary_annual_cents"] or 0
        salary_est = salary_annual // 12

        apply_recurring_for_month(db, today)

        # “Income for current month” from transactions (only positives)
        inc = db.execute("""
            SELECT COALESCE(SUM(CASE WHEN amount_cents > 0 THEN amount_cents ELSE 0 END), 0) AS income
            FROM transactions
            WHERE substr(date, 1, 7) = ?
        """, (mkey,)).fetchone()

        income_monthly = inc["income"] if inc["income"] > 0 else salary_est

        # Total budget
        rows = db.execute(
            """
            SELECT c.name, b.amount_cents
            FROM budgets b JOIN categories c ON c.id=b.category_id
            WHERE b.month=? ORDER BY c.name
            """,
            (mkey,),
        ).fetchall()
        B_total = sum(r["amount_cents"] for r in rows)

        # Month to date spending
        s = db.execute(
            """
            SELECT COALESCE(ABS(SUM(CASE WHEN amount_cents<0 THEN amount_cents ELSE 0 END)),0) AS spent
            FROM transactions
            WHERE substr(date,1,7)=?
            """,
            (mkey,),
        ).fetchone()
        S_so_far = s["spent"]

        pr = pro_rata(B_total, today)
        variance = S_so_far - int(pr["target"])
        cap = daily_cap(B_total, S_so_far, today)

        # monthly savings estimate (income - spending)
        expenses_month = S_so_far
        savings_month = income_monthly - expenses_month

        # category breakdown for chart
        cat_rows = db.execute(
            """
            SELECT
                c.name,
                COALESCE(b.amount_cents, 0) AS budget,
                COALESCE(
                    ABS(
                        SUM(
                            CASE
                                WHEN t.amount_cents < 0 THEN t.amount_cents
                                ELSE 0
                            END
                        )
                    ),
                    0
                ) AS spent
            FROM categories c
            LEFT JOIN category_groups g
                ON g.id = c.group_id
            LEFT JOIN budgets b
                ON b.category_id = c.id
            AND b.month = ?
            LEFT JOIN transactions t
                ON t.category_id = c.id
            AND substr(t.date, 1, 7) = ?
            WHERE COALESCE(g.type, 'expense') = 'expense'
            GROUP BY c.id, c.name
            ORDER BY c.name
            """,
            (mkey, mkey),
        ).fetchall()

        # group breakdown for table/chart
        group_rows = db.execute(
            """
            WITH
            cat_budget AS (
                SELECT
                    c.id AS category_id,
                    c.group_id,
                    SUM(b.amount_cents) AS budget
                FROM categories c
                JOIN budgets b
                    ON b.category_id = c.id
                AND b.month = ?
                GROUP BY c.id, c.group_id
            ),
            cat_spent AS (
                SELECT
                    t.category_id,
                    ABS(SUM(t.amount_cents)) AS spent
                FROM transactions t
                WHERE t.amount_cents < 0
                AND substr(t.date, 1, 7) = ?
                GROUP BY t.category_id
            )

            SELECT
                COALESCE(g.name, 'Ungrouped') AS group_name,
                COALESCE(g.type, 'expense')   AS group_type,
                g.sort_order                  AS sort_order,
                (g.sort_order IS NULL)        AS sort_is_null,

                COALESCE(SUM(cb.budget), 0)              AS budget,
                COALESCE(SUM(COALESCE(cs.spent, 0)), 0)  AS spent

            FROM category_groups g
            LEFT JOIN cat_budget cb ON cb.group_id = g.id
            LEFT JOIN cat_spent  cs ON cs.category_id = cb.category_id
            GROUP BY g.id, g.name, g.type, g.sort_order

            UNION ALL

            SELECT
                'Ungrouped' AS group_name,
                'expense'   AS group_type,
                NULL        AS sort_order,
                1           AS sort_is_null,
                0           AS budget,
                COALESCE(ABS(SUM(t.amount_cents)), 0) AS spent
            FROM transactions t
            LEFT JOIN categories c ON c.id = t.category_id
            WHERE t.amount_cents < 0
            AND substr(t.date, 1, 7) = ?
            AND (c.group_id IS NULL OR t.category_id IS NULL)

            ORDER BY sort_is_null, sort_order, group_name
            """,
            (mkey, mkey, mkey),
        ).fetchall()


        months = month_seq(start_mkey, mkey)

        # Trend chart data
        trend_map = {
            m: {"mkey": m, "income": 0, "spent": 0}
            for m in months
        }

        rows = db.execute(
            """
            SELECT
            substr(date,1,7) AS mkey,
            COALESCE(SUM(CASE WHEN amount_cents > 0 THEN amount_cents ELSE 0 END),0) AS income,
            COALESCE(ABS(SUM(CASE WHEN amount_cents < 0 THEN amount_cents ELSE 0 END)),0) AS spent
            FROM transactions
            WHERE substr(date,1,7) BETWEEN ? AND ?
            GROUP BY substr(date,1,7)
            """,
            (start_mkey, mkey),
        ).fetchall()

        for r in rows:
            trend_map[r["mkey"]] = {
                "mkey": r["mkey"],
                "income": r["income"],
                "spent": r["spent"],
            }

        trend = [trend_map[m] for m in months]
        spent_vals = [r["spent"] for r in trend]

        # # Moving average for 3 months
        ma3 = []
        for i in range(len(spent_vals)):
            window = spent_vals[max(0, i - 2): i + 1]
            ma3.append(sum(window) / len(window))

        # Top categories in range
        top_cats_range = db.execute(
            """
            SELECT
            COALESCE(c.name, 'Uncategorized') AS category,
            COALESCE(ABS(SUM(t.amount_cents)),0) AS spent
            FROM transactions t
            LEFT JOIN categories c ON c.id = t.category_id
            WHERE t.amount_cents < 0
            AND substr(t.date,1,7) BETWEEN ? AND ?
            GROUP BY category
            ORDER BY spent DESC
            LIMIT 10
            """,
            (start_mkey, mkey),
        ).fetchall()

    return render_template(
        'index.html',
        today=today,
        mkey=mkey,
        income_monthly=income_monthly,
        B_total=B_total,
        S_so_far=S_so_far,
        variance=variance,
        cap=cap,
        savings_month=savings_month,
        cats=cat_rows,
        groups=group_rows,
        range_key=range_key,
        start_mkey=start_mkey,
        trend=trend,
        ma3=ma3,
        top_cats_range=top_cats_range,
    )

# Accounts CRUD
@app.route("/accounts", methods=["GET", "POST"])
def accounts():
    with get_db() as db:
        if request.method == "POST":
            name = request.form["name"]
            typ = request.form["type"]

            # Validate allowed types
            if typ not in ("debit", "credit", "investment"):
                flash("Invalid account type.", "error")
                return redirect(url_for("accounts"))

            db.execute("INSERT INTO accounts(name,type) VALUES(?,?)", (name, typ))
            flash("Account added.", "success")
            return redirect(url_for("accounts"))

        accts = db.execute("SELECT * FROM accounts ORDER BY id").fetchall()
    return render_template("accounts.html", accounts=accts)


@app.post("/accounts/<int:account_id>/update")
def update_account(account_id):
    name = request.form["name"].strip()
    typ = request.form["type"]

    if typ not in ("debit", "credit", "investment"):
        flash("Invalid account type.", "error")
        return redirect(url_for("accounts"))

    with get_db() as db:
        db.execute(
            "UPDATE accounts SET name = ?, type = ? WHERE id = ?",
            (name, typ, account_id),
        )

    flash("Account updated.", "success")
    return redirect(url_for("accounts"))

@app.post("/accounts/<int:account_id>/delete")
def delete_account(account_id):
    # Uses SQLite's foreign keys + cascading deletes
    # SQLite docs: https://sqlite.org/pragma.html#pragma_foreign_keys
    with get_db() as db:
        db.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    flash("Account deleted.", "success")
    return redirect(url_for("accounts"))

# Budgets
# ChatGPT was used to help build the budget system
@app.route('/budgets', methods=['GET', 'POST'])
def budgets():
    today = date.today()
    month = request.args.get('month') or month_key(today)

    with get_db() as db:
        # ---------- POST: save / clear ----------
        if request.method == 'POST':
            month = request.form['month']
            action = request.form.get('action', 'save')

            if action == 'clear':
                db.execute("DELETE FROM budgets WHERE month = ?", (month,))
                flash(f'Cleared all budgets for {month}.', 'success')
                return redirect(url_for('budgets', month=month))

            # Save/upsert budgets
            items = []
            for key, val in request.form.items():
                if key.startswith('cat_'):
                    cat_id = int(key.split('_', 1)[1])
                    amt = float(val or 0)
                    items.append((month, cat_id, int(round(amt * 100))))

            for m, cid, cents in items:
                db.execute(
                    """
                    INSERT INTO budgets(month, category_id, amount_cents)
                    VALUES(?,?,?)
                    ON CONFLICT(month, category_id)
                    DO UPDATE SET amount_cents = excluded.amount_cents
                    """,
                    (m, cid, cents),
                )

            flash('Budgets saved.', 'success')
            return redirect(url_for('budgets', month=month))

        # ---------- GET: show budgets + rollover suggestions ----------
        cats = db.execute(
            """
            SELECT
                c.id,
                c.name,
                COALESCE(g.name, '') AS group_name
            FROM categories c
            LEFT JOIN category_groups g ON g.id = c.group_id
            ORDER BY g.sort_order IS NULL, g.sort_order, g.name, c.name
            """
        ).fetchall()

        # existing budgets for this month
        rows = db.execute(
            "SELECT category_id, amount_cents FROM budgets WHERE month=?",
            (month,),
        ).fetchall()
        existing = {r['category_id']: r['amount_cents'] for r in rows}
        prev_month = prev_month_key(month)

        # rollover = last_month_budget - last_month_spent
        prev_rows = db.execute(
            """
            SELECT
                b.category_id,
                b.amount_cents AS budget_cents,
                COALESCE(
                    ABS(
                        SUM(
                            CASE
                                WHEN t.amount_cents < 0 THEN t.amount_cents
                                ELSE 0
                            END
                        )
                    ),
                    0
                ) AS spent_cents
            FROM budgets b
            LEFT JOIN transactions t
                ON t.category_id = b.category_id
               AND substr(t.date,1,7) = ?
            WHERE b.month = ?
            GROUP BY b.category_id
            """,
            (prev_month, prev_month),
        ).fetchall()

        rollover = {}
        suggested = {}

        for row in prev_rows:
            cid = row['category_id']
            B_prev = row['budget_cents']
            S_prev = row['spent_cents']

            delta = B_prev - S_prev
            rollover[cid] = delta

            # Only autosuggest if user hasnt already set this month’s value
            if cid not in existing:
                suggested_budget = B_prev + delta
                suggested[cid] = max(0, suggested_budget)

    return render_template(
        'budgets.html',
        month=month,
        cats=cats,
        existing=existing,
        rollover=rollover,
        suggested=suggested,
        prev_month=prev_month,
    )

# Categories CRUD
@app.route('/categories', methods=['GET', 'POST'])
def categories():
    with get_db() as db:
        if request.method == 'POST':
            name = request.form.get('name', '').strip()
            if not name:
                flash("Category name is required.", "error")
                return redirect(url_for('categories'))
            try:
                db.execute("INSERT INTO categories(name) VALUES (?)", (name,))
                flash("Category added.", "success")
            except Exception:
                flash("That category already exists.", "error")
            return redirect(url_for('categories'))

        cats = db.execute("SELECT id, name FROM categories ORDER BY name").fetchall()
    return render_template('categories.html', cats=cats)


@app.post('/categories/<int:cat_id>/delete')
def delete_category(cat_id):
    with get_db() as db:
        # if recurring requires a category, block deletion
        in_use = db.execute("SELECT 1 FROM recurring WHERE category_id = ? LIMIT 1", (cat_id,)).fetchone()
        if in_use:
            flash("Category is used by a recurring item. Delete/disable that recurring item first.", "error")
            return redirect(url_for('categories'))

        db.execute("DELETE FROM categories WHERE id = ?", (cat_id,))
    flash("Category deleted.", "success")
    return redirect(url_for('categories'))

# Category Groups
@app.route("/category-groups", methods=["GET", "POST"])
def category_groups():
    with get_db() as db:
        if request.method == "POST":
            name = request.form.get("name", "").strip()
            sort_raw = request.form.get("sort_order", "").strip() or None
            gtype = request.form.get("type", "expense")

            if gtype not in ("expense", "income"):
                flash("Invalid group type.", "error")
                return redirect(url_for("category_groups"))

            if not name:
                flash("Group name is required.", "error")
                return redirect(url_for("category_groups"))

            try:
                sort_order = int(sort_raw) if sort_raw is not None else None
                db.execute(
                    "INSERT INTO category_groups(name, sort_order, type) VALUES (?, ?, ?)",
                    (name, sort_order, gtype),
                )
                flash("Category group added.", "success")
            except ValueError:
                flash("Sort order must be a number.", "error")
            except sqlite3.IntegrityError:
                flash("Group name must be unique.", "error")

            return redirect(url_for("category_groups"))

        groups = db.execute(
            """
            SELECT id, name, sort_order, type
            FROM category_groups
            ORDER BY sort_order IS NULL, sort_order, name
            """
        ).fetchall()

        cats = db.execute(
            """
            SELECT c.id, c.name, c.group_id,
                   g.name AS group_name
            FROM categories c
            LEFT JOIN category_groups g ON g.id = c.group_id
            ORDER BY g.sort_order IS NULL, g.sort_order, g.name, c.name
            """
        ).fetchall()

    return render_template("category_groups.html", groups=groups, cats=cats)


@app.post("/categories/<int:cat_id>/set-group")
def set_category_group(cat_id):
    group_raw = request.form.get("group_id", "")

    group_id = int(group_raw) if group_raw else None

    with get_db() as db:
        db.execute(
            "UPDATE categories SET group_id = ? WHERE id = ?",
            (group_id, cat_id),
        )

    flash("Category group updated.", "success")
    return redirect(url_for("category_groups"))


@app.post("/category-groups/<int:group_id>/delete")
def delete_category_group(group_id):
    # Unassign categories, then delete group
    with get_db() as db:
        db.execute(
            "UPDATE categories SET group_id = NULL WHERE group_id = ?",
            (group_id,),
        )
        db.execute(
            "DELETE FROM category_groups WHERE id = ?",
            (group_id,),
        )

    flash("Category group deleted.", "success")
    return redirect(url_for("category_groups"))

# Net Worth
# Uses SQLite's UPSERT to update snapshot per account_id, as_of
# Docs: https://sqlite.org/lang_upsert.html
@app.route("/net-worth", methods=["GET", "POST"])
def net_worth():
    today = date.today().isoformat()
    as_of = request.form.get("as_of") if request.method == "POST" else request.args.get("as_of")
    as_of = as_of or today

    with get_db() as db:
        accounts = db.execute(
            "SELECT id, name, type FROM accounts ORDER BY type, name"
        ).fetchall()

        if request.method == "POST":
            # Upsert a balance for each account for the chosen date
            for a in accounts:
                raw = request.form.get(f"bal_{a['id']}", "").strip()
                if raw == "":
                    continue
                try:
                    amount = float(raw)
                    if amount < 0:
                        raise ValueError()
                except ValueError:
                    flash(f"Invalid balance for {a['name']}. Use a non-negative number.", "error")
                    return redirect(url_for("net_worth", as_of=as_of))

                cents = int(round(amount * 100))
                db.execute(
                    """
                    INSERT INTO account_balances(account_id, as_of, balance_cents)
                    VALUES (?, ?, ?)
                    ON CONFLICT(account_id, as_of)
                    DO UPDATE SET balance_cents = excluded.balance_cents
                    """,
                    (a["id"], as_of, cents),
                )

            flash(f"Saved balances for {as_of}.", "success")
            return redirect(url_for("net_worth", as_of=as_of))

        # Pull balances for that date to prefill form
        balances = db.execute(
            """
            SELECT ab.account_id, ab.balance_cents
            FROM account_balances ab
            WHERE ab.as_of = ?
            """,
            (as_of,),
        ).fetchall()
        bal_map = {r["account_id"]: r["balance_cents"] for r in balances}

        # compute assets/liabilities/net at the selected as_of date
        summary = db.execute(
            """
            SELECT
              COALESCE(SUM(CASE WHEN a.type IN ('debit','investment') THEN ab.balance_cents ELSE 0 END),0) AS assets,
              COALESCE(SUM(CASE WHEN a.type = 'credit' THEN ab.balance_cents ELSE 0 END),0) AS liabilities
            FROM accounts a
            LEFT JOIN account_balances ab
              ON ab.account_id = a.id AND ab.as_of = ?
            """,
            (as_of,),
        ).fetchone()

        assets = summary["assets"]
        liabilities = summary["liabilities"]
        net = assets - liabilities

        # History points
        history = db.execute(
            """
            SELECT
              ab.as_of AS as_of,
              COALESCE(SUM(CASE WHEN a.type IN ('debit','investment') THEN ab.balance_cents ELSE 0 END),0) AS assets,
              COALESCE(SUM(CASE WHEN a.type = 'credit' THEN ab.balance_cents ELSE 0 END),0) AS liabilities
            FROM account_balances ab
            JOIN accounts a ON a.id = ab.account_id
            GROUP BY ab.as_of
            ORDER BY ab.as_of
            """
        ).fetchall()

    return render_template(
        "net_worth.html",
        as_of=as_of,
        accounts=accounts,
        bal_map=bal_map,
        assets=assets,
        liabilities=liabilities,
        net=net,
        history=history,
    )

# Recurring CRUD
@app.route("/recurring", methods=["GET", "POST"])
def recurring():
    with get_db() as db:
        if request.method == "POST":
            # Validate category is present
            category_raw = request.form.get('category_id', '')
            if not category_raw:
                flash("Category is required for recurring items.", "error")
                return redirect(url_for('recurring'))
            category_id = int(category_raw)

            # Validate direction
            direction = request.form.get('direction', 'out')
            if direction not in ('in', 'out'):
                flash("Invalid direction.", "error")
                return redirect(url_for('recurring'))

            # Core fields
            name = request.form["name"]
            account_id = int(request.form["account_id"])
            category_id = (
                int(request.form["category_id"])
                if request.form.get("category_id")
                else None
            )
            amount = float(request.form["amount"])
            day_of_month = int(request.form["day_of_month"])
            active = 1 if request.form.get("active") == "on" else 0

            db.execute(
                """
                INSERT INTO recurring (name, account_id, category_id, amount_cents, day_of_month, direction, active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (name, account_id, category_id, int(round(amount*100)), day_of_month, direction, active))


            flash("Recurring item added.", "success")
            return redirect(url_for("recurring"))

        # Render recurring list + form dropdowns
        recs = db.execute(
            """
            SELECT r.id, r.name, r.amount_cents, r.day_of_month, r.direction, r.active,
                a.name AS account_name,
                c.name AS category_name
            FROM recurring r
            JOIN accounts a ON a.id = r.account_id
            LEFT JOIN categories c ON c.id = r.category_id
            ORDER BY r.day_of_month, r.name
            """
        ).fetchall()
        accts = db.execute("SELECT id, name FROM accounts ORDER BY name").fetchall()
        cats = db.execute(
            """
            SELECT
                c.id,
                c.name,
                COALESCE(g.name, '') AS group_name
            FROM categories c
            LEFT JOIN category_groups g ON g.id = c.group_id
            ORDER BY g.sort_order IS NULL, g.sort_order, g.name, c.name
            """
        ).fetchall()

    return render_template("recurring.html", recs=recs, accts=accts, cats=cats)

@app.post("/recurring/<int:rec_id>/toggle")
def toggle_recurring(rec_id):
    with get_db() as db:
        row = db.execute(
            "SELECT active FROM recurring WHERE id = ?",
            (rec_id,),
        ).fetchone()
        if row is not None:
            new_active = 0 if row["active"] else 1
            db.execute(
                "UPDATE recurring SET active = ? WHERE id = ?",
                (new_active, rec_id),
            )
            flash("Recurring item updated.", "success")
    return redirect(url_for("recurring"))


@app.post("/recurring/<int:rec_id>/delete")
def delete_recurring(rec_id):
    with get_db() as db:
        db.execute("DELETE FROM recurring WHERE id = ?", (rec_id,))
    flash("Recurring item deleted.", "success")
    return redirect(url_for("recurring"))

# Settings page
@app.route("/settings", methods=["GET", "POST"])
def settings():
    if request.method == "POST":
        salary = float(request.form.get("salary_annual", 0))
        with get_db() as db:
            db.execute(
                "UPDATE users SET salary_annual_cents=? WHERE id=1",
                (int(round(salary * 100)),),
            )
        flash("Updated salary.", "success")
        return redirect(url_for("settings"))
    with get_db() as db:
        row = db.execute("SELECT salary_annual_cents FROM users WHERE id=1").fetchone()
    return render_template(
        "settings.html", salary_annual=(row["salary_annual_cents"] or 0) / 100
    )

# tag system
HEX_RE = re.compile(r"^#[0-9a-fA-F]{6}$")

@app.route("/tags", methods=["GET", "POST"])
def tags():
    with get_db() as db:
        if request.method == "POST":
            name = (request.form.get("name") or "").strip()
            color = (request.form.get("color") or "").strip() or "#64748b"

            if not name:
                flash("Tag name is required.", "error")
                return redirect(url_for("tags"))

            if not name.startswith("#"):
                name = "#" + name

            if not HEX_RE.match(color):
                flash("Color must be a valid hex value like #ff0000.", "error")
                return redirect(url_for("tags"))

            try:
                db.execute("INSERT INTO tags(name, color) VALUES (?, ?)", (name, color))
                flash("Tag created.", "success")
            except sqlite3.IntegrityError:
                flash("That tag already exists.", "error")

            return redirect(url_for("tags"))

        tags = db.execute("SELECT id, name, color FROM tags ORDER BY name").fetchall()

    return render_template("tags.html", tags=tags)


@app.post("/tags/<int:tag_id>/delete")
def delete_tag(tag_id):
    with get_db() as db:
        db.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
    flash("Tag deleted.", "success")
    return redirect(url_for("tags"))

# Transactions
# chatGPT was used to help implement the transaction system
# SQLite GROUP_CONCAT docs: https://sqlite.org/lang_aggfunc.html
@app.route("/transactions", methods=["GET", "POST"])
def transactions():
    today = date.today()
    with get_db() as db:
        apply_recurring_for_month(db, today)
        # ---- POST ----
        if request.method == "POST":
            # validate amount
            amount_raw = request.form.get("amount", "").strip()
            if not amount_raw:
                flash("Amount is required.", "error")
                return redirect(url_for("transactions"))

            try:
                amount = float(amount_raw)
            except ValueError:
                flash("Amount must be a number.", "error")
                return redirect(url_for("transactions"))

            # validate category
            category_raw = request.form.get("category_id", "").strip()
            if not category_raw:
                flash("Please choose a category for each transaction.", "error")
                return redirect(url_for("transactions"))

            try:
                category_id = int(category_raw)
            except ValueError:
                flash("Invalid category.", "error")
                return redirect(url_for("transactions"))

            # core fields
            account_id = int(request.form["account_id"])
            date_ = request.form["date"]
            desc = request.form.get("description")

            direction = request.form.get("direction", "out")
            if direction not in ("in", "out"):
                flash("Invalid direction.", "error")
                return redirect(url_for("transactions"))

            # cents sign convention
            cents = int(round(amount * 100))
            if direction == "out":
                cents = -abs(cents)
            else:
                cents = abs(cents)

            # insert transaction
            cur = db.execute(
                """
                INSERT INTO transactions(account_id, date, description, amount_cents, category_id)
                VALUES (?, ?, ?, ?, ?)
                """,
                (account_id, date_, desc, cents, category_id),
            )
            tx_id = cur.lastrowid

            # attach tags
            tag_ids = request.form.getlist("tag_ids")
            for tid in tag_ids:
                try:
                    db.execute(
                        """
                        INSERT OR IGNORE INTO transaction_tags(transaction_id, tag_id)
                        VALUES (?, ?)
                        """,
                        (tx_id, int(tid)),
                    )
                except ValueError:
                    pass

            flash("Transaction added.", "success")
            return redirect(url_for("transactions"))

        # ---- GET: render page ----
        tags = db.execute("SELECT id, name, color FROM tags ORDER BY name").fetchall()

        tx = db.execute(
            """
            SELECT
                t.id, t.date, a.name AS account, t.description, t.amount_cents,
                c.name AS category,
                COALESCE(GROUP_CONCAT(tags.name || '|' || tags.color, ','), '') AS tags
            FROM transactions t
            JOIN accounts a ON a.id=t.account_id
            LEFT JOIN categories c ON c.id=t.category_id
            LEFT JOIN transaction_tags tt ON tt.transaction_id = t.id
            LEFT JOIN tags ON tags.id = tt.tag_id
            GROUP BY t.id
            ORDER BY date DESC, t.id DESC
            LIMIT 200
            """
        ).fetchall()

        cats = db.execute(
            """
            SELECT
                c.id,
                c.name,
                COALESCE(g.name, '') AS group_name
            FROM categories c
            LEFT JOIN category_groups g ON g.id = c.group_id
            ORDER BY g.sort_order IS NULL, g.sort_order, g.name, c.name
            """
        ).fetchall()

        accts = db.execute("SELECT id, name FROM accounts ORDER BY name").fetchall()

    return render_template("transactions.html", tx=tx, cats=cats, accts=accts, tags=tags)

@app.post("/transactions/<int:tx_id>/delete")
def delete_transaction(tx_id):
    with get_db() as db:
        db.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
    flash("Transaction deleted.", "success")
    return redirect(url_for("transactions"))

if __name__ == "__main__":
    app.run(debug=True)
