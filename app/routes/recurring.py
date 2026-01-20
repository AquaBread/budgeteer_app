"""
Recurring Blueprint - Routes for recurring transaction management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.services.recurring_service import RecurringService
from app.utils.validators import validate_direction, parse_float, parse_int


recurring_bp = Blueprint('recurring', __name__)


@recurring_bp.route("/", methods=["GET", "POST"])
def index():
    """List recurring items and handle creation."""
    if request.method == "POST":
        # Validate category is present
        category_raw = request.form.get('category_id', '')
        if not category_raw:
            flash("Category is required for recurring items.", "error")
            return redirect(url_for('recurring.index'))
        category_id = parse_int(category_raw, None)
        if category_id is None:
            flash("Invalid category.", "error")
            return redirect(url_for('recurring.index'))
        
        # Validate direction
        direction = request.form.get('direction', 'out')
        if not validate_direction(direction):
            flash("Invalid direction.", "error")
            return redirect(url_for('recurring.index'))
        
        # Core fields
        name = request.form["name"]
        account_id = int(request.form["account_id"])
        amount = parse_float(request.form["amount"], 0)
        day_of_month = int(request.form["day_of_month"])
        active = request.form.get("active") == "on"
        
        RecurringService.create_recurring(
            name=name,
            account_id=account_id,
            category_id=category_id,
            amount=amount,
            day_of_month=day_of_month,
            direction=direction,
            active=active
        )
        
        flash("Recurring item added.", "success")
        return redirect(url_for("recurring.index"))
    
    # Render recurring list + form dropdowns
    recs = RecurringService.get_all_with_details()
    accts = AccountRepository.get_all()
    cats = CategoryRepository.get_all_with_groups()
    
    return render_template("recurring.html", recs=recs, accts=accts, cats=cats)


@recurring_bp.post("/<int:rec_id>/toggle")
def toggle(rec_id):
    """Toggle the active status of a recurring item."""
    RecurringService.toggle_active(rec_id)
    flash("Recurring item updated.", "success")
    return redirect(url_for("recurring.index"))


@recurring_bp.post("/<int:rec_id>/delete")
def delete(rec_id):
    """Delete a recurring item."""
    RecurringService.delete(rec_id)
    flash("Recurring item deleted.", "success")
    return redirect(url_for("recurring.index"))
