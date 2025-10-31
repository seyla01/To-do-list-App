# models/users_model.py
from config import Config
import mysql.connector
from mysql.connector import Error
from werkzeug.security import generate_password_hash, check_password_hash

def get_db_connection():
    return mysql.connector.connect(
        host=Config.MYSQL_HOST,
        user=Config.MYSQL_USER,
        password=Config.MYSQL_PASSWORD,
        database=Config.MYSQL_DB,
        port=Config.MYSQL_PORT,
        use_pure=True
    )

def create_user(username, email, password):
    conn = get_db_connection()
    cursor = conn.cursor()
    hashed = generate_password_hash(password)
    cursor.execute(
        "INSERT INTO users (username, email, password_hash) VALUES (%s, %s, %s)",
        (username, email, hashed)
    )
    conn.commit()
    cursor.close()
    conn.close()

def get_user_by_email(email):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    cursor.execute("SELECT * FROM users WHERE email=%s", (email,))
    user = cursor.fetchone()
    cursor.close()
    conn.close()
    return user

def verify_password(user, password):
    return check_password_hash(user["password_hash"], password)
