"""
Transaction Repository - Database queries for transactions
"""
from typing import List, Optional
from db import get_db


class TransactionRepository:
    """Handles all database operations for transactions."""
    
    @staticmethod
    def get_recent(limit: int = 200) -> List[dict]:
        """Get recent transactions with account, category, and tag info."""
        with get_db() as db:
            return db.execute(
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
                LIMIT ?
                """,
                (limit,)
            ).fetchall()
    
    @staticmethod
    def create(account_id: int, date: str, description: str, 
               amount_cents: int, category_id: int, recurring_id: Optional[int] = None) -> int:
        """Create a new transaction and return its ID."""
        with get_db() as db:
            cursor = db.execute(
                """
                INSERT INTO transactions(account_id, date, description, amount_cents, category_id, recurring_id)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (account_id, date, description, amount_cents, category_id, recurring_id),
            )
            return cursor.lastrowid
    
    @staticmethod
    def delete(transaction_id: int) -> None:
        """Delete a transaction."""
        with get_db() as db:
            db.execute("DELETE FROM transactions WHERE id = ?", (transaction_id,))
    
    @staticmethod
    def get_income_for_month(month_key: str) -> int:
        """Get total income (positive transactions) for a given month."""
        with get_db() as db:
            result = db.execute(
                """
                SELECT COALESCE(SUM(CASE WHEN amount_cents > 0 THEN amount_cents ELSE 0 END), 0) AS income
                FROM transactions
                WHERE substr(date, 1, 7) = ?
                """, 
                (month_key,)
            ).fetchone()
            return result["income"] if result else 0
    
    @staticmethod
    def get_spending_for_month(month_key: str) -> int:
        """Get total spending (negative transactions) for a given month."""
        with get_db() as db:
            result = db.execute(
                """
                SELECT COALESCE(ABS(SUM(CASE WHEN amount_cents<0 THEN amount_cents ELSE 0 END)),0) AS spent
                FROM transactions
                WHERE substr(date,1,7)=?
                """,
                (month_key,),
            ).fetchone()
            return result["spent"] if result else 0
    
    @staticmethod
    def get_trend_data(start_month: str, end_month: str) -> List[dict]:
        """Get income and spending trends for a date range."""
        with get_db() as db:
            return db.execute(
                """
                SELECT
                    substr(date,1,7) AS mkey,
                    COALESCE(SUM(CASE WHEN amount_cents > 0 THEN amount_cents ELSE 0 END),0) AS income,
                    COALESCE(ABS(SUM(CASE WHEN amount_cents < 0 THEN amount_cents ELSE 0 END)),0) AS spent
                FROM transactions
                WHERE substr(date,1,7) BETWEEN ? AND ?
                GROUP BY substr(date,1,7)
                """,
                (start_month, end_month),
            ).fetchall()
    
    @staticmethod
    def get_top_categories_in_range(start_month: str, end_month: str, limit: int = 10) -> List[dict]:
        """Get top spending categories in a date range."""
        with get_db() as db:
            return db.execute(
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
                LIMIT ?
                """,
                (start_month, end_month, limit),
            ).fetchall()
    
    @staticmethod
    def check_exists_for_recurring(recurring_id: int, date: str) -> bool:
        """Check if a transaction already exists for a recurring item on a specific date."""
        with get_db() as db:
            result = db.execute(
                """
                SELECT 1 FROM transactions
                WHERE recurring_id = ? AND date = ?
                """,
                (recurring_id, date),
            ).fetchone()
            return result is not None
    
    @staticmethod
    def attach_tags(transaction_id: int, tag_ids: List[int]) -> None:
        """Attach tags to a transaction."""
        with get_db() as db:
            for tag_id in tag_ids:
                db.execute(
                    """
                    INSERT OR IGNORE INTO transaction_tags(transaction_id, tag_id)
                    VALUES (?, ?)
                    """,
                    (transaction_id, tag_id),
                )
