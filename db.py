import mysql.connector
import time

def get_db():
    """Return a new database connection."""
    connection = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # add your MySQL password if any
        database="todo_app",
        port=3306,
        use_pure=True
    )
    return connection


# Optional: run a test when executing this file directly
if __name__ == "__main__":
    print("🚀 Testing MySQL connection...")

    try:
        print("⏳ Attempting connection...")
        start = time.time()

        conn = get_db()

        print("✅ Connected!")
        print("Server Info:", conn.get_server_info())
        conn.close()

    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")
    except Exception as e:
        print(f"⚠️ Unknown error: {e}")
