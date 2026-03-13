import sqlite3
import os
from contextlib import contextmanager
import json

DB_FILE = "conversational_bi.db"

@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # User Authentication Table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)", (username, password_hash))
            conn.commit()
            return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None # Username already exists

def get_user(username):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cursor.fetchone()

def create_chat_session(session_id, user_id, title="New Chat"):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat_sessions (id, user_id, title) VALUES (?, ?, ?)", (session_id, user_id, title))
        conn.commit()

def get_user_sessions(user_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chat_sessions WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
        return cursor.fetchall()

def rename_chat_session(session_id, title):
     with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE chat_sessions SET title = ? WHERE id = ?", (title, session_id))
        conn.commit()

def delete_chat_session(session_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_sessions WHERE id = ?", (session_id,))
        conn.commit()

def save_message(session_id, role, content, chart_json=None, insight=None):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO messages (session_id, role, content, chart_json, insight)
            VALUES (?, ?, ?, ?, ?)
        ''', (session_id, role, content, chart_json, insight))
        conn.commit()

def get_session_messages(session_id):
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC", (session_id,))
        rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            msg = {
                "role": row["role"],
                "content": row["content"]
            }
            if row["chart_json"]:
                # The chart_json will be a string serialized by plotly.io in app.py
                msg["chart_json"] = row["chart_json"]
            if row["insight"]:
                msg["insight"] = row["insight"]
            messages.append(msg)
        return messages

if __name__ == "__main__":
    init_db()
    print("Database Initialized.")
