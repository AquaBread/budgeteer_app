"""
Budget Repository - Database queries for budgets
"""
from typing import List, Dict
from db import get_db


class BudgetRepository:
    """Handles all database operations for budgets."""
    
    @staticmethod
    def get_for_month(month_key: str) -> List[dict]:
        """Get all budgets for a specific month."""
        with get_db() as db:
            return db.execute(
                """
                SELECT c.name, b.amount_cents
                FROM budgets b 
                JOIN categories c ON c.id=b.category_id
                WHERE b.month=? 
                ORDER BY c.name
                """,
                (month_key,),
            ).fetchall()
    
    @staticmethod
    def get_total_for_month(month_key: str) -> int:
        """Get total budget amount for a month."""
        rows = BudgetRepository.get_for_month(month_key)
        return sum(r["amount_cents"] for r in rows)
    
    @staticmethod
    def get_budget_map(month_key: str) -> Dict[int, int]:
        """Get a map of category_id -> budget amount for a month."""
        with get_db() as db:
            rows = db.execute(
                "SELECT category_id, amount_cents FROM budgets WHERE month=?",
                (month_key,),
            ).fetchall()
            return {r['category_id']: r['amount_cents'] for r in rows}
    
    @staticmethod
    def upsert(month_key: str, category_id: int, amount_cents: int) -> None:
        """Insert or update a budget for a category in a month."""
        with get_db() as db:
            db.execute(
                """
                INSERT INTO budgets(month, category_id, amount_cents)
                VALUES(?,?,?)
                ON CONFLICT(month, category_id)
                DO UPDATE SET amount_cents = excluded.amount_cents
                """,
                (month_key, category_id, amount_cents),
            )
    
    @staticmethod
    def clear_month(month_key: str) -> None:
        """Delete all budgets for a specific month."""
        with get_db() as db:
            db.execute("DELETE FROM budgets WHERE month = ?", (month_key,))
    
    @staticmethod
    def get_category_breakdown(month_key: str) -> List[dict]:
        """Get budget vs spending breakdown by category."""
        with get_db() as db:
            return db.execute(
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
                (month_key, month_key),
            ).fetchall()
    
    @staticmethod
    def get_previous_month_data(month_key: str) -> List[dict]:
        """Get budget and spending data from the previous month for rollover calculations."""
        with get_db() as db:
            return db.execute(
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
                (month_key, month_key),
            ).fetchall()
