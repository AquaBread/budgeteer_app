"""
Accounts Blueprint - Routes for account management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.repositories.account_repository import AccountRepository
from app.utils.validators import validate_account_type


accounts_bp = Blueprint('accounts', __name__)


@accounts_bp.route("/", methods=["GET", "POST"])
def index():
    """List all accounts and handle account creation."""
    if request.method == "POST":
        name = request.form["name"]
        typ = request.form["type"]
        
        # Validate allowed types
        if not validate_account_type(typ):
            flash("Invalid account type.", "error")
            return redirect(url_for("accounts.index"))
        
        AccountRepository.create(name, typ)
        flash("Account added.", "success")
        return redirect(url_for("accounts.index"))
    
    accts = AccountRepository.get_all()
    return render_template("accounts.html", accounts=accts)


@accounts_bp.post("/<int:account_id>/update")
def update(account_id):
    """Update an existing account."""
    name = request.form["name"].strip()
    typ = request.form["type"]
    
    if not validate_account_type(typ):
        flash("Invalid account type.", "error")
        return redirect(url_for("accounts.index"))
    
    AccountRepository.update(account_id, name, typ)
    flash("Account updated.", "success")
    return redirect(url_for("accounts.index"))


@accounts_bp.post("/<int:account_id>/delete")
def delete(account_id):
    """Delete an account (cascades to related records via foreign keys)."""
    AccountRepository.delete(account_id)
    flash("Account deleted.", "success")
    return redirect(url_for("accounts.index"))
