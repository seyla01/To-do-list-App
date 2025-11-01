import os
from db import get_db  # Make sure this exists and returns a valid DB connection

class DashboardModel:

    @staticmethod
    def get_stats():
        conn = get_db()
        if not conn:
            return {"total_users": 0, "active_projects": 0, "tasks_completed": 0, "revenue": 0}

        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute("SELECT COUNT(*) AS total_users FROM users")
            total_users = cursor.fetchone()["total_users"]

            cursor.execute("SELECT COUNT(*) AS active_projects FROM projects WHERE status='active'")
            active_projects = cursor.fetchone()["active_projects"]

            cursor.execute("SELECT COUNT(*) AS tasks_completed FROM tasks WHERE status='completed'")
            tasks_completed = cursor.fetchone()["tasks_completed"]

        finally:
            cursor.close()
            conn.close()

        return {
            "total_users": total_users,
            "active_projects": active_projects,
            "tasks_completed": tasks_completed,
        }

    @staticmethod
    def get_recent_users(limit=5):
        conn = get_db()
        if not conn:
            return []

        cursor = conn.cursor(dictionary=True)
        try:
            cursor.execute(
                "SELECT username, email, role, status FROM users ORDER BY id DESC LIMIT %s",
                (limit,)
            )
            users = cursor.fetchall()
        finally:
            cursor.close()
            conn.close()
        return users

    @staticmethod
    def get_weekly_tasks():
        labels = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        week_data = []

        conn = get_db()
        if not conn:
            return labels, [0] * 7

        cursor = conn.cursor()
        try:
            for day in labels:
                cursor.execute(
                    "SELECT COUNT(*) FROM tasks WHERE status='completed' AND DAYNAME(created_at)=%s",
                    (day,)
                )
                week_data.append(cursor.fetchone()[0])
        finally:
            cursor.close()
            conn.close()

        return labels, week_data
