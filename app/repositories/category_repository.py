"""
Category Repository - Database queries for categories and category groups
"""
from typing import List, Optional
from db import get_db


class CategoryRepository:
    """Handles all database operations for categories."""
    
    @staticmethod
    def get_all() -> List[dict]:
        """Get all categories ordered by name."""
        with get_db() as db:
            return db.execute(
                "SELECT id, name FROM categories ORDER BY name"
            ).fetchall()
    
    @staticmethod
    def get_all_with_groups() -> List[dict]:
        """Get all categories with their group information."""
        with get_db() as db:
            return db.execute(
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
    
    @staticmethod
    def get_all_with_group_details() -> List[dict]:
        """Get all categories with full group details."""
        with get_db() as db:
            return db.execute(
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
    
    @staticmethod
    def create(name: str) -> int:
        """Create a new category and return its ID."""
        with get_db() as db:
            cursor = db.execute(
                "INSERT INTO categories(name) VALUES (?)", 
                (name,)
            )
            return cursor.lastrowid
    
    @staticmethod
    def delete(category_id: int) -> None:
        """Delete a category."""
        with get_db() as db:
            db.execute("DELETE FROM categories WHERE id = ?", (category_id,))
    
    @staticmethod
    def is_used_by_recurring(category_id: int) -> bool:
        """Check if a category is used by any recurring items."""
        with get_db() as db:
            result = db.execute(
                "SELECT 1 FROM recurring WHERE category_id = ? LIMIT 1", 
                (category_id,)
            ).fetchone()
            return result is not None
    
    @staticmethod
    def set_group(category_id: int, group_id: Optional[int]) -> None:
        """Set or clear the group for a category."""
        with get_db() as db:
            db.execute(
                "UPDATE categories SET group_id = ? WHERE id = ?",
                (group_id, category_id),
            )


class CategoryGroupRepository:
    """Handles all database operations for category groups."""
    
    @staticmethod
    def get_all() -> List[dict]:
        """Get all category groups ordered by sort order."""
        with get_db() as db:
            return db.execute(
                """
                SELECT id, name, sort_order, type
                FROM category_groups
                ORDER BY sort_order IS NULL, sort_order, name
                """
            ).fetchall()
    
    @staticmethod
    def create(name: str, sort_order: Optional[int], group_type: str) -> int:
        """Create a new category group and return its ID."""
        with get_db() as db:
            cursor = db.execute(
                "INSERT INTO category_groups(name, sort_order, type) VALUES (?, ?, ?)",
                (name, sort_order, group_type),
            )
            return cursor.lastrowid
    
    @staticmethod
    def delete(group_id: int) -> None:
        """Delete a category group (unassigns categories first)."""
        with get_db() as db:
            # Unassign categories
            db.execute(
                "UPDATE categories SET group_id = NULL WHERE group_id = ?",
                (group_id,),
            )
            # Delete group
            db.execute(
                "DELETE FROM category_groups WHERE id = ?",
                (group_id,),
            )
    
    @staticmethod
    def get_group_breakdown(month_key: str) -> List[dict]:
        """Get budget vs spending breakdown by group."""
        with get_db() as db:
            return db.execute(
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
                (month_key, month_key, month_key),
            ).fetchall()
    
    @staticmethod
    def get_categories_with_groups() -> List[dict]:
        """Get all categories with their group assignments."""
        with get_db() as db:
            return db.execute(
                """
                SELECT c.id, c.name, c.group_id,
                       g.name AS group_name
                FROM categories c
                LEFT JOIN category_groups g ON g.id = c.group_id
                ORDER BY g.sort_order IS NULL, g.sort_order, g.name, c.name
                """
            ).fetchall()
