from flask import Blueprint, render_template
from flask_login import login_required, current_user

admin_bp = Blueprint('admin', __name__)

@admin_bp.before_request
@login_required
def ensure_admin():
    if not current_user.is_admin:
        # For simplicity, returning a message or redirecting
        return "Access Denied", 403

@admin_bp.route('/')
def index():
    return render_template('admin/dashboard.html')

@admin_bp.route('/users')
def users():
    return render_template('admin/users.html')

@admin_bp.route('/settings')
def settings():
    return render_template('admin/settings.html')