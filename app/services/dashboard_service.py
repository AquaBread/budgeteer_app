"""
Dashboard Service - Business logic for dashboard calculations and data aggregation
"""
from datetime import date
from typing import Dict, List

from app.repositories.budget_repository import BudgetRepository
from app.repositories.category_repository import CategoryGroupRepository
from app.repositories.transaction_repository import TransactionRepository
from app.repositories.user_repository import UserRepository
from app.utils.date_helpers import month_key, month_seq, add_months, month_key_from_ym
from calculations import pro_rata, daily_cap


class DashboardService:
    """Handles business logic for dashboard data and calculations."""
    
    @staticmethod
    def get_dashboard_data(today: date, range_key: str = "1") -> Dict:
        """
        Get all dashboard data including metrics, charts, and trends.
        
        Args:
            today: Current date
            range_key: Range selector ("1", "3", "6", "ytd")
        
        Returns:
            Dictionary containing all dashboard data
        """
        mkey = month_key(today)
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
        
        # Get user salary
        salary_annual = UserRepository.get_salary() or 0
        salary_est = salary_annual // 12
        
        # Income for current month
        income_monthly = TransactionRepository.get_income_for_month(mkey)
        if income_monthly == 0:
            income_monthly = salary_est
        
        # Total budget
        B_total = BudgetRepository.get_total_for_month(mkey)
        
        # Month to date spending
        S_so_far = TransactionRepository.get_spending_for_month(mkey)
        
        # Pro-rata calculations
        pr = pro_rata(B_total, today)
        variance = S_so_far - int(pr["target"])
        cap = daily_cap(B_total, S_so_far, today)
        
        # Monthly savings estimate
        savings_month = income_monthly - S_so_far
        
        # Category breakdown for chart
        cat_rows = BudgetRepository.get_category_breakdown(mkey)
        
        # Group breakdown for table/chart
        group_rows = CategoryGroupRepository.get_group_breakdown(mkey)
        
        # Trend chart data
        trend_data = DashboardService._get_trend_data(months, start_mkey, mkey)
        
        # Top categories in range
        top_cats_range = TransactionRepository.get_top_categories_in_range(start_mkey, mkey)
        
        return {
            "today": today,
            "mkey": mkey,
            "income_monthly": income_monthly,
            "B_total": B_total,
            "S_so_far": S_so_far,
            "variance": variance,
            "cap": cap,
            "savings_month": savings_month,
            "cats": cat_rows,
            "groups": group_rows,
            "range_key": range_key,
            "start_mkey": start_mkey,
            "trend": trend_data["trend"],
            "ma3": trend_data["ma3"],
            "top_cats_range": top_cats_range,
        }
    
    @staticmethod
    def _get_trend_data(months: List[str], start_mkey: str, end_mkey: str) -> Dict:
        """Calculate trend data including moving averages."""
        # Initialize trend map
        trend_map = {
            m: {"mkey": m, "income": 0, "spent": 0}
            for m in months
        }
        
        # Get actual data
        rows = TransactionRepository.get_trend_data(start_mkey, end_mkey)
        
        for r in rows:
            trend_map[r["mkey"]] = {
                "mkey": r["mkey"],
                "income": r["income"],
                "spent": r["spent"],
            }
        
        trend = [trend_map[m] for m in months]
        spent_vals = [r["spent"] for r in trend]
        
        # Moving average for 3 months
        ma3 = []
        for i in range(len(spent_vals)):
            window = spent_vals[max(0, i - 2): i + 1]
            ma3.append(sum(window) / len(window))
        
        return {
            "trend": trend,
            "ma3": ma3
        }
