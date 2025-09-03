import shutil
import os
from datetime import datetime

def backup_database():
    """Simple database backup - just copy the SQLite file"""
    source = 'instance/inventory.db'
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_name = f'backup_inventory_{timestamp}.db'
    
    if os.path.exists(source):
        shutil.copy2(source, backup_name)
        print(f"✅ Database backed up to: {backup_name}")
        return backup_name
    else:
        print("❌ Database file not found!")
        return None

if __name__ == '__main__':
    backup_database()