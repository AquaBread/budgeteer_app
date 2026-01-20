"""
User Repository - Database queries for user settings
"""
from db import get_db


class UserRepository:
    """Handles all database operations for user settings."""
    
    @staticmethod
    def get_salary() -> int:
        """Get the user's annual salary in cents."""
        with get_db() as db:
            row = db.execute(
                "SELECT salary_annual_cents FROM users WHERE id=1"
            ).fetchone()
            return row["salary_annual_cents"] if row else 0
    
    @staticmethod
    def update_salary(salary_cents: int) -> None:
        """Update the user's annual salary."""
        with get_db() as db:
            db.execute(
                "UPDATE users SET salary_annual_cents=? WHERE id=1",
                (salary_cents,),
            )
