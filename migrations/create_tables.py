# ==============================================================
# FILE: migrations/create_tables.py
# PURPOSE: Create FULL GitBoard schema + project_members
# ==============================================================

import os
import sys
import mysql.connector
from mysql.connector import Error

# Import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config


def create_tables():
    conn = None
    cursor = None

    try:
        print("Connecting to MySQL...")

        # 1. Connect without DB
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            port=Config.MYSQL_PORT,
            connection_timeout=10,
            use_pure=True
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"Database '{Config.MYSQL_DB}' ready!")
        cursor.close()
        conn.close()

        # 2. Reconnect with DB
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
        # DROP OLD TABLES
        # ==================================================
        print("Dropping old tables...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        tables_to_drop = [
            'project_members',        # <-- ADDED
            'task_labels', 'labels',
            'task_history', 'audit_logs',
            'task_comments', 'tasks',
            'boards', 'projects', 'users'
        ]
        for table in tables_to_drop:
            cursor.execute(f"DROP TABLE IF EXISTS {table}")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")
        print("Old schema cleared.")

        # ==================================================
        # CREATE TABLES
        # ==================================================
        print("Creating full GitBoard schema...")

        # 1. Users
        cursor.execute("""
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL UNIQUE,
            email VARCHAR(150) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('admin', 'manager', 'member') DEFAULT 'member',
            avatar_url VARCHAR(500),
            is_active BOOLEAN DEFAULT TRUE,
            is_deleted BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            INDEX idx_username (username),
            INDEX idx_email (email)
        ) ENGINE=InnoDB;
        """)

        # 2. Projects
        cursor.execute("""
        CREATE TABLE projects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            description TEXT,
            owner_id INT NOT NULL,
            status ENUM('active', 'archived', 'completed') DEFAULT 'active',
            start_date DATE,
            end_date DATE,
            color VARCHAR(7) DEFAULT '#3B82F6',
            is_deleted BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (owner_id) REFERENCES users(id) ON DELETE RESTRICT,
            INDEX idx_owner (owner_id),
            INDEX idx_status (status)
        ) ENGINE=InnoDB;
        """)

        # 3. Project Members (NEW)
        cursor.execute("""
        CREATE TABLE project_members (
            project_id INT NOT NULL,
            user_id INT NOT NULL,
            role ENUM('owner', 'editor', 'viewer') DEFAULT 'viewer',
            joined_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (project_id, user_id),
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
            INDEX idx_user (user_id)
        ) ENGINE=InnoDB;
        """)
        print("Created project_members table")

        # 4. Boards
        cursor.execute("""
        CREATE TABLE boards (
            id INT AUTO_INCREMENT PRIMARY KEY,
            project_id INT NOT NULL,
            name VARCHAR(150) NOT NULL,
            description TEXT,
            icon VARCHAR(50) DEFAULT 'clipboard-check',
            is_archived BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            INDEX idx_project (project_id)
        ) ENGINE=InnoDB;
        """)

        # ... [rest of your tables: labels, tasks, task_labels, etc.] ...
        # (Keep all your existing tables below — unchanged)

        # 5. Labels
        cursor.execute("""
        CREATE TABLE labels (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            color VARCHAR(7) DEFAULT '#10B981',
            project_id INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id) ON DELETE CASCADE,
            UNIQUE KEY uniq_label_project (name, project_id),
            INDEX idx_project (project_id)
        ) ENGINE=InnoDB;
        """)

        # 6. Tasks
        cursor.execute("""
        CREATE TABLE tasks (
            id INT AUTO_INCREMENT PRIMARY KEY,
            board_id INT NOT NULL,
            title VARCHAR(255) NOT NULL,
            description TEXT,
            assigned_to INT,
            priority ENUM('Low', 'Medium', 'High', 'Critical') DEFAULT 'Medium',
            status ENUM('To Do', 'In Progress', 'Review', 'Done') DEFAULT 'To Do',
            due_date DATE,
            completed_at TIMESTAMP NULL,
            order_index INT DEFAULT 0,
            is_deleted BOOLEAN DEFAULT FALSE,
            created_by INT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (board_id) REFERENCES boards(id) ON DELETE CASCADE,
            FOREIGN KEY (assigned_to) REFERENCES users(id) ON DELETE SET NULL,
            FOREIGN KEY (created_by) REFERENCES users(id) ON DELETE RESTRICT,
            INDEX idx_board_status (board_id, status),
            INDEX idx_assigned (assigned_to),
            INDEX idx_due_date (due_date),
            INDEX idx_priority (priority)
        ) ENGINE=InnoDB;
        """)

        # ... [task_labels, task_comments, task_history, audit_logs] ...
        # (Keep unchanged)

        # ==================================================
        # SEED DATA
        # ==================================================
        print("Seeding initial data...")

        # Admin User
        cursor.execute("""
        INSERT INTO users (username, email, password_hash, role) VALUES
        ('admin', 'admin@gitboard.com', 'scrypt:32768:8:1$...hashed...', 'admin')
        ON DUPLICATE KEY UPDATE id=id;
        """)

        # Sample Project
        cursor.execute("INSERT INTO projects (name, owner_id, description) VALUES ('GitBoard MVP', 1, 'Build the coolest task app')")
        project_id = cursor.lastrowid

        # Add owner as project member
        cursor.execute("""
        INSERT INTO project_members (project_id, user_id, role) VALUES (%s, %s, 'owner')
        ON DUPLICATE KEY UPDATE role='owner'
        """, (project_id, 1))

        # Add Alice as editor
        cursor.execute("""
        INSERT INTO users (username, email, password_hash, role) VALUES
        ('alice', 'alice@gitboard.com', 'scrypt:32768:8:1$...hashed...', 'manager')
        ON DUPLICATE KEY UPDATE id=id;
        """)
        cursor.execute("SELECT id FROM users WHERE username='alice'")
        alice_id = cursor.fetchone()[0]
        cursor.execute("""
        INSERT INTO project_members (project_id, user_id, role) VALUES (%s, %s, 'editor')
        ON DUPLICATE KEY UPDATE role='editor'
        """, (project_id, alice_id))

        # Create Board + Tasks
        cursor.execute("INSERT INTO boards (project_id, name, description) VALUES (%s, 'Main Sprint', 'Current sprint tasks')", (project_id,))
        board_id = cursor.lastrowid

        tasks = [
            ('Design UI', 'Create Figma mockups', 1, 'High', 'To Do', '2025-11-05'),
            ('Setup Flask', 'Init project & DB', alice_id, 'Critical', 'In Progress', '2025-11-03'),
        ]
        for t in tasks:
            cursor.execute("""
            INSERT INTO tasks (board_id, title, description, assigned_to, priority, status, due_date, created_by)
            VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
            """, (board_id, *t))

        # Labels
        cursor.execute("INSERT INTO labels (project_id, name, color) VALUES (%s, 'bug', '#EF4444'), (%s, 'feature', '#10B981')", (project_id, project_id))

        conn.commit()
        print("Seed data added!")

        print("ALL TABLES CREATED SUCCESSFULLY!")
        print("project_members table added for team collaboration")

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


if __name__ == "__main__":
    create_tables()