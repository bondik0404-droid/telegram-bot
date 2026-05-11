import sqlite3
import logging
from datetime import datetime

DB_NAME = "bot.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    
    # Таблица пользователей
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            joined_date TEXT,
            last_active TEXT
        )
    ''')
    
    # Таблица заметок
    cur.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            title TEXT,
            content TEXT,
            created_at TEXT
        )
    ''')
    
    conn.commit()
    conn.close()
    logging.info("✅ База данных инициализирована")

def add_or_update_user(user):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    now = datetime.now().isoformat()
    
    cur.execute('''
        INSERT OR REPLACE INTO users 
        (user_id, username, first_name, last_name, joined_date, last_active)
        VALUES (?, ?, ?, ?, COALESCE((SELECT joined_date FROM users WHERE user_id=?), ?), ?)
    ''', (user.id, user.username, user.first_name, user.last_name, user.id, now, now))
    
    conn.commit()
    conn.close()

def add_note(user_id, title, content):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("INSERT INTO notes (user_id, title, content, created_at) VALUES (?, ?, ?, ?)",
                (user_id, title, content, datetime.now().isoformat()))
    conn.commit()
    note_id = cur.lastrowid
    conn.close()
    return note_id

def get_user_notes(user_id):
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT id, title, content, created_at FROM notes WHERE user_id = ? ORDER BY created_at DESC", (user_id,))
    notes = cur.fetchall()
    conn.close()
    return notes

def get_stats():
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    users_count = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM notes")
    notes_count = cur.fetchone()[0]
    conn.close()
    return users_count, notes_count
