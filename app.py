# ==============================================================
# FILE: app.py
# PURPOSE: Main Flask entry-point – factory pattern, secure, production-ready
# ==============================================================

import os
from datetime import datetime
from flask import Flask, redirect, url_for, render_template, session, flash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# ================================
# CREATE APP (Factory Pattern)
# ================================
def create_app():
    app = Flask(__name__, template_folder="templates", static_folder="static")

    # -----------------------------
    # CONFIGURATION
    # -----------------------------
    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-secret-change-in-prod-123"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SECURE=os.getenv("FLASK_ENV") == "production",
        SESSION_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=3600,  # 1 hour
        DEBUG=os.getenv("FLASK_ENV") == "development"
    )

    # -----------------------------
    # TEMPLATE FILTERS
    # -----------------------------
    @app.template_filter("datetime")
    def format_datetime(value, fmt="%b %d, %Y"):
        return value.strftime(fmt) if value else ""

    @app.template_filter("avatar")
    def avatar_url(username):
        return f"https://ui-avatars.com/api/?name={username}&background=random&bold=true"

    # -----------------------------
    # CONTEXT PROCESSORS
    # -----------------------------
    # Make `now()` available in all templates
    @app.context_processor
    def inject_now():
        return {'now': datetime.utcnow}

    # -----------------------------
    # ERROR HANDLERS
    # -----------------------------
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        return render_template("errors/500.html"), 500

    # -----------------------------
    # BLUEPRINTS
    # -----------------------------
    from routes.auth_routes import auth_bp
    from routes.board_routes import boards_bp

    app.register_blueprint(boards_bp, url_prefix="/boards")

    from routes.dashboard_routes import dashboard_bp
    from routes.board_routes import boards_bp

    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(dashboard_bp, url_prefix="/dashboard")

    # -----------------------------
    # ROOT ROUTE
    # -----------------------------
    @app.route("/")
    def index():
        if session.get("user_id"):
            return redirect(url_for("dashboard.dashboard"))
        return redirect(url_for("auth.login"))

    # -----------------------------
    # HEALTH CHECK
    # -----------------------------
    @app.route("/health")
    def health():
        return {
            "status": "healthy",
            "app": "GitBoard",
            "timestamp": datetime.utcnow().isoformat()
        }, 200

    # -----------------------------
    # LOGIN REQUIRED DECORATOR (Global)
    # -----------------------------
    from functools import wraps

    def login_required(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get("user_id"):
                flash("Please log in to continue.", "error")
                return redirect(url_for("auth.login"))
            return f(*args, **kwargs)
        return decorated_function

    app.login_required = login_required  # ← Make available globally

    return app


# ================================
# RUN APP
# ================================
if __name__ == "__main__":
    app = create_app()
    host = os.getenv("FLASK_HOST", "127.0.0.1")
    port = int(os.getenv("FLASK_PORT", 5000))
    debug = os.getenv("FLASK_ENV") == "development"

    print(f"GitBoard running at http://{host}:{port}")
    print(f"Mode: {'Development' if debug else 'Production'}")
    app.run(host=host, port=port, debug=debug, use_reloader=debug)
