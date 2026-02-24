import sqlite3

db_path = 'backend/src/database/music.db'
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# Get tables
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print('Tables:', tables)

# Check songs table structure
cursor.execute("PRAGMA table_info(songs)")
cols = cursor.fetchall()
print('\nSongs columns:')
for col in cols:
    print(f"  {col}")

# Count
cursor.execute("SELECT COUNT(*) FROM songs")
count = cursor.fetchone()[0]
print(f'\nTotal songs: {count}')

# Sample
if count > 0:
    cursor.execute("SELECT * FROM songs LIMIT 1")
    cols_names = [description[0] for description in cursor.description]
    print(f'\nColumns: {cols_names}')
    sample = cursor.fetchone()
    print('Sample:', sample)

conn.close()
