# ==============================================================
# FILE: migrations/seed_data.py
# PURPOSE: Seed rich, realistic data + project_members
# AUTHOR: Chandy Neat (Powered by Grok)
# ==============================================================

import os
import sys
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta

# Load config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config


def seed_data():
    conn = None
    cursor = None

    try:
        print("Connecting to MySQL...")

        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            database=Config.MYSQL_DB,
            port=Config.MYSQL_PORT,
            connection_timeout=10,
            use_pure=True
        )
        cursor = conn.cursor()
        print("Connected to MySQL!")

        # ==================================================
        # USERS
        # ==================================================
        print("Creating users...")
        users = [
            ("admin", "admin@gitboard.com", "admin123", "admin", "Admin User"),
            ("alice", "alice@gitboard.com", "alice123", "manager", "Alice Johnson"),
            ("bob", "bob@gitboard.com", "bob123", "member", "Bob Smith"),
            ("carol", "carol@gitboard.com", "carol123", "member", "Carol Lee"),
            ("dave", "dave@gitboard.com", "dave123", "member", "Dave Kim"),
            ("eve", "eve@gitboard.com", "eve123", "member", "Eve Chen"),
        ]

        user_ids = {}
        for username, email, password, role, _ in users:
            hashed = generate_password_hash(password)
            cursor.execute("""
                INSERT INTO users (username, email, password_hash, role, avatar_url)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id
            """, (username, email, hashed, role, f"https://ui-avatars.com/api/?name={username}&background=random"))
            cursor.execute("SELECT id FROM users WHERE username=%s", (username,))
            user_ids[username] = cursor.fetchone()[0]

        print(f"Created {len(user_ids)} users")

        # ==================================================
        # PROJECTS
        # ==================================================
        print("Creating projects...")
        projects = [
            ("GitBoard MVP", "Build the coolest task app ever", user_ids["admin"], "#8B5CF6", "active"),
            ("Website Redesign", "Modern UI/UX refresh", user_ids["alice"], "#3B82F6", "active"),
            ("Mobile App", "iOS & Android launch", user_ids["bob"], "#10B981", "active"),
            ("Bug Bash", "Fix all the bugs!", user_ids["carol"], "#EF4444", "active"),
            ("Archive Me", "Old project", user_ids["dave"], "#6B7280", "archived"),
        ]

        project_ids = []
        owner_map = {}  # project_name -> owner_id
        for name, desc, owner, color, status in projects:
            cursor.execute("""
                INSERT INTO projects (name, description, owner_id, color, status)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id
            """, (name, desc, owner, color, status))
            cursor.execute("SELECT id FROM projects WHERE name=%s", (name,))
            project_id = cursor.fetchone()[0]
            project_ids.append(project_id)
            owner_map[name] = owner

        print(f"Created {len(project_ids)} projects")

        # ==================================================
        # PROJECT MEMBERS (NEW!)
        # ==================================================
        print("Adding project members...")
        project_members = [
            # GitBoard MVP
            (project_ids[0], user_ids["admin"], "owner"),
            (project_ids[0], user_ids["alice"], "editor"),
            (project_ids[0], user_ids["bob"], "viewer"),
            (project_ids[0], user_ids["carol"], "editor"),
            # Website Redesign
            (project_ids[1], user_ids["alice"], "owner"),
            (project_ids[1], user_ids["bob"], "editor"),
            (project_ids[1], user_ids["dave"], "viewer"),
            # Mobile App
            (project_ids[2], user_ids["bob"], "owner"),
            (project_ids[2], user_ids["eve"], "editor"),
            # Bug Bash
            (project_ids[3], user_ids["carol"], "owner"),
            (project_ids[3], user_ids["dave"], "editor"),
            # Archive Me
            (project_ids[4], user_ids["dave"], "owner"),
        ]

        for project_id, user_id, role in project_members:
            cursor.execute("""
                INSERT INTO project_members (project_id, user_id, role)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE role=%s
            """, (project_id, user_id, role, role))

        print(f"Added {len(project_members)} project memberships")

        # ==================================================
        # BOARDS
        # ==================================================
        print("Creating boards...")
        boards = [
            (project_ids[0], "Sprint 1", "First sprint of MVP", "rocket"),
            (project_ids[0], "Backlog", "Future features", "inbox"),
            (project_ids[1], "Design Phase", "UI mockups & assets", "palette"),
            (project_ids[2], "Development", "Code & test", "code"),
            (project_ids[3], "Bug Tracker", "Known issues", "bug"),
        ]

        board_ids = []
        for proj_id, name, desc, icon in boards:
            cursor.execute("""
                INSERT INTO boards (project_id, name, description, icon)
                VALUES (%s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id
            """, (proj_id, name, desc, icon))
            cursor.execute("SELECT id FROM boards WHERE name=%s AND project_id=%s", (name, proj_id))
            board_ids.append(cursor.fetchone()[0])

        print(f"Created {len(board_ids)} boards")

        # ==================================================
        # LABELS
        # ==================================================
        print("Creating labels...")
        labels = [
            (project_ids[0], "feature", "#10B981"),
            (project_ids[0], "bug", "#EF4444"),
            (project_ids[0], "enhancement", "#F59E0B"),
            (project_ids[1], "urgent", "#DC2626"),
            (project_ids[2], "backend", "#6366F1"),
            (project_ids[2], "frontend", "#EC4899"),
        ]

        label_ids = {}
        for proj_id, name, color in labels:
            cursor.execute("""
                INSERT INTO labels (project_id, name, color)
                VALUES (%s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id
            """, (proj_id, name, color))
            cursor.execute("SELECT id FROM labels WHERE name=%s AND project_id=%s", (name, proj_id))
            label_id = cursor.fetchone()[0]
            label_ids[f"{proj_id}_{name}"] = label_id

        print(f"Created {len(label_ids)} labels")

        # ==================================================
        # TASKS
        # ==================================================
        print("Creating tasks...")
        tasks = [
            # Sprint 1 (GitBoard MVP)
            (board_ids[0], "Setup Flask Backend", "Init project, routes, DB", user_ids["alice"], "Critical", "In Progress", "2025-11-05", user_ids["admin"]),
            (board_ids[0], "Design Kanban UI", "Figma mockups with glassmorphism", user_ids["bob"], "High", "Review", "2025-11-03", user_ids["alice"]),
            (board_ids[0], "Drag & Drop", "Sortable.js integration", user_ids["carol"], "Medium", "To Do", "2025-11-07", user_ids["bob"]),
            (board_ids[0], "User Auth", "Login, register, JWT", user_ids["dave"], "High", "Done", "2025-10-30", user_ids["admin"]),
            # Backlog
            (board_ids[1], "Dark Mode", "Add theme toggle", None, "Low", "To Do", None, user_ids["admin"]),
            (board_ids[1], "Mobile App", "React Native version", user_ids["eve"], "Medium", "To Do", "2025-12-01", user_ids["alice"]),
            # Design Phase
            (board_ids[2], "Create Logo", "Brand identity", user_ids["bob"], "Medium", "Done", "2025-10-28", user_ids["alice"]),
            # Bug Tracker
            (board_ids[4], "Login Button Broken", "Fix on mobile", user_ids["carol"], "High", "In Progress", "2025-11-02", user_ids["dave"]),
        ]

        task_ids = []
        for t in tasks:
            board_id, title, desc, assigned, priority, status, due, creator = t
            cursor.execute("""
                INSERT INTO tasks 
                (board_id, title, description, assigned_to, priority, status, due_date, created_by, order_index)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE id=id
            """, (board_id, title, desc, assigned, priority, status, due, creator, len(task_ids)))
            cursor.execute("SELECT id FROM tasks WHERE title=%s AND board_id=%s", (title, board_id))
            task_ids.append(cursor.fetchone()[0])

        print(f"Created {len(task_ids)} tasks")

        # ==================================================
        # TASK LABELS
        # ==================================================
        print("Assigning labels to tasks...")
        task_label_map = [
            (task_ids[0], label_ids[f"{project_ids[0]}_feature"]),
            (task_ids[1], label_ids[f"{project_ids[0]}_enhancement"]),
            (task_ids[2], label_ids[f"{project_ids[0]}_feature"]),
            (task_ids[7], label_ids[f"{project_ids[0]}_bug"]),
        ]
        for task_id, label_id in task_label_map:
            cursor.execute("""
                INSERT IGNORE INTO task_labels (task_id, label_id) VALUES (%s, %s)
            """, (task_id, label_id))

        # ==================================================
        # COMMENTS
        # ==================================================
        print("Adding comments...")
        comments = [
            (task_ids[0], user_ids["alice"], "Backend setup complete! Ready for routes."),
            (task_ids[0], user_ids["bob"], "Can you add error handling?"),
            (task_ids[1], user_ids["carol"], "Love the glassmorphism effect!"),
            (task_ids[7], user_ids["dave"], "Reproduced on iOS Safari. Working on fix."),
        ]
        for task_id, user_id, comment in comments:
            cursor.execute("""
                INSERT INTO task_comments (task_id, user_id, comment)
                VALUES (%s, %s, %s)
            """, (task_id, user_id, comment))

        # ==================================================
        # TASK HISTORY
        # ==================================================
        print("Recording task history...")
        history = [
            (task_ids[0], user_ids["alice"], "status", "To Do", "In Progress"),
            (task_ids[3], user_ids["dave"], "status", "In Progress", "Done"),
        ]
        for task_id, user_id, field, old, new in history:
            cursor.execute("""
                INSERT INTO task_history (task_id, user_id, field_changed, old_value, new_value)
                VALUES (%s, %s, %s, %s, %s)
            """, (task_id, user_id, field, old, new))

        # ==================================================
        # AUDIT LOGS
        # ==================================================
        print("Logging actions...")
        audit_logs = [
            (user_ids["admin"], "seed", None, "Ran initial seeder", "127.0.0.1", "Python Script"),
            (user_ids["alice"], "task.create", task_ids[0], "Created backend task", "192.168.1.1", "Chrome"),
            (user_ids["bob"], "project.join", project_ids[0], "Joined GitBoard MVP", "192.168.1.2", "Firefox"),
        ]
        for user_id, action, entity_id, details, ip, ua in audit_logs:
            cursor.execute("""
                INSERT INTO audit_logs (user_id, action, entity_id, details, ip_address, user_agent)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (user_id, action, entity_id, details, ip, ua))

        # ==================================================
        # COMMIT
        # ==================================================
        conn.commit()
        print("SEED DATA INSERTED SUCCESSFULLY!")
        print(f"Users: {len(user_ids)} | Projects: {len(project_ids)} | Tasks: {len(task_ids)} | Members: {len(project_members)}")

    except Error as e:
        print(f"MySQL Error: {e}")
        if conn:
            conn.rollback()

    except Exception as e:
        print(f"Unexpected Error: {e}")
        if conn:
            conn.rollback()

    finally:
        if cursor:
            cursor.close()
        if conn and conn.is_connected():
            conn.close()
            print("MySQL connection closed.")


# ==============================================================
# RUN SEEDER
# ==============================================================
if __name__ == "__main__":
    seed_data()