import mysql.connector
from config import Config
import os

def run_migration():
    print("🚀 Running migration...")

    try:
        # Connect to MySQL server (without selecting DB yet)
        conn = mysql.connector.connect(
            host=Config.MYSQL_HOST,
            user=Config.MYSQL_USER,
            password=Config.MYSQL_PASSWORD
        )
        cursor = conn.cursor()

        # Create database if not exists
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {Config.MYSQL_DB}")
        cursor.execute(f"USE {Config.MYSQL_DB}")

        # Run the migration SQL
        sql_path = os.path.join(os.path.dirname(__file__), 'migrations', 'init_db.sql')
        with open(sql_path, 'r', encoding='utf-8') as f:
            sql_commands = f.read().split(';')

            for command in sql_commands:
                command = command.strip()
                if command:
                    cursor.execute(command)

        conn.commit()
        print("✅ Migration completed successfully!")
    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")
    finally:
        if conn.is_connected():
            cursor.close()
            conn.close()

if __name__ == "__main__":
    run_migration()
