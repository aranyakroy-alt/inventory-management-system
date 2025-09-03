#!/usr/bin/env python3
"""
Phase 6A Database Migration - Complete Script
Backs up database, adds User tables, creates admin user
"""

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

def migrate_to_phase6():
    """Add Phase 6 user tables and create admin user"""
    
    # Import here to avoid issues if models don't exist yet
    from app import app, db
    from models import User, UserRole
    
    with app.app_context():
        print("🔄 Creating Phase 6 database tables...")
        
        # Create all tables (including new User table)
        db.create_all()
        print("✅ Database tables created")
        
        # Check if admin user exists
        existing_admin = User.query.filter_by(username='admin').first()
        
        if not existing_admin:
            # Create default admin user
            admin = User(
                username='admin',
                email='admin@inventory.com',
                first_name='System',
                last_name='Administrator', 
                role=UserRole.ADMIN,
                is_active=True
            )
            admin.set_password('admin123')
            
            db.session.add(admin)
            db.session.commit()
            
            print("✅ Admin user created:")
            print("   Username: admin")
            print("   Password: admin123")
        else:
            print("ℹ️  Admin user already exists")
        
        print("🎉 Phase 6A migration complete!")

def run_phase6_migration():
    """Complete Phase 6A setup: backup + migrate"""
    
    print("🚀 Starting Phase 6A Migration...")
    print("=" * 50)
    
    # Step 1: Backup
    print("Step 1: Creating backup...")
    backup_name = backup_database()
    if not backup_name:
        print("❌ Backup failed - stopping migration")
        return
    
    # Step 2: Migrate
    print("\nStep 2: Migrating to Phase 6A...")
    try:
        migrate_to_phase6()
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        print(f"💡 Restore backup: cp {backup_name} instance/inventory.db")
        return
    
    print("\n🎉 Phase 6A migration successful!")
    print(f"💾 Backup saved as: {backup_name}")
    print("\n🔐 Login with:")
    print("   Username: admin")
    print("   Password: admin123")

if __name__ == '__main__':
    run_phase6_migration()