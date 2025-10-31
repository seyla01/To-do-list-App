# ==============================================================
# FILE: migrations/create_tables.py
# PURPOSE: Create all database tables for Task Management System (GitBoard Style)
# AUTHOR: Chandy Neat (Modified by ChatGPT)
# ==============================================================

import os
import sys
import mysql.connector
from mysql.connector import Error

# ✅ Import config from root folder
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from config import Config


def create_tables():
    conn = None
    cursor = None

    try:
        print("🚀 Connecting to MySQL...")

        # 1️⃣ Connect without database to ensure DB exists
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD,
            port=Config.MYSQL_PORT,
            connection_timeout=5,
            use_pure=True
        )
        cursor = conn.cursor()
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
        print(f"✅ Database '{Config.MYSQL_DB}' ready!")
        cursor.close()
        conn.close()

        # 2️⃣ Reconnect specifying the database
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
        print("✅ Connected to MySQL successfully!")

        # ==================================================
        # 🧹 DROP OLD TABLES
        # ==================================================
        print("⚙️ Dropping existing tables (if any)...")
        cursor.execute("SET FOREIGN_KEY_CHECKS = 0;")
        cursor.execute("""
            DROP TABLE IF EXISTS 
                audit_logs,
                task_comments,
                tasks,
                boards,
                projects,
                users;
        """)
        cursor.execute("SET FOREIGN_KEY_CHECKS = 1;")

        # ==================================================
        # 🧱 CREATE TABLES
        # ==================================================
        print("🧩 Creating tables...")

        cursor.execute("""
        CREATE TABLE users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) NOT NULL,
            email VARCHAR(150) NOT NULL UNIQUE,
            password_hash VARCHAR(255) NOT NULL,
            role ENUM('admin', 'member') DEFAULT 'member',
            status ENUM('active', 'inactive') DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        cursor.execute("""
        CREATE TABLE projects (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(150) NOT NULL,
            description TEXT,
            created_by INT NOT NULL,
            status ENUM('active', 'archived') DEFAULT 'active',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (created_by) REFERENCES users(id)
                ON UPDATE CASCADE
                ON DELETE CASCADE
        );
        """)

        cursor.execute("""
        CREATE TABLE boards (
            id INT AUTO_INCREMENT PRIMARY KEY,
            project_id INT NOT NULL,
            name VARCHAR(150) NOT NULL,
            description TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
                ON UPDATE CASCADE
                ON DELETE CASCADE
        );
        """)

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
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            FOREIGN KEY (board_id) REFERENCES boards(id)
                ON UPDATE CASCADE
                ON DELETE CASCADE,
            FOREIGN KEY (assigned_to) REFERENCES users(id)
                ON UPDATE CASCADE
                ON DELETE SET NULL
        );
        """)

        cursor.execute("""
        CREATE TABLE task_comments (
            id INT AUTO_INCREMENT PRIMARY KEY,
            task_id INT NOT NULL,
            user_id INT NOT NULL,
            comment TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (task_id) REFERENCES tasks(id)
                ON UPDATE CASCADE
                ON DELETE CASCADE,
            FOREIGN KEY (user_id) REFERENCES users(id)
                ON UPDATE CASCADE
                ON DELETE CASCADE
        );
        """)

        cursor.execute("""
        CREATE TABLE audit_logs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT,
            action TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users(id)
                ON UPDATE CASCADE
                ON DELETE SET NULL
        );
        """)

        # ==================================================
        # ✅ COMMIT CHANGES
        # ==================================================
        conn.commit()
        print("🎉 All GitBoard tables created successfully!")

    except Error as e:
        print(f"❌ MySQL Error: {e}")

    except Exception as e:
        print(f"⚠️ Unexpected Error: {e}")

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
    create_tables()
