"""
Merge musicmood.db into music.db - Keep music.db as primary
"""
import sqlite3
import shutil
import os
from datetime import datetime

def merge_databases():
    """Merge old musicmood.db into music.db"""
    
    old_db = 'backend/src/database/musicmood.db'
    new_db = 'backend/src/database/music.db'
    backup_db = f'backend/src/database/music_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db'
    
    print("="*70)
    print("🎵 MERGING DATABASES - musicmood.db → music.db")
    print("="*70)
    
    # Check if old db exists
    if not os.path.exists(old_db):
        print(f"\n❌ Old database not found: {old_db}")
        print("✓ Keeping music.db as is")
        return
    
    if not os.path.exists(new_db):
        print(f"\n❌ New database not found: {new_db}")
        return
    
    print(f"\n📂 Old DB: {old_db}")
    print(f"📂 New DB: {new_db}")
    
    # Create backup of new db
    print(f"\n💾 Creating backup: {backup_db}")
    shutil.copy2(new_db, backup_db)
    print("✓ Backup created")
    
    # Connect to both databases
    old_conn = sqlite3.connect(old_db)
    old_conn.row_factory = sqlite3.Row
    old_cursor = old_conn.cursor()
    
    new_conn = sqlite3.connect(new_db)
    new_cursor = new_conn.cursor()
    
    # Get tables from old db
    old_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    old_tables = [row[0] for row in old_cursor.fetchall()]
    
    print(f"\n📊 Old database tables: {old_tables}")
    
    # Get tables from new db
    new_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    new_tables = [row[0] for row in new_cursor.fetchall()]
    
    print(f"📊 New database tables: {new_tables}")
    
    merged_count = 0
    
    # For each table, merge data
    for table in old_tables:
        if table == 'sqlite_sequence':
            continue
        
        print(f"\n🔄 Processing table: {table}")
        
        # Get columns
        old_cursor.execute(f"PRAGMA table_info({table})")
        old_cols = [row[1] for row in old_cursor.fetchall()]
        
        if table not in new_tables:
            print(f"   ⚠️  Table {table} not in new DB, skipping")
            continue
        
        new_cursor.execute(f"PRAGMA table_info({table})")
        new_cols = [row[1] for row in new_cursor.fetchall()]
        
        # Get common columns
        common_cols = [c for c in old_cols if c in new_cols]
        
        if not common_cols:
            print(f"   ⚠️  No common columns, skipping")
            continue
        
        # Get data from old db
        old_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        old_count = old_cursor.fetchone()[0]
        
        new_cursor.execute(f"SELECT COUNT(*) FROM {table}")
        new_count = new_cursor.fetchone()[0]
        
        print(f"   Old: {old_count} rows | New: {new_count} rows")
        
        # Check if new db has all the data
        if new_count >= old_count:
            print(f"   ✓ New DB already has all/more data, keeping new")
            merged_count += 1
            continue
        
        # Otherwise, migrate missing songs from old to new
        if table == 'songs':
            old_cursor.execute(f"SELECT * FROM {table}")
            old_rows = old_cursor.fetchall()
            
            # Get song names from new db
            new_cursor.execute(f"SELECT song_name FROM songs")
            new_song_names = set(row[0] for row in new_cursor.fetchall())
            
            inserted = 0
            for row in old_rows:
                row_dict = dict(row)
                song_name = row_dict.get('song_name', '')
                
                # Only insert if not already in new db
                if song_name not in new_song_names:
                    cols = ', '.join(common_cols)
                    values = ', '.join(['?' for _ in common_cols])
                    row_values = tuple(row_dict[c] for c in common_cols)
                    
                    new_cursor.execute(f"INSERT INTO {table} ({cols}) VALUES ({values})", row_values)
                    inserted += 1
                    new_song_names.add(song_name)
            
            print(f"   ✓ Inserted {inserted} new songs from old DB")
            merged_count += inserted
    
    # Commit and close
    new_conn.commit()
    new_conn.close()
    old_conn.close()
    
    print("\n" + "="*70)
    print(f"✅ MERGE COMPLETED - {merged_count} records merged")
    print("="*70)
    
    # Remove old db
    try:
        os.remove(old_db)
        print(f"\n🗑️  Deleted old database: {old_db}")
    except Exception as e:
        print(f"\n⚠️  Could not delete old DB: {e}")
    
    # Verify final state
    print(f"\n📊 Final database state:")
    final_conn = sqlite3.connect(new_db)
    final_cursor = final_conn.cursor()
    final_cursor.execute("SELECT COUNT(*) FROM songs")
    final_count = final_cursor.fetchone()[0]
    print(f"   Total songs in music.db: {final_count}")
    final_conn.close()
    
    print("\n✨ Database merge complete!")
    print(f"📂 Primary DB: {new_db}")
    print(f"📂 Backup: {backup_db}")

if __name__ == "__main__":
    merge_databases()
