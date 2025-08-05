import sqlite3
import json
from datetime import datetime

def init_db():
    try:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        # جدول users
        c.execute('''
            CREATE TABLE IF NOT EXISTS users (
                username TEXT PRIMARY KEY,
                ip_address TEXT,
                port INTEGER,
                status TEXT DEFAULT 'online'
            )
        ''')
        # جدول messages
        c.execute('''
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT,
                content TEXT,
                timestamp TEXT,
                receiver_ids TEXT,
                FOREIGN KEY (sender_id) REFERENCES users (username)
            )
        ''')
        conn.commit()
        print("[DATABASE] Database initialized")
    except sqlite3.Error as e:
        print(f"[DATABASE] Error initializing database: {e}")
    finally:
        conn.close()

def add_or_update_user(username, ip_address, port):
    try:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute('''
            INSERT OR REPLACE INTO users (username, ip_address, port, status)
            VALUES (?, ?, ?, 'online')
        ''', (username, ip_address, port))
        conn.commit()
        print(f"[DATABASE] User {username} added/updated: {ip_address}:{port}")
    except sqlite3.Error as e:
        print(f"[DATABASE] Error adding/updating user {username}: {e}")
    finally:
        conn.close()

def set_user_offline(username):
    try:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute('''
            UPDATE users SET status = 'offline' WHERE username = ?
        ''', (username,))
        conn.commit()
        print(f"[DATABASE] User {username} set to offline")
    except sqlite3.Error as e:
        print(f"[DATABASE] Error setting user {username} offline: {e}")
    finally:
        conn.close()

def save_message(sender_id, content, receiver_ids):
    try:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        timestamp = datetime.now().isoformat()
        receiver_ids_json = json.dumps(receiver_ids)  # سریال‌سازی لیست گیرندگان
        c.execute('''
            INSERT INTO messages (sender_id, content, timestamp, receiver_ids)
            VALUES (?, ?, ?, ?)
        ''', (sender_id, content, timestamp, receiver_ids_json))
        conn.commit()
        print(f"[DATABASE] Message from {sender_id} saved with content: {content}, receivers: {receiver_ids}")
    except sqlite3.Error as e:
        print(f"[DATABASE] Error saving message from {sender_id}: {e}")
    finally:
        conn.close()

def get_online_users():
    try:
        conn = sqlite3.connect('chat.db')
        c = conn.cursor()
        c.execute('SELECT username FROM users WHERE status = "online"')
        online_users = [row[0] for row in c.fetchall()]
        print(f"[DATABASE] Online users: {online_users}")
        return online_users
    except sqlite3.Error as e:
        print(f"[DATABASE] Error fetching online users: {e}")
        return []
    finally:
        conn.close()