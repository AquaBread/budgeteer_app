"""
Budgets Blueprint - Routes for budget management
"""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.repositories.budget_repository import BudgetRepository
from app.repositories.category_repository import CategoryRepository
from app.utils.date_helpers import prev_month_key
from app.utils.validators import parse_float, dollars_to_cents
from calculations import month_key


budgets_bp = Blueprint('budgets', __name__)


@budgets_bp.route('/', methods=['GET', 'POST'])
def index():
    """Budget management page with rollover suggestions."""
    today = date.today()
    month = request.args.get('month') or month_key(today)
    
    if request.method == 'POST':
        month = request.form['month']
        action = request.form.get('action', 'save')
        
        if action == 'clear':
            BudgetRepository.clear_month(month)
            flash(f'Cleared all budgets for {month}.', 'success')
            return redirect(url_for('budgets.index', month=month))
        
        # Save/upsert budgets
        items = []
        for key, val in request.form.items():
            if key.startswith('cat_'):
                cat_id = int(key.split('_', 1)[1])
                amt = parse_float(val, 0)
                items.append((month, cat_id, dollars_to_cents(amt)))
        
        for m, cid, cents in items:
            BudgetRepository.upsert(m, cid, cents)
        
        flash('Budgets saved.', 'success')
        return redirect(url_for('budgets.index', month=month))
    
    # GET: show budgets + rollover suggestions
    cats = CategoryRepository.get_all_with_groups()
    existing = BudgetRepository.get_budget_map(month)
    prev_month = prev_month_key(month)
    
    # Rollover = last_month_budget - last_month_spent
    prev_rows = BudgetRepository.get_previous_month_data(prev_month)
    
    rollover = {}
    suggested = {}
    
    for row in prev_rows:
        cid = row['category_id']
        B_prev = row['budget_cents']
        S_prev = row['spent_cents']
        
        delta = B_prev - S_prev
        rollover[cid] = delta
        
        # Only autosuggest if user hasn't already set this month's value
        if cid not in existing:
            suggested_budget = B_prev + delta
            suggested[cid] = max(0, suggested_budget)
    
    return render_template(
        'budgets.html',
        month=month,
        cats=cats,
        existing=existing,
        rollover=rollover,
        suggested=suggested,
        prev_month=prev_month,
    )
