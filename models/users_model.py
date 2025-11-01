from db import get_db



def create_user(username, email, password_hash, role='user'):
    with get_db() as conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO users (username, email, password_hash, role)
                    VALUES (%s, %s, %s, %s)
                """, (username, email, password_hash, role))
                conn.commit()
                return cur.lastrowid  # ← Return user ID
        except Exception as e:
            print(f"Create user error: {e}")
            conn.rollback()
            return None

def get_user_by_username(username):
    conn = get_db()
    with conn.cursor(dictionary=True) as cur:
        cur.execute("SELECT * FROM users WHERE username=%s", (username,))
        user = cur.fetchone()
    conn.close()
    return user

def get_user_by_id(user_id):
    conn = get_db()
    with conn.cursor(dictionary=True) as cur:
        cur.execute("SELECT * FROM users WHERE id=%s", (user_id,))
        user = cur.fetchone()
    conn.close()
    return user