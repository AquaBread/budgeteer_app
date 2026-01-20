"""
Settings Blueprint - Routes for user settings
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.repositories.user_repository import UserRepository
from app.utils.validators import parse_float, dollars_to_cents, cents_to_dollars


settings_bp = Blueprint('settings', __name__)


@settings_bp.route("/", methods=["GET", "POST"])
def index():
    """User settings page."""
    if request.method == "POST":
        salary = parse_float(request.form.get("salary_annual", "0"), 0)
        UserRepository.update_salary(dollars_to_cents(salary))
        flash("Updated salary.", "success")
        return redirect(url_for("settings.index"))
    
    salary_cents = UserRepository.get_salary()
    return render_template(
        "settings.html", 
        salary_annual=cents_to_dollars(salary_cents)
    )
