"""
Recurring Repository - Database queries for recurring transactions
"""
from typing import List
from db import get_db


class RecurringRepository:
    """Handles all database operations for recurring transactions."""
    
    @staticmethod
    def get_all_active() -> List[dict]:
        """Get all active recurring items."""
        with get_db() as db:
            return db.execute(
                """
                SELECT id, name, account_id, category_id, amount_cents, day_of_month, direction
                FROM recurring
                WHERE active = 1
                """
            ).fetchall()
    
    @staticmethod
    def get_all_with_details() -> List[dict]:
        """Get all recurring items with account and category names."""
        with get_db() as db:
            return db.execute(
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
    
    @staticmethod
    def create(name: str, account_id: int, category_id: int, amount_cents: int,
               day_of_month: int, direction: str, active: int = 1) -> int:
        """Create a new recurring item and return its ID."""
        with get_db() as db:
            cursor = db.execute(
                """
                INSERT INTO recurring (name, account_id, category_id, amount_cents, day_of_month, direction, active)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (name, account_id, category_id, amount_cents, day_of_month, direction, active)
            )
            return cursor.lastrowid
    
    @staticmethod
    def toggle_active(recurring_id: int) -> None:
        """Toggle the active status of a recurring item."""
        with get_db() as db:
            row = db.execute(
                "SELECT active FROM recurring WHERE id = ?",
                (recurring_id,),
            ).fetchone()
            if row is not None:
                new_active = 0 if row["active"] else 1
                db.execute(
                    "UPDATE recurring SET active = ? WHERE id = ?",
                    (new_active, recurring_id),
                )
    
    @staticmethod
    def delete(recurring_id: int) -> None:
        """Delete a recurring item."""
        with get_db() as db:
            db.execute("DELETE FROM recurring WHERE id = ?", (recurring_id,))
