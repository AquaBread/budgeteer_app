"""
Dashboard Blueprint - Routes for the main dashboard
"""
from datetime import date
from flask import Blueprint, render_template, request

from app.services.dashboard_service import DashboardService
from app.services.recurring_service import RecurringService


dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route("/")
def index():
    """Main dashboard page with financial overview and charts."""
    today = date.today()
    
    # Apply recurring transactions for the current month
    RecurringService.apply_recurring_for_month(today)
    
    # Get range selector
    range_key = request.args.get("range", "1")  # "1", "3", "6", "ytd"
    
    # Get all dashboard data
    data = DashboardService.get_dashboard_data(today, range_key)
    
    return render_template('index.html', **data)
