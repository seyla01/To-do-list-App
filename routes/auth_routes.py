# routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from werkzeug.security import generate_password_hash, check_password_hash
from models.users_model import create_user, get_user_by_username, get_user_by_id

auth_bp = Blueprint('auth', __name__, template_folder='../templates/auth')

# ========================================
# REGISTER
# ========================================
@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username'].strip()
        email = request.form['email'].strip()
        password = request.form['password']
        role = request.form.get('role', 'user')  # default: user

        # Validate
        if not username or not password or not email:
            flash('All fields are required.', 'error')
            return redirect(url_for('auth.register'))

        if get_user_by_username(username):
            flash('Username already exists.', 'error')
            return redirect(url_for('auth.register'))

        # ALWAYS HASH PASSWORD (even for admin)
        hashed_pw = generate_password_hash(password)

        # Create user
        user_id = create_user(username, email, hashed_pw, role)
        if user_id:
            flash('Registered successfully! Please login.', 'success')
            return redirect(url_for('auth.login'))
        else:
            flash('Registration failed. Try again.', 'error')

    return render_template('auth/register.html')


# ========================================
# LOGIN
# ========================================
@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username'].strip()
        password = request.form['password']
        user = get_user_by_username(username)

        if user:
            # Admin login bypasses password check
            if user['role'] == 'admin' or check_password_hash(user['password_hash'], password):
                # Login success
                session['user_id'] = user['id']
                session['username'] = user['username']
                session['role'] = user['role']
                session['is_admin'] = (user['role'] == 'admin')  # ← Easy admin check

                flash('Logged in successfully!', 'success')
                return redirect(url_for('dashboard.dashboard'))

        # If user not found or password invalid (for non-admin)
        flash('Invalid username or password.', 'error')

    return render_template('auth/login.html')


# ========================================
# LOGOUT
# ========================================
@auth_bp.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))


# ========================================
# PROFILE
# ========================================
@auth_bp.route('/profile')
def profile():
    if 'user_id' not in session:
        flash('Please log in to view your profile.', 'error')
        return redirect(url_for('auth.login'))

    user = get_user_by_id(session['user_id'])
    if not user:
        flash('User not found.', 'error')
        return redirect(url_for('auth.login'))

    return render_template('auth/profile.html', user=user)


# ========================================
# ADMIN CHECK DECORATOR (Optional)
# ========================================
from functools import wraps

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            flash('Admin access required.', 'error')
            return redirect(url_for('dashboard.dashboard'))
        return f(*args, **kwargs)
    return decorated_function