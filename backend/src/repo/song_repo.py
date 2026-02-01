"""Repository layer for song data operations."""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple
import sqlite3

from backend.src.services.constants import Song, TABLE_SONGS


def connect(db_path: str) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    con.row_factory = sqlite3.Row
    return con


def get_table_columns(con: sqlite3.Connection, table: str) -> List[str]:
    cur = con.cursor()
    cur.execute(f"PRAGMA table_info({table})")
    return [r[1] for r in cur.fetchall()]


def ensure_columns(con: sqlite3.Connection, table: str, column_defs: List[str]) -> None:
    """Add columns if missing. column_defs like: 'valence_score REAL'."""
    existing = set(get_table_columns(con, table))
    cur = con.cursor()
    for coldef in column_defs:
        name = coldef.split()[0]
        if name not in existing:
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {coldef}")
    con.commit()


def fetch_songs(con: sqlite3.Connection, where: Optional[str] = None, params: Tuple = ()) -> List[Song]:
    cur = con.cursor()
    q = f"SELECT * FROM {TABLE_SONGS}"
    if where:
        q += f" WHERE {where}"
    cur.execute(q, params)
    return [dict(row) for row in cur.fetchall()]


def fetch_song_by_id(con: sqlite3.Connection, song_id: int) -> Optional[Song]:
    rows = fetch_songs(con, "song_id=?", (song_id,))
    return rows[0] if rows else None


def update_song(con: sqlite3.Connection, song_id: int, updates: Dict[str, object]) -> None:
    if not updates:
        return
    cols = list(updates.keys())
    set_clause = ", ".join([f"{c}=?" for c in cols])
    vals = [updates[c] for c in cols]
    vals.append(song_id)
    cur = con.cursor()
    cur.execute(f"UPDATE {TABLE_SONGS} SET {set_clause} WHERE song_id=?", vals)


def _default_missing_where() -> str:
    return "mood IS NULL OR intensity IS NULL OR mood_score IS NULL"

