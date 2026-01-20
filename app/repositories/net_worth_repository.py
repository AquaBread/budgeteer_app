"""
Net Worth Repository - Database queries for account balances and net worth
"""
from typing import List, Dict
from db import get_db


class NetWorthRepository:
    """Handles all database operations for net worth tracking."""
    
    @staticmethod
    def upsert_balance(account_id: int, as_of: str, balance_cents: int) -> None:
        """Insert or update an account balance snapshot."""
        with get_db() as db:
            db.execute(
                """
                INSERT INTO account_balances(account_id, as_of, balance_cents)
                VALUES (?, ?, ?)
                ON CONFLICT(account_id, as_of)
                DO UPDATE SET balance_cents = excluded.balance_cents
                """,
                (account_id, as_of, balance_cents),
            )
    
    @staticmethod
    def get_balances_for_date(as_of: str) -> Dict[int, int]:
        """Get all account balances for a specific date."""
        with get_db() as db:
            rows = db.execute(
                """
                SELECT ab.account_id, ab.balance_cents
                FROM account_balances ab
                WHERE ab.as_of = ?
                """,
                (as_of,),
            ).fetchall()
            return {r["account_id"]: r["balance_cents"] for r in rows}
    
    @staticmethod
    def get_summary_for_date(as_of: str) -> dict:
        """Get assets, liabilities, and net worth for a specific date."""
        with get_db() as db:
            result = db.execute(
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
            
            assets = result["assets"] if result else 0
            liabilities = result["liabilities"] if result else 0
            
            return {
                "assets": assets,
                "liabilities": liabilities,
                "net": assets - liabilities
            }
    
    @staticmethod
    def get_history() -> List[dict]:
        """Get net worth history over time."""
        with get_db() as db:
            return db.execute(
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
