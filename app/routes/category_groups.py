"""
Category Groups Blueprint - Routes for category group management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3

from app.repositories.category_repository import CategoryRepository, CategoryGroupRepository
from app.utils.validators import validate_group_type, parse_int


category_groups_bp = Blueprint('category_groups', __name__)


@category_groups_bp.route("/", methods=["GET", "POST"])
def index():
    """List category groups and handle group creation."""
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        sort_raw = request.form.get("sort_order", "").strip() or None
        gtype = request.form.get("type", "expense")
        
        if not validate_group_type(gtype):
            flash("Invalid group type.", "error")
            return redirect(url_for("category_groups.index"))
        
        if not name:
            flash("Group name is required.", "error")
            return redirect(url_for("category_groups.index"))
        
        try:
            sort_order = parse_int(sort_raw, None) if sort_raw is not None else None
            CategoryGroupRepository.create(name, sort_order, gtype)
            flash("Category group added.", "success")
        except ValueError:
            flash("Sort order must be a number.", "error")
        except sqlite3.IntegrityError:
            flash("Group name must be unique.", "error")
        
        return redirect(url_for("category_groups.index"))
    
    groups = CategoryGroupRepository.get_all()
    cats = CategoryGroupRepository.get_categories_with_groups()
    
    return render_template("category_groups.html", groups=groups, cats=cats)


@category_groups_bp.post("/categories/<int:cat_id>/set-group")
def set_category_group(cat_id):
    """Set the group for a category."""
    group_raw = request.form.get("group_id", "")
    group_id = parse_int(group_raw, None) if group_raw else None
    
    CategoryRepository.set_group(cat_id, group_id)
    flash("Category group updated.", "success")
    return redirect(url_for("category_groups.index"))


@category_groups_bp.post("/<int:group_id>/delete")
def delete(group_id):
    """Delete a category group (unassigns categories first)."""
    CategoryGroupRepository.delete(group_id)
    flash("Category group deleted.", "success")
    return redirect(url_for("category_groups.index"))
