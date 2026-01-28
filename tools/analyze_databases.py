"""
Analyze all databases and prepare for comprehensive merge
"""
import sqlite3
import os

def analyze_databases():
    """Analyze all database files and their tables"""
    
    db_dir = 'backend/src/database'
    db_files = []
    
    # Find all .db files
    for root, dirs, files in os.walk(db_dir):
        for file in files:
            if file.endswith('.db'):
                path = os.path.join(root, file)
                db_files.append(path)
    
    print("="*80)
    print("📊 DATABASE ANALYSIS - Tất Cả Các File Database")
    print("="*80)
    
    database_info = {}
    
    for db_path in sorted(db_files):
        print(f"\n📂 {db_path}")
        print("-" * 80)
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Get all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            print(f"   Tables: {len(tables)}")
            
            table_info = {}
            for table in tables:
                if table == 'sqlite_sequence':
                    continue
                
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                row_count = cursor.fetchone()[0]
                
                cursor.execute(f"PRAGMA table_info({table})")
                columns = [row[1] for row in cursor.fetchall()]
                
                table_info[table] = {
                    'rows': row_count,
                    'columns': columns
                }
                
                print(f"      - {table:25s} ({row_count:4d} rows, {len(columns):2d} cols)")
            
            database_info[db_path] = table_info
            conn.close()
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print("\n" + "="*80)
    print("📋 TABLE SUMMARY - Danh Sách Các Bảng Có Trong Các Database")
    print("="*80)
    
    all_tables = set()
    for db_path, tables in database_info.items():
        all_tables.update(tables.keys())
    
    for table in sorted(all_tables):
        print(f"\n📌 Table: {table}")
        for db_path, tables in sorted(database_info.items()):
            if table in tables:
                info = tables[table]
                print(f"   ✓ {os.path.basename(db_path):40s} {info['rows']:6d} rows | Cols: {', '.join(info['columns'][:5])}")
            else:
                print(f"   ✗ {os.path.basename(db_path):40s} (không có)")
    
    print("\n" + "="*80)
    print("🎯 MERGE STRATEGY")
    print("="*80)
    print("""
PRIMARY DATABASE: music.db
- Là database chính
- Dữ liệu từ nó được ưu tiên
- Tất cả bảng khác sẽ hợp nhất vào nó

MERGE PLAN:
1. Giữ tất cả dữ liệu từ music.db (ưu tiên)
2. Thêm các bảng từ database khác (nếu chưa có)
3. Gộp dữ liệu từ bảng có cùng tên (nếu cần)
4. Xóa file database cũ (backup trước)

TABLES CẦN HỢP NHẤT:
""")
    
    primary_db = 'backend/src/database/music.db'
    primary_tables = database_info.get(primary_db, {})
    
    for table in sorted(all_tables):
        sources = [os.path.basename(db) for db, tables in database_info.items() if table in tables]
        if len(sources) > 1:
            if table in primary_tables:
                print(f"  • {table:25s} - Ưu tiên từ music.db (có {primary_tables[table]['rows']} rows)")
            else:
                print(f"  • {table:25s} - Sẽ thêm vào từ {sources[0]}")
        else:
            print(f"  • {table:25s} - Chỉ có trong {sources[0]}")

if __name__ == "__main__":
    analyze_databases()
