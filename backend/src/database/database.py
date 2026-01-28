import sqlite3
import os
from datetime import datetime
from typing import List, Dict, Optional

DB_PATH = os.path.join(os.path.dirname(__file__), "music.db")

def _get_connection():
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = _get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        total_songs_listened INTEGER DEFAULT 0,
        favorite_mood TEXT DEFAULT NULL,
        favorite_artist TEXT DEFAULT NULL)""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS chat_history (
        history_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        mood TEXT, intensity TEXT, song_id INTEGER, reason TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id))""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS songs (
        song_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL, artist TEXT NOT NULL, genre TEXT,
        suy_score REAL, reason TEXT, moods TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)""")
    
    cursor.execute("""CREATE TABLE IF NOT EXISTS recommendations (
        recommendation_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL, song_id INTEGER NOT NULL,
        mood TEXT, intensity TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (user_id) REFERENCES users(user_id),
        FOREIGN KEY (song_id) REFERENCES songs(song_id))""")
    
    conn.commit()
    conn.close()
    print(f"Database initialized at {DB_PATH}")

def seed_sample_songs():
    conn = _get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM songs")
    if cursor.fetchone()[0] == 0:
        songs = [
            ("Bước Qua Nhau", "V.O.", "V-Pop", 8.5, "Uplifting melody", "Vui"),
            ("Có Chàng Trai Viết Lên Cây", "Phan Mạnh Quỳnh", "V-Pop", 8.0, "Romantic", "Suy tư"),
            ("Nơi Này Có Anh", "Sơn Tùng M-TP", "V-Pop", 7.8, "Emotional", "Buồn"),
        ]
        for song in songs:
            cursor.execute("INSERT INTO songs (name, artist, genre, suy_score, reason, moods) VALUES (?, ?, ?, ?, ?, ?)", song)
        conn.commit()
        print("Sample songs seeded successfully")
    conn.close()

def add_user(username: str, email: str, password: str) -> Optional[int]:
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, email, password) VALUES (?, ?, ?)", (username, email, password))
        conn.commit()
        user_id = cursor.lastrowid
        conn.close()
        return user_id
    except:
        return None

def get_user(username: str) -> Optional[Dict]:
    conn = _get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return dict(user) if user else None

def get_all_songs() -> List[Dict]:
    conn = _get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM songs")
    songs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return songs

def add_recommendation(user_id: int, song_id: int, mood: str, intensity: str) -> bool:
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO recommendations (user_id, song_id, mood, intensity) VALUES (?, ?, ?, ?)", (user_id, song_id, mood, intensity))
        conn.commit()
        conn.close()
        return True
    except:
        return False

def get_user_recommendations(user_id: int, limit: int = 20) -> List[Dict]:
    conn = _get_connection()
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    cursor.execute("SELECT r.*, s.name, s.artist FROM recommendations r LEFT JOIN songs s ON r.song_id = s.song_id WHERE r.user_id = ? ORDER BY r.timestamp DESC LIMIT ?", (user_id, limit))
    recs = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return recs

def add_chat_history(user_id: int, mood: str = None, intensity: str = None, song_id: int = None) -> bool:
    try:
        conn = _get_connection()
        cursor = conn.cursor()
        cursor.execute("INSERT INTO chat_history (user_id, mood, intensity, song_id) VALUES (?, ?, ?, ?)", (user_id, mood, intensity, song_id))
        conn.commit()
        conn.close()
        return True
    except:
        return False
