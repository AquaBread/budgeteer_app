"""
Categories Blueprint - Routes for category management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3

from app.repositories.category_repository import CategoryRepository


categories_bp = Blueprint('categories', __name__)


@categories_bp.route('/', methods=['GET', 'POST'])
def index():
    """List categories and handle category creation."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        if not name:
            flash("Category name is required.", "error")
            return redirect(url_for('categories.index'))
        try:
            CategoryRepository.create(name)
            flash("Category added.", "success")
        except sqlite3.IntegrityError:
            flash("That category already exists.", "error")
        return redirect(url_for('categories.index'))
    
    cats = CategoryRepository.get_all()
    return render_template('categories.html', cats=cats)


@categories_bp.post('/<int:cat_id>/delete')
def delete(cat_id):
    """Delete a category if not in use."""
    # Check if recurring requires this category
    if CategoryRepository.is_used_by_recurring(cat_id):
        flash("Category is used by a recurring item. Delete/disable that recurring item first.", "error")
        return redirect(url_for('categories.index'))
    
    CategoryRepository.delete(cat_id)
    flash("Category deleted.", "success")
    return redirect(url_for('categories.index'))
