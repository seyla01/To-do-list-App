from flask import Blueprint, render_template, request, redirect, url_for, session, flash
from functools import wraps
from models.boards_model import (
    get_boards_by_project,
    create_board,
    update_board,
    get_board,
    get_tasks_by_board
)

boards_bp = Blueprint("boards", __name__, template_folder="../templates/boards")

# ===========================
# Auth Decorator
# ===========================
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function

# ===========================
# List all boards for a project
# ===========================
@boards_bp.route("/projects/<int:project_id>/boards")
@login_required
def list_boards(project_id):
    boards = get_boards_by_project(project_id)
    if not boards:
        flash("No boards found for this project yet.", "info")
    return render_template("boards/boards_list.html", boards=boards, project_id=project_id)

# ===========================
# Create a board
# ===========================
@boards_bp.route("/projects/<int:project_id>/boards/create", methods=["GET", "POST"])
@login_required
def board_create(project_id):
    if request.method == "POST":
        name = request.form.get("name").strip()
        description = request.form.get("description").strip()
        if not name:
            flash("Board name is required.", "error")
            return render_template("boards/board_form.html", project_id=project_id, board=None)

        # Optional: track creator if 'created_by' column exists
        create_board(name, description, project_id)
        flash("Board created successfully!", "success")
        return redirect(url_for("boards.list_boards", project_id=project_id))
    
    return render_template("boards/board_form.html", project_id=project_id, board=None)

# ===========================
# Edit a board
# ===========================
@boards_bp.route("/boards/<int:board_id>/edit", methods=["GET", "POST"])
@login_required
def board_edit(board_id):
    board = get_board(board_id)
    if not board:
        flash("Board not found!", "error")
        return redirect(url_for("boards.list_boards", project_id=1))  # fallback

    # Optional: enforce edit permissions if you track created_by
    # if board['created_by'] != session['user_id']:
    #     flash("You cannot edit this board.", "error")
    #     return redirect(url_for("boards.list_boards", project_id=board['project_id']))

    if request.method == "POST":
        name = request.form.get("name").strip()
        description = request.form.get("description").strip()
        if not name:
            flash("Board name cannot be empty.", "error")
            return render_template("boards/board_form.html", board=board)

        update_board(board_id, name, description)
        flash("Board updated successfully!", "success")
        return redirect(url_for("boards.list_boards", project_id=board["project_id"]))

    return render_template("boards/board_form.html", board=board)

# ===========================
# View board tasks by status (Kanban)
# ===========================
@boards_bp.route("/boards/<int:board_id>")
@login_required
def board_view(board_id):
    board = get_board(board_id)
    if not board:
        flash("Board not found!", "error")
        return redirect(url_for("boards.list_boards", project_id=1))  # fallback

    tasks = get_tasks_by_board(board_id)
    return render_template("boards/board_view.html", board=board, tasks=tasks)
