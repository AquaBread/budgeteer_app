"""
Account Repository - Database queries for accounts
"""
from typing import List, Optional
from db import get_db


class AccountRepository:
    """Handles all database operations for accounts."""
    
    @staticmethod
    def get_all() -> List[dict]:
        """Get all accounts ordered by ID."""
        with get_db() as db:
            return db.execute("SELECT * FROM accounts ORDER BY id").fetchall()
    
    @staticmethod
    def get_by_id(account_id: int) -> Optional[dict]:
        """Get a single account by ID."""
        with get_db() as db:
            return db.execute(
                "SELECT * FROM accounts WHERE id = ?", 
                (account_id,)
            ).fetchone()
    
    @staticmethod
    def create(name: str, account_type: str) -> int:
        """Create a new account and return its ID."""
        with get_db() as db:
            cursor = db.execute(
                "INSERT INTO accounts(name, type) VALUES(?, ?)", 
                (name, account_type)
            )
            return cursor.lastrowid
    
    @staticmethod
    def update(account_id: int, name: str, account_type: str) -> None:
        """Update an existing account."""
        with get_db() as db:
            db.execute(
                "UPDATE accounts SET name = ?, type = ? WHERE id = ?",
                (name, account_type, account_id),
            )
    
    @staticmethod
    def delete(account_id: int) -> None:
        """Delete an account (cascades to related records)."""
        with get_db() as db:
            db.execute("DELETE FROM accounts WHERE id = ?", (account_id,))
    
    @staticmethod
    def get_all_ordered_by_type() -> List[dict]:
        """Get all accounts ordered by type and name."""
        with get_db() as db:
            return db.execute(
                "SELECT id, name, type FROM accounts ORDER BY type, name"
            ).fetchall()
