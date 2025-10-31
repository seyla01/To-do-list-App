# routes/auth_routes.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from models.users_model import create_user, get_user_by_email, verify_password

auth_bp = Blueprint("auth", __name__, template_folder="../templates/auth")

# ====================
# Register Route
# ====================
@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        email = request.form["email"]
        password = request.form["password"]
        confirm = request.form["confirm_password"]

        if password != confirm:
            flash("Passwords do not match!", "error")
            return redirect(url_for("auth.register"))

        if get_user_by_email(email):
            flash("Email already exists!", "error")
            return redirect(url_for("auth.register"))

        create_user(username, email, password)
        flash("Account created successfully! Please login.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

# ====================
# Login Route
# ====================
@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]

        user = get_user_by_email(email)
        if user and verify_password(user, password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            flash(f"Welcome back, {user['username']}!", "success")
            return redirect(url_for("boards.list_boards", project_id=1))
        else:
            flash("Invalid credentials!", "error")
            return redirect(url_for("auth.login"))

    return render_template("login.html")

# ====================
# Logout Route
# ====================
@auth_bp.route("/logout")
def logout():
    session.clear()
    flash("Logged out successfully.", "success")
    return redirect(url_for("auth.login"))
