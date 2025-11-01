# routes/boards.py
from flask import Blueprint, render_template, request, redirect, url_for, session, flash, jsonify
from functools import wraps
from models.boards_model import (
    get_boards_by_project, get_board, create_board, update_board, delete_board,
    get_tasks_by_board, create_task, get_task, update_task, delete_task, update_task_status
)
from models.project_model import get_project_by_id, get_project_members

boards_bp = Blueprint("boards", __name__, template_folder="../templates/boards")

# ==============================================================  
# AUTH & PERMISSION HELPERS
# ==============================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to access this page.", "error")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)
    return decorated_function


def project_access_required(roles=None):
    """
    Decorator: Check if user has access to project.
    roles: ['owner', 'editor', 'viewer'] — None = any access
    """
    if roles is None:
        roles = ['owner', 'editor', 'viewer']

    def decorator(f):
        @wraps(f)
        def decorated_function(project_id, *args, **kwargs):
            if "user_id" not in session:
                flash("Login required.", "error")
                return redirect(url_for("auth.login"))

            project = get_project_by_id(project_id)
            if not project:
                flash("Project not found.", "error")
                return redirect(url_for("projects.list_projects"))

            members = get_project_members(project_id)
            user_role = next((m['role'] for m in members if m['user_id'] == session['user_id']), None)

            if not user_role or user_role not in roles:
                flash("You don't have permission to access this project.", "error")
                return redirect(url_for("projects.list_projects"))

            # Inject into kwargs
            kwargs['user_role'] = user_role
            kwargs['project'] = project
            return f(project_id, *args, **kwargs)
        return decorated_function
    return decorator


# ========================================
# DELETE BOARD
# ========================================
@boards_bp.route("/boards/<int:board_id>/delete", methods=["POST"])
@login_required
def delete_board_route(board_id):
    board = get_board(board_id)
    if not board:
        flash("Board not found.", "error")
        return redirect(url_for("projects.list_projects"))

    # Permission check: only owner or admin can delete
    members = get_project_members(board['project_id'])
    user_role = next((m['role'] for m in members if m['user_id'] == session['user_id']), None)

    if user_role not in ['owner'] and not session.get('is_admin'):
        flash("You don't have permission to delete this board.", "error")
        return redirect(url_for("boards.board_view", board_id=board_id))

    # Perform delete
    success = delete_board(board_id)
    if success:
        flash("Board deleted successfully.", "success")
        return redirect(url_for("projects.list_projects"))
    else:
        flash("Failed to delete board.", "error")
        return redirect(url_for("boards.board_view", board_id=board_id))


# ==============================================================  
# BOARD ROUTES
# ==============================================================

@boards_bp.route("/projects/<int:project_id>/boards")
@login_required
@project_access_required(roles=['owner', 'editor', 'viewer'])
def list_boards(project_id, **kwargs):
    boards = get_boards_by_project(project_id)
    return render_template(
        "boards/list.html",
        project=kwargs['project'],
        boards=boards,
        user_role=kwargs['user_role']
    )


@boards_bp.route("/projects/<int:project_id>/boards/create", methods=["GET", "POST"])
@login_required
@project_access_required(roles=['owner', 'editor'])
def create_board_route(project_id, **kwargs):
    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description", "")
        if not name:
            flash("Board name is required.", "error")
            return redirect(request.url)

        board_id = create_board(name, description, project_id)
        if board_id:
            flash("Board created!", "success")
            return redirect(url_for("boards.board_view", board_id=board_id))
        flash("Failed to create board.", "error")

    return render_template(
        "boards/create.html",
        project=kwargs['project']
    )


@boards_bp.route("/boards/<int:board_id>/edit", methods=["GET", "POST"])
@login_required
def edit_board_route(board_id):
    board = get_board(board_id)
    if not board:
        flash("Board not found.", "error")
        return redirect(url_for("projects.list_projects"))

    # Check project access
    project = get_project_by_id(board['project_id'])
    members = get_project_members(board['project_id'])
    user_role = next((m['role'] for m in members if m['user_id'] == session['user_id']), None)
    if user_role not in ['owner', 'editor']:
        flash("You can't edit this board.", "error")
        return redirect(url_for("boards.board_view", board_id=board_id))

    if request.method == "POST":
        name = request.form.get("name")
        description = request.form.get("description", "")
        if not name:
            flash("Name is required.", "error")
            return redirect(request.url)

        if update_board(board_id, name, description):
            flash("Board updated!", "success")
            return redirect(url_for("boards.board_view", board_id=board_id))
        flash("Update failed.", "error")

    return render_template("boards/edit.html", board=board, project=project)


