import os
import sqlite3
import psycopg2
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

DB_FILE = "conversational_bi.db"
# Check if we are running in the cloud (Render) with a PostgreSQL database URL
DATABASE_URL = os.environ.get("DATABASE_URL")
IS_POSTGRES = DATABASE_URL is not None

@contextmanager
def get_db_connection():
    if IS_POSTGRES:
        conn = psycopg2.connect(DATABASE_URL)
        try:
            yield conn
        finally:
            conn.close()
    else:
        conn = sqlite3.connect(DB_FILE)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()

def get_cursor(conn):
    if IS_POSTGRES:
        return conn.cursor(cursor_factory=RealDictCursor)
    else:
        return conn.cursor()

def p(query):
    """ Helper to handle SQL placeholders (psycopg2 uses %s, sqlite uses ?) """
    if IS_POSTGRES:
        return query.replace('?', '%s')
    return query

def init_db():
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        
        # User Authentication Table
        auto_inc = "SERIAL" if IS_POSTGRES else "INTEGER PRIMARY KEY AUTOINCREMENT"
        pk_sql = f"id {auto_inc}" if IS_POSTGRES else f"id {auto_inc}"
        if IS_POSTGRES:
            pk_sql = "id SERIAL PRIMARY KEY"
            
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS users (
                {pk_sql},
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL
            )
        ''')
        
        # Chat Sessions Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS chat_sessions (
                id TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                title TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id) ON DELETE CASCADE
            )
        ''')
        
        # Messages inside a Session Table
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS messages (
                {pk_sql},
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                chart_json TEXT,
                insight TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (session_id) REFERENCES chat_sessions (id) ON DELETE CASCADE
            )
        ''')
        
        conn.commit()

# --- Database Operations ---

def create_user(username, password_hash):
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        try:
            if IS_POSTGRES:
                cursor.execute("INSERT INTO users (username, password_hash) VALUES (%s, %s) RETURNING id", (username, password_hash))
                user_id = cursor.fetchone()['id']
            else:
                cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
                user_id = cursor.lastrowid
            conn.commit()
            return user_id
        except Exception as e:
            # Handle unique constraint violation for duplicate username
            if "UNIQUE" in str(e).upper() or "UNIQUE CONSTRAINT" in str(e).upper():
                 return None
            return None

def get_user(username):
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(p("SELECT * FROM users WHERE username = ?"), (username,))
        return cursor.fetchone()

def create_chat_session(session_id, user_id, title="New Chat"):
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(p("INSERT INTO chat_sessions (id, user_id, title) VALUES (?, ?, ?)"), (session_id, user_id, title))
        conn.commit()

def get_user_sessions(user_id):
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(p("SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY created_at DESC"), (user_id,))
        return cursor.fetchall()

def rename_chat_session(session_id, title):
     with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(p("UPDATE chat_sessions SET title = ? WHERE id = ?"), (title, session_id))
        conn.commit()

def delete_chat_session(session_id):
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(p("DELETE FROM chat_sessions WHERE id = ?"), (session_id,))
        conn.commit()

def save_message(session_id, role, content, chart_json=None, insight=None):
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(p('''
            INSERT INTO messages (session_id, role, content, chart_json, insight)
            VALUES (?, ?, ?, ?, ?)
        '''), (session_id, role, content, chart_json, insight))
        conn.commit()

def get_session_messages(session_id):
    with get_db_connection() as conn:
        cursor = get_cursor(conn)
        cursor.execute(p("SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC"), (session_id,))
        rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            # When using psycopg2 RealDictRow, dictionary access works like sqlite3.Row
            msg = {
                "role": row["role"],
                "content": row["content"]
            }
            if row["chart_json"]:
                msg["chart_json"] = row["chart_json"]
            if row["insight"]:
                msg["insight"] = row["insight"]
            messages.append(msg)
        return messages

if __name__ == "__main__":
    init_db()
    print(f"Database Initialized. Using PostgreSQL: {IS_POSTGRES}")
