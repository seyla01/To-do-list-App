from models.db import get_db



# ===============================
# Get all boards for a project
# ===============================
def get_boards_by_project(project_id):
    conn = get_db()
    if not conn:
        return []

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM boards WHERE project_id=%s ORDER BY created_at DESC", (project_id,))
    boards = cursor.fetchall()

    # Add task counts for each board
    for board in boards:
        cursor.execute("""
            SELECT 
                SUM(status='To Do') AS todo,
                SUM(status='In Progress') AS in_progress,
                SUM(status='Review') AS review,
                SUM(status='Done') AS done
            FROM tasks
            WHERE board_id=%s
        """, (board['id'],))
        board['task_counts'] = cursor.fetchone()

    cursor.close()
    conn.close()
    return boards

# ===============================
# Get single board by ID
# ===============================
def get_board(board_id):
    conn = get_db()
    if not conn:
        return None

    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM boards WHERE id=%s", (board_id,))
    board = cursor.fetchone()
    cursor.close()
    conn.close()
    return board

# ===============================
# Create a new board
# ===============================
def create_board(name, description, project_id):
    conn = get_db()
    if not conn:
        return False

    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO boards (name, description, project_id) VALUES (%s, %s, %s)",
        (name, description, project_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True

# ===============================
# Update an existing board
# ===============================
def update_board(board_id, name, description):
    conn = get_db()
    if not conn:
        return False

    cursor = conn.cursor()
    cursor.execute(
        "UPDATE boards SET name=%s, description=%s WHERE id=%s",
        (name, description, board_id)
    )
    conn.commit()
    cursor.close()
    conn.close()
    return True

# ===============================
# Get tasks grouped by status for a board
# ===============================
def get_tasks_by_board(board_id):
    conn = get_db()
    if not conn:
        return {}

    cursor = conn.cursor(dictionary=True)
    statuses = ['To Do', 'In Progress', 'Review', 'Done']
    tasks_by_status = {}

    for status in statuses:
        cursor.execute(
            "SELECT * FROM tasks WHERE board_id=%s AND status=%s ORDER BY due_date ASC",
            (board_id, status)
        )
        tasks_by_status[status] = cursor.fetchall()

    cursor.close()
    conn.close()
    return tasks_by_status
