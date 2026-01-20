"""
Tag Repository - Database queries for tags
"""
from typing import List
from db import get_db


class TagRepository:
    """Handles all database operations for tags."""
    
    @staticmethod
    def get_all() -> List[dict]:
        """Get all tags ordered by name."""
        with get_db() as db:
            return db.execute(
                "SELECT id, name, color FROM tags ORDER BY name"
            ).fetchall()
    
    @staticmethod
    def create(name: str, color: str) -> int:
        """Create a new tag and return its ID."""
        with get_db() as db:
            cursor = db.execute(
                "INSERT INTO tags(name, color) VALUES (?, ?)", 
                (name, color)
            )
            return cursor.lastrowid
    
    @staticmethod
    def delete(tag_id: int) -> None:
        """Delete a tag."""
        with get_db() as db:
            db.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
