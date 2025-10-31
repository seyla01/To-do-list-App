# ==============================================================
# FILE: migrations/seed_data.py
# PURPOSE: Seed initial data into GitBoard tables
# ==============================================================

import os
import sys
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash  # For hashing passwords

# Load config from root folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config


def seed_data():
    conn = None
    cursor = None

    try:
        print("🚀 Connecting to MySQL...")

        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            port=Config.MYSQL_PORT,
            connection_timeout=5,
            use_pure=True
        )
        cursor = conn.cursor()
        print("✅ Connected to MySQL!")

        # ==================================================
        # 👤 Create Admin User
        # ==================================================
        print("👤 Creating admin user...")
        admin_username = "admin"
        admin_email = "admin@example.com"
        admin_password = generate_password_hash("admin123")  # hashed password
        cursor.execute(
            "INSERT INTO users (username, email, password_hash, role) VALUES (%s, %s, %s, %s)",
            (admin_username, admin_email, admin_password, "admin")
        )

        # ==================================================
        # 📁 Create Sample Project
        # ==================================================
        print("📁 Creating sample project...")
        cursor.execute(
            "INSERT INTO projects (name, description, created_by) VALUES (%s, %s, %s)",
            ("Sample Project", "This is a sample project", 1)
        )

        # ==================================================
        # 📋 Create Sample Board
        # ==================================================
        print("📋 Creating sample board...")
        cursor.execute(
            "INSERT INTO boards (project_id, name, description) VALUES (%s, %s, %s)",
            (1, "To Do Board", "Board for tasks in progress")
        )

        # ==================================================
        # 📝 Create Sample Task
        # ==================================================
        print("📝 Creating sample task...")
        cursor.execute(
            "INSERT INTO tasks (board_id, title, description, assigned_to) VALUES (%s, %s, %s, %s)",
            (1, "Sample Task", "This is a sample task", 1)
        )

        # ==================================================
        # 💬 Optional: Add a comment to task
        # ==================================================
        print("💬 Adding a sample comment...")
        cursor.execute(
            "INSERT INTO task_comments (task_id, user_id, comment) VALUES (%s, %s, %s)",
            (1, 1, "This is a sample comment on the task.")
        )

        # ==================================================
        # 📝 Optional: Add audit log
        # ==================================================
        print("📝 Adding a sample audit log...")
        cursor.execute(
            "INSERT INTO audit_logs (user_id, action) VALUES (%s, %s)",
            (1, "Seeded initial data")
        )

        # ==================================================
        # ✅ Commit changes
        # ==================================================
        conn.commit()
        print("🎉 Seeder data inserted successfully!")

    except Error as e:
        print(f"❌ MySQL Error: {e}")

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            print("🔒 MySQL connection closed.")


# ==============================================================
# MAIN EXECUTION
# ==============================================================
if __name__ == "__main__":
    seed_data()
