from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from functools import wraps
from app.models.user import User
from app import db

admin_bp = Blueprint('admin', __name__)

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('You need to be an admin to access this page.', 'error')
            return redirect(url_for('main.index'))
        return f(*args, **kwargs)
    return decorated_function

@admin_bp.route('/admin')
@login_required
@admin_required
def admin_dashboard():
    users = User.query.all()
    return render_template('admin/dashboard.html', users=users)

@admin_bp.route('/admin/user/<int:user_id>', methods=['POST'])
@login_required
@admin_required
def update_user(user_id):
    user = User.query.get_or_404(user_id)
    action = request.form.get('action')

    if action == 'update_role':
        new_role = request.form.get('role')
        if new_role in ['admin', 'korea', 'china', 'global', 'none']:
            user.role = new_role
            db.session.commit()
            flash(f'Updated role for user {user.username} to {new_role}', 'success')

    elif action == 'delete':
        if user != current_user:  # Prevent admin from deleting themselves
            db.session.delete(user)
            db.session.commit()
            flash(f'Deleted user {user.username}', 'success')
        else:
            flash('You cannot delete your own admin account', 'error')

    return redirect(url_for('admin.admin_dashboard'))

@admin_bp.route('/admin/user/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    username = request.form.get('username')
    email = request.form.get('email')
    password = request.form.get('password')
    role = request.form.get('role')

    if User.query.filter_by(username=username).first():
        flash('Username already exists', 'error')
        return redirect(url_for('admin.admin_dashboard'))

    if User.query.filter_by(email=email).first():
        flash('Email already exists', 'error')
        return redirect(url_for('admin.admin_dashboard'))

    new_user = User(
        username=username,
        email=email,
        role=role
    )
    new_user.set_password(password)

    db.session.add(new_user)
    db.session.commit()

    flash(f'Created new user {username}', 'success')
    return redirect(url_for('admin.admin_dashboard'))
