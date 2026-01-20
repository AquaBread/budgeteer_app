"""
Net Worth Blueprint - Routes for net worth tracking
"""
from datetime import date
from flask import Blueprint, render_template, request, redirect, url_for, flash

from app.repositories.account_repository import AccountRepository
from app.repositories.net_worth_repository import NetWorthRepository
from app.utils.validators import parse_float, dollars_to_cents


net_worth_bp = Blueprint('net_worth', __name__)


@net_worth_bp.route("/", methods=["GET", "POST"])
def index():
    """Net worth tracking page with balance snapshots."""
    today = date.today().isoformat()
    as_of = request.form.get("as_of") if request.method == "POST" else request.args.get("as_of")
    as_of = as_of or today
    
    accounts = AccountRepository.get_all_ordered_by_type()
    
    if request.method == "POST":
        # Upsert a balance for each account for the chosen date
        for a in accounts:
            raw = request.form.get(f"bal_{a['id']}", "").strip()
            if raw == "":
                continue
            
            amount = parse_float(raw, None)
            if amount is None or amount < 0:
                flash(f"Invalid balance for {a['name']}. Use a non-negative number.", "error")
                return redirect(url_for("net_worth.index", as_of=as_of))
            
            cents = dollars_to_cents(amount)
            NetWorthRepository.upsert_balance(a["id"], as_of, cents)
        
        flash(f"Saved balances for {as_of}.", "success")
        return redirect(url_for("net_worth.index", as_of=as_of))
    
    # Pull balances for that date to prefill form
    bal_map = NetWorthRepository.get_balances_for_date(as_of)
    
    # Compute assets/liabilities/net at the selected as_of date
    summary = NetWorthRepository.get_summary_for_date(as_of)
    
    # History points
    history = NetWorthRepository.get_history()
    
    return render_template(
        "net_worth.html",
        as_of=as_of,
        accounts=accounts,
        bal_map=bal_map,
        assets=summary["assets"],
        liabilities=summary["liabilities"],
        net=summary["net"],
        history=history,
    )
