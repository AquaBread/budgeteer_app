"""
Tags Blueprint - Routes for tag management
"""
from flask import Blueprint, render_template, request, redirect, url_for, flash
import sqlite3

from app.repositories.tag_repository import TagRepository
from app.utils.validators import validate_hex_color


tags_bp = Blueprint('tags', __name__)


@tags_bp.route("/", methods=["GET", "POST"])
def index():
    """List tags and handle tag creation."""
    if request.method == "POST":
        name = (request.form.get("name") or "").strip()
        color = (request.form.get("color") or "").strip() or "#64748b"
        
        if not name:
            flash("Tag name is required.", "error")
            return redirect(url_for("tags.index"))
        
        if not name.startswith("#"):
            name = "#" + name
        
        if not validate_hex_color(color):
            flash("Color must be a valid hex value like #ff0000.", "error")
            return redirect(url_for("tags.index"))
        
        try:
            TagRepository.create(name, color)
            flash("Tag created.", "success")
        except sqlite3.IntegrityError:
            flash("That tag already exists.", "error")
        
        return redirect(url_for("tags.index"))
    
    tags = TagRepository.get_all()
    return render_template("tags.html", tags=tags)


@tags_bp.post("/<int:tag_id>/delete")
def delete(tag_id):
    """Delete a tag."""
    TagRepository.delete(tag_id)
    flash("Tag deleted.", "success")
    return redirect(url_for("tags.index"))
