# ==============================================================
# FILE: app.py
# PURPOSE: Main Flask app for GitBoard-style Task Management
# ==============================================================

from flask import Flask, redirect, url_for
from dotenv import load_dotenv
import os


# Load .env
load_dotenv()

# ================================
# 🔹 Flask App Configuration
# ================================
app = Flask(__name__)
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "supersecretkey123")

# ================================
# 🔹 Import Blueprints
# ================================
from routes import board_routes  # Make sure you have routes/__init__.py to load them
app.register_blueprint(board_routes.boards_bp)

from routes import auth_routes
app.register_blueprint(auth_routes.auth_bp)

# Optional: you can add projects, tasks, users routes here as well
# from routes import projects_routes, tasks_routes, users_routes
# app.register_blueprint(projects_routes.projects_bp)
# app.register_blueprint(tasks_routes.tasks_bp)
# app.register_blueprint(users_routes.users_bp)

# ================================
# 🔹 Home / Index Route
# ================================
@app.route("/")
def home():
    return redirect(url_for("boards.list_boards", project_id=1))  # default project_id=1 for testing

# ================================
# 🔹 Run App
# ================================
if __name__ == "__main__":
    # Optional: enable debug for development
    app.run(debug=True, host="0.0.0.0", port=5000)


















    
