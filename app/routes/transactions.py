"""
Transactions Blueprint - Routes for transaction management
"""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.repositories.account_repository import AccountRepository
from app.repositories.category_repository import CategoryRepository
from app.repositories.tag_repository import TagRepository
from app.repositories.transaction_repository import TransactionRepository
from app.services.recurring_service import RecurringService
from app.utils.validators import validate_direction, parse_float, parse_int, dollars_to_cents


transactions_bp = Blueprint('transactions', __name__)


@transactions_bp.route("/", methods=["GET", "POST"])
def index():
    """List transactions and handle transaction creation."""
    today = date.today()
    
    # Apply recurring transactions
    RecurringService.apply_recurring_for_month(today)
    
    if request.method == "POST":
        # Validate amount
        amount_raw = request.form.get("amount", "").strip()
        if not amount_raw:
            flash("Amount is required.", "error")
            return redirect(url_for("transactions.index"))
        
        amount = parse_float(amount_raw, None)
        if amount is None:
            flash("Amount must be a number.", "error")
            return redirect(url_for("transactions.index"))
        
        # Validate category
        category_raw = request.form.get("category_id", "").strip()
        if not category_raw:
            flash("Please choose a category for each transaction.", "error")
            return redirect(url_for("transactions.index"))
        
        category_id = parse_int(category_raw, None)
        if category_id is None:
            flash("Invalid category.", "error")
            return redirect(url_for("transactions.index"))
        
        # Core fields
        account_id = int(request.form["account_id"])
        date_ = request.form["date"]
        desc = request.form.get("description")
        
        direction = request.form.get("direction", "out")
        if not validate_direction(direction):
            flash("Invalid direction.", "error")
            return redirect(url_for("transactions.index"))
        
        # Cents sign convention
        cents = dollars_to_cents(amount)
        if direction == "out":
            cents = -abs(cents)
        else:
            cents = abs(cents)
        
        # Insert transaction
        tx_id = TransactionRepository.create(
            account_id=account_id,
            date=date_,
            description=desc,
            amount_cents=cents,
            category_id=category_id
        )
        
        # Attach tags
        tag_ids = request.form.getlist("tag_ids")
        tag_ids_int = [parse_int(tid, None) for tid in tag_ids]
        tag_ids_int = [tid for tid in tag_ids_int if tid is not None]
        
        if tag_ids_int:
            TransactionRepository.attach_tags(tx_id, tag_ids_int)
        
        flash("Transaction added.", "success")
        return redirect(url_for("transactions.index"))
    
    # GET: render page
    tags = TagRepository.get_all()
    tx = TransactionRepository.get_recent()
    cats = CategoryRepository.get_all_with_groups()
    accts = AccountRepository.get_all()
    
    return render_template("transactions.html", tx=tx, cats=cats, accts=accts, tags=tags)


@transactions_bp.post("/<int:tx_id>/delete")
def delete(tx_id):
    """Delete a transaction."""
    TransactionRepository.delete(tx_id)
    flash("Transaction deleted.", "success")
    return redirect(url_for("transactions.index"))
