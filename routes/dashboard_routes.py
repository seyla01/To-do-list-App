# routes/dashboard_routes.py
from flask import Blueprint, render_template, session, redirect, url_for, flash
from models.project_model import get_project_members
from models.boards_model import get_boards_by_project, get_tasks_by_board

dashboard_bp = Blueprint('dashboard', __name__, template_folder='../templates')

@dashboard_bp.route('/')
def dashboard():
    if 'user_id' not in session:
        flash("Please log in to continue.", "error")
        return redirect(url_for('auth.login'))

    user_id = session['user_id']
    projects = get_project_members(user_id)

    # Task stats
    stats = {'To Do': 0, 'In Progress': 0, 'Review': 0, 'Done': 0}
    for project in projects:
        boards = get_boards_by_project(project['id'])
        for board in boards:
            tasks = get_tasks_by_board(board['id'])
            for status, task_list in tasks.items():
                stats[status] += len(task_list)

    return render_template('dashboard/dashboard.html', projects=projects, stats=stats)