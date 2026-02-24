"""
Add user data from musicmood.db to music.db
"""
import sqlite3

def add_missing_users():
    """Add users from musicmood.db to music.db"""
    
    primary_db = 'backend/src/database/music.db'
    source_db = 'backend/src/database/musicmood.db'
    
    print("="*70)
    print("👥 ADDING USERS FROM musicmood.db")
    print("="*70)
    
    primary_conn = sqlite3.connect(primary_db)
    primary_cursor = primary_conn.cursor()
    
    source_conn = sqlite3.connect(source_db)
    source_cursor = source_conn.cursor()
    
    # Get users from source
    source_cursor.execute("SELECT * FROM users")
    source_users = source_cursor.fetchall()
    
    source_cursor.execute("PRAGMA table_info(users)")
    source_cols = [row[1] for row in source_cursor.fetchall()]
    
    print(f"\nSource users to add: {len(source_users)}")
    print(f"Source columns: {source_cols}")
    
    # Get primary users columns
    primary_cursor.execute("PRAGMA table_info(users)")
    primary_cols = [row[1] for row in primary_cursor.fetchall()]
    
    print(f"Primary columns: {primary_cols}")
    
    # Get common columns
    common_cols = [c for c in source_cols if c in primary_cols]
    print(f"Common columns: {common_cols}")
    
    # Get existing usernames
    primary_cursor.execute("SELECT username FROM users")
    existing_users = set(row[0] for row in primary_cursor.fetchall())
    
    added = 0
    for row in source_users:
        row_dict = dict(zip(source_cols, row))
        username = row_dict.get('username', '')
        
        if username and username not in existing_users:
            # Build columns and values, handling password
            cols = []
            values_list = []
            
            for col in primary_cols:
                if col == 'password_hash':
                    # Use password from source if available
                    cols.append(col)
                    values_list.append(row_dict.get('password', 'hashed_pwd_' + username))
                elif col in row_dict:
                    cols.append(col)
                    values_list.append(row_dict[col])
            
            cols_str = ', '.join(cols)
            values_str = ', '.join(['?' for _ in cols])
            
            try:
                primary_cursor.execute(
                    f"INSERT INTO users ({cols_str}) VALUES ({values_str})",
                    tuple(values_list)
                )
                added += 1
                print(f"  ✓ Added user: {username}")
                existing_users.add(username)
            except Exception as e:
                print(f"  ⚠️  Failed to add {username}: {e}")
    
    primary_conn.commit()
    primary_conn.close()
    source_conn.close()
    
    print(f"\n✅ Added {added} users to primary database")

if __name__ == "__main__":
    add_missing_users()
