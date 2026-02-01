#!/usr/bin/env python
"""Migrate existing database to new schema with enhanced columns."""

import sqlite3
import os

current_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(current_dir, "music.db")

print(f"Migrating database: {db_path}")

con = sqlite3.connect(db_path)
cursor = con.cursor()

# Get existing columns
cursor.execute("PRAGMA table_info(songs)")
existing_cols = {row[1] for row in cursor.fetchall()}
print(f"Existing columns: {len(existing_cols)}")

# New columns to add
new_columns = {
    "speechiness": "INTEGER",
    "instrumentalness": "INTEGER",
    "liveness": "INTEGER",
    "popularity": "INTEGER",
    "valence_score": "REAL",
    "arousal_score": "REAL",
    "mood_confidence": "REAL"
    # Note: created_at requires special handling in SQLite
}

# Add missing columns
added_count = 0
for col_name, col_type in new_columns.items():
    if col_name not in existing_cols:
        try:
            cursor.execute(f"ALTER TABLE songs ADD COLUMN {col_name} {col_type}")
            print(f"✓ Added column: {col_name}")
            added_count += 1
        except Exception as e:
            print(f"✗ Failed to add {col_name}: {e}")
    else:
        print(f"- Column already exists: {col_name}")

con.commit()
con.close()

print(f"\n✓ Migration complete! Added {added_count} new columns")

# Verify
con = sqlite3.connect(db_path)
cursor = con.cursor()
cursor.execute("PRAGMA table_info(songs)")
all_cols = cursor.fetchall()
print(f"\nFinal schema: {len(all_cols)} columns")
for col in all_cols:
    print(f"  - {col[1]:25s} {col[2]}")
con.close()
