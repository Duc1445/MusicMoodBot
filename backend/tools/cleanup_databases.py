"""
Clean up old databases and create final backup
"""
import shutil
import os
from datetime import datetime

def cleanup_and_backup():
    """Clean up old databases and create backup"""
    
    db_dir = 'backend/src/database'
    primary_db = os.path.join(db_dir, 'music.db')
    
    # Files to delete
    old_files = [
        'backend/src/database/musicmood.db',
        'backend/src/database/music_backup_20260128_081827.db',
        'backend/src/database/music_master_backup_20260128_082458.db',
        'backend/src/database/music_master_backup_20260128_082527.db',
        'backend/src/database/exports/backups/music_backup_20260127_221930.db',
    ]
    
    print("="*80)
    print("🧹 CLEANUP & BACKUP - Xóa Database Rác và Tạo Backup")
    print("="*80)
    
    # Create backup first
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_name = f'music_final_backup_{timestamp}.db'
    backup_path = os.path.join(db_dir, backup_name)
    
    print(f"\n💾 Creating final backup...")
    print(f"   From: {primary_db}")
    print(f"   To:   {backup_path}")
    
    try:
        shutil.copy2(primary_db, backup_path)
        print(f"   ✓ Backup created successfully")
        backup_size = os.path.getsize(backup_path) / 1024
        print(f"   Size: {backup_size:.1f} KB")
    except Exception as e:
        print(f"   ❌ Error creating backup: {e}")
        return
    
    # Delete old files
    print(f"\n🗑️  Deleting old database files...")
    print("-" * 80)
    
    deleted_count = 0
    total_freed = 0
    
    for file_path in old_files:
        if os.path.exists(file_path):
            try:
                size = os.path.getsize(file_path) / 1024
                os.remove(file_path)
                print(f"   ✓ Deleted: {os.path.basename(file_path):45s} ({size:.1f} KB)")
                deleted_count += 1
                total_freed += size
            except Exception as e:
                print(f"   ❌ Error deleting {file_path}: {e}")
        else:
            print(f"   ⏭️  Not found: {os.path.basename(file_path)}")
    
    # Verify primary database still exists
    print(f"\n✅ Verifying primary database...")
    if os.path.exists(primary_db):
        size = os.path.getsize(primary_db) / 1024
        print(f"   ✓ Primary DB intact: {os.path.basename(primary_db)} ({size:.1f} KB)")
    else:
        print(f"   ❌ Primary DB missing!")
        return
    
    # Verify backup exists
    print(f"\n✅ Verifying backup...")
    if os.path.exists(backup_path):
        size = os.path.getsize(backup_path) / 1024
        print(f"   ✓ Backup intact: {backup_name} ({size:.1f} KB)")
    else:
        print(f"   ❌ Backup missing!")
        return
    
    # List remaining databases
    print(f"\n📂 Remaining database files:")
    remaining = []
    for root, dirs, files in os.walk(db_dir):
        for file in files:
            if file.endswith('.db'):
                path = os.path.join(root, file)
                rel_path = os.path.relpath(path, db_dir)
                size = os.path.getsize(path) / 1024
                remaining.append((rel_path, size))
                print(f"   ✓ {rel_path:50s} ({size:.1f} KB)")
    
    print("\n" + "="*80)
    print("📊 SUMMARY:")
    print("="*80)
    print(f"""
✅ Cleanup Results:
   • Files deleted: {deleted_count}
   • Space freed: {total_freed:.1f} KB
   • Primary DB: music.db (preserved)
   • Backup created: {backup_name}

📂 Database Location:
   Primary: backend/src/database/music.db
   Backup:  backend/src/database/{backup_name}

✨ Database is now clean and organized!
""")

if __name__ == "__main__":
    cleanup_and_backup()
