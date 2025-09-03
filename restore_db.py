import os
import sys

def restore_database(backup_file):
    """Restore database from backup"""
    if not os.path.exists(backup_file):
        print(f"❌ Backup file {backup_file} not found!")
        return False
    
    # Backup current db before restore
    if os.path.exists('instance/inventory.db'):
        shutil.copy2('instance/inventory.db', 'instance/inventory_before_restore.db')
    
    # Restore
    shutil.copy2(backup_file, 'instance/inventory.db')
    print(f"✅ Database restored from {backup_file}")
    return True

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python restore_db.py backup_filename.db")
    else:
        restore_database(sys.argv[1])