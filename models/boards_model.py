# models/boards_model.py
from db import get_db
from typing import List, Dict, Optional, Any


# ===============================
# Get all boards for a project
# ===============================
def get_boards_by_project(project_id: int) -> List[Dict[str, Any]]:
    """
    Returns list of boards with task counts per status.
    """
    with get_db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute(
                "SELECT * FROM boards WHERE project_id = %s ORDER BY created_at DESC",
                (project_id,)
            )
            boards = cur.fetchall()

            for board in boards:
                cur.execute("""
                    SELECT 
                        SUM(CASE WHEN status = 'To Do' THEN 1 ELSE 0 END) AS todo,
                        SUM(CASE WHEN status = 'In Progress' THEN 1 ELSE 0 END) AS in_progress,
                        SUM(CASE WHEN status = 'Review' THEN 1 ELSE 0 END) AS review,
                        SUM(CASE WHEN status = 'Done' THEN 1 ELSE 0 END) AS done
                    FROM tasks
                    WHERE board_id = %s
                """, (board['id'],))
                counts = cur.fetchone()
                board['task_counts'] = {
                    'To Do': counts['todo'] or 0,
                    'In Progress': counts['in_progress'] or 0,
                    'Review': counts['review'] or 0,
                    'Done': counts['done'] or 0
                }
    return boards


# ===============================
# Get single board by ID
# ===============================
def get_board(board_id: int) -> Optional[Dict[str, Any]]:
    """
    Returns a single board or None.
    """
    with get_db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM boards WHERE id = %s", (board_id,))
            return cur.fetchone()


# ===============================
# Create a new board
# ===============================
def create_board(name: str, description: str, project_id: int) -> Optional[int]:
    """
    Returns board_id on success, None on failure.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "INSERT INTO boards (name, description, project_id, created_at) "
                "VALUES (%s, %s, %s, NOW())",
                (name, description, project_id)
            )
            conn.commit()
            return cur.lastrowid


# ===============================
# Update an existing board
# ===============================
def update_board(board_id: int, name: str, description: str) -> bool:
    """
    Returns True if updated.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE boards SET name = %s, description = %s WHERE id = %s",
                (name, description, board_id)
            )
            conn.commit()
            return cur.rowcount > 0


# ===============================
# Delete a board (cascade)
# ===============================
def delete_board(board_id: int) -> bool:
    """
    Deletes board + all tasks.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE board_id = %s", (board_id,))
            cur.execute("DELETE FROM boards WHERE id = %s", (board_id,))
            conn.commit()
            return cur.rowcount > 0


# ===============================
# Get tasks grouped by status
# ===============================
def get_tasks_by_board(board_id: int) -> Dict[str, List[Dict[str, Any]]]:
    """
    Returns tasks grouped by status.
    """
    statuses = ['To Do', 'In Progress', 'Review', 'Done']
    grouped = {s: [] for s in statuses}

    with get_db() as conn:
        with conn.cursor(dictionary=True) as cur:
            for status in statuses:
                cur.execute(
                    """
                    SELECT id, title, assigned_to, due_date, status, created_at
                    FROM tasks
                    WHERE board_id = %s AND status = %s
                    ORDER BY created_at DESC
                    """,
                    (board_id, status)
                )
                grouped[status] = cur.fetchall()
    return grouped


# ===============================
# Get a single task
# ===============================
def get_task(task_id: int) -> Optional[Dict[str, Any]]:
    with get_db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            return cur.fetchone()


# ===============================
# Create a new task
# ===============================
def create_task(
    board_id: int,
    title: str,
    assigned_to: Optional[int] = None,
    due_date: Optional[str] = None,
    status: str = 'To Do'
) -> Optional[Dict[str, Any]]:
    """
    Returns full task dict.
    """
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO tasks (board_id, title, assigned_to, due_date, status, created_at)
                VALUES (%s, %s, %s, %s, %s, NOW())
                """,
                (board_id, title, assigned_to, due_date, status)
            )
            conn.commit()
            task_id = cur.lastrowid
            cur.execute("SELECT * FROM tasks WHERE id = %s", (task_id,))
            return cur.fetchone()


# ===============================
# Update task (any field)
# ===============================
def update_task(task_id: int, **kwargs) -> bool:
    """
    Allowed: title, assigned_to, due_date, status
    """
    allowed = ['title', 'assigned_to', 'due_date', 'status']
    updates = {k: v for k, v in kwargs.items() if k in allowed}
    if not updates:
        return False

    set_clause = ", ".join(f"{k} = %s" for k in updates)
    values = list(updates.values()) + [task_id]

    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute(f"UPDATE tasks SET {set_clause} WHERE id = %s", values)
            conn.commit()
            return cur.rowcount > 0


# ===============================
# Update task status (drag & drop)
# ===============================
def update_task_status(task_id: int, new_status: str) -> bool:
    return update_task(task_id, status=new_status)

# ... your existing functions ...

def delete_board(board_id: int) -> bool:
    """
    Deletes a board and ALL its tasks (cascading).
    Returns True on success, False on failure.
    """
    with get_db() as conn:
        try:
            with conn.cursor() as cur:
                # Step 1: Delete all tasks (optional — CASCADE does this)
                # cur.execute("DELETE FROM tasks WHERE board_id = %s", (board_id,))

                # Step 2: Delete the board
                cur.execute("DELETE FROM boards WHERE id = %s", (board_id,))
                deleted = cur.rowcount > 0
                conn.commit()
                return deleted
        except Exception as e:
            print(f"Error deleting board {board_id}: {e}")
            conn.rollback()
            return False

# ===============================
# Delete a task
# ===============================
def delete_task(task_id: int) -> bool:
    with get_db() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM tasks WHERE id = %s", (task_id,))
            conn.commit()
            return cur.rowcount > 0