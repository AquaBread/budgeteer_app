"""
Recurring Service - Business logic for recurring transactions
"""
from calendar import monthrange
from datetime import date
from typing import List

from app.repositories.recurring_repository import RecurringRepository
from app.repositories.transaction_repository import TransactionRepository


class RecurringService:
    """Handles business logic for recurring transactions."""
    
    @staticmethod
    def apply_recurring_for_month(today: date) -> None:
        """
        Ensures recurring expenses up to today exist as transactions for this month.
        Uses calendar.monthrange to tie day_of_month to last day of month.
        
        Python docs: https://docs.python.org/3/library/calendar.html#calendar.monthrange
        """
        year, month = today.year, today.month
        days_in_month = monthrange(year, month)[1]
        
        recs = RecurringRepository.get_all_active()
        
        for r in recs:
            # Tie day_of_month to last day of month
            d = min(r["day_of_month"], days_in_month)
            
            # Only create if that day is <= today
            if d > today.day:
                continue
            
            dt_str = f"{year:04d}-{month:02d}-{d:02d}"
            
            # Check if we already created a transaction for this recurring item on that date
            if TransactionRepository.check_exists_for_recurring(r["id"], dt_str):
                continue
            
            # Convert stored amount into signed transaction amount
            direction = r["direction"]
            amt = abs(r["amount_cents"])
            if direction == "in":
                amt = amt
            else:
                amt = -amt
            
            TransactionRepository.create(
                account_id=r["account_id"],
                date=dt_str,
                description=r["name"],
                amount_cents=amt,
                category_id=r["category_id"],
                recurring_id=r["id"]
            )
    
    @staticmethod
    def create_recurring(name: str, account_id: int, category_id: int, 
                        amount: float, day_of_month: int, direction: str, 
                        active: bool = True) -> int:
        """Create a new recurring transaction."""
        amount_cents = int(round(amount * 100))
        active_int = 1 if active else 0
        
        return RecurringRepository.create(
            name=name,
            account_id=account_id,
            category_id=category_id,
            amount_cents=amount_cents,
            day_of_month=day_of_month,
            direction=direction,
            active=active_int
        )
    
    @staticmethod
    def get_all_with_details() -> List[dict]:
        """Get all recurring items with account and category details."""
        return RecurringRepository.get_all_with_details()
    
    @staticmethod
    def toggle_active(recurring_id: int) -> None:
        """Toggle the active status of a recurring item."""
        RecurringRepository.toggle_active(recurring_id)
    
    @staticmethod
    def delete(recurring_id: int) -> None:
        """Delete a recurring item."""
        RecurringRepository.delete(recurring_id)
