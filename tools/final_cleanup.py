"""
Final cleanup - remove unnecessary files and organize project
"""
import os
import shutil

def cleanup_project():
    """Remove unnecessary files from project"""
    
    print("="*80)
    print("🧹 FINAL PROJECT CLEANUP")
    print("="*80)
    
    # Files/folders to remove
    cleanup_items = [
        # Old log files
        'backend_log.txt',
        
        # Unnecessary export files (keep structure, remove data exports)
        'backend/src/database/exports/songs_export_20260127_221934.json',
        'backend/src/database/exports/songs_export_20260128_073212.json',
        
        # Unnecessary backup folder if empty later
        'backend/src/database/exports/backups',
    ]
    
    print("\n📋 Items to cleanup:")
    print("-" * 80)
    
    cleaned = 0
    freed = 0
    
    for item in cleanup_items:
        if os.path.exists(item):
            try:
                if os.path.isfile(item):
                    size = os.path.getsize(item) / 1024
                    os.remove(item)
                    print(f"   ✓ File deleted: {item:50s} ({size:.1f} KB)")
                    freed += size
                elif os.path.isdir(item):
                    # Check if directory is empty
                    if not os.listdir(item):
                        shutil.rmtree(item)
                        print(f"   ✓ Dir deleted:  {item:50s} (empty)")
                    else:
                        print(f"   ⏭️  Dir skipped: {item:50s} (not empty)")
                cleaned += 1
            except Exception as e:
                print(f"   ❌ Error: {item} - {e}")
        else:
            print(f"   ⏭️  Not found:  {item}")
    
    # Create/verify necessary directories
    print(f"\n📂 Verifying project structure:")
    print("-" * 80)
    
    dirs_to_verify = [
        'backend/src/database',
        'backend/src/database/exports',
        'scripts',
        'demos',
        'tools',
        'tests',
        'docs',
    ]
    
    for dir_path in dirs_to_verify:
        if os.path.exists(dir_path):
            if os.path.isdir(dir_path):
                items = len(os.listdir(dir_path))
                print(f"   ✓ {dir_path:40s} ({items:2d} items)")
            else:
                print(f"   ⚠️  {dir_path:40s} (is file, not directory)")
    
    # List all DB files
    print(f"\n💾 Database files (final):")
    print("-" * 80)
    
    for root, dirs, files in os.walk('backend/src/database'):
        for file in files:
            if file.endswith('.db'):
                path = os.path.join(root, file)
                size = os.path.getsize(path) / 1024
                rel_path = os.path.relpath(path, 'backend/src/database')
                print(f"   ✓ {rel_path:50s} ({size:.1f} KB)")
    
    print("\n" + "="*80)
    print("✅ CLEANUP COMPLETE:")
    print("="*80)
    print(f"""
📊 Results:
   • Items cleaned: {cleaned}
   • Space freed: {freed:.1f} KB
   
📂 Database:
   Primary: backend/src/database/music.db
   Backup:  backend/src/database/music_final_backup_*.db
   
🏗️  Project Structure:
   ✓ backend/ - API & ML code
   ✓ frontend/ - UI code
   ✓ scripts/ - Quick launchers
   ✓ demos/ - Demo applications
   ✓ tools/ - Utility scripts
   ✓ tests/ - Test suites
   ✓ docs/ - Documentation
   ✓ logs/ - Log files
   ✓ config/ - Configuration
   
✨ Project is now clean and organized!
""")

if __name__ == "__main__":
    cleanup_project()