# ========================================
# VIEW BOARD
# ========================================
@boards_bp.route("/boards/<int:board_id>")
@login_required
def board_view(board_id):
    board = get_board(board_id)
    if not board:
        flash("Board not found.", "error")
        return redirect(url_for("projects.list_projects"))

    members = get_project_members(board['project_id'])
    user_role = next((m['role'] for m in members if m['user_id'] == session['user_id']), None)
    if not user_role:
        flash("Access denied.", "error")
        return redirect(url_for("projects.list_projects"))

    tasks = get_tasks_by_board(board_id)
    project = get_project_by_id(board['project_id'])

    can_edit = user_role in ['owner', 'editor']

    return render_template(
        "boards/board_view.html",
        board=board,
        tasks=tasks,
        project=project,
        user_role=user_role,
        can_edit=can_edit
    )


# ==============================================================  
# TASK API (JSON) — Drag & Drop + CRUD
# ==============================================================
@boards_bp.route("/boards/<int:board_id>/tasks", methods=["POST"])
@login_required
def create_task_route(board_id):
    import traceback
    try:
        print("Received POST /tasks with board_id:", board_id)
        print("JSON payload:", request.get_json())

        board = get_board(board_id)
        if not board:
            return jsonify(error="Board not found"), 404

        members = get_project_members(board['project_id'])
        user_role = next((m['role'] for m in members if m['user_id'] == session['user_id']), None)
        if user_role not in ['owner', 'editor']:
            return jsonify(error="Permission denied"), 403

        data = request.get_json() or {}
        title = data.get('title', '').strip()
        if not title:
            return jsonify(error="Title is required"), 400

        assigned_to = data.get('assigned_to')
        if assigned_to in [None, ""]:
            assigned_to = None
        else:
            try:
                assigned_to = int(assigned_to)
            except ValueError:
                return jsonify(error="Invalid assignee"), 400

        due_date = data.get('due_date') or None
        status = data.get('status', 'To Do')
        if status not in ['To Do', 'In Progress', 'Review', 'Done']:
            status = 'To Do'

        task = create_task(
            board_id=board_id,
            title=title,
            assigned_to=assigned_to,
            due_date=due_date,
            status=status
        )

        if not task:
            return jsonify(error="Failed to create task"), 500

        return jsonify({
            'id': task['id'],
            'title': task['title'],
            'status': task['status'],
            'assigned_to': task['assigned_to'],
            'assigned_username': task.get('assigned_username'),
            'due_date': task['due_date'],
            'created_at': task['created_at'].isoformat()
        }), 201

    except Exception:
        traceback.print_exc()
        return jsonify(error="Internal Server Error"), 500


@boards_bp.route("/boards/<int:board_id>/tasks/<int:task_id>", methods=["GET"])
@login_required
def get_task_route(board_id, task_id):
    task = get_task(task_id)
    if not task or task['board_id'] != board_id:
        return jsonify(error="Task not found"), 404
    return jsonify(task)


@boards_bp.route("/boards/<int:board_id>/tasks/<int:task_id>", methods=["PUT"])
@login_required
def update_task_route(board_id, task_id):
    task = get_task(task_id)
    if not task or task['board_id'] != board_id:
        return jsonify(error="Not found"), 404

    members = get_project_members(task['board_id'])
    user_role = next((m['role'] for m in members if m['user_id'] == session['user_id']), None)
    if user_role not in ['owner', 'editor']:
        return jsonify(error="No permission"), 403

    data = request.get_json() or {}
    if update_task(task_id, **data):
        return jsonify(success=True)
    return jsonify(error="Update failed"), 500


@boards_bp.route("/boards/<int:board_id>/tasks/<int:task_id>/move", methods=["POST"])
@login_required
def move_task_route(board_id, task_id):
    board = get_board(board_id)
    if not board:
        return jsonify(error="Not found"), 404

    members = get_project_members(board['project_id'])
    user_role = next((m['role'] for m in members if m['user_id'] == session['user_id']), None)
    if not user_role:
        return jsonify(error="Access denied"), 403

    data = request.get_json() or {}
    new_status = data.get("status")
    if new_status not in ['To Do', 'In Progress', 'Review', 'Done']:
        return jsonify(error="Invalid status"), 400

    if update_task_status(task_id, new_status):
        return jsonify(success=True)
    return jsonify(error="Move failed"), 500


@boards_bp.route("/boards/<int:board_id>/tasks/<int:task_id>", methods=["DELETE"])
@login_required
def delete_task_route(board_id, task_id):
    board = get_board(board_id)
    if not board:
        return jsonify(error="Not found"), 404

    members = get_project_members(board['project_id'])
    user_role = next((m['role'] for m in members if m['user_id'] == session['user_id']), None)
    if user_role not in ['owner', 'editor']:
        return jsonify(error="Permission denied"), 403

    if delete_task(task_id):
        return jsonify(success=True)
    return jsonify(error="Delete failed"), 500
