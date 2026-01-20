"""
Category Group Assignment Route - Separate route for setting category groups
"""
from flask import request, redirect, url_for, flash

from app.repositories.category_repository import CategoryRepository
from app.routes.category_groups import category_groups_bp
from app.utils.validators import parse_int


@category_groups_bp.post("/categories/<int:cat_id>/set-group")
def set_category_group(cat_id):
    """Set the group for a category."""
    group_raw = request.form.get("group_id", "")
    group_id = parse_int(group_raw, None) if group_raw else None
    
    CategoryRepository.set_group(cat_id, group_id)
    flash("Category group updated.", "success")
    return redirect(url_for("category_groups.index"))
