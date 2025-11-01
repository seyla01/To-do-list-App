# models/project_model.py
from db import get_db

def get_project_by_id(project_id):
    with get_db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("SELECT * FROM projects WHERE id = %s", (project_id,))
            return cur.fetchone()

def get_project_members(project_id):
    with get_db() as conn:
        with conn.cursor(dictionary=True) as cur:
            cur.execute("""
                SELECT u.id AS user_id, u.username, pm.role 
                FROM project_members pm
                JOIN users u ON pm.user_id = u.id
                WHERE pm.project_id = %s
            """, (project_id,))
            return cur.fetchall()